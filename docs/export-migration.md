# Export & Migration Guide

vDrive's bulk export and migration tools give you complete control over your data. Download all your photos, galleries, and metadata in one operation, or easily migrate from competitor platforms.

## Why Data Freedom Matters

Unlike other platforms that lock you in, vDrive believes your data should always be accessible:

- **No Manual Downloads** - Export thousands of photos in one click
- **Preserve Organization** - Gallery structure and metadata maintained
- **Easy Migration** - Import from Pixieset, Pic-Time, ShootProof, and more
- **No Platform Lock-in** - Your data, your choice

## Bulk Export

### What Gets Exported?

When you create an export, you get:

- ✅ Original high-resolution files
- ✅ All metadata (EXIF, titles, descriptions, tags)
- ✅ Gallery organization and folder structure
- ✅ Thumbnails (optional)
- ✅ Face tags and AI data (optional)

### Export Options

#### 1. Workspace Export
Export everything from your entire workspace:

- All galleries and photos
- All metadata and organization
- Complete backup of your work

**Best for:** Full backups, platform migration, archival

**Typical size:** 10GB - 500GB depending on workspace size

#### 2. Gallery Export
Export a specific gallery:

- All photos in the gallery
- Gallery metadata and settings
- Folder structure preserved

**Best for:** Delivering client galleries, selective backups

**Typical size:** 500MB - 50GB depending on gallery size

#### 3. Selection Export
Export custom selection of photos:

- Choose specific photos across galleries
- Includes metadata for selected photos
- Flat structure or organized by gallery

**Best for:** Creating collections, sharing specific images

**Typical size:** 100MB - 10GB depending on selection

### How to Create an Export

1. **Navigate to Export Page**
   - Click "Export" in the main navigation
   - Or go to Settings → Data & Export

2. **Choose Export Type**
   - Select workspace, gallery, or selection
   - Configure options (metadata, thumbnails)

3. **Confirm and Create**
   - Review export details
   - Click "Create Export"
   - Job starts processing

4. **Download Your Files**
   - Receive notification when ready (typically 5-30 minutes)
   - Download ZIP file via secure link
   - Link expires after 72 hours

### Export File Structure

Your export ZIP contains organized folders:

```
workspace-export-2024-01-16/
├── galleries/
│   ├── wedding-sarah-john/
│   │   ├── photos/
│   │   │   ├── IMG_001.jpg
│   │   │   ├── IMG_002.jpg
│   │   │   └── ...
│   │   ├── thumbnails/          # If included
│   │   │   ├── IMG_001_thumb.jpg
│   │   │   └── ...
│   │   └── gallery-metadata.json
│   ├── engagement-session/
│   │   └── ...
│   └── ...
├── metadata/
│   ├── workspace.json           # Workspace settings
│   ├── galleries.json           # All gallery metadata
│   └── assets.json              # Photo metadata with EXIF
└── README.txt                   # Export information
```

### Metadata Files

#### workspace.json
```json
{
  "workspace_id": "ws_abc123",
  "name": "Jane's Photography Studio",
  "created_at": "2023-01-15T10:00:00Z",
  "export_date": "2024-01-16T15:30:00Z",
  "total_galleries": 127,
  "total_assets": 45230
}
```

#### galleries.json
```json
[
  {
    "gallery_id": "gal_xyz789",
    "name": "Sarah & John Wedding",
    "slug": "sarah-john-wedding",
    "created_at": "2023-06-15T10:00:00Z",
    "photo_count": 342,
    "settings": {
      "is_public": true,
      "password_protected": false
    }
  }
]
```

#### assets.json
```json
[
  {
    "asset_id": "ast_123",
    "filename": "IMG_001.jpg",
    "gallery": "sarah-john-wedding",
    "size_bytes": 5242880,
    "width": 4000,
    "height": 3000,
    "captured_at": "2023-06-15T14:30:00Z",
    "camera": "Canon EOS R5",
    "lens": "RF 24-70mm F2.8",
    "exif": {
      "iso": 400,
      "aperture": "f/2.8",
      "shutter_speed": "1/500",
      "focal_length": "50mm"
    },
    "tags": ["ceremony", "bride", "outdoor"],
    "faces": [
      {
        "name": "Sarah",
        "confidence": 0.98
      }
    ]
  }
]
```

### Export Limits & Processing Time

| Workspace Size | Estimated Time | Download Size |
|----------------|----------------|---------------|
| < 1,000 photos | 5-10 minutes | < 5 GB |
| 1,000 - 5,000 photos | 10-30 minutes | 5-25 GB |
| 5,000 - 20,000 photos | 30-90 minutes | 25-100 GB |
| 20,000+ photos | 1-3 hours | 100GB+ |

**Note:** Export files are stored for 72 hours. After expiration, you can create a new export at any time.

## Platform Migration

### Supported Platforms

Import your galleries and photos from these platforms:

