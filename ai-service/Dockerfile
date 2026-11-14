# ==============================================================================
# NexGrad AI Microservice Dockerfile (Multi-stage Python 3.12/3.14 slim image)
# ==============================================================================

FROM python:3.12-slim AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --user --no-warn-script-location -r requirements.txt

# Final Runtime Image
FROM python:3.12-slim AS runner

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8001

# Create non-root system user
RUN groupadd -g 1001 aiuser && \
    useradd -u 1001 -g aiuser -m -s /bin/bash aiuser

COPY --from=builder /root/.local /home/aiuser/.local
ENV PATH=/home/aiuser/.local/bin:$PATH

COPY --chown=aiuser:aiuser . /app/

USER aiuser

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]

