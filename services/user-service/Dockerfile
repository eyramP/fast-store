FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_HTTP_TIMEOUT=120

WORKDIR /app

COPY pyproject.toml uv.lock ./

COPY services/user-service/pyproject.toml services/user-service/
COPY services/user-service/README.md services/user-service/
COPY services/user-service/src services/user-service/src

RUN uv sync \
    --package user-service \
    --frozen \
    --no-dev


FROM python:3.13-slim-bookworm AS runner

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/services/user-service/src /app/services/user-service/src
COPY shared /app/shared

ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/services/user-service/src"
ENV PYTHONPATH="/app/services/user-service:/app"

EXPOSE 8000

CMD ["uvicorn", "user_service.main:app", "--host", "0.0.0.0", "--port", "8000"]