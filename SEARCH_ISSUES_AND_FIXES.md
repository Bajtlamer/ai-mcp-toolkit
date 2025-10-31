# Search System Issues & Fixes

## Problems Found

### 1. ✅ FIXED: Missing Required Resource Fields
**Problem**: Ingestion service wasn't populating required MCP fields
- Missing: `uri`, `name`, `description`, `resource_type`, `owner_id`
- This caused resources to fail validation or have null values

**Fix Applied**: Updated `ingestion_service.py` to populate BOTH:
- OLD MCP fields (uri, name, description, resource_type, owner_id)
- NEW search fields (file_id, file_name, file_type, etc.)

### 2. ❌ NOT FIXED: Search Doesn't Search Actual Text Content
**Problem**: Search only uses:
- Vector embeddings (semantic similarity)
- Metadata fields (vendor, keywords, entities)

**NOT searching**:
- `content` field (the actual PDF text!)
- `summary` field
- ResourceChunk text content

**Why This Fails**: 
When you upload a PDF with text, the text isn't being searched. Only the embedding similarity is checked, which requires the query to be semantically similar to the summary/filename.

### 3. ❌ NOT FIXED: Auto-Search on Every Keystroke
**Problem**: Search triggers automatically after 500ms of typing
- You want "prompt-like" search (type full query, press Enter/button)
- Current: searches as you type "XYZ" → searches "X", then "XY", then "XYZ"

### 4. ❌ NOT FIXED: No Full-Text Search on Content
**Problem**: Need to add MongoDB text search or regex search on:
- `Resource.content` - the actual file text
- `Resource.summary` - file summary
- `Resource.name` / `Resource.file_name` - filename
- `ResourceChunk.text` - chunk text for detailed search

## Recommended Fixes

### Fix 1: Add Text-Based Search
Add a new search method that does actual text matching:

```python
async def _text_search(self, query, company_id, limit):
    # Search in content, summary, name fields
    # Use MongoDB regex or full-text search
    resources = await Resource.find({
        'company_id': company_id,
        '$or': [
            {'content': {'$regex': query, '$options': 'i'}},
            {'summary': {'$regex': query, '$options': 'i'}},
            {'name': {'$regex': query, '$options': 'i'}},
            {'entities': query},  # exact match in entities
        ]
    }).to_list(limit)
```

### Fix 2: Remove Auto-Search
In search UI (`search/+page.svelte`):
- Remove `on:input={onQueryChange}` from textarea
- Only search on Enter key or button click
- Remove debounceTimer logic

### Fix 3: Store PDF Text in Content Field
In `ingestion_service.py`:
- For PDFs: extract ALL text and store in `content` field
- For CSVs: store formatted text representation
- For text files: store the text content

Currently we're NOT storing the extracted text anywhere searchable!

## What Needs To Happen Next

1. **Test Current Fix**: Restart server, upload a PDF, check if fields are populated
2. **Add Text Search**: Modify `search_service.py` to search actual content
3. **Remove Auto-Search**: Modify UI to only search on explicit action
4. **Store Content**: Ensure processors extract and store searchable text

## Testing Checklist

- [ ] Upload PDF with text → check `content` field has text
- [ ] Search for word from PDF → should find it
- [ ] Search for company name in PDF → should find it
- [ ] Check Resource has: uri, name, description, file_name, file_type
- [ ] Search only triggers on Enter or button click

---

**Status**: Partial fix applied (required fields). Text search still needs implementation.
