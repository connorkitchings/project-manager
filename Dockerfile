# Stage 1: Frontend build
FROM node:20-slim AS frontend

WORKDIR /app/ui

COPY ui/package.json ui/package-lock.json ./
RUN npm ci

COPY ui/ ./
RUN npm run build

# Stage 2: Python builder
FROM python:3.11-slim AS builder

RUN pip install uv

WORKDIR /app

COPY pyproject.toml uv.lock* ./
COPY src/ src/

RUN uv venv && . .venv/bin/activate && uv sync --no-dev

# Stage 3: Runtime
FROM python:3.11-slim AS runtime

WORKDIR /app

RUN useradd --create-home --shell /bin/bash appuser

COPY --from=builder /app/.venv ./.venv
COPY src/ src/
COPY config/ config/
COPY --from=frontend /app/ui/dist ui/dist

RUN mkdir -p data && chown -R appuser:appuser /app

USER appuser

ENV PATH="/app/.venv/bin:$PATH"
ENV PORT=8000

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/meta')" || exit 1

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "--threads", "4", "project_manager.api.main:app"]
