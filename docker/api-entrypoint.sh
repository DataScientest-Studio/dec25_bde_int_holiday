#!/bin/bash
set -e

echo "Starting API container..."

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
until PGPASSWORD="${POSTGRES_PASSWORD}" psql -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -c '\q' 2>/dev/null; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 2
done

echo "PostgreSQL is ready!"

# Run init.sql first (creates tables)
echo "Running database initialization..."
PGPASSWORD="${POSTGRES_PASSWORD}" psql -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -f /app/sql/init.sql || echo "Init already applied, skipping"

# Run migration (alters existing tables)
echo "Running database migration..."
PGPASSWORD="${POSTGRES_PASSWORD}" psql -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -f /app/sql/02_schema_migration.sql || echo "Migration already applied, skipping"

echo "Database ready!"

# Start the API server
exec uvicorn src.api.main:app --host 0.0.0.0 --port 8000