import asyncio
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI
import aio_pika
from shared.telemetry import setup_telemetry
from fastapi import FastAPI
from opentelemetry import propagate, trace

tracer = trace.get_tracer(__name__)

# Mock Database for Inventory
inventory_db = {
    99: {"name": "Super Fast Laptop", "stock": 10},
    15: {"name": "Nike dunk 2", "stock": 12},
}

async def process_message(message: aio_pika.abc.AbstractIncomingMessage):
    try:
        # Extract the trace context that order-service
        # injected into the RabbitMQ message.
        headers = dict(message.headers or {})
        context = propagate.extract(headers)

        # Create a consumer span whose parent is
        # the order-service messaging span.
        with tracer.start_as_current_span(
            "inventory.process_message",
            context=context,
        ) as span:
            event_data = json.loads(
                message.body.decode()
            )
            span.set_attribute(
                "messaging.system",
                "rabbitmq",
            )
            span.set_attribute(
                "messaging.destination.name",
                message.routing_key,
            )
            print(event_data)

            event_data = json.loads(message.body.decode())
            print(f"📦 Received Event: {event_data}")

            product_id = event_data.get("product_id")

            # SIMULATE A FATAL ERROR
            if product_id == 999:
                print("❌ Fatal error: Simulated crash! Rejecting message.")

                # Reject the message and DO NOT requeue it
                # This triggers the Dead Letter Exchange (DLX)
                await message.reject(requeue=False)
                return

            # Normal business logic
            if product_id in inventory_db and inventory_db[product_id]["stock"] > 0:
                inventory_db[product_id]["stock"] -= 1
                print(f"✅ Stock reduced! Remaining stock for product {product_id}: {inventory_db[product_id]['stock']}")
            else:
                print(f"❌ Out of stock or invalid product: {product_id}")

            # Manually acknowledge the message was processed successfully
            await message.ack()
    except Exception as e:
        span.record_exception(e)
        span.set_status(
            trace.Status(
                trace.StatusCode.ERROR,
                str(e)
            )
        )
        print(f"❌ Error processing message: {e}")
        # If any Python error occurs, safely dead-letter the message
        await message.reject(requeue=False)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Connect to RabbitMQ with retry
    for i in range(5):
        try:
            connection = await aio_pika.connect_robust("amqp://guest:guest@rabbitmq:5672/")
            channel = await connection.channel()
            break
        except Exception as e:
            print(f"RabbitMQ not ready yet, retrying in 2 seconds (attempt {i+1}/5)...")
            await asyncio.sleep(2)
    else:
        raise Exception("Failed to connect to RabbitMQ after 5 attempts")

    # 2. Declare the Dead Letter Exchange (DLX) and Dead Letter Queue (DLQ)
    dlx = await channel.declare_exchange("dlx", aio_pika.ExchangeType.DIRECT)
    dlq = await channel.declare_queue("order_events_dlq", durable=True)
    await dlq.bind(dlx, routing_key="order_events")

    # 3. Declare the main queue and tell it to route failures to the DLX
    queue = await channel.declare_queue(
        "order_events",
        durable=True,
        arguments= {
                "x-dead-letter-exchange": "dlx",
                "x-dead-letter-routing-key": "order_events",
            }
    )

    # Bind order_events to the orders exchange
    order_exchange = await channel.declare_exchange(
        "orders",
        aio_pika.ExchangeType.DIRECT,
        durable=True
    )
    await queue.bind(
        order_exchange,
        routing_key="order_events"
    )

    # 4. Consume messages
    await queue.consume(process_message)
    print("🎧 Inventory Service is now listening for order events...")

    yield

    await connection.close()

app = FastAPI(
    lifespan=lifespan,
    telemetry={"auto_configure": False},
)

setup_telemetry(app, "inventory-service")

# A simple endpoint to check current stock
@app.get("/inventory/{product_id}")
def get_stock(product_id: int):
    return inventory_db.get(product_id, {"error": "Product not found"})