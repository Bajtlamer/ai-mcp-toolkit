# Professional File Upload System with UUID & Auto-Detection

**Date**: 2025-10-27  
**Status**: ✅ Implemented  
**Type**: Major Enhancement

## Overview

Implemented a production-ready file upload system that automatically detects file properties, generates unique filenames, and stores comprehensive metadata. This prevents naming conflicts, handles exotic filenames, and allows users to upload multiple versions of files.

## Key Features

### 1. ✅ UUID-Based Unique Filenames

Every uploaded file gets a **UUID-based unique filename**:

```python
# Original: "Photomate nabídka.pdf"
# Stored as: "a1b2c3d4-e5f6-7890-abcd-ef1234567890.pdf"
# URI: "file:///user_id/a1b2c3d4-e5f6-7890-abcd-ef1234567890.pdf"
```

**Benefits**:
- ✅ No filename conflicts (guaranteed unique)
- ✅ Handles exotic characters safely (`ñ`, `ä`, `中文`, etc.)
- ✅ Prevents path traversal attacks
- ✅ Users can upload same filename multiple times
- ✅ Original filename preserved in metadata

### 2. ✅ Automatic File Type Detection

Backend automatically detects file properties:

```python
# Auto-detected properties:
- MIME type (using python-magic if available)
- File category (document, image, code, etc.)
- File size (human-readable: "2.5 MB")
- Content hash (SHA-256 for deduplication)
- File extension
- Structure-specific metadata
```

**File Categories**:
- 📄 Documents: PDF, DOC, DOCX
- 📊 Spreadsheets: XLS, XLSX, CSV
- 📑 Presentations: PPT, PPTX
- 💻 Code: Python, JavaScript, Java, etc.
- 📝 Text: TXT, MD, JSON, XML, YAML
- 🖼️ Images: PNG, JPG, GIF, SVG
- 🎵 Audio: MP3, WAV, FLAC
- 🎬 Video: MP4, AVI, MOV
- 📦 Archives: ZIP, TAR, RAR
- 📁 Other: Everything else

### 3. ✅ Rich Metadata Storage

Comprehensive metadata stored for each file:

```json
{
  "original_filename": "Photomate nabídka.pdf",
  "unique_filename": "a1b2c3d4-e5f6-7890-abcd-ef1234567890.pdf",
  "file_size": 2621440,
  "file_size_human": "2.50 MB",
  "content_hash": "8f3a4b2c1d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1",
  "mime_type_detected": "application/pdf",
  "mime_type_browser": "application/pdf",
  "file_extension": ".pdf",
  "file_category": "document",
  "upload_timestamp": "2025-10-27T20:00:00.000Z",
  "is_binary": true,
  "uploaded_by": "john_doe",
  
  // PDF-specific metadata
  "pdf_bytes": "base64_encoded_content...",
  "pdf_pages": 15,
  "pdf_title": "Product Catalog",
  "pdf_author": "Jane Smith",
  
  // Duplication detection
  "duplicate_warning": "Same content as 'old_file.pdf' uploaded on 2025-10-25"
}
```

### 4. ✅ Content Deduplication Detection

System detects duplicate content but **doesn't block uploads**:

```python
# User uploads same content twice
# First upload: Creates resource
# Second upload: Creates NEW resource + adds warning in metadata

metadata['duplicate_of'] = "resource_id_of_first_upload"
metadata['duplicate_warning'] = "Same content detected..."
```

**Why allow duplicates?**
- User might want multiple versions
- File might be updated externally
- Different contexts/purposes
- User should have control

### 5. ✅ Format-Specific Processing

#### PDF Files
```python
# Extracted metadata:
- Number of pages
- PDF metadata (title, author, subject)
- Embedded text (extracted on access)
- Base64 stored for later processing
```

#### Image Files
```python
# Extracted metadata:
- Dimensions (width x height)
- Format (PNG, JPEG, etc.)
- Color mode (RGB, RGBA, etc.)
```

#### Text Files
```python
# Extracted metadata:
- Character count
- Line count
- Encoding (UTF-8, etc.)
- Full content stored
```

### 6. ✅ Multiple Uploads Allowed

Users can upload the same file multiple times:

```bash
# Upload 1: "report.pdf" (version 1)
URI: file:///user_id/uuid1.pdf
Original: "report.pdf"

# Upload 2: "report.pdf" (version 2, updated content)
URI: file:///user_id/uuid2.pdf  
Original: "report.pdf"
✅ BOTH FILES COEXIST!
```

