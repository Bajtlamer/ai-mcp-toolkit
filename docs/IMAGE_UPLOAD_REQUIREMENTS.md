# Image Upload and Description Requirements

## Critical Requirements

### 1. Description Handling for Images

**REQUIREMENT**: When images are uploaded, both USER description and AI-generated description must be MERGED, not replaced.

**Implementation**:
- User provides description during upload → Use it
- AI generates description from image content → Use it
- **MERGE BOTH**: `"{user_description}. {ai_description}"`
- Technical metadata (dimensions, format) stored separately in `metadata.technical_metadata`

**Files Modified**:
- `src/ai_mcp_toolkit/server/http_server.py` - Added `description` field to upload endpoint
- `src/ai_mcp_toolkit/services/ingestion_service.py` - Merge logic for descriptions
- `src/ai_mcp_toolkit/processors/image_processor.py` - Preserve user description, store technical info separately

**Priority Order**:
1. User description + AI description (MERGED)
2. User description only
3. AI description only
4. Technical info or filename

### 2. Default Resource Type

**REQUIREMENT**: When creating a new resource, the default type MUST be **FILE**, not TEXT.

**Implementation**:
- `ui/src/routes/resources/+page.svelte` - `openCreateModal()` function sets `resource_type: 'file'`

### 3. Technical Metadata Storage

**REQUIREMENT**: Technical information (image dimensions, format, EXIF data) must be stored in `metadata.technical_metadata`, NOT in the user-visible description field.

**Implementation**:
- Image processor creates `technical_metadata` field
- Stored in Resource.metadata.properties
- User description remains clean and editable

## Testing Checklist

- [ ] Upload image without description → AI description used
- [ ] Upload image with user description → Both descriptions merged
- [ ] Edit image description → User edits preserved, not overwritten
- [ ] View technical metadata → Stored separately, accessible via API
- [ ] Create new resource → Default type is FILE
- [ ] Upload file via resources page → Description field preserved

## Related Files

- `/src/ai_mcp_toolkit/server/http_server.py` - Upload endpoint
- `/src/ai_mcp_toolkit/services/ingestion_service.py` - Ingestion logic
- `/src/ai_mcp_toolkit/processors/image_processor.py` - Image processing
- `/src/ai_mcp_toolkit/managers/resource_manager.py` - Resource updates
- `/ui/src/routes/resources/+page.svelte` - Resource creation UI

## Notes

- Always restart Python backend after changes to ingestion/processor code
- Frontend changes are hot-reloaded automatically
- Check backend logs for description merge confirmation: "✅ Merged user + AI description"
