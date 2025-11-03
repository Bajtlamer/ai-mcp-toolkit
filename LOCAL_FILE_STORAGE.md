# Local File Storage System

**Date**: 2025-01-03  
**Status**: ✅ Implemented  
**Type**: Core Feature

## Overview

All uploaded files are now stored locally on the server in addition to their metadata being stored in MongoDB. This ensures users can always view, download, or display their original files from search results, even if the MongoDB database is unavailable.

## Key Features

### 1. ✅ Dual Storage Strategy

**MongoDB Atlas**:
- File metadata (name, description, tags, etc.)
- Extracted content and text
- Vector embeddings for semantic search
- Search chunks and keywords
- User ownership and permissions

**Local File System**:
- Original uploaded files (binary)
- Organized by user and date
- UUID-based filenames
- Preserves original file extension

### 2. ✅ File Storage Structure

```
~/.ai-mcp-toolkit/uploads/
├── {user_id}/
│   ├── 2025/
│   │   ├── 01/
│   │   │   ├── a1b2c3d4-e5f6-7890-abcd-ef1234567890.pdf
│   │   │   ├── f9e8d7c6-b5a4-3210-9876-543210fedcba.jpg
│   │   │   └── c3d4e5f6-a7b8-9012-cdef-1234567890ab.xlsx
│   │   ├── 02/
│   │   │   └── ...
│   ├── 2024/
│   │   └── ...
```

**Benefits**:
- ✅ User isolation (each user has own directory)
- ✅ Date organization (easy to find files by upload date)
- ✅ UUID filenames (no conflicts, safe for any character set)
- ✅ Extension preservation (MIME type detection)
- ✅ Scales well (distributed across year/month subdirectories)

### 3. ✅ Integration with Upload Pipeline

**Upload Flow**:
```
1. User uploads file via /resources/upload
   ↓
2. Generate UUID for file
   ↓
3. Save file to local storage: ~/.ai-mcp-toolkit/uploads/{user_id}/{year}/{month}/{uuid}.{ext}
   ↓
4. Process file (extract text, generate embeddings, create chunks)
   ↓
5. Store metadata in MongoDB with file_id = UUID
   ↓
6. Return success with resource info
```

**Key Code Changes**:

- **FileStorageService**: New service in `src/ai_mcp_toolkit/services/file_storage_service.py`
  - `save_file()` - Save binary file to disk
  - `get_file()` - Retrieve file from disk
  - `delete_file()` - Remove file from disk
  - `file_exists()` - Check if file exists
  - `get_file_path()` - Get full path to file
  - `get_storage_stats()` - Get storage usage stats

- **IngestionService**: Modified `ingest_file()` method
  - Saves file to local storage **before** processing
  - Stores `file_id` (UUID) in resource metadata
  - Records storage info in `metadata.file_storage`

- **HTTPServer**: New endpoint `/resources/download/{file_id}`
  - Retrieves original file from local storage
  - Verifies user ownership/permissions
  - Returns file with appropriate MIME type and headers
  - Supports `inline` viewing in browser (e.g., PDFs)

### 4. ✅ File Download/View Endpoint

**Endpoint**: `GET /resources/download/{file_id}`

**Purpose**:
- View PDFs directly in browser
- Download original files
- Display images from search results
- Access any uploaded file

**Example Usage**:

```bash
# View PDF in browser
curl http://localhost:8000/resources/download/a1b2c3d4-e5f6-7890-abcd-ef1234567890

# Or in frontend:
<a href="/api/resources/download/{file_id}" target="_blank">View PDF</a>
<img src="/api/resources/download/{file_id}" alt="Image from search" />
```

**Response Headers**:
```
Content-Type: application/pdf
Content-Disposition: inline; filename="Invoice-Q4-2025.pdf"
Content-Length: 1234567
Cache-Control: public, max-age=3600
```

**Security**:
- ✅ Requires authentication (server-side session)
- ✅ Ownership verification (users can only access their own files)
- ✅ Admin override (admins can access all files)
- ✅ Audit logging (all downloads are logged)

### 5. ✅ Resource Metadata

Each resource now contains storage information in metadata:

```json
{
  "id": "resource_id",
  "file_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "file_name": "Invoice-Q4-2025.pdf",
  "mime_type": "application/pdf",
  "metadata": {
    "original_filename": "Invoice-Q4-2025.pdf",
    "file_storage": {
      "file_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "file_path": "/Users/roza/.ai-mcp-toolkit/uploads/user123/2025/01/a1b2c3d4.pdf",
      "relative_path": "user123/2025/01/a1b2c3d4.pdf",
      "stored_at": "2025-01-03T12:00:00Z"
    }
  }
}
```

### 6. ✅ Use Cases

**1. PDF Viewing from Search Results**:
```svelte
<!-- Frontend component -->
{#if result.mime_type === 'application/pdf'}
  <a href="/api/resources/download/{result.file_id}" target="_blank">
    View PDF
  </a>
{/if}
```

**2. Image Display**:
```svelte
<img 
  src="/api/resources/download/{result.file_id}" 
  alt={result.file_name}
  class="max-w-sm"
/>
```

**3. File Download**:
```svelte
<button on:click={() => window.open(`/api/resources/download/${result.file_id}`)}>
  Download Original File
</button>
```

**4. Resource Management**:
- View original files from resource library
- Re-download files after months/years
- Verify file contents without re-uploading

### 7. ✅ Storage Management

**Statistics API**:
```python
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

**Delete File** (automatic when resource is deleted):
```python
file_storage.delete_file(file_id="uuid", user_id="user123")
```

**Check Existence**:
```python
if file_storage.file_exists(file_id="uuid", user_id="user123"):
    print("File exists")
