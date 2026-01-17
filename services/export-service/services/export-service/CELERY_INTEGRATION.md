# Celery Task Dispatch Integration

## Implementation Summary

Integrated Celery task dispatch in the export service to enable asynchronous processing of export jobs.

## Changes Made

### 1. Added Imports
- `AsyncResult` from `celery.result` - For handling Celery task results
- `process_export_job` from `src.app.workers.export_tasks` - The Celery task to dispatch

### 2. Implemented `_dispatch_export_task()` Method
**Location:** `ExportService._dispatch_export_task()`

**Purpose:** Dispatches a Celery task to process an export job asynchronously.

**Behavior:**
- Uses `process_export_job.apply_async()` to queue the task
- Routes to the "exports" queue with "export.process" routing key
- Returns an `AsyncResult` with the task ID for tracking
- Logs task dispatch with export_id and celery_task_id
- Handles exceptions gracefully and returns None on failure

### 3. Implemented `_cancel_export_task()` Method
**Location:** `ExportService._cancel_export_task()`

**Purpose:** Cancels a running Celery task for an export job.

**Behavior:**
- Logs the cancellation request
- Returns True if cancellation was attempted
- Includes TODO comment for production implementation (storing task_id in export_job model)
- Note: The export job status is the source of truth - workers will check it before/during processing

### 4. Updated `create_export_job()` Method
**Changes:**
- Removed TODO comment
- Added call to `_dispatch_export_task(export_job.id)` after committing the export job
- Added `celery_task_id` to the logging context
- Task dispatch happens after database commit to ensure job exists

### 5. Updated `cancel_export_job()` Method
**Changes:**
- Removed TODO comment
- Added call to `_cancel_export_task(export_id)` after updating job status

## Verification Steps

### Manual Verification (Requires Docker Environment)

1. **Start required services:**
   ```bash
   cd infrastructure/docker
   docker compose up -d redis postgres
   ```

2. **Start export service:**
   ```bash
   cd infrastructure/docker
   docker compose up -d export-service
   ```

3. **Start Celery worker:**
   ```bash
   cd infrastructure/docker
   docker compose up -d export-worker
   ```

4. **Create an export job via API:**
   ```bash
   # Get auth token first
   export TOKEN="your-jwt-token"

   # Create export job
   curl -X POST http://localhost:8009/api/v1/export/jobs \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "export_type": "workspace",
       "options": {
         "include_metadata": true
       }
     }'
   ```

5. **Verify Celery task is dispatched:**
   ```bash
   # Check export service logs
   docker compose logs -f export-service | grep "Dispatched Celery task"

   # Check Celery worker logs
   docker compose logs -f export-worker | grep "Processing export job"
   ```

6. **Verify job status updates:**
   ```bash
   # Get export job status
   export EXPORT_ID="export-job-id-from-step-4"
   curl http://localhost:8009/api/v1/export/jobs/$EXPORT_ID \
     -H "Authorization: Bearer $TOKEN"

   # Should see status progress: pending → processing → completed
   ```

### Expected Behavior

1. **When export job is created:**
   - Export job record is created in database with status "pending"
   - Celery task is dispatched to "exports" queue
   - Export service logs show: `Dispatched Celery task for export {export_id}`
   - Response includes all export job details

2. **When Celery worker picks up task:**
   - Worker logs show: `Processing export job {export_id}`
   - Job status updates to "processing"
   - Worker fetches assets, creates ZIP, uploads to R2
   - Job status updates to "completed" with file URL

3. **When export job is cancelled:**
   - Job status updates to "cancelled" in database
   - Cancel method logs: `Cancellation requested for export {export_id}`
   - Worker checks job status and stops processing if cancelled

### Error Scenarios

1. **Celery broker (Redis) unavailable:**
   - Task dispatch logs error
   - Returns None from `_dispatch_export_task()`
   - Export job remains in "pending" status
   - Job can be retried later

2. **Worker not running:**
   - Task is queued in Redis
   - Worker will process it when it starts
   - Job remains in "pending" status until worker picks it up

3. **Worker fails during processing:**
   - Worker retries up to 3 times with exponential backoff
   - If all retries fail, job status updates to "failed"
   - Error message is stored in export_job.error_message

## Integration Points

### Export Service → Celery Queue
- **Method:** `ExportService._dispatch_export_task()`
- **Queue:** "exports"
- **Routing Key:** "export.process"
- **Task:** `src.app.workers.export_tasks.process_export_job`

### Celery Worker → Export Repository
- **Worker reads:** Job details (workspace_id, export_type, options)
- **Worker updates:** Status, progress, file_url, file_size, expires_at
- **Worker writes:** Error messages on failure

## Future Enhancements

1. **Store Celery task_id in export_job model:**
   ```python
   # Add to ExportJob model
   celery_task_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
   ```

2. **Implement proper task cancellation:**
   ```python
   # In _cancel_export_task()
   from src.app.workers.celery_app import celery_app
   celery_app.control.revoke(task_id, terminate=True)
   ```

3. **Add task progress callbacks:**
   - Update job progress in real-time as assets are processed
   - Use Celery task state updates

4. **Add priority queue support:**
   - High-priority exports (small galleries) → exports_priority queue
   - Large exports → exports queue

## Testing

### Unit Tests (Future)
```python
# tests/unit/test_export_service.py
def test_dispatch_export_task():
    # Mock Celery task
    # Verify task is dispatched with correct arguments
    pass

def test_dispatch_export_task_failure():
    # Mock Celery task to raise exception
    # Verify error is logged and None is returned
    pass
```

### Integration Tests (Future)
```python
# tests/integration/test_celery_integration.py
def test_export_job_end_to_end():
    # Create export job
    # Verify task is dispatched
    # Wait for worker to process
    # Verify job status updates to completed
    pass
```
