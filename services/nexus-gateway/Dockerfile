# ============================================================================
# Nexus Gateway - Production Dockerfile
# Reference: https://docs.nexusglobalpayments.org/
# ============================================================================
# 
# Multi-stage build for optimal image size and security
# Stage 1: Build stage with all dev dependencies
# Stage 2: Runtime stage with only production dependencies

FROM python:3.12-slim AS builder

WORKDIR /app

# Install build dependencies for lxml and other native packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    libxml2-dev \
    libxslt-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first for better caching
COPY pyproject.toml .

# Install dependencies without editable mode
# Use pip-compile or direct install approach
RUN pip install --no-cache-dir pip wheel setuptools hatchling
RUN pip install --no-cache-dir fastapi uvicorn[standard] python-multipart \
    asyncpg sqlalchemy[asyncio] alembic redis aiokafka \
    lxml pydantic-xml pydantic pydantic-settings email-validator \
    python-jose[cryptography] passlib[bcrypt] \
    opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp \
    opentelemetry-instrumentation-fastapi opentelemetry-instrumentation-asyncpg \
    opentelemetry-instrumentation-redis structlog \
    httpx python-dateutil orjson

# ===========================================================================
# Runtime stage
# ===========================================================================

FROM python:3.12-slim AS runtime

WORKDIR /app

# Install only runtime dependencies for lxml
RUN apt-get update && apt-get install -y --no-install-recommends \
    libxml2 \
    libxslt1.1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY src/ ./src/

# Copy XSD schemas (if present in nexus-gateway/specs, otherwise use volume mount)
COPY specs/ ./specs/

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash nexus
USER nexus

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run application
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