## Technical Implementation

### File Upload Flow

```
1. User uploads file
   ↓
2. Backend receives file + content
   ↓
3. Calculate SHA-256 hash (for deduplication)
   ↓
4. Detect MIME type (python-magic or browser)
   ↓
5. Generate UUID + preserve extension
   ↓
6. Create user-scoped URI: file:///user_id/uuid.ext
   ↓
7. Detect file category
   ↓
8. Extract format-specific metadata
   ↓
9. Check for duplicate content (warning only)
   ↓
10. Store in MongoDB with full metadata
    ↓
11. Return success with resource info
```

### URI Structure

**Pattern**: `file:///{user_id}/{uuid}{extension}`

**Examples**:
```
file:///67a1b2c3d4e5f6789abcdef0/a1b2c3d4-e5f6-7890-abcd-ef1234567890.pdf
file:///67a1b2c3d4e5f6789abcdef0/f9e8d7c6-b5a4-3210-9876-543210fedcba.jpg
file:///67a1b2c3d4e5f6789abcdef1/c3d4e5f6-a7b8-9012-cdef-1234567890ab.pdf
```

### Helper Methods

```python
def _format_file_size(size_bytes: int) -> str:
    """Convert bytes to human-readable format (KB, MB, GB)."""
    
def _detect_file_category(mime_type: str, extension: str) -> str:
    """Categorize file as document, image, code, etc."""
```

### MIME Type Detection

1. **Browser-provided** (file.content_type)
2. **python-magic detection** (if available, reads magic numbers)
3. **Extension fallback** (if both fail)

```python
try:
    import magic
    mime_type = magic.from_buffer(content_bytes[:2048], mime=True)
except ImportError:
    # Use browser-provided type
    mime_type = file.content_type
```

## Security Improvements

### Previous Issues (FIXED)

❌ **Problem**: Users could upload `../../etc/passwd`  
✅ **Fixed**: UUID filename prevents path traversal

❌ **Problem**: Exotic characters caused errors (ñ, ä, 中文)  
✅ **Fixed**: Original name only in metadata, UUID for storage

❌ **Problem**: Filename conflicts between users  
✅ **Fixed**: User-scoped + UUID guarantees uniqueness

❌ **Problem**: Same filename = rejected upload  
✅ **Fixed**: Multiple uploads allowed, each gets unique ID

### Security Features

✅ **Path Traversal Protection**: UUID filenames can't contain `/` or `..`  
✅ **User Isolation**: Files scoped by user ID  
✅ **Content Verification**: Hash stored for integrity checks  
✅ **Metadata Sanitization**: All user input validated  
✅ **MIME Type Verification**: Server-side detection  

## Database Schema

### Resource Document

```python
{
  "_id": ObjectId("..."),
  "uri": "file:///user_id/uuid.pdf",
  "name": "Product Catalog",  # User-friendly name
  "description": "Document file: Photomate nabídka.pdf (2.50 MB)",
  "mime_type": "application/pdf",
  "resource_type": "FILE",
  "owner_id": "user_id",
  "content": "[PDF file: ..., 2.50 MB, 15 pages]",
  "metadata": {
    "created_at": "2025-10-27T20:00:00Z",
    "modified_at": "2025-10-27T20:00:00Z",
    "properties": {
      // All the rich metadata shown above
    }
  },
  "created_at": "2025-10-27T20:00:00Z",
  "updated_at": "2025-10-27T20:00:00Z"
}
```

## API Changes

### Upload Endpoint

```http
POST /resources/upload
Content-Type: multipart/form-data

file: <binary data>
name: "My Product Catalog" (optional)
description: "Q4 2025 catalog" (optional, auto-generated if empty)
```

**Response**:
```json
{
  "id": "resource_id",
  "uri": "file:///user_id/uuid.pdf",
  "name": "My Product Catalog",
  "description": "Document file: Photomate nabídka.pdf (2.50 MB)",
  "mime_type": "application/pdf",
  "resource_type": "FILE",
  "owner_id": "user_id",
  "content": "[PDF file: ..., 2.50 MB, 15 pages]",
  "created_at": "2025-10-27T20:00:00.000Z",
  "updated_at": "2025-10-27T20:00:00.000Z"
}
```

### Auto-Generated Description

If `description` is empty, backend auto-generates it:

```python
# For normal uploads
"Document file: report.pdf (1.25 MB)"

# For duplicate content
"Document file: report.pdf (1.25 MB) [Duplicate content detected]"
```