```

### 8. ✅ Configuration

**Environment Variables** (`.env`):

```bash
# Data directory (base path for all data)
DATA_DIR=~/.ai-mcp-toolkit

# Files are stored in: ${DATA_DIR}/uploads/
# Optional: Override default path
# FILE_STORAGE_PATH=/custom/path/to/uploads
```

**Default Paths**:
- Development: `~/.ai-mcp-toolkit/uploads/`
- Production: `/var/lib/ai-mcp-toolkit/uploads/`
- Custom: Set `FILE_STORAGE_PATH` environment variable

### 9. ✅ Migration Notes

**Existing Resources**:
- Old resources (before this feature) don't have `file_id` or local storage
- They continue to work with MongoDB-only storage
- New uploads automatically save to local storage
- **No migration required** for existing data

**Future Enhancement**:
- Could add a migration script to re-upload existing resources to local storage
- Low priority since new uploads work correctly

### 10. ✅ Backup Strategy

**What to Backup**:

1. **MongoDB Database** (metadata, embeddings, search chunks)
   ```bash
   mongodump --uri="mongodb+srv://..." --out=/backup/mongodb/
   ```

2. **Local File Storage** (original files)
   ```bash
   tar -czf /backup/uploads-2025-01-03.tar.gz ~/.ai-mcp-toolkit/uploads/
   ```

3. **Redis Cache** (optional, can be regenerated)
   ```bash
   redis-cli --rdb /backup/redis/dump.rdb
   ```

**Restore Process**:
```bash
# 1. Restore MongoDB
mongorestore --uri="mongodb+srv://..." /backup/mongodb/

# 2. Restore files
tar -xzf /backup/uploads-2025-01-03.tar.gz -C ~/

# 3. Restart server (Redis will auto-regenerate)
```

### 11. ✅ Performance Considerations

**File Access**:
- ✅ Fast local disk reads (no network latency)
- ✅ Operating system file caching
- ✅ CDN-ready (could add CDN layer later)

**Storage Scalability**:
- Year/month organization prevents directory overload
- Each directory typically contains 100-1000 files
- Modern filesystems handle millions of files easily

**Disk Space**:
- Plan for ~1GB per user per year (varies by usage)
- Monitor disk usage with built-in stats API
- Consider cleanup policies for old files

### 12. ✅ Security Features

**File Isolation**:
- Each user's files in separate directory
- UUID filenames prevent path traversal
- No predictable file paths

**Access Control**:
- Server-side authentication required
- Ownership verification on every download
- Admin-only access to other users' files
- Audit logging for all file access

**Safe Filenames**:
- UUID-based (no special characters)
- Extension preserved for MIME detection
- Original filename stored in metadata only

## Implementation Files

**New Files**:
- `src/ai_mcp_toolkit/services/file_storage_service.py` - File storage service
- `ui/src/routes/api/resources/download/[file_id]/+server.js` - Frontend proxy endpoint
- `LOCAL_FILE_STORAGE.md` - This documentation

**Modified Files**:
- `src/ai_mcp_toolkit/services/ingestion_service.py` - Integrated file storage
- `src/ai_mcp_toolkit/server/http_server.py` - Added download endpoint
- `src/ai_mcp_toolkit/services/search_service.py` - Added file_id and mime_type to results
- `src/ai_mcp_toolkit/services/suggestion_service.py` - Added helper methods
- `ui/src/routes/search/+page.svelte` - Added View button for PDFs/images
- `.env.example` - Added storage configuration
- `ui/src/routes/agents/pdf-extractor/+page.svelte` - Fixed resource fetching

## Testing

**Manual Testing Steps**:

1. **Upload a file**:
   ```bash
   curl -X POST http://localhost:8000/resources/upload \
     -H "Cookie: session=..." \
     -F "file=@test.pdf" \
     -F "description=Test file"
   ```

2. **Check file exists**:
   ```bash
   ls -la ~/.ai-mcp-toolkit/uploads/{user_id}/2025/01/
   ```

3. **Download file**:
   ```bash
   curl http://localhost:8000/resources/download/{file_id} \
     -H "Cookie: session=..." \
     -o downloaded.pdf
   ```

4. **Verify in browser**:
   - Open `http://localhost:8000/resources/download/{file_id}`
   - PDF should open inline
   - Image should display
   - Other files should download

## Future Enhancements

### Potential Additions:

1. **Cloud Storage Integration** (S3/GCS):
   - Optional cloud backup
   - Hybrid local + cloud storage
   - CDN distribution

2. **Storage Quotas**:
   - Per-user storage limits
   - Admin-configurable quotas
   - Usage notifications

3. **File Versioning**:
   - Keep multiple versions of same file
   - Version history and rollback
   - Diff between versions

4. **Automatic Cleanup**:
   - Delete files older than X months
   - Archive old files to cold storage
   - Configurable retention policies

5. **Compression**:
   - Auto-compress large files
   - On-the-fly decompression on download
   - Save disk space

6. **Thumbnail Generation**:
   - Auto-generate thumbnails for images/PDFs
   - Display in search results
   - Faster preview loading

## Conclusion

✅ **Completed Features**:
- Local file storage with UUID filenames
- User-isolated, date-organized directory structure
- Download/view endpoint with authentication
- Integration with upload pipeline
- Metadata tracking of storage info
- Automatic file saving on upload
- Security and access control
- Storage statistics API

✅ **Benefits**:
- Users can always access original files
- PDFs viewable directly in browser
- Images displayable from search results
- No data loss if MongoDB unavailable
- Better user experience
- Production-ready and scalable

---

*Implemented: 2025-01-03*  
*Files: file_storage_service.py, ingestion_service.py, http_server.py*  
*Storage Location: ~/.ai-mcp-toolkit/uploads/{user_id}/{year}/{month}/{uuid}.{ext}*
