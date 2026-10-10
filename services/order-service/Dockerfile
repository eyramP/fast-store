FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_HTTP_TIMEOUT=120

WORKDIR /app

COPY pyproject.toml uv.lock ./

COPY services/user-service/pyproject.toml services/user-service/
COPY services/product-service/pyproject.toml services/product-service/
COPY services/order-service/pyproject.toml services/order-service/
COPY services/inventory-service/pyproject.toml services/inventory-service/

COPY services/user-service/README.md services/user-service/
COPY services/product-service/README.md services/product-service/
COPY services/order-service/README.md services/order-service/
COPY services/inventory-service/README.md services/inventory-service/

COPY services/order-service/src services/order-service/src
COPY shared shared

RUN uv sync --package order-service --frozen --no-dev

FROM python:3.13-slim-bookworm AS runner

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/services/order-service/src /app/services/order-service/src
COPY --from=builder /app/shared /app/shared

ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app:/app/services/order-service/src"
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["/app/.venv/bin/python", "-m", "uvicorn", "order_service.main:app", "--host", "0.0.0.0", "--port", "8000"]