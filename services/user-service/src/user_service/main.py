from fastapi import FastAPI, Depends, status, Response, HTTPException
from contextlib import asynccontextmanager
from .db import engine, get_session
from sqlmodel import SQLModel, Session, select, text
from .models import User, UserPublic
import grpc
from . import product_pb2
from . import product_pb2_grpc
from fastapi.middleware.cors import CORSMiddleware
from . auth import create_access_token, verify_password, hash_password
from shared.jwt_utils import verify_token
from shared.telemetry import setup_telemetry
from opentelemetry.instrumentation.grpc import (
    GrpcInstrumentorClient,
)
from prometheus_fastapi_instrumentator import Instrumentator

@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    yield

app = FastAPI(
    lifespan=lifespan,
    telemetry={"auto_configure": False},
)

# Existing OpenTelemetry tracing
setup_telemetry(app, "user-service")
# Existing gRPC client tracing
GrpcInstrumentorClient().instrument()
# Prometheus HTTP metrics
Instrumentator().instrument(app).expose(
    app,
    endpoint="/metrics",
    include_in_schema=False,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/health")
def health_check():
    return {
        "status": "Ok",
        "service": "User service"
    }

@app.post("/users", response_model=UserPublic)
def create_user(user: User, session: Session = Depends(get_session)):
    user.password = hash_password(user.password)
    session.add(user)
    session.commit()
    session.refresh(user)

    return user

@app.get("/users", response_model=list[UserPublic])
def read_users(session: Session = Depends(get_session)):
    users = session.exec(select(User)).all()
    return users

@app.get("/users/{user_id}/purchases/{product_id}")
def get_user_purchase(user_id: int, product_id: int, token_data: dict = Depends(verify_token)):

    if str(user_id) != token_data.get("sub"):
        raise HTTPException(status_code=403, detail="You are not authrized to access this resource")

    # Connect to the product service via gRPC
    with grpc.insecure_channel("product-service:50051") as channel:
        stub = product_pb2_grpc.ProductServiceStub(channel)

        response = stub.GetProduct(
            product_pb2.ProductRequest(id=product_id),
        )

    return {
        "user_id": user_id,
        "product_details": {
            "id": response.id,
            "name": response.name,
            "price": response.price,
        },
        "source": "gRPC"
    }

@app.post("/login")
def login(user_data: User, session: Session = Depends(get_session)):
    statement = select(User).where(User.email == user_data.email)
    db_user = session.exec(statement).first()

    if not db_user or not verify_password(user_data.password, db_user.password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    token = create_access_token(data={"sub": str(db_user.id), "email": db_user.email})
    return {"access_token": token, "token_type": "bearer"}

@app.get("/health/liveness", tags=["Health"])
def liveness_probe():
    """Checks if the FastAPI server is running."""
    return {"status": "alive"}

@app.get("/health/readiness", tags=["Health"])
def readiness_probe(response: Response, session: Session = Depends(get_session)):
    """Checks if the service is ready to handle traffic (e.g., DB connected)."""
    try:
        # Execute a simple ping to the database
        session.exec(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        # If the DB is unreachable, return a 503 error
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unhealthy", "detail": str(e)}

