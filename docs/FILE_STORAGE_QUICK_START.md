# Local File Storage - Quick Start Guide

**Feature**: Local File Storage System  
**Status**: ✅ Production Ready  
**Date**: 2025-01-03

## What It Does

All uploaded files are now automatically saved to your server's local filesystem in addition to MongoDB. This means:

- ✅ **View PDFs** directly in browser from search results
- ✅ **Display images** from semantic search
- ✅ **Download original files** anytime
- ✅ **No data loss** - files persist even if database is unavailable

## Quick Examples

### 1. View PDF from Search Results

```svelte
<!-- Frontend: Display PDF link in search results -->
{#if result.mime_type === 'application/pdf'}
  <a href="/api/resources/download/{result.file_id}" target="_blank">
    📄 View PDF
  </a>
{/if}
```

### 2. Display Image

```svelte
<!-- Frontend: Show image from search -->
<img 
  src="/api/resources/download/{result.file_id}" 
  alt={result.file_name}
  class="w-64 h-64 object-cover rounded"
/>
```

### 3. Download Any File

```svelte
<!-- Frontend: Download button -->
<button on:click={() => window.open(`/api/resources/download/${result.file_id}`)}>
  Download Original
</button>
```

## File Organization

```
~/.ai-mcp-toolkit/uploads/
├── {user_id}/
│   └── {year}/
│       └── {month}/
│           ├── abc123-uuid.pdf
│           ├── def456-uuid.jpg
│           └── ghi789-uuid.xlsx
```

**Example**:
```
~/.ai-mcp-toolkit/uploads/
├── 67a1b2c3d4e5f6789abcdef0/
│   └── 2025/
│       └── 01/
│           ├── a1b2c3d4-e5f6-7890-abcd-ef1234567890.pdf
│           └── f9e8d7c6-b5a4-3210-9876-543210fedcba.jpg
```

## API Endpoint

### Download/View File

```http
GET /resources/download/{file_id}
Authorization: Required (session cookie)
```

**Response**:
- Status: `200 OK`
- Headers:
  - `Content-Type`: File's MIME type (e.g., `application/pdf`)
  - `Content-Disposition`: `inline; filename="original-name.pdf"`
  - `Content-Length`: File size in bytes
  - `Cache-Control`: `public, max-age=3600`

**Example**:
```bash
curl http://localhost:8000/resources/download/a1b2c3d4-e5f6-7890 \
  -H "Cookie: session=..."
```

## Configuration

**Environment Variable** (optional):

```bash
# Default: ~/.ai-mcp-toolkit/uploads/
DATA_DIR=~/.ai-mcp-toolkit

# Optional: Custom storage path
# FILE_STORAGE_PATH=/custom/path/to/uploads
```

## How It Works

### Upload Flow

```
1. User uploads file → /resources/upload
2. Generate UUID for file
3. Save to: ~/.ai-mcp-toolkit/uploads/{user_id}/{year}/{month}/{uuid}.ext
4. Process file (text extraction, embeddings)
5. Store metadata in MongoDB with file_id
6. Return success
```

### Download Flow

```
1. User requests file → /resources/download/{file_id}
2. Verify authentication & ownership
3. Retrieve file from local storage
4. Return file with appropriate headers
5. Log access in audit log
```

## Security

- ✅ **Authentication required** - Session-based auth
- ✅ **Ownership verification** - Users see only their files
- ✅ **Admin override** - Admins can access any file
- ✅ **Audit logging** - All downloads logged
- ✅ **User isolation** - Separate directories per user
- ✅ **Safe filenames** - UUID-based (no path traversal)

## Storage Stats

```python
from ai_mcp_toolkit.services.file_storage_service import get_file_storage_service

# Get user's storage usage
file_storage = get_file_storage_service()
stats = file_storage.get_storage_stats(user_id="user123")

# Returns:
{
  "total_files": 45,
  "total_size_bytes": 125829120,
  "total_size_mb": 120.0
}
```

## Backup

### What to Backup

1. **MongoDB** (metadata, embeddings):
   ```bash
   mongodump --uri="mongodb+srv://..." --out=/backup/mongodb/
   ```

2. **Local Files** (original binaries):
   ```bash
   tar -czf uploads-backup-$(date +%Y-%m-%d).tar.gz ~/.ai-mcp-toolkit/uploads/
   ```

### Restore

```bash
# Restore MongoDB
mongorestore --uri="mongodb+srv://..." /backup/mongodb/

# Restore files
tar -xzf uploads-backup-2025-01-03.tar.gz -C ~/
```

## Troubleshooting

### File Not Found

**Error**: `File not found in storage`

**Causes**:
- File was uploaded before this feature was implemented
- File was deleted from filesystem
- Wrong file_id

**Solution**:
- Re-upload the file
- Check `~/.ai-mcp-toolkit/uploads/{user_id}/` directory
- Verify `file_id` in MongoDB resource document

### Permission Denied

**Error**: `Access denied` or `403 Forbidden`

**Causes**:
- Not logged in
- Trying to access another user's file
- Session expired

**Solution**:
- Login again
- Verify you own the resource
- Check session cookie is valid

### Disk Space

**Monitor disk usage**:
```bash
du -sh ~/.ai-mcp-toolkit/uploads/
du -sh ~/.ai-mcp-toolkit/uploads/*/
```

**Clean old files** (manual for now):
```bash
# Find files older than 1 year
find ~/.ai-mcp-toolkit/uploads/ -type f -mtime +365
```

## Files Modified

**New Files**:
- `src/ai_mcp_toolkit/services/file_storage_service.py`
- `LOCAL_FILE_STORAGE.md`
- `docs/FILE_STORAGE_QUICK_START.md`

**Modified Files**:
- `src/ai_mcp_toolkit/services/ingestion_service.py`
- `src/ai_mcp_toolkit/server/http_server.py`
- `ui/src/routes/agents/pdf-extractor/+page.svelte`
- `.env.example`
- `ENHANCEMENT_TASKS.md`

## Next Steps

### For Users
- Upload files normally - they're automatically saved locally
- Use `/api/resources/download/{file_id}` to view/download
- Check storage usage with stats API

### For Developers
- Use `get_file_storage_service()` to interact with storage
- File operations are automatic during upload/delete
- Add file links to UI components (see examples above)

### Future Enhancements
- Cloud storage integration (S3/GCS)
- Per-user storage quotas
- Automatic cleanup policies
- Thumbnail generation for previews
- File versioning

## Support

**Documentation**:
- Complete guide: `LOCAL_FILE_STORAGE.md`
- Task tracking: `ENHANCEMENT_TASKS.md` (Phase 3.7)

**Questions?**
- Check logs: `~/.ai-mcp-toolkit/logs/`
- Storage path: `~/.ai-mcp-toolkit/uploads/`
- Backend logs will show file operations

---

**TL;DR**: Files are now saved locally. Use `/api/resources/download/{file_id}` to view/download them. Everything works automatically. 🎉
