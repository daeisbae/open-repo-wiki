# Dockerfile for OpenRepoWiki ECS Processor
# Base on Python 3.11 slim image for minimal footprint
#
# Requirements: Phase 4 infrastructure

FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY services/processor/requirements.txt /app/services/processor/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/services/processor/requirements.txt

# Copy shared libraries
COPY shared/ /app/shared/

# Copy services module init
COPY services/__init__.py /app/services/__init__.py

# Copy processor code
COPY services/processor/ /app/services/processor/

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app
USER appuser

# Health check (optional - ECS uses task health)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Entry point - run the processor main module
ENTRYPOINT ["python", "-m", "services.processor.main"]
