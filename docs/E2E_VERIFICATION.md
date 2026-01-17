# End-to-End Export Flow Verification Guide

**Date:** 2026-01-16
**Subtask:** subtask-6-3
**Purpose:** Comprehensive verification of the bulk export and migration tools feature

---

## Overview

This guide provides step-by-step instructions for verifying the complete export flow from frontend UI through backend API to Celery worker processing and file download.

## Prerequisites

### 1. Services Running
All services must be running in Docker:
```bash
cd infrastructure/docker
docker compose up -d
```

### 2. Verify Service Health
```bash
# Check all services are running
docker compose ps

# Check export-service health
curl -f http://localhost:8009/health
# Expected: {"status":"healthy","service":"export-service",...}

# Check export-service via Traefik
curl -f http://localhost:80/api/v1/export/health
# Expected: {"status":"healthy",...}

# Check export-worker is running
docker compose logs export-worker | grep "ready"
# Expected: celery@... ready
```

### 3. Database Migrations Applied
```bash
# Check export-service migrations
docker compose exec export-service alembic current
# Expected: 002_migration_jobs (head)

# Verify export_jobs table exists
docker compose exec postgres psql -U vDrive -d vDrive -c "\dt export_jobs"
# Expected: Table "public.export_jobs"

# Verify migration_jobs table exists
docker compose exec postgres psql -U vDrive -d vDrive -c "\dt migration_jobs"
# Expected: Table "public.migration_jobs"
```

### 4. Test User Account
You need a test user account with at least one workspace. If you don't have one:
```bash
# Register via frontend: http://localhost:3000/sign-up
# Complete onboarding: http://localhost:3000/onboarding/workspace
# Or use existing test account
```

---

## Test Case 1: Workspace Export Flow (Full E2E)

