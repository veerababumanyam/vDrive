#!/bin/bash
# ===========================================
# RawDrive Onboarding Service Docker Entrypoint
# ===========================================
# Runs migrations and seeds test data before starting the app

set -e

echo "=============================================="
echo "  RawDrive Onboarding Service Startup"
echo "=============================================="

# Wait for PostgreSQL to be ready
echo "[1/4] Waiting for PostgreSQL..."
for i in {1..30}; do
    if python -c "
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def check():
    try:
        engine = create_async_engine('$DATABASE_URL')
        async with engine.connect() as conn:
            await conn.execute(text('SELECT 1'))
        await engine.dispose()
        return True
    except:
        return False

exit(0 if asyncio.run(check()) else 1)
" 2>/dev/null; then
        echo "  PostgreSQL is ready!"
        break
    fi
    echo "  Waiting for PostgreSQL... ($i/30)"
    sleep 2
done

# Run Alembic migrations
echo "[2/4] Running database migrations..."
alembic upgrade head
echo "  Migrations complete!"

# Seed test data (only in development)
if [ "${APP_ENV:-development}" = "development" ] || [ "${SEED_TEST_DATA:-false}" = "true" ]; then
    echo "[3/4] Seeding test data..."
    python scripts/seed_test_users.py || echo "  Warning: Seeding failed (users may already exist)"
else
    echo "[3/4] Skipping test data seeding (production mode)"
fi

# Start the application
echo "[4/4] Starting application..."
echo "=============================================="
exec uvicorn src.app.main:app --host 0.0.0.0 --port 8006
