# Resource Per-User Scoping Fix

**Date**: 2025-10-27  
**Issue**: Resources were globally unique, preventing different users from uploading files with the same name  
**Status**: ✅ Fixed

## Problem

When a user tried to upload a file that had already been uploaded by another user (even with different content), they received an error:

```
Resource already exists: file:///Photomate nabídka.pdf
```

This happened because:
1. Resource URIs were generated as `file:///filename` (without user ID)
2. The uniqueness check in `ResourceManager.create_resource()` only checked the URI globally
3. All files were stored in a "flat" structure without user-specific organization

## Root Cause

**File**: `src/ai_mcp_toolkit/server/http_server.py`, line 1098
```python
# OLD CODE - Global URI
uri = f"file:///{file.filename}"
```

**File**: `src/ai_mcp_toolkit/managers/resource_manager.py`, line 239
```python
# OLD CODE - Global uniqueness check
existing = await Resource.find_one(Resource.uri == uri)
```

## Solution

### 1. User-Scoped URI Generation

Include the user ID in the URI to create a logical folder structure:

```python
# NEW CODE - Per-user URI
uri = f"file:///{user.id}/{file.filename}"
```

**Example URIs**:
- User A: `file:///67a1b2c3d4e5f6789abcdef0/photo.pdf`
- User B: `file:///67a1b2c3d4e5f6789abcdef1/photo.pdf`

These URIs are now unique even if the filename is the same!

### 2. User-Scoped Uniqueness Check

Update the duplicate check to consider both URI and owner:

```python
# NEW CODE - Per-user uniqueness check
existing = await Resource.find_one(
    Resource.uri == uri,
    Resource.owner_id == owner_id
)
```

This ensures that:
- Each user can upload files with the same name
- Users cannot upload the same file twice (within their own scope)
- The system maintains data isolation between users

## Benefits

✅ **Data Isolation**: Each user's resources are logically separated  
✅ **No Name Conflicts**: Multiple users can upload files with identical names  
✅ **Per-User Uniqueness**: Users still can't upload duplicates to their own space  
✅ **Clear Organization**: URIs follow a `user_id/filename` structure  
✅ **Security**: Existing ownership checks continue to work as before

## Technical Details

### URI Format

**Pattern**: `file:///{user_id}/{filename}`

**Examples**:
```
file:///67a1b2c3d4e5f6789abcdef0/invoice.pdf
file:///67a1b2c3d4e5f6789abcdef0/report.docx
file:///67a1b2c3d4e5f6789abcdef1/invoice.pdf  # Different user, same filename ✅
```

### Database Queries

Resources are already filtered by `owner_id` in all query operations:

```python
# List resources (already per-user)
if not is_admin and user_id:
    query["owner_id"] = user_id

# Read resource (already ownership checked)
if not is_admin and user_id and resource.owner_id != user_id:
    raise ValueError("Access denied")

# Update/Delete (already ownership checked)
if not is_admin and user_id and resource.owner_id != user_id:
    raise ValueError("Access denied")
```

### Backward Compatibility

**Existing Resources**: Old resources with URIs like `file:///filename` will continue to work:
- They are already associated with an `owner_id`
- Ownership checks will still apply
- They can be read/updated/deleted by their owners

**New Uploads**: Will use the new URI format with user ID prefix

**Migration**: No migration needed! Old and new formats coexist safely because:
1. Old resources already have `owner_id` set
2. Ownership filtering prevents cross-user access
3. New uploads create user-scoped URIs automatically

## Testing

### Test Scenarios

1. ✅ **Same filename, different users**:
   - User A uploads `test.pdf`
   - User B uploads `test.pdf` (different content)
   - Both succeed with unique URIs

2. ✅ **Duplicate upload, same user**:
   - User A uploads `test.pdf`
   - User A tries to upload `test.pdf` again
   - Error: "Resource already exists"

3. ✅ **User isolation**:
   - User A uploads `secret.pdf`
   - User B cannot access `file:///user_a_id/secret.pdf`
   - Ownership check prevents access

4. ✅ **Admin access**:
   - Admin can list all resources
   - Admin sees resources from all users
   - Admin can read any resource

### Manual Testing

```bash
# User A uploads a file
curl -X POST http://localhost:8000/resources/upload \
  -H "Cookie: session_token=user_a_session" \
  -F "file=@test.pdf" \
  -F "description=Test document"

# User B uploads same filename (should work now!)
curl -X POST http://localhost:8000/resources/upload \
  -H "Cookie: session_token=user_b_session" \
  -F "file=@test.pdf" \
  -F "description=Another test document"
```

## Files Changed

### Modified Files

1. **`src/ai_mcp_toolkit/server/http_server.py`**
   - Line 1098: Changed URI generation to include user ID
   - Before: `uri = f"file:///{file.filename}"`
   - After: `uri = f"file:///{user.id}/{file.filename}"`

2. **`src/ai_mcp_toolkit/managers/resource_manager.py`**
   - Lines 239-242: Updated uniqueness check to include owner_id
   - Before: Single condition check on URI only
   - After: Compound check on both URI and owner_id

## Related Code

### Ownership Filtering (Already Implemented)

Resources are automatically filtered by owner in all operations:

- **List**: `query["owner_id"] = user_id` (line 54)
- **Read**: Ownership check (line 109)
- **Update**: Ownership check (line 309)
- **Delete**: Ownership check (line 364)

### Frontend Impact

**No changes needed** in the frontend! The UI already:
- Sends files with authentication cookies
- Backend automatically extracts user from session
- Resource operations are already per-user scoped
- Resource lists show only the user's resources

## Security Considerations

✅ **User Isolation**: URI includes user ID but this is not a security issue because:
   - All operations require authentication
   - Ownership checks validate `owner_id` from database
   - Users cannot access resources by guessing URIs

✅ **No Information Leakage**: The user ID in URI is the same ID already stored in:
   - `owner_id` field in database
   - Session cookies
   - Audit logs

✅ **Consistent Security**: All existing security measures remain in place:
   - Authentication required for all endpoints
   - Ownership validation on read/update/delete
   - Admin role checks for global operations
   - Audit logging for all actions

## Conclusion

The fix is minimal, focused, and solves the problem without breaking existing functionality:

- **2 lines changed** in total
- **No database migration** required
- **No frontend changes** needed
- **Backward compatible** with existing resources
- **Security maintained** through existing ownership checks

Users can now upload files with the same name without conflicts, while maintaining proper data isolation and security! 🎉

---

*Fix Applied: 2025-10-27*
*Files: http_server.py, resource_manager.py*
