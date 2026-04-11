#!/bin/sh
set -e

echo "=== Employee Service Startup ==="

# DB readiness is guaranteed by Docker Compose `depends_on: condition: service_healthy`
# on the hrms-db service. No nc polling loop needed.
echo "Running Alembic migrations..."
alembic upgrade head
echo "Migrations complete. Starting server..."

exec gunicorn app.main:app \
  -k uvicorn.workers.UvicornWorker \
  -w 1 \
  --bind 0.0.0.0:8001 \
  --timeout 60 \
  --graceful-timeout 15 \
  --log-level warning
