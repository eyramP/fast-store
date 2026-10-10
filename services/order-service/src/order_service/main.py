import asyncio
import json
from contextlib import asynccontextmanager
import aio_pika
from fastapi import FastAPI
from opentelemetry import propagate
from shared.telemetry import setup_telemetry


# Global connection variable
rabbitmq_connection = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global rabbitmq_connection
    # Connect to RabbitMQ container with retry
    for i in range(5):
        try:
            rabbitmq_connection = await aio_pika.connect_robust("amqp://guest:guest@rabbitmq:5672/")
            break
        except Exception as e:
            print(f"RabbitMQ not ready yet, retrying in 2 seconds (attempt {i+1}/5)...")
            await asyncio.sleep(2)
    else:
        raise Exception("Failed to connect to RabbitMQ after 5 attempts")

    print("Connected to RabbitMQ!")

    # Create the exchange used by Order Service to publish events
    async with rabbitmq_connection.channel() as channel:
            await channel.declare_exchange(
                 "orders",
                 aio_pika.ExchangeType.DIRECT,
                 durable=True
            )
    yield
    # Cleanup on shutdown
    await rabbitmq_connection.close()

app = FastAPI(
    lifespan=lifespan,
    telemetry={"auto_configure": False},
)

setup_telemetry(app, "order-service")

@app.post("/orders/")
async def place_order(product_id: int, user_id: int):
    # 1. Create the event data
    order_event = {
        "event": "OrderPlaced",
        "product_id": product_id,
        "user_id": user_id,
        "status": "pending"
    }

    # 2. Publish to RabbitMQ
    headers = {}
    propagate.inject(headers)

    async with rabbitmq_connection.channel() as channel:
        exchange = await channel.declare_exchange(
             "orders",
             aio_pika.ExchangeType.DIRECT,
             durable=True
        )
        message = aio_pika.Message(
             body=json.dumps(order_event).encode(),
             delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
             content_type="application/json",
             headers=headers
        )
        await exchange.publish(
            message,
            routing_key="order_events",
        )

    # 3. Return instantly!
    return {"message": "Order received and is being processed in the background."}