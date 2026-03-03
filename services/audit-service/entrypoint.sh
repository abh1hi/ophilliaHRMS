#!/bin/sh
set -e

echo "Running Alembic migrations..."
alembic upgrade head

echo "Starting Audit Service on port 8006..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8006
