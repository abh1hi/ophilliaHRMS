#!/bin/sh
set -e

echo "=== Employee Service Startup ==="
echo "Running Alembic migrations..."
alembic upgrade head
echo "Migrations complete. Starting server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8001