| Platform | API Support | Gallery Import | Metadata Import | Notes |
|----------|-------------|----------------|-----------------|-------|
| **Pixieset** | ✅ Yes | ✅ Yes | ✅ Yes | Full API access |
| **Pic-Time** | ✅ Yes | ✅ Yes | ✅ Yes | Full API access |
| **ShootProof** | ✅ Yes | ✅ Yes | ⚠️ Partial | Limited metadata |
| **Zenfolio** | ✅ Yes | ✅ Yes | ✅ Yes | Full API access |
| **SmugMug** | ✅ Yes | ✅ Yes | ✅ Yes | OAuth required |

### How Migration Works

1. **Connect Your Account**
   - Provide platform credentials (API key or login)
   - vDrive securely authenticates
   - Your credentials are not stored after migration

2. **Select Galleries**
   - Choose which galleries to import
   - Or import all galleries at once
   - Preview gallery structure

3. **Start Migration**
   - Migration begins processing
   - Photos downloaded from source platform
   - Galleries created in vDrive
   - Metadata preserved

4. **Track Progress**
   - Real-time progress updates
   - See which gallery is currently importing
   - Estimated time remaining
   - Pause or cancel if needed

### Migration Steps by Platform

#### Pixieset Migration

1. **Get API Key**
   - Log into Pixieset
   - Go to Account Settings → API
   - Click "Generate API Key"
   - Copy the key

2. **Start Migration in vDrive**
   - Navigate to Export → Import from Platform
   - Select "Pixieset"
   - Paste your API key
   - Click "Connect"

3. **Import Galleries**
   - Review list of galleries
   - Select galleries to import (or "Select All")
   - Configure import options
   - Click "Start Migration"

4. **Wait for Completion**
   - Migration processes in background
   - Receive notification when complete
   - Galleries appear in your workspace

**Estimated time:** 10-15 minutes per 1,000 photos

#### Pic-Time Migration

1. **Get Credentials**
   - You'll need your Pic-Time username and password
   - Or generate an API token in Pic-Time settings

2. **Start Migration in vDrive**
   - Navigate to Export → Import from Platform
   - Select "Pic-Time"
   - Enter username and password (or API token)
   - Click "Connect"

3. **Import Galleries**
   - Select galleries to import
   - Choose import options
   - Click "Start Migration"

**Estimated time:** 12-18 minutes per 1,000 photos

#### ShootProof Migration

1. **Get Session Token**
   - Log into ShootProof
   - Go to Settings → API Access
   - Generate session token
   - Copy the token

2. **Start Migration in vDrive**
   - Navigate to Export → Import from Platform
   - Select "ShootProof"
   - Paste session token
   - Click "Connect"

3. **Import Events**
   - ShootProof calls them "events" (same as galleries)
   - Select events to import
   - Click "Start Migration"

**Note:** ShootProof has limited metadata API, so some photo details may not transfer.

**Estimated time:** 15-20 minutes per 1,000 photos

#### Zenfolio Migration

1. **Get API Key**
   - Log into Zenfolio
   - Go to Account → API Access
   - Create new API application
   - Copy API key

2. **Start Migration in vDrive**
   - Navigate to Export → Import from Platform
   - Select "Zenfolio"
   - Enter API key
   - Click "Connect"

3. **Import PhotoSets**
   - Review your PhotoSets (galleries)
   - Select which to import
   - Click "Start Migration"

**Estimated time:** 10-15 minutes per 1,000 photos

#### SmugMug Migration

1. **Authorize vDrive**
   - Navigate to Export → Import from Platform
   - Select "SmugMug"
   - Click "Connect with SmugMug"
   - Authorize vDrive in SmugMug popup

2. **Import Albums**
   - Review your SmugMug albums
   - Select albums to import
   - Click "Start Migration"

**Note:** SmugMug uses OAuth, so you don't need to copy/paste API keys.

**Estimated time:** 10-12 minutes per 1,000 photos

### What Gets Migrated?

#### Photos
- ✅ Original high-resolution files
- ✅ File names preserved
- ✅ Upload date preserved
- ✅ EXIF data (if available)

#### Galleries
- ✅ Gallery names
- ✅ Gallery descriptions
- ✅ Folder structure
- ✅ Gallery organization
- ⚠️ Gallery settings (privacy, passwords) - must be reconfigured

#### Metadata
- ✅ Photo titles
- ✅ Photo descriptions
- ✅ Photo tags (if supported by platform)
- ⚠️ Client information - not imported
- ❌ Order history - not imported
- ❌ Analytics data - not imported

### Migration Limitations

**What Doesn't Migrate:**
- Client contact information
- Purchase/order history
- Payment information
- Analytics and view data
- Custom branding/templates
- E-commerce settings
- Client favorites/selections
- Comments and feedback
- Download history

**These must be manually reconfigured in vDrive after migration.**

### Troubleshooting Migration

#### Authentication Failed

**Problem:** "Invalid credentials" or "Authentication failed"

**Solutions:**
- Verify API key is copied correctly (no extra spaces)
- Check if API key has expired
- Ensure API access is enabled in source platform
- For OAuth platforms (SmugMug), try re-authorizing

#### Migration Stuck or Slow

**Problem:** Migration shows no progress for 10+ minutes

