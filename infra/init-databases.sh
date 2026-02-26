#!/bin/bash
set -e

# Wait for PostgreSQL to be ready before creating databases
until pg_isready -U postgres; do
  echo "Waiting for PostgreSQL to be ready..."
  sleep 1
done

echo "PostgreSQL is ready. Creating separate databases for Option B Architecture..."

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    SELECT 'CREATE DATABASE auth_db'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'auth_db')\gexec

    SELECT 'CREATE DATABASE employee_db'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'employee_db')\gexec

    SELECT 'CREATE DATABASE attendance_db'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'attendance_db')\gexec

    SELECT 'CREATE DATABASE students_db'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'students_db')\gexec
EOSQL

echo "Databases created successfully:"
psql -U "$POSTGRES_USER" -lqt | cut -d \| -f 1 | grep -w -E "auth_db|employee_db|attendance_db|students_db"
