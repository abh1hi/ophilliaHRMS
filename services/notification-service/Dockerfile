# ── Stage 1: Build dependencies ──────────────────────────────────────────────
FROM python:3.11-slim AS builder
WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends build-essential libpq-dev && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: Production ─────────────────────────────────────────────────────
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libpq5 curl && rm -rf /var/lib/apt/lists/*
COPY --from=builder /install /usr/local
RUN useradd -m -r appuser && chown -R appuser:appuser /app
USER appuser
COPY --chown=appuser:appuser . .
RUN chmod +x entrypoint.sh
EXPOSE 8007
ENTRYPOINT ["./entrypoint.sh"]
