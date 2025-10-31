# Contextual Search Implementation Progress

**Started**: 2025-10-31  
**Status**: 🚧 In Progress  

---

## ✅ Phase 1: Data Model Redesign (COMPLETE)

**Duration**: 30 minutes  
**Date**: 2025-10-31  

### What Was Done

#### 1. Updated Resource Model
**File**: `src/ai_mcp_toolkit/models/documents.py`

Added **30+ new fields** to Resource model:

**Core Identifiers**:
- `file_id` - Unique file identifier
- `file_name` - Original filename
- `file_type` - File type classification

**Multi-Tenant**:
- `company_id` - For tenant isolation (ACL)

**File Metadata**:
- `size_bytes` - File size
- `tags` - Tagging system
- `summary` - AI-generated summary

**Structured Search Fields**:
- `vendor` - Normalized vendor names (google, t-mobile)
- `currency` - ISO currency codes (USD, EUR, CZK)
- `amounts_cents` - Money amounts in cents [930, 1500]
- `invoice_no` - Invoice numbers
- `entities` - Named entities
- `keywords` - Exact searchable values
- `dates` - Extracted dates

**Image-Specific**:
- `image_labels` - Image classifications [london, bridge]
- `ocr_text` - OCR extracted text
- `image_width`, `image_height` - Dimensions

**CSV-Specific**:
- `csv_schema` - Column definitions
- `csv_stats` - Statistics (row count, min/max values)

**Multi-Modal Embeddings**:
- `text_embedding` - Text semantic vector (1536 dims)
- `image_embedding` - Image semantic vector (768 dims)
- `embeddings_model` - Model identifier

**Indexes Added**:
- company_id, file_type, vendor, currency
- Compound indexes for efficient queries
- Date range indexes

#### 2. Created ResourceChunk Model
**File**: `src/ai_mcp_toolkit/models/documents.py`

New model for chunk-level search (PDF pages, CSV rows, image regions):

**Fields**:
- `parent_id` - Reference to parent Resource
- `chunk_type` - "text", "page", "row", "cell", "region"
- `chunk_index` - Sequential index
- `page_number` - For PDFs
- `row_index`, `col_index` - For CSVs
- `bbox` - Bounding box for images [x, y, w, h]
- `text` - Extracted text content
- `text_embedding`, `image_embedding` - Vector embeddings
- All searchable fields (currency, amounts, entities, keywords, dates)

**Indexes**:
- parent_id, company_id, chunk_type
- page_number, row_index (for precise navigation)
- Compound indexes for search optimization

#### 3. Updated Database Initialization
**File**: `src/ai_mcp_toolkit/models/database.py`

- Added ResourceChunk to Beanie document models list
- Will be automatically indexed on first connection

### Backward Compatibility

✅ All existing fields preserved  
✅ New fields are optional (don't break existing code)  
✅ Legacy `embeddings` field kept for compatibility  
✅ Existing resources continue to work without migration  

### Testing

```python
# Test new models
from ai_mcp_toolkit.models.documents import Resource, ResourceChunk

# Create resource with new fields
resource = Resource(
    uri="file:///user_id/uuid.pdf",
    name="Invoice",
    file_type="pdf",
    company_id="user_123",
    vendor="google",
    currency="USD",
    amounts_cents=[930],
    keywords=["INV-1234"],
    text_embedding=[0.1, 0.2, ...]  # 1536 dims
)

# Create chunk
chunk = ResourceChunk(
    parent_id=str(resource.id),
    chunk_type="page",
    page_number=1,
    text="Page 1 content...",
    company_id="user_123",
    text_embedding=[0.1, 0.2, ...]
)
```

---

## 🚧 Phase 2: File Processors (NEXT)

**Estimated Time**: 8-12 hours  
**Status**: Not Started  

### Tasks

- [ ] Create PDFProcessor for PDF extraction
- [ ] Create CSVProcessor for CSV parsing
- [ ] Create ImageProcessor for image analysis
- [ ] Create TextProcessor for structured files
- [ ] Update upload endpoint to route to processors

### Files to Create

- `src/ai_mcp_toolkit/processors/__init__.py`
- `src/ai_mcp_toolkit/processors/pdf_processor.py`
- `src/ai_mcp_toolkit/processors/csv_processor.py`
- `src/ai_mcp_toolkit/processors/image_processor.py`
- `src/ai_mcp_toolkit/processors/text_processor.py`
- `src/ai_mcp_toolkit/processors/base_processor.py`

---

## 📋 Phase 3: Atlas Search Indexes (TODO)

**Estimated Time**: 2-3 hours  
**Status**: Not Started  

Manual setup via MongoDB Atlas UI:
- Resources index (hybrid search)
- Chunks index (precise matching)

---

## 📋 Phase 4: Query Router (TODO)

**Estimated Time**: 6-8 hours  
**Status**: Not Started  

Files to create:
- `src/ai_mcp_toolkit/search/query_classifier.py`
- `src/ai_mcp_toolkit/search/search_builder.py`
- `/search/contextual` endpoint

---

## 📋 Phase 5: Viewer Routes (TODO)

**Estimated Time**: 4-6 hours  
**Status**: Not Started  

---

## 📋 Phase 6: Frontend UI (TODO)

**Estimated Time**: 6-8 hours  
**Status**: Not Started  

---

## 📋 Phase 7: Testing (TODO)

**Estimated Time**: 8 hours  
**Status**: Not Started  

---

## Next Steps

1. ✅ **Restart server** to load new models
2. ✅ **Verify** models are registered
3. ➡️ **Start Phase 2** - Create file processors

### Restart Command

```bash
# Stop current server (if running)
# Start fresh
cd /Users/roza/Sites/ai-mcp-toolkit
python main.py
```

### Verify Models

```python
# In Python console
from ai_mcp_toolkit.models.documents import Resource, ResourceChunk
print("Resource fields:", Resource.model_fields.keys())
print("ResourceChunk fields:", ResourceChunk.model_fields.keys())
```

---

**Status**: Phase 1 complete! Ready for Phase 2. 🚀
