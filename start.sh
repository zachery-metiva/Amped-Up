#!/bin/bash
set -e

echo "=== PORT=${PORT} ==="
echo "=== DATABASE_URL set: $([ -n "$DATABASE_URL" ] && echo yes || echo NO) ==="

echo "=== Running Alembic migrations ==="
python -m alembic upgrade head
echo "=== Migrations complete ==="

echo "=== Starting uvicorn on port ${PORT:-8000} ==="
exec python -m uvicorn backend.main:app --host 0.0.0.0 --port "${PORT:-8000}"
