#!/bin/sh
set -e

echo "=== Onboarding Service Startup ==="

# Wait for PostgreSQL to accept connections
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
  -w 1 \
  --bind 0.0.0.0:8008 \
  --timeout 60 \
  --graceful-timeout 15 \
  --log-level warning
