#!/bin/bash
# Verification script for Celery app configuration
# Run this inside Docker container with: bash verify_celery.sh

echo "=== Celery App Verification ==="
echo ""

echo "1. Testing Celery import..."
python3 -c "from src.app.workers.celery_app import celery_app; print('✓ Import successful')" || exit 1

echo ""
echo "2. Checking Celery configuration..."
python3 -c "
from src.app.workers.celery_app import celery_app
print(f'✓ App name: {celery_app.main}')
print(f'✓ Broker: {celery_app.conf.broker_url}')
print(f'✓ Backend: {celery_app.conf.result_backend}')
print(f'✓ Task serializer: {celery_app.conf.task_serializer}')
print(f'✓ Timezone: {celery_app.conf.timezone}')
" || exit 1

echo ""
echo "3. Pinging Celery workers..."
celery -A src.app.workers.celery_app inspect ping || echo "⚠ No workers running (expected if worker not started)"

echo ""
echo "=== Verification Complete ==="
