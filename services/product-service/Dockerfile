FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_HTTP_TIMEOUT=120

WORKDIR /app

COPY pyproject.toml uv.lock ./

COPY services/product-service/pyproject.toml services/product-service/
COPY services/product-service/README.md services/product-service/
COPY services/product-service/src services/product-service/src
COPY shared /app/shared

RUN uv sync \
    --package product-service \
    --frozen \
    --no-dev


FROM python:3.13-slim-bookworm AS runner

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/services/product-service/src /app/services/product-service/src
COPY --from=builder /app/shared /app/shared

ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app:/app/services/product-service/src"

EXPOSE 50051

CMD ["product-service"]