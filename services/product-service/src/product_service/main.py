import grpc
from concurrent import futures
from . import product_pb2
from . import product_pb2_grpc
from shared.telemetry import setup_tracer
from opentelemetry.instrumentation.grpc import (
    GrpcInstrumentorServer,
)

setup_tracer("product-service")
GrpcInstrumentorServer().instrument()

class ProductService(product_pb2_grpc.ProductServiceServicer):
    def GetProduct(self, request, context):
        print(f"Received request for product with ID: {request.id}")

        return product_pb2.ProductResponse(
            id=request.id,
            name="Fast Laptop",
            price=1999.99,
        )

def main():

    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10)
    )

    product_pb2_grpc.add_ProductServiceServicer_to_server(
        ProductService(),
        server,
    )

    server.add_insecure_port("[::]:50051")

    server.start()

    print("Product service running on port 50051")

    server.wait_for_termination()


if __name__ == "__main__":
    main()