# Resource Update & Reindexing Implementation Plan

## Overview
Implement automatic background reindexing when resources are created, updated, or deleted to keep all search indexes, embeddings, and suggestions consistent.

## Problems to Solve

### 1. Image Description Overwriting
**Current Issue:** When image metadata is updated, the `summary` field is overwritten with technical info like "JPEG image (753x658)", losing any user-provided description.

**Location:** `src/ai_mcp_toolkit/processors/image_processor.py:64`

**Solution:**
- Change `summary` to store technical metadata separately
- Preserve user `description` field
- Merge both when displaying: `"{user_description} | {technical_info}"`

### 2. Stale Chunks After Resource Updates
**Current Issue:** When resource metadata (name, description, tags) changes, existing chunks still contain old searchable_text, making search results stale.

**Solution:**
- Detect metadata changes in resource update handler
- Regenerate chunks with updated searchable_text
- Re-generate embeddings for updated chunks
- Update all search indexes

### 3. Stale Redis Suggestions
**Current Issue:** Search autocomplete suggestions in Redis are not updated when resources change, showing outdated or deleted content.

**Solution:**
- Hook into resource create/update/delete operations
- Regenerate Redis suggestion indexes in background
- Remove suggestions for deleted resources

## Implementation Plan

### Phase 1: Fix Image Description Preservation

#### 1.1 Modify Image Processor
**File:** `src/ai_mcp_toolkit/processors/image_processor.py`

Change line 64 from:
```python
'summary': f"{image_format} image ({width}x{height})",
```

To store technical info separately:
```python
'technical_metadata': f"{image_format} image ({width}x{height})",
'summary': metadata.get('description', f"{image_format} image ({width}x{height})"),
```

#### 1.2 Update Resource Model
**File:** `src/ai_mcp_toolkit/models/documents.py`

Add optional field:
```python
technical_metadata: Optional[str] = None
```

#### 1.3 Merge on Display
When showing resources in UI or API responses, combine:
```python
display_description = resource.description or resource.summary
if resource.technical_metadata:
    display_description += f" | {resource.technical_metadata}"
```

### Phase 2: Implement Resource Event System

#### 2.1 Create Event Service
**File:** `src/ai_mcp_toolkit/services/resource_event_service.py`

```python
class ResourceEventService:
    """Handle resource lifecycle events for background reindexing."""
    
    async def on_resource_created(self, resource_id: str, company_id: str):
        """Triggered after resource is created."""
        # Generate initial embeddings
        # Add to Redis suggestions
        pass
    
    async def on_resource_updated(self, resource_id: str, company_id: str, changed_fields: List[str]):
        """Triggered after resource metadata is updated."""
        # Check if searchable fields changed (name, description, tags, etc.)
        # If yes: regenerate chunks, embeddings, suggestions
        pass
    
    async def on_resource_deleted(self, resource_id: str, company_id: str):
        """Triggered before resource is deleted."""
        # Remove from Redis suggestions
        # Clean up orphaned chunks/embeddings
        pass
```

#### 2.2 Create Reindexing Service
**File:** `src/ai_mcp_toolkit/services/reindexing_service.py`

```python
class ReindexingService:
    """Background service to reindex resources when they change."""
    
    async def reindex_resource(self, resource_id: str, company_id: str):
        """Regenerate all indexes for a resource."""
        # 1. Fetch resource
        # 2. Delete old chunks
        # 3. Regenerate chunks with current metadata
        # 4. Regenerate embeddings
        # 5. Update Redis suggestions
        # 6. Extract keywords/entities if needed
        pass
    
    async def update_redis_suggestions(self, resource_id: str, company_id: str):
        """Update Redis search suggestions for a resource."""
        # Extract searchable terms
        # Update suggestion indexes
        pass
    
    async def remove_from_suggestions(self, resource_id: str, company_id: str):
        """Remove deleted resource from Redis suggestions."""
        pass
```

### Phase 3: Hook Events into Resource Manager

#### 3.1 Modify Resource Manager
**File:** `src/ai_mcp_toolkit/managers/resource_manager.py`

Add event hooks to:
- `create_resource()` → call `on_resource_created()`
- `update_resource()` → call `on_resource_updated()`  
- `delete_resource()` → call `on_resource_deleted()`

