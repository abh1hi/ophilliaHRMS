#!/bin/sh
set -e

echo "=== Employee Service Startup ==="

# Wait for PostgreSQL to accept connections (replaces brittle `sleep 5`)
echo "Waiting for database..."
until nc -z hrms-db 5432; do
  sleep 0.5
done
echo "Database ready."

echo "Running Alembic migrations..."
alembic upgrade head
echo "Migrations complete. Starting server..."

exec gunicorn app.main:app \
  -k uvicorn.workers.UvicornWorker \
  -w 2 \
  --bind 0.0.0.0:8001 \
  --timeout 30 \
  --graceful-timeout 10 \
  --log-level warning