## Benefits Summary

### For Users

✅ Upload files with any name, any language  
✅ Upload same file multiple times (versions)  
✅ Automatic file organization  
✅ Duplicate detection warnings  
✅ Rich metadata available  

### For System

✅ No filename conflicts (guaranteed)  
✅ Better security (path traversal protected)  
✅ Easier debugging (unique IDs)  
✅ Content deduplication tracking  
✅ Format-specific processing  
✅ Comprehensive audit trail  

### For Developers

✅ Clean URI structure  
✅ Rich metadata for features  
✅ Extensible system  
✅ No special case handling  
✅ Industry-standard approach  

## Dependencies

### Required
- `uuid` (Python stdlib)
- `hashlib` (Python stdlib)
- `pathlib` (Python stdlib)

### Optional (Enhanced Detection)
- `python-magic` (MIME type detection from file content)
- `pypdf` (PDF metadata extraction) - already installed
- `Pillow` (Image metadata extraction) - needed for images

### Install Optional Dependencies

```bash
# For better MIME detection
pip install python-magic

# For image processing
pip install Pillow
```

## Frontend Impact

**No changes needed!** Frontend continues to work as before:

- Sends file via `multipart/form-data`
- Backend handles all detection automatically
- Response includes all metadata
- Original filename available in `metadata.properties.original_filename`

## Migration Path

### Existing Resources

Old resources with URIs like `file:///user_id/original_name.pdf` continue to work:
- They already have `owner_id`
- They can be read/updated/deleted
- New uploads use UUID format
- Both formats coexist safely

### No Migration Required

✅ Old format: `file:///user_id/filename.pdf`  
✅ New format: `file:///user_id/uuid.pdf`  
✅ Both work with existing code  

## Testing Scenarios

### 1. Exotic Filenames
```bash
# Upload: "Photomate nabídka.pdf"
# Result: ✅ Stored as uuid.pdf, original name in metadata

# Upload: "文档-中文.pdf"
# Result: ✅ Stored as uuid.pdf, original name preserved

# Upload: "file@#$%^&*().txt"
# Result: ✅ Stored as uuid.txt, special chars safe in metadata
```

### 2. Multiple Uploads
```bash
# User uploads report.pdf
# Result: file:///user_id/uuid1.pdf

# User uploads report.pdf again (updated version)
# Result: file:///user_id/uuid2.pdf
# ✅ Both files coexist
```

### 3. Duplicate Content Detection
```bash
# Upload: invoice.pdf (content hash: abc123...)
# Result: Created

# Upload: invoice_copy.pdf (SAME content hash: abc123...)
# Result: Created + metadata.duplicate_warning added
```

### 4. Automatic Detection
```bash
# Upload: unknown_file (no extension)
# Result: Backend detects MIME type from content
# Result: Categorizes correctly
# Result: Stores with detected info
```

## Logging Examples

```
INFO: User john_doe uploaded: report.pdf -> a1b2c3d4.pdf (2.50 MB, document, hash: 8f3a4b2c...)
INFO: Detected MIME type: application/pdf (browser sent: application/pdf)
INFO: User jane_doe uploading duplicate content (hash: 8f3a4b2c...)
WARNING: File exotic_name.txt marked as text but decode failed
```

## Future Enhancements

### Possible Additions

1. **Virus Scanning**: Integrate ClamAV or similar
2. **Thumbnail Generation**: Auto-generate previews for images/PDFs
3. **Content Extraction**: OCR for scanned documents
4. **File Compression**: Auto-compress large files
5. **Cloud Storage**: S3/GCS integration for large files
6. **Version Control**: Explicit versioning system
7. **Expiration**: Auto-delete old files
8. **Quota Management**: Per-user storage limits

## Conclusion

This implementation follows **industry best practices** used by:
- Amazon S3
- Google Drive
- Dropbox
- GitHub
- Imgur

**Key Achievements**:
- ✅ UUID-based unique filenames
- ✅ Automatic file detection
- ✅ Rich metadata storage
- ✅ Multiple uploads allowed
- ✅ Content deduplication tracking
- ✅ Security hardening
- ✅ User-friendly
- ✅ Developer-friendly
- ✅ Production-ready

Users can now upload any file, with any name, as many times as they want, and the system handles it professionally! 🚀

---

*Implemented: 2025-10-27*  
*Files: http_server.py, resource_manager.py*  
*No frontend changes required*