Example:
```python
async def update_resource(self, resource_id: str, updates: Dict):
    # Fetch old resource to detect changes
    old_resource = await Resource.get(resource_id)
    
    # Apply updates
    for key, value in updates.items():
        setattr(old_resource, key, value)
    
    await old_resource.save()
    
    # Detect changed fields
    changed_fields = list(updates.keys())
    
    # Trigger reindexing if searchable fields changed
    searchable_fields = {'name', 'description', 'summary', 'tags', 'keywords'}
    if any(field in searchable_fields for field in changed_fields):
        # Fire event (async, non-blocking)
        asyncio.create_task(
            self.event_service.on_resource_updated(
                resource_id, old_resource.company_id, changed_fields
            )
        )
    
    return old_resource
```

### Phase 4: Implement Chunk Regeneration

#### 4.1 Chunk Regeneration Logic
When resource metadata changes:

1. **Fetch all chunks** for the resource
2. **Update searchable_text** in each chunk with new metadata:
   ```python
   from src.ai_mcp_toolkit.utils.text_normalizer import create_searchable_text
   
   searchable_text = create_searchable_text(
       resource.name,
       resource.description,
       resource.summary,
       ' '.join(resource.tags),
       ' '.join(resource.keywords),
       chunk.text,  # Original chunk text
       chunk.ocr_text
   )
   ```
3. **Regenerate embeddings** for updated chunks
4. **Save updated chunks**

#### 4.2 Selective Reindexing
Optimize by only regenerating what changed:
- If only `description` changed → update chunk metadata only
- If `tags` changed → regenerate keywords/entities
- If `name` changed → update searchable_text in all chunks

### Phase 5: Redis Suggestions Update

#### 5.1 Suggestion Extraction
Extract searchable terms from resource:
- Filename tokens
- Description words
- Tags
- Keywords
- Entity names
- OCR text tokens

#### 5.2 Update Redis Keys
```python
async def update_suggestions(self, resource_id: str, company_id: str):
    resource = await Resource.get(resource_id)
    
    # Extract terms
    terms = set()
    terms.update(tokenize(resource.name))
    terms.update(tokenize(resource.description))
    terms.update(resource.tags)
    terms.update(resource.keywords)
    
    # Add to Redis sorted sets
    for term in terms:
        await redis.zadd(
            f"suggestions:{company_id}:{term[0]}",  # First letter for prefix
            {term: time.time()}
        )
```

#### 5.3 Cleanup on Delete
```python
async def remove_suggestions(self, resource_id: str, company_id: str):
    # Remove all terms associated with this resource
    # This requires tracking resource_id -> terms mapping
    pass
```

## Environment Flags

Add configuration to enable/disable features:

```python
# .env
ENABLE_AUTO_REINDEXING=true
ENABLE_EMBEDDING_UPDATE=true
ENABLE_REDIS_SYNC=true
REINDEX_BATCH_SIZE=10
```

## Testing Plan

### Test Cases

1. **Create resource** → verify chunks, embeddings, suggestions created
2. **Update description** → verify chunks regenerated with new text
3. **Update tags** → verify Redis suggestions updated
4. **Delete resource** → verify suggestions removed, chunks deleted
5. **Bulk update** → verify batch processing works efficiently

### Validation

After each operation, verify:
- ✅ Chunks have updated `searchable_text`
- ✅ Search finds resources with new metadata
- ✅ Autocomplete shows updated suggestions
- ✅ Embeddings match current content
- ✅ No orphaned chunks or stale data

## Performance Considerations

### Async Background Processing
- Use `asyncio.create_task()` for non-blocking updates
- Queue heavy operations (embedding regeneration)
- Batch process multiple resources

### Rate Limiting
- Limit reindexing frequency per resource (max 1x per minute)
- Use debouncing for rapid updates
- Priority queue: UI-triggered updates > automatic updates

### Monitoring
- Log reindexing operations
- Track success/failure rates
- Alert on queue backlog

## Rollout Plan

### Phase 1: Image Description Fix (Quick Win)
- Modify image processor
- Deploy and test
- Verify user descriptions preserved

### Phase 2: Event System (Foundation)
- Implement event service
- Add hooks to resource manager
- Test event firing

### Phase 3: Chunk Regeneration (Core Feature)
- Implement reindexing service
- Test chunk updates
- Verify search consistency

### Phase 4: Redis Sync (Polish)
- Implement suggestion updates
- Test autocomplete accuracy
- Monitor performance

### Phase 5: Cleanup & Optimization
- Add environment flags
- Optimize batch processing
- Add monitoring/alerts

## Documentation Updates

Update the following docs:
- API documentation (resource update behavior)
- Architecture overview (event-driven reindexing)
- Performance tuning guide
- Troubleshooting guide

## Success Metrics

- ✅ Zero stale search results after resource updates
- ✅ Autocomplete always shows current resources
- ✅ User descriptions never lost
- ✅ < 5 second delay for reindexing to complete
- ✅ < 1% failure rate for background tasks
