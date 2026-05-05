FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml ./
RUN uv sync --no-dev --no-install-project

FROM python:3.12-slim

WORKDIR /app

COPY --from=builder /app/.venv .venv

COPY backend/ backend/
COPY frontend/ frontend/
COPY i18n/ i18n/

EXPOSE 8000
CMD ["/app/.venv/bin/uvicorn", "main:app", "--app-dir", "backend", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