### Step 1: Login to Frontend
1. Navigate to: http://localhost:3000/signin
2. Enter credentials for test user
3. Click "Sign In"
4. Verify redirect to Dashboard (http://localhost:3000/dashboard)

**Expected Result:**
- ✅ User successfully logged in
- ✅ Dashboard page loads without errors
- ✅ No console errors in browser DevTools

### Step 2: Navigate to Export Page
1. From Dashboard, click "Export Data" or navigate to: http://localhost:3000/export
2. Verify Export page renders

**Expected Result:**
- ✅ Export page loads with 4 export options displayed
- ✅ "Export All Photos", "Export Gallery", "Create Archive", "Import from Platform" cards visible
- ✅ No console errors
- ✅ Background animations render smoothly

### Step 3: Start Export Wizard
1. Click "Export All Photos" card
2. Verify wizard opens with step indicator

**Expected Result:**
- ✅ ExportWizard component renders
- ✅ Step 1 (Configure) is active
- ✅ Three export type cards displayed: Workspace, Gallery, Selection
- ✅ Options toggles visible: "Include metadata", "Include thumbnails"

### Step 4: Configure Export
1. Select "Workspace" export type (should be selected by default)
2. Toggle "Include metadata" ON (should be default)
3. Toggle "Include thumbnails" OFF (should be default)
4. Click "Next" button

**Expected Result:**
- ✅ Workspace card has selected state (gradient background)
- ✅ Toggle switches work correctly
- ✅ "Next" button is enabled
- ✅ Step 2 (Confirm) becomes active

### Step 5: Confirm Export
1. Review export summary:
   - Export Type: "Workspace Export"
   - Options: "Metadata included"
2. Click "Create Export" button
3. Watch for loading state

**Expected Result:**
- ✅ Summary displays correct configuration
- ✅ "Create Export" button shows loading spinner
- ✅ Success message appears after creation
- ✅ Export job is created

### Step 6: Verify API Request
Open browser DevTools Network tab and check:

**Request:**
```
POST http://localhost/api/v1/export/jobs
Headers:
  Authorization: Bearer <token>
  Content-Type: application/json
Body:
  {
    "export_type": "workspace",
    "options": {
      "include_metadata": true,
      "include_thumbnails": false
    }
  }
```

**Response:**
```json
{
  "id": "uuid-here",
  "workspace_id": "workspace-uuid",
  "user_id": "user-uuid",
  "status": "pending",
  "export_type": "workspace",
  "options": {...},
  "total_assets": 0,
  "processed_assets": 0,
  "file_url": null,
  "file_size": null,
  "error_message": null,
  "expires_at": null,
  "created_at": "2026-01-16T...",
  "updated_at": "2026-01-16T..."
}
```

**Expected Result:**
- ✅ API returns 201 Created status
- ✅ Response includes job ID and initial status "pending"
- ✅ No authentication errors (401)
- ✅ No validation errors (422)

### Step 7: Verify Celery Worker Processes Job
Monitor the export-worker logs:

```bash
# In a separate terminal
docker compose logs -f export-worker
```

**Expected Log Sequence:**
```
[INFO] Task process_export_job[<task-id>] received
[INFO] Starting export job <job-id> processing
[INFO] Fetching workspace assets for workspace <workspace-id>
[INFO] Fetched X assets from gallery service
[INFO] Creating ZIP file for export <job-id>
[INFO] Created ZIP file: /tmp/export-<job-id>.zip (X MB)
[INFO] Uploading export file to R2: exports/<workspace-id>/<job-id>.zip
[INFO] Export file uploaded successfully, size: X bytes
[INFO] Export job <job-id> completed successfully
[INFO] Task process_export_job[<task-id>] succeeded in Xs
```

**Expected Result:**
- ✅ Worker picks up task within 5 seconds
- ✅ Worker fetches assets from gallery service
- ✅ ZIP file is created
- ✅ File is uploaded to R2 storage
- ✅ Job status updated to "completed"
- ✅ No errors or exceptions in logs

### Step 8: Verify Job Status Updates in UI
The ExportProgress component should poll every 2 seconds:

**Status: pending**
- ✅ Yellow/orange status indicator
- ✅ "Pending" text displayed
- ✅ Progress bar at 0%
- ✅ Cancel button visible

**Status: processing** (when worker starts)
- ✅ Blue status indicator
- ✅ "Processing" text displayed
- ✅ Progress bar shows percentage (if total_assets > 0)
- ✅ "Processing X of Y assets" text visible
- ✅ Estimated time remaining displayed
- ✅ Cancel button visible

**Status: completed** (when worker finishes)
- ✅ Green status indicator
- ✅ "Completed" text displayed
- ✅ Progress bar at 100%
- ✅ File size displayed (formatted: "12.5 MB")
- ✅ Download button appears
- ✅ Expiration notice visible ("Expires in 72 hours")

### Step 9: Verify Download Link
1. Click "Download Export" button
2. File should download in browser

**Backend Check:**
```bash
# Verify presigned URL is generated
curl -I "<download-url-from-job>"
# Expected: 200 OK with Content-Type: application/zip
```

**Expected Result:**
- ✅ Download button opens new tab with presigned URL
- ✅ ZIP file downloads successfully
- ✅ File size matches reported size
- ✅ URL has expiration parameter (expires in 1 hour by default)

### Step 10: Verify ZIP File Contents
1. Extract the downloaded ZIP file
2. Verify structure:

**Expected ZIP Structure:**
```
export-<job-id>.zip
├── gallery-name-1/
│   ├── photo1.jpg
│   ├── photo2.jpg
│   └── .metadata/
│       ├── photo1.json
│       └── photo2.json
├── gallery-name-2/
│   ├── photo3.jpg
│   └── .metadata/
│       └── photo3.json
└── README.txt
```

**Expected Result:**
- ✅ ZIP extracts without errors
- ✅ Gallery folder structure preserved
- ✅ All photos are present
- ✅ Metadata JSON files present (if include_metadata was enabled)
- ✅ README.txt with export information included

---

## Test Case 2: Gallery Export Flow

### Steps
1. Navigate to: http://localhost:3000/export
2. Click "Export Gallery"
3. In wizard:
   - Select "Gallery" export type
   - Enter gallery ID or select from dropdown (if implemented)
   - Toggle options as desired
   - Click "Next"
4. Review summary and click "Create Export"
5. Verify progress updates
6. Download and verify ZIP contains only that gallery's photos

**Expected Result:**
- ✅ Only specified gallery exported
- ✅ ZIP contains single gallery folder
- ✅ All other verification steps same as Test Case 1

---

## Test Case 3: Export List View

### Steps
1. Create multiple export jobs (repeat Test Case 1 multiple times)
2. Navigate to export list view (if implemented) or observe ExportList component
3. Verify all jobs are displayed
4. Test status filter dropdown

**Expected Result:**
- ✅ All export jobs for workspace are listed
- ✅ Jobs sorted by created_at DESC (newest first)
- ✅ Status filter works (all, pending, processing, completed, failed, cancelled)
- ✅ Each job shows correct status and progress
- ✅ Pagination works (if more than 10 jobs)

---

## Test Case 4: Export Cancellation

### Steps
1. Start a workspace export (Test Case 1, Steps 1-5)
2. While job is "pending" or "processing", click "Cancel" button
3. Confirm cancellation (if modal appears)
4. Verify job status updates to "cancelled"

**Expected Result:**
- ✅ Cancel button is visible for pending/processing jobs
- ✅ API request sent: DELETE /api/v1/export/jobs/{id}
- ✅ Job status updates to "cancelled" in UI
- ✅ Worker stops processing (if already started)
- ✅ No file is uploaded to R2
- ✅ Download button does not appear

---

## Test Case 5: Error Handling

### 5a. Network Error
1. Stop export-service: `docker compose stop export-service`
2. Try to create export job
3. Verify error message displayed

**Expected Result:**
- ✅ User-friendly error message: "Unable to connect to server"
- ✅ No crash, no blank screen
- ✅ User can retry

### 5b. Worker Failure
1. Simulate worker failure:
```bash
# Modify gallery service to return 500 error temporarily
docker compose exec export-worker pkill -9 celery
```
2. Create export job
3. Restart worker: `docker compose restart export-worker`
4. Verify job retries and eventually completes or fails

**Expected Result:**
- ✅ Worker retries up to 3 times
- ✅ If all retries fail, job status = "failed"
- ✅ Error message displayed in UI
- ✅ User can retry by creating new export

### 5c. Concurrent Export Limit
1. Create 2 export jobs quickly (within 1 second)
2. Try to create a 3rd export job

**Expected Result:**
- ✅ First 2 jobs are accepted
- ✅ 3rd job returns 429 Too Many Requests
- ✅ Error message: "Maximum concurrent exports reached (2)"
- ✅ User must wait for one to complete before starting another

---

## Test Case 6: Multi-Tenancy Verification

### Steps
1. Login as User A (Workspace A)
2. Create export job
3. Note the job ID
4. Logout and login as User B (Workspace B)
5. Try to access User A's export job:
   - Direct API: GET /api/v1/export/jobs/{user-a-job-id}
   - Or try to manipulate URL in frontend

**Expected Result:**
- ✅ User B cannot see User A's export job
- ✅ API returns 404 Not Found (not 403, to avoid leaking existence)
- ✅ User B's export list only shows their workspace's jobs
- ✅ No data leakage between workspaces

---

## Test Case 7: Migration Import Flow

### Steps
1. Navigate to: http://localhost:3000/export
2. Click "Import from Platform"
3. Verify redirect to: http://localhost:3000/migration
4. Verify MigrationWizard renders with 3 steps
5. Select platform (e.g., "Pixieset")
6. Enter credentials (use test API key)
7. Confirm and create migration job
8. Verify progress updates similar to export flow

**Expected Result:**
- ✅ Migration wizard renders correctly
- ✅ 5 platforms available: Pixieset, Pic-Time, ShootProof, Zenfolio, SmugMug
- ✅ Platform-specific credential fields displayed
- ✅ Credential validation works
- ✅ Migration job created successfully
- ✅ Progress updates visible
- ✅ Import completes and photos appear in workspace

---

## Test Case 8: Cleanup of Expired Exports

### Steps
1. Create an export job and let it complete
2. Manually update expires_at to past date:
```bash
docker compose exec postgres psql -U vDrive -d vDrive -c "
UPDATE export_jobs
SET expires_at = NOW() - INTERVAL '1 day'
WHERE id = '<job-id>';
"
```
3. Trigger cleanup task:
```bash
# Either wait for scheduled cleanup (runs hourly)
# Or trigger manually:
docker compose exec export-worker celery -A src.app.workers.celery_app call src.app.workers.export_tasks.cleanup_expired_exports
```
4. Verify job and file are deleted

**Expected Result:**
- ✅ Cleanup task runs successfully
- ✅ Expired export job deleted from database
- ✅ Export file deleted from R2 storage
- ✅ Job no longer appears in UI
- ✅ Download URL returns 404

---

## Performance Benchmarks

### Export Processing Time (approximate)

| Asset Count | File Size | Expected Time |
|-------------|-----------|---------------|
| 10 photos   | 50 MB     | 10-30 seconds |
| 100 photos  | 500 MB    | 1-3 minutes   |
| 1000 photos | 5 GB      | 10-20 minutes |
| 10000 photos| 50 GB     | 2-4 hours     |

**Note:** Times vary based on:
- Network speed (fetching from gallery service)
- CPU (ZIP compression)
- R2 upload speed
- Photo file sizes

---

## Monitoring & Observability

### Prometheus Metrics
Check metrics at: http://localhost:8009/metrics

**Key Metrics:**
```
# Total export jobs created
export_jobs_total{status="completed"} 5
export_jobs_total{status="failed"} 1

# Total assets processed
export_assets_processed_total 1500

# Export job duration (histogram)
export_job_duration_seconds_bucket{le="60"} 3
export_job_duration_seconds_bucket{le="300"} 10

# Active export jobs
export_jobs_active 2
```

### Structured Logs
```bash
# View export-service logs
docker compose logs export-service | grep "export_created"
docker compose logs export-service | grep "export_completed"

# View worker logs
docker compose logs export-worker | grep "process_export_job"
```

---

## Common Issues & Troubleshooting

### Issue: Worker not picking up tasks
**Symptoms:** Jobs stay in "pending" status forever

**Debug:**
```bash
# Check worker is running
docker compose ps export-worker

# Check Redis connection
docker compose exec export-worker celery -A src.app.workers.celery_app inspect ping

# Check worker is registered
docker compose exec export-worker celery -A src.app.workers.celery_app inspect active_queues
```

**Fix:**
```bash
docker compose restart export-worker
```

### Issue: Download URL returns 403 Forbidden
**Symptoms:** Presigned URL doesn't work

**Debug:**
- Check R2 credentials are correct
- Verify file exists in R2 bucket
- Check URL hasn't expired (1 hour default)

**Fix:**
- Regenerate download URL by fetching job status again

### Issue: ZIP file is corrupted
**Symptoms:** Cannot extract downloaded ZIP

**Debug:**
- Check worker logs for errors during ZIP creation
- Verify all photos were fetched successfully
- Check disk space on worker container

**Fix:**
- Cancel failed job and retry
- Check gallery service is returning valid photo data

### Issue: Metadata not included in export
**Symptoms:** .metadata folders are empty

**Debug:**
- Verify include_metadata option was enabled
- Check gallery service returns metadata in asset objects
- Check worker logs for metadata fetch errors

**Fix:**
- Ensure gallery service includes EXIF, tags, faces in API response

---

## Verification Checklist

Use this checklist to confirm all functionality works:

### Backend Services
- [ ] export-service starts successfully
- [ ] export-worker starts successfully
- [ ] Health checks pass (/health, /ready)
- [ ] Metrics endpoint accessible (/metrics)
- [ ] Database migrations applied (export_jobs, migration_jobs tables exist)
- [ ] Traefik routes to export-service correctly

### API Endpoints
- [ ] POST /api/v1/export/jobs creates export job
- [ ] GET /api/v1/export/jobs lists export jobs
- [ ] GET /api/v1/export/jobs/{id} returns job status
- [ ] DELETE /api/v1/export/jobs/{id} cancels job
- [ ] All endpoints require authentication (401 without token)
- [ ] All endpoints enforce workspace isolation

### Frontend UI
- [ ] /export page renders without errors
- [ ] Export wizard opens and navigates between steps
- [ ] Export options are configurable
- [ ] Export job creation works
- [ ] ExportProgress component displays status
- [ ] Progress bar updates in real-time
- [ ] Download button appears when complete
- [ ] Download works and file is valid
- [ ] Cancel button works for pending/processing jobs
- [ ] ExportList component shows all jobs
- [ ] Status filter works correctly
- [ ] /migration page renders without errors
- [ ] Migration wizard works end-to-end

### Celery Workers
- [ ] Worker processes export jobs
- [ ] Worker fetches assets from gallery service
- [ ] Worker creates ZIP files correctly
- [ ] Worker uploads files to R2
- [ ] Worker updates job status correctly
- [ ] Worker handles errors gracefully
- [ ] Worker retries failed tasks
- [ ] Cleanup task deletes expired exports

### Security & Multi-Tenancy
- [ ] JWT authentication required on all endpoints
- [ ] workspace_id enforced in all queries
- [ ] Users cannot access other workspaces' exports
- [ ] Presigned URLs expire after configured time
- [ ] Credentials in migration_jobs are stored securely

### Error Handling
- [ ] Network errors display user-friendly messages
- [ ] Worker failures trigger retries
- [ ] Failed jobs show error messages
- [ ] Concurrent export limit enforced
- [ ] Invalid requests return 422 with clear errors

### Performance
- [ ] Export jobs complete in reasonable time
- [ ] Real-time polling doesn't overload backend
- [ ] Large exports (1000+ photos) complete successfully
- [ ] Memory usage stays within limits
- [ ] No memory leaks in worker

---

## Sign-off

**Date:** _______________
**Tester:** _______________
**Result:** [ ] PASS  [ ] FAIL
**Notes:** _______________

---

## Next Steps After Verification

If all tests pass:
1. Mark subtask-6-3 as completed
2. Proceed to subtask-6-4 (documentation)
3. Update implementation_plan.json
4. Git commit with: "auto-claude: subtask-6-3 - End-to-end export flow verification"

If tests fail:
1. Document failures in build-progress.txt
2. Fix issues in relevant subtasks
3. Re-run verification
4. Do not mark subtask complete until all tests pass
