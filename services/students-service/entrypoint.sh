#!/bin/sh

echo "Waiting for PostgreSQL..."
while ! nc -z hrms-db 5432; do
  sleep 0.1
done
echo "PostgreSQL started"

echo "Waiting for RabbitMQ..."
while ! nc -z rabbitmq 5672; do
  sleep 0.1
done
echo "RabbitMQ started"

echo "Running Alembic migrations..."
alembic upgrade head

echo "Starting students-service..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8003 --proxy-headers