**Solutions:**
- Check your internet connection
- Source platform may be rate-limiting requests
- Large galleries take longer (this is normal)
- Cancel and retry if stuck for 30+ minutes

#### Missing Photos

**Problem:** Some photos didn't import

**Solutions:**
- Check if photos were in hidden/private galleries
- Source platform may have deleted files
- Large files (>50MB) may timeout - contact support
- Check migration logs for specific errors

#### Metadata Missing

**Problem:** Photo titles, descriptions, or tags missing

**Solutions:**
- Source platform may not support metadata export
- Metadata may be stored differently on source platform
- Some platforms have limited API metadata access
- ShootProof has known metadata limitations

#### Gallery Structure Changed

**Problem:** Folder organization different after import

**Solutions:**
- Different platforms organize galleries differently
- vDrive uses flat gallery structure (no nested folders)
- Folders may be imported as separate galleries
- You can reorganize after import

## Best Practices

### Before Exporting

1. **Clean up workspace** - Delete unwanted photos to reduce export size
2. **Organize galleries** - Ensure galleries are properly named and organized
3. **Check storage** - Ensure you have enough space for download
4. **Schedule exports** - Create exports during off-peak hours for faster processing

### Before Migrating

1. **Backup source platform** - Create backup before migration starts
2. **Review galleries** - Decide which galleries to migrate
3. **Document settings** - Note custom settings that won't migrate
4. **Clean source data** - Delete unwanted galleries before migration
5. **Test small first** - Migrate 1-2 galleries to test before full migration

### After Migration

1. **Verify galleries** - Check all galleries imported correctly
2. **Spot-check photos** - Open random photos to verify quality
3. **Reconfigure settings** - Set gallery privacy, passwords, etc.
4. **Update client links** - Send new gallery URLs to clients
5. **Keep source active** - Don't delete source platform immediately

## Security & Privacy

### Data Security

- All exports are encrypted in transit (HTTPS)
- Export links are secure and expire after 72 hours
- Only you can access your export files
- Export files are automatically deleted after expiration

### Migration Security

- Platform credentials are used once and not stored
- All data transfer is encrypted (HTTPS)
- No data is shared with third parties
- Source platform data is not modified (read-only access)

### Compliance

- **GDPR** - Request deletion of export data at any time
- **Privacy** - Export/migration data is not used for any other purpose
- **Retention** - Export files deleted after 72 hours
- **Audit** - All export/migration events are logged

## API Access

Developers can access export functionality via API:

```bash
# Create export
curl -X POST https://app.vdrive.io/api/v1/export/jobs \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "export_type": "workspace",
    "options": {
      "include_metadata": true,
      "include_thumbnails": false
    }
  }'

# Get export status
curl -X GET https://app.vdrive.io/api/v1/export/jobs/{job_id} \
  -H "Authorization: Bearer YOUR_TOKEN"

# Download export
# Use file_url from status response
curl -X GET {file_url} -O
```

Full API documentation: https://app.vdrive.io/docs

## Frequently Asked Questions

### How long do export links last?

Export links expire after 72 hours. After expiration, you can create a new export at any time. There's no limit on how many exports you can create.

### Can I export to Google Drive or Dropbox?

Currently, exports download as ZIP files. You can then upload the ZIP to Google Drive, Dropbox, or any cloud storage. Direct integration is planned for future releases.

### How much does export cost?

Bulk export is included free with all vDrive plans. There are no additional charges for creating exports or migrations.

### Can I schedule automatic exports?

Not yet, but this feature is planned. Currently, you must manually create exports. You can create exports as often as you like.

### What if my export is too large?

If your workspace is very large (100GB+), consider:
- Exporting galleries individually instead of entire workspace
- Excluding thumbnails to reduce size
- Contacting support for assistance with large exports

### Do migrations count against my storage?

Yes, migrated photos count toward your storage quota, just like uploaded photos. Upgrade your plan if you need more storage.

### Can I migrate from multiple platforms?

Yes! You can run multiple migrations from different platforms. They can even run simultaneously.

### What happens to my source platform data?

Migration uses read-only access - your source platform data is not modified or deleted. You can keep using the source platform during and after migration.

### Can I cancel a migration in progress?

Yes, click "Cancel" on the migration status page. Photos already migrated will remain in vDrive. You can restart or resume later.

### How do I migrate from a platform not listed?

Contact support at support@vdrive.io. We're actively adding support for more platforms. In the meantime, you can:
1. Export from source platform (if they offer bulk export)
2. Use vDrive's bulk upload feature
3. Manually upload galleries

## Support

Need help with export or migration?

- **Documentation:** https://docs.vdrive.io
- **Video Tutorials:** https://vdrive.io/tutorials
- **Email Support:** support@vdrive.io
- **Live Chat:** Available in app (bottom-right corner)
- **Community Forum:** https://community.vdrive.io

## Feedback

We're constantly improving export and migration tools. Share your feedback:

- Feature requests: https://feedback.vdrive.io
- Bug reports: support@vdrive.io
- Platform requests: Tell us which platforms to support next!

---

*Last updated: January 16, 2024*
