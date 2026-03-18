#!/bin/bash
set -e

echo "Starting API container..."

# Set default values for PostgreSQL connection
POSTGRES_HOST=${POSTGRES_HOST:-postgres}
POSTGRES_PORT=${POSTGRES_PORT:-5432}
POSTGRES_USER=${POSTGRES_USER:-holiday}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-holiday}
POSTGRES_DB=${POSTGRES_DB:-holiday}

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
MAX_ATTEMPTS=30
ATTEMPT=0

until [ $ATTEMPT -ge $MAX_ATTEMPTS ]; do
  if PGPASSWORD="${POSTGRES_PASSWORD}" psql -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -c '\q' 2>/dev/null; then
    echo "✓ PostgreSQL is ready!"
    break
  fi
  ATTEMPT=$((ATTEMPT + 1))
  echo "PostgreSQL is unavailable - attempt $ATTEMPT/$MAX_ATTEMPTS - sleeping"
  sleep 2
done

if [ $ATTEMPT -ge $MAX_ATTEMPTS ]; then
  echo "✗ PostgreSQL failed to respond after $MAX_ATTEMPTS attempts"
  exit 1
fi

# Run init.sql first (creates tables)
echo "Running database initialization..."
PGPASSWORD="${POSTGRES_PASSWORD}" psql -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -f /app/sql/init.sql 2>/dev/null || echo "⚠ Init already applied or SQL file not found, skipping"

# Run migration (alters existing tables)
echo "Running database migration..."
PGPASSWORD="${POSTGRES_PASSWORD}" psql -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -f /app/sql/02_schema_migration.sql 2>/dev/null || echo "⚠ Migration already applied or SQL file not found, skipping"

echo "✓ Database ready!"

# Start the API server
echo "Starting Uvicorn server on 0.0.0.0:8000..."
exec uvicorn src.api.main:app --host 0.0.0.0 --port 8000