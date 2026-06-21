# syntax=docker/dockerfile:1

# --- Base: shared Python + uv layer -----------------------------------------
FROM python:3.14-slim AS base
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/
WORKDIR /app

# --- Builder: resolve + install dependencies (cached on lockfile) -----------
FROM base AS builder
COPY pyproject.toml uv.lock* ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --group dev --group test || \
    uv sync --no-install-project --group dev --group test
COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-editable || uv pip install -e .

# --- Dev: hot reload for local development ----------------------------------
# Uses the `todo-api` console script (installed into the venv by `uv sync` in
# the builder); API_RELOAD=1 makes main() start uvicorn with --reload.
FROM base AS dev
COPY --from=builder /opt/venv /opt/venv
COPY . .
ENV API_RELOAD=1
EXPOSE 8000
CMD ["todo-api"]

# --- Prod: lean runtime image -----------------------------------------------
FROM base AS prod
COPY --from=builder /opt/venv /opt/venv
COPY src ./src
COPY migrations ./migrations
RUN useradd --create-home --uid 1000 appuser && chown -R appuser /app
USER appuser
EXPOSE 8000
CMD ["todo-api"]
