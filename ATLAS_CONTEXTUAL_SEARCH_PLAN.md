# Atlas Contextual Search System - Implementation Plan

**Created**: 2025-10-31  
**Status**: 📋 Planning Phase  
**Priority**: 🔴 High (Core Feature)  
**Estimated Time**: 5-7 days  
**Type**: Major Architecture Enhancement

---

## Executive Summary

Build a **production-ready intelligent search system** that "just finds it" across PDFs, text files, CSVs, images, and structured data using MongoDB Atlas hybrid search (vector + lexical + filters).

### Key Goals

✅ **Universal Search** - One search box for all file types  
✅ **Hybrid Search** - Vector embeddings + keyword + numeric/date filters  
✅ **Precise Links** - Jump to exact PDF page / CSV row / image region  
✅ **Smart Routing** - Auto-detect money, IDs, dates, image queries  
✅ **Multi-Modal** - Text + Image embeddings (CLIP/SigLIP)  
✅ **No Hallucinations** - Only real retrieved data  
✅ **User Isolation** - Per-user ACL via `companyId`/`userId`  

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    MCP Server (Orchestrator)                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  User Query: "invoice 9 USD" or "CSV with ID 2363836738"        │
│         ↓                                                        │
│  Query Router (classify intent)                                  │
│         ↓                                                        │
│  Build Atlas $search compound query:                            │
│    - must: currency=USD, amounts=[830-1030]                     │
│    - should: knnVector(textEmbedding) + text(keywords)          │
│         ↓                                                        │
│  MongoDB Atlas Hybrid Search                                     │
│    - Vector Search (semantic)                                   │
│    - Text Search (lexical)                                      │
│    - Filters (numeric, date, exact)                             │
│         ↓                                                        │
│  Return results with links:                                      │
│    - PDF: /viewer/pdf?file=X&page=4                            │
│    - CSV: /viewer/csv?file=X&row=123                           │
│    - Image: /viewer/image?file=X&bbox=...                      │
│         ↓                                                        │
│  Optional: LLM phrasing (no hallucinations)                     │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Data Model Redesign (Day 1, 4-6 hours)

### Current State
- Simple Resource model with basic metadata
- No chunking strategy
- No structured fields for search

### Target State
- Unified file + chunk model
- Rich metadata extraction
- Multi-modal embeddings support

### Task 1.1: Update Resource Model

**File**: `src/ai_mcp_toolkit/models/documents.py`

**New fields for file-level documents**:

```python
class Resource(Document):
    # === Existing fields ===
    uri: str
    name: str
    description: str
    mime_type: str
    resource_type: ResourceType
    owner_id: str
    content: Optional[str]
    
    # === NEW: Core identifiers ===
    file_id: str  # "files/2025/10/INV-1234.pdf"
    file_name: str  # Original filename
    file_type: str  # "pdf", "text", "csv", "image", "structured"
    
    # === NEW: Multi-tenant / ACL ===
    company_id: str  # For tenant isolation (use owner_id for now)
    
    # === NEW: File metadata ===
    size_bytes: int
    tags: List[str] = []
    summary: Optional[str] = None  # AI-generated summary
    
    # === NEW: Structured data fields ===
    vendor: Optional[str] = None  # Normalized vendor name
    currency: Optional[str] = None  # "USD", "EUR", "CZK"
    amounts_cents: List[int] = []  # Money amounts in cents [930, 1500]
    invoice_no: Optional[str] = None
    entities: List[str] = []  # Named entities ["t-mobile", "contract"]
    keywords: List[str] = []  # Exact searchable values (IDs, emails, etc.)
    dates: List[datetime] = []  # Extracted dates
    
    # === NEW: Image-specific ===
    image_labels: List[str] = []  # ["london", "bridge", "cityscape"]
    ocr_text: Optional[str] = None
    image_width: Optional[int] = None
    image_height: Optional[int] = None
    
    # === NEW: CSV-specific ===
    csv_schema: Optional[Dict[str, Any]] = None  # {"columns": ["date", "amount"]}
    csv_stats: Optional[Dict[str, Any]] = None  # {"rowCount": 123, "minAmount": 100}
    
    # === NEW: Multi-modal embeddings ===
    text_embedding: Optional[List[float]] = None  # Text semantic vector
    image_embedding: Optional[List[float]] = None  # Image semantic vector
    embeddings_model: Optional[str] = None  # Model used
    
    # === Existing metadata ===
    metadata: ResourceMetadata
    created_at: datetime
    updated_at: datetime
    
    class Settings:
        name = "resources"
        indexes = [
            "owner_id",
            "company_id",
            "file_type",
            "currency",
            "vendor",
            [("dates", pymongo.ASCENDING)],
            # Atlas Search index created separately
        ]
```

### Task 1.2: Create Chunk Model

**File**: `src/ai_mcp_toolkit/models/documents.py`

```python
class ResourceChunk(Document):
    """Chunk/part of a larger resource (PDF pages, CSV rows, image regions)."""
    
    # === Parent reference ===
    parent_id: str  # Reference to Resource._id
    resource_uri: str  # For easy lookup
    
    # === Chunk identification ===
    chunk_type: str  # "text", "page", "row", "cell", "region"
    chunk_index: int  # Sequential index
    
    # === Location metadata ===
    page_number: Optional[int] = None  # For PDFs
    row_index: Optional[int] = None  # For CSVs
    col_index: Optional[int] = None  # For CSV cells
    bbox: Optional[List[float]] = None  # [x, y, width, height] for images/PDFs
    
    # === Content ===
    text: Optional[str] = None  # Extracted text
    text_embedding: Optional[List[float]] = None
    image_embedding: Optional[List[float]] = None
    
    # === Structured fields (inherited from parent for search) ===
    company_id: str  # ACL
    file_type: str
    currency: Optional[str] = None
    amounts_cents: List[int] = []
    entities: List[str] = []
    keywords: List[str] = []  # Exact values (for CSV cells)
    dates: List[datetime] = []
    
    # === Image-specific ===
    image_labels: List[str] = []
    ocr_text: Optional[str] = None
    
    # === Search score (populated at query time) ===
    score: Optional[float] = None
    
    created_at: datetime
    
    class Settings:
        name = "resource_chunks"
        indexes = [
            "parent_id",
            "company_id",
            "chunk_type",
            "page_number",
            "row_index",
            [("dates", pymongo.ASCENDING)],
        ]
```

### Task 1.3: Create Migration Script

**File**: `src/ai_mcp_toolkit/scripts/migrate_to_unified_search.py`

```python
"""Migrate existing resources to new unified search model."""

async def migrate_existing_resources():
    """
    1. Add new fields to existing Resource documents
    2. No chunks created yet (Phase 2)
    3. Preserve all existing data
    """
    pass
```

---

## Phase 2: Ingestion Pipeline per File Type (Day 2-3, 8-12 hours)

### Task 2.1: PDF Ingestion

**File**: `src/ai_mcp_toolkit/processors/pdf_processor.py` (NEW)

```python
class PDFProcessor:
    """Extract metadata and chunks from PDFs."""
    
    async def process(self, file_bytes: bytes, metadata: dict) -> dict:
        """
        Returns:
        {
            "file_metadata": {...},  # File-level fields
            "chunks": [...]           # Page-level chunks
        }
        """
        # 1. Extract text from all pages
        # 2. Extract metadata (dates, amounts, entities)
        # 3. Create page-level chunks
        # 4. Generate text embeddings per chunk
        # 5. OCR if needed (pytesseract)
        pass
    
    def extract_amounts(self, text: str) -> List[int]:
        """Extract money amounts in cents."""
        # Regex: $9.30, 9.30 USD, €10.00
        pass
    
    def extract_entities(self, text: str) -> List[str]:
        """Extract entities: vendors, invoice numbers, etc."""
        pass
```

### Task 2.2: CSV Ingestion

**File**: `src/ai_mcp_toolkit/processors/csv_processor.py` (NEW)

```python
class CSVProcessor:
    """Extract schema and create searchable rows from CSV."""
    
    async def process(self, file_bytes: bytes, metadata: dict) -> dict:
        """
        Returns:
        {
            "file_metadata": {
                "csv_schema": {"columns": ["date", "amount", "vendor"]},
                "csv_stats": {"rowCount": 123, "minAmount": 100}
            },
            "chunks": [
                {
                    "chunk_type": "row",
                    "row_index": 0,
                    "text": "date: 2025-10-01, amount: 9.30, vendor: t-mobile",
                    "keywords": ["2025-10-01", "9.30", "t-mobile"],
                    "amounts_cents": [930]
                },
                ...
            ]
        }
        """
        # 1. Parse CSV (pandas/csv module)
        # 2. Detect schema (columns, types)
        # 3. Calculate stats
        # 4. Create row-level chunks with:
        #    - Serialized text for embedding
        #    - Exact values in keywords
        #    - Extracted amounts/dates
        # 5. For huge CSVs (>10k rows), sample or index-only
        pass
```

### Task 2.3: Image Ingestion

**File**: `src/ai_mcp_toolkit/processors/image_processor.py` (NEW)

```python
class ImageProcessor:
    """Extract captions, labels, OCR, and embeddings from images."""
    
    async def process(self, file_bytes: bytes, metadata: dict) -> dict:
        """
        Returns:
        {
            "file_metadata": {
                "image_labels": ["london", "bridge", "night"],
                "ocr_text": "Tower Bridge",
                "image_width": 1920,
                "image_height": 1080,
                "image_embedding": [0.1, 0.2, ...]
            },
            "chunks": []  # No chunks for simple images (or regions if needed)
        }
        """
        # 1. Generate caption (BLIP/Florence/Qwen-VL via Ollama?)
        # 2. Extract labels (via caption or classification model)
        # 3. OCR text (pytesseract/paddle-ocr)
        # 4. Generate image embedding (CLIP/SigLIP)
        # 5. Detect places/landmarks (optional)
        pass
    
    async def generate_image_embedding(self, image: PIL.Image) -> List[float]:
        """Use CLIP/SigLIP to generate image vector."""
        # Option A: Ollama with llava or similar
        # Option B: OpenAI CLIP API
        # Option C: Local transformers CLIP
        pass
```

### Task 2.4: Text/Structured File Ingestion

**File**: `src/ai_mcp_toolkit/processors/text_processor.py` (NEW)

```python
class TextProcessor:
    """Process plain text, JSON, XML, INI, YAML, etc."""
    
    async def process(self, file_bytes: bytes, metadata: dict) -> dict:
        """
        Returns:
        {
            "file_metadata": {...},
            "chunks": [...]  # Chunked by paragraphs or fixed size
        }
        """
        # 1. Detect encoding
        # 2. Parse structured formats (JSON/YAML/INI)
        # 3. Extract key-value pairs
        # 4. Create chunks
        # 5. Extract entities/keywords
        pass
```

### Task 2.5: Update Upload Endpoint

**File**: `src/ai_mcp_toolkit/server/http_server.py`

```python
from ..processors.pdf_processor import PDFProcessor
from ..processors.csv_processor import CSVProcessor
from ..processors.image_processor import ImageProcessor
from ..processors.text_processor import TextProcessor

@app.post("/resources/upload")
async def upload_resource(...):
    # ... existing code ...
    
    # NEW: Route to appropriate processor
    processor = None
    if mime_type == 'application/pdf':
        processor = PDFProcessor()
    elif mime_type == 'text/csv':
        processor = CSVProcessor()
    elif mime_type.startswith('image/'):
        processor = ImageProcessor()
    elif mime_type.startswith('text/'):
        processor = TextProcessor()
    
    if processor:
        result = await processor.process(content_bytes, metadata)
        
        # Create file-level Resource
        resource = await resource_manager.create_resource(
            **result['file_metadata']
        )
        
        # Create chunks
        for chunk_data in result['chunks']:
            chunk = ResourceChunk(
                parent_id=str(resource.id),
                company_id=owner_id,
                **chunk_data
            )
            await chunk.save()
```

---

## Phase 3: MongoDB Atlas Search Index (Day 3, 2-3 hours)

### Task 3.1: Create Atlas Search Index

**Manual via Atlas UI** or **Atlas CLI**:

```json
{
  "name": "resources_unified_search",
  "type": "search",
  "database": "ai_mcp_toolkit",
  "collectionName": "resources",
  "mappings": {
    "dynamic": false,
    "fields": {
      "company_id": {
        "type": "string",
        "analyzer": "keyword"
      },
      "file_type": {
        "type": "string",
        "analyzer": "keyword"
      },
      "file_name": {
        "type": "string",
        "analyzer": "standard"
      },
      "mime_type": {
        "type": "string",
        "analyzer": "keyword"
      },
      "tags": {
        "type": "string",
        "analyzer": "standard"
      },
      "vendor": {
        "type": "string",
        "analyzer": "keyword"
      },
      "currency": {
        "type": "string",
        "analyzer": "keyword"
      },
      "amounts_cents": {
        "type": "number"
      },
      "invoice_no": {
        "type": "string",
        "analyzer": "keyword"
      },
      "keywords": {
        "type": "string",
        "analyzer": "keyword"
      },
      "entities": {
        "type": "string",
        "analyzer": "standard"
      },
      "dates": {
        "type": "date"
      },
      "text": {
        "type": "string",
        "analyzer": "standard"
      },
      "content": {
        "type": "string",
        "analyzer": "standard"
      },
      "summary": {
        "type": "string",
        "analyzer": "standard"
      },
      "ocr_text": {
        "type": "string",
        "analyzer": "standard"
      },
      "image_labels": {
        "type": "string",
        "analyzer": "standard"
      },
      "text_embedding": {
        "type": "knnVector",
        "dimensions": 1536,
        "similarity": "cosine"
      },
      "image_embedding": {
        "type": "knnVector",
        "dimensions": 768,
        "similarity": "cosine"
      }
    }
  }
}
```

### Task 3.2: Create Chunks Index

```json
{
  "name": "chunks_unified_search",
  "type": "search",
  "database": "ai_mcp_toolkit",
  "collectionName": "resource_chunks",
  "mappings": {
    "dynamic": false,
    "fields": {
      "parent_id": { "type": "string", "analyzer": "keyword" },
      "company_id": { "type": "string", "analyzer": "keyword" },
      "chunk_type": { "type": "string", "analyzer": "keyword" },
      "file_type": { "type": "string", "analyzer": "keyword" },
      "page_number": { "type": "number" },
      "row_index": { "type": "number" },
      "text": { "type": "string", "analyzer": "standard" },
      "keywords": { "type": "string", "analyzer": "keyword" },
      "entities": { "type": "string", "analyzer": "standard" },
      "currency": { "type": "string", "analyzer": "keyword" },
      "amounts_cents": { "type": "number" },
      "dates": { "type": "date" },
      "ocr_text": { "type": "string", "analyzer": "standard" },
      "image_labels": { "type": "string", "analyzer": "standard" },
      "text_embedding": {
        "type": "knnVector",
        "dimensions": 1536,
        "similarity": "cosine"
      },
      "image_embedding": {
        "type": "knnVector",
        "dimensions": 768,
        "similarity": "cosine"
      }
    }
  }
}
```

---

## Phase 4: Query Router & Search Logic (Day 4, 6-8 hours)

### Task 4.1: Create Query Classifier

**File**: `src/ai_mcp_toolkit/search/query_classifier.py` (NEW)

```python
class QueryClassifier:
    """Analyze user query to determine search strategy."""
    
    def classify(self, query: str) -> dict:
        """
        Returns:
        {
            "has_money": True,
            "currency": "USD",
            "amounts_cents": [930],
            "tolerance_percent": 10,
            
            "has_exact_ids": True,
            "exact_values": ["2363836738", "INV-1234"],
            
            "has_date": True,
            "dates": ["2025-10-01"],
            
            "wants_images": True,
            "image_query": "london bridge",
            
            "wants_csv": False,
            
            "semantic_query": "invoice from t-mobile",
            "keywords": ["invoice", "t-mobile"]
        }
        """
        result = {
            "has_money": False,
            "has_exact_ids": False,
            "has_date": False,
            "wants_images": False,
            "wants_csv": False,
            "semantic_query": query,
            "keywords": []
        }
        
        # 1. Detect money patterns
        money_patterns = [
            r'\$(\d+\.?\d*)',
            r'(\d+\.?\d*)\s*(USD|EUR|CZK|GBP)',
            r'(\d+\.?\d*)\s*(dollars?|euros?)'
        ]
        # ... extract amounts and currency
        
        # 2. Detect long IDs (digits/alphanumeric)
        id_patterns = [
            r'\b\d{8,}\b',  # Long numbers
            r'\bINV-\d+\b',  # Invoice patterns
            r'\b[A-Z]{2}\d{2}\w+\b'  # IBAN-like
        ]
        # ... extract exact IDs
        
        # 3. Detect dates
        # Use dateutil.parser or regex
        
        # 4. Detect image intent
        image_keywords = ['image', 'photo', 'picture', 'screenshot']
        if any(kw in query.lower() for kw in image_keywords):
            result["wants_images"] = True
        
        # 5. Detect CSV intent
        if 'csv' in query.lower() or 'spreadsheet' in query.lower():
            result["wants_csv"] = True
        
        return result
```

### Task 4.2: Create Search Builder

**File**: `src/ai_mcp_toolkit/search/search_builder.py` (NEW)

```python
class SearchBuilder:
    """Build MongoDB Atlas $search compound queries."""
    
    def __init__(self, embedding_manager, clip_manager=None):
        self.embedding_manager = embedding_manager
        self.clip_manager = clip_manager
    
    async def build_search_pipeline(
        self,
        query: str,
        classification: dict,
        company_id: str,
        limit: int = 30
    ) -> List[dict]:
        """
        Build Atlas $search aggregation pipeline.
        
        Returns MongoDB aggregation pipeline like:
        [
            {
                "$search": {
                    "index": "resources_unified_search",
                    "compound": {
                        "must": [...],
                        "should": [...],
                        "minimumShouldMatch": 1
                    }
                }
            },
            {"$limit": 30},
            {"$project": {...}}
        ]
        """
        
        must_clauses = []
        should_clauses = []
        
        # 1. MUST: Company/User isolation (ACL)
        must_clauses.append({
            "equals": {
                "path": "company_id",
                "value": company_id
            }
        })
        
        # 2. MUST: Money filters
        if classification["has_money"]:
            cents = classification["amounts_cents"][0]
            tolerance = int(cents * classification["tolerance_percent"] / 100)
            
            must_clauses.append({
                "equals": {
                    "path": "currency",
                    "value": classification["currency"]
                }
            })
            
            must_clauses.append({
                "range": {
                    "path": "amounts_cents",
                    "gte": cents - tolerance,
                    "lte": cents + tolerance
                }
            })
        
        # 3. MUST: Exact ID matches
        if classification["has_exact_ids"]:
            for exact_val in classification["exact_values"]:
                must_clauses.append({
                    "phrase": {
                        "path": "keywords",
                        "query": exact_val
                    }
                })
        
        # 4. SHOULD: Semantic vector search
        if classification["semantic_query"]:
            # Generate embedding
            query_embedding = await self.embedding_manager.generate_embedding(
                classification["semantic_query"]
            )
            
            should_clauses.append({
                "knnBeta": {
                    "path": "text_embedding",
                    "vector": query_embedding,
                    "k": 64
                }
            })
        
        # 5. SHOULD: Image search (multi-modal)
        if classification["wants_images"]:
            # Text search on image fields
            should_clauses.append({
                "text": {
                    "path": ["image_labels", "ocr_text", "summary"],
                    "query": classification["image_query"]
                }
            })
            
            # Cross-modal: text query → image embedding
            if self.clip_manager:
                image_embedding = await self.clip_manager.text_to_image_embedding(
                    classification["image_query"]
                )
                should_clauses.append({
                    "knnBeta": {
                        "path": "image_embedding",
                        "vector": image_embedding,
                        "k": 32
                    }
                })
        
        # 6. SHOULD: Keyword/lexical search
        search_fields = ["content", "text", "summary", "entities", "vendor", "file_name"]
        should_clauses.append({
            "text": {
                "path": search_fields,
                "query": query,
                "score": {
                    "boost": {
                        "value": 2.0
                    }
                }
            }
        })
        
        # 7. Build pipeline
        pipeline = [
            {
                "$search": {
                    "index": "resources_unified_search",
                    "compound": {
                        "must": must_clauses,
                        "should": should_clauses,
                        "minimumShouldMatch": 1 if should_clauses else 0
                    }
                }
            },
            {"$limit": limit},
            {
                "$project": {
                    "file_id": 1,
                    "file_name": 1,
                    "file_type": 1,
                    "vendor": 1,
                    "currency": 1,
                    "amounts_cents": 1,
                    "invoice_no": 1,
                    "image_labels": 1,
                    "page_number": 1,
                    "row_index": 1,
                    "bbox": 1,
                    "summary": 1,
                    "score": {"$meta": "searchScore"},
                    "highlights": {"$meta": "searchHighlights"}
                }
            }
        ]
        
        return pipeline
```

### Task 4.3: Create Search Endpoint

**File**: `src/ai_mcp_toolkit/server/http_server.py`

```python
from ..search.query_classifier import QueryClassifier
from ..search.search_builder import SearchBuilder

@app.post("/search/contextual")
async def contextual_search(
    query: str,
    limit: int = 30,
    search_chunks: bool = False,
    user: User = Depends(require_auth)
):
    """
    Universal contextual search across all resource types.
    
    Examples:
    - "invoice 9 USD"
    - "CSV with ID 2363836738"
    - "image including London"
    - "contract with T-Mobile"
    """
    try:
        # 1. Classify query
        classifier = QueryClassifier()
        classification = classifier.classify(query)
        
        logger.info(f"Query classification: {classification}")
        
        # 2. Build search pipeline
        builder = SearchBuilder(
            embedding_manager=embedding_manager,
            clip_manager=clip_manager if has_clip else None
        )
        
        company_id = str(user.id)  # Using user.id as company_id for now
        
        # Choose collection: files or chunks
        if search_chunks or classification.get("wants_precise"):
            collection = ResourceChunk
            index_name = "chunks_unified_search"
        else:
            collection = Resource
            index_name = "resources_unified_search"
        
        pipeline = await builder.build_search_pipeline(
            query=query,
            classification=classification,
            company_id=company_id,
            limit=limit
        )
        
        # 3. Execute search
        results = await collection.aggregate(pipeline).to_list()
        
        # 4. Generate links
        results_with_links = []
        for doc in results:
            link = generate_viewer_link(doc)
            results_with_links.append({
                **doc,
                "link": link,
                "snippet": generate_snippet(doc, classification)
            })
        
        logger.info(
            f"Contextual search by {user.username}: '{query}' → "
            f"{len(results)} results"
        )
        
        return {
            "query": query,
            "classification": classification,
            "results": results_with_links,
            "count": len(results)
        }
        
    except Exception as e:
        logger.error(f"Contextual search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


def generate_viewer_link(doc: dict) -> str:
    """Generate link to open file at exact location."""
    file_id = doc.get("file_id")
    file_type = doc.get("file_type")
    
    if file_type == "pdf" and doc.get("page_number"):
        return f"/viewer/pdf?file={file_id}&page={doc['page_number']}"
    
    elif file_type == "csv":
        if doc.get("row_index") is not None:
            row = doc["row_index"]
            col = doc.get("col_index")
            if col is not None:
                return f"/viewer/csv?file={file_id}&row={row}&col={col}"
            return f"/viewer/csv?file={file_id}&row={row}"
    
    elif file_type == "image":
        link = f"/viewer/image?file={file_id}"
        if doc.get("bbox"):
            bbox = doc["bbox"]
            link += f"&x={bbox[0]}&y={bbox[1]}&w={bbox[2]}&h={bbox[3]}"
        return link
    
    else:
        return f"/viewer/file?file={file_id}"
```

---

## Phase 5: Link Generation & Viewer Routes (Day 5, 4-6 hours)

### Task 5.1: PDF Viewer Endpoint

**File**: `src/ai_mcp_toolkit/server/http_server.py`

```python
@app.get("/viewer/pdf")
async def view_pdf(
    file: str,
    page: int = 1,
    user: User = Depends(require_auth)
):
    """
    Serve PDF with page parameter.
    Frontend can use PDF.js to jump to page.
    """
    # 1. Verify user owns the resource
    # 2. Return PDF bytes or redirect to storage
    # 3. Include page parameter in response metadata
    pass
```

### Task 5.2: CSV Viewer Endpoint

```python
@app.get("/viewer/csv")
async def view_csv(
    file: str,
    row: Optional[int] = None,
    col: Optional[int] = None,
    user: User = Depends(require_auth)
):
    """
    Return CSV data with highlighted row/cell.
    """
    # 1. Parse CSV
    # 2. Return as JSON with highlight info
    # 3. Frontend can render with ag-Grid or similar
    pass
```

### Task 5.3: Image Viewer Endpoint

```python
@app.get("/viewer/image")
async def view_image(
    file: str,
    x: Optional[float] = None,
    y: Optional[float] = None,
    w: Optional[float] = None,
    h: Optional[float] = None,
    user: User = Depends(require_auth)
):
    """
    Serve image with optional bounding box.
    """
    # Return image bytes + bbox metadata
    pass
```

---

## Phase 6: Frontend Search UI (Day 6, 6-8 hours)

### Task 6.1: Universal Search Component

**File**: `ui/src/lib/components/UniversalSearch.svelte` (NEW)

```svelte
<script>
  import { Search, Filter, FileText, Image, Table } from 'lucide-svelte';
  
  let query = '';
  let results = [];
  let loading = false;
  let filters = {
    fileType: 'all',  // pdf, csv, image, text, all
    dateRange: null,
    minAmount: null,
    maxAmount: null
  };
  
  async function search() {
    loading = true;
    try {
      const response = await fetch('/search/contextual', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          query,
          limit: 50
        })
      });
      
      const data = await response.json();
      results = data.results;
    } finally {
      loading = false;
    }
  }
  
  function getIcon(fileType) {
    switch(fileType) {
      case 'pdf': return FileText;
      case 'image': return Image;
      case 'csv': return Table;
      default: return FileText;
    }
  }
</script>

<div class="max-w-6xl mx-auto p-6">
  <!-- Search Box -->
  <div class="mb-6">
    <div class="relative">
      <input
        type="text"
        bind:value={query}
        on:keydown={(e) => e.key === 'Enter' && search()}
        placeholder="Search: 'invoice 9 USD', 'CSV with ID 2363836738', 'image of London'..."
        class="w-full px-4 py-3 pl-12 pr-4 text-lg border-2 border-gray-300 rounded-xl focus:border-blue-500 focus:outline-none"
      />
      <Search class="absolute left-4 top-3.5 w-5 h-5 text-gray-400" />
      
      <button
        on:click={search}
        disabled={loading || !query}
        class="absolute right-2 top-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
      >
        {loading ? 'Searching...' : 'Search'}
      </button>
    </div>
    
    <!-- Search hints -->
    <div class="mt-2 text-sm text-gray-500">
      Try: <button class="text-blue-600 hover:underline" on:click={() => query = 'invoice 9 USD'}>invoice 9 USD</button>,
      <button class="text-blue-600 hover:underline" on:click={() => query = 'CSV with contract'}>CSV with contract</button>,
      <button class="text-blue-600 hover:underline" on:click={() => query = 'image of tower'}>image of tower</button>
    </div>
  </div>
  
  <!-- Results -->
  {#if results.length > 0}
    <div class="space-y-3">
      {#each results as result}
        <a
          href={result.link}
          class="block p-4 bg-white border border-gray-200 rounded-lg hover:shadow-md transition-shadow"
        >
          <div class="flex items-start space-x-3">
            <div class="flex-shrink-0 mt-1">
              <svelte:component this={getIcon(result.file_type)} class="w-5 h-5 text-gray-500" />
            </div>
            
            <div class="flex-1 min-w-0">
              <div class="flex items-center justify-between">
                <h3 class="text-lg font-semibold text-gray-900 truncate">
                  {result.file_name}
                </h3>
                <span class="text-sm text-gray-500">
                  {(result.score * 100).toFixed(0)}% match
                </span>
              </div>
              
              {#if result.snippet}
                <p class="mt-1 text-sm text-gray-600">
                  {@html result.snippet}
                </p>
              {/if}
              
              <div class="mt-2 flex items-center space-x-4 text-xs text-gray-500">
                {#if result.page_number}
                  <span>Page {result.page_number}</span>
                {/if}
                {#if result.row_index !== undefined}
                  <span>Row {result.row_index}</span>
                {/if}
                {#if result.currency && result.amounts_cents?.length}
                  <span class="font-semibold text-green-600">
                    {result.currency} {(result.amounts_cents[0] / 100).toFixed(2)}
                  </span>
                {/if}
                {#if result.vendor}
                  <span class="text-blue-600">{result.vendor}</span>
                {/if}
              </div>
            </div>
          </div>
        </a>
      {/each}
    </div>
  {:else if !loading && query}
    <div class="text-center py-12 text-gray-500">
      No results found for "{query}"
    </div>
  {/if}
</div>
```

### Task 6.2: File Viewers

Create viewer components:
- `ui/src/routes/viewer/pdf/+page.svelte`
- `ui/src/routes/viewer/csv/+page.svelte`
- `ui/src/routes/viewer/image/+page.svelte`

---

## Phase 7: Testing & Optimization (Day 7, Full Day)

### Task 7.1: Test Scenarios

```bash
# 1. Money search
curl -X POST http://localhost:8000/search/contextual \
  -d '{"query": "invoice 9 USD"}'

# Expected: Resources with currency=USD, amounts_cents near 930

# 2. Exact ID search
curl -X POST http://localhost:8000/search/contextual \
  -d '{"query": "CSV with ID 2363836738"}'

# Expected: CSV rows with exact keyword match

# 3. Image search
curl -X POST http://localhost:8000/search/contextual \
  -d '{"query": "image including London"}'

# Expected: Images with labels containing "london"

# 4. Vendor search
curl -X POST http://localhost:8000/search/contextual \
  -d '{"query": "contract with T-Mobile"}'

# Expected: Resources with vendor="t-mobile"
```

### Task 7.2: Performance Benchmarks

- Search latency < 500ms for vector search
- Index size monitoring
- Cache hit rates
- Result relevance scoring

### Task 7.3: User Acceptance Testing

- Test with real documents
- Verify link navigation
- Check ACL (users can't see others' data)
- Test edge cases

---

## Dependencies

### Required

```bash
# Already installed
- pymongo
- motor (async MongoDB)
- beanie (ODM)

# New requirements
pip install pytesseract  # OCR
pip install Pillow  # Image processing
pip install pandas  # CSV processing
pip install python-magic  # File type detection
pip install dateutil  # Date parsing
```

### Optional (Image Embeddings)

```bash
# Option A: Use Ollama with LLaVA
ollama pull llava

# Option B: Use OpenAI CLIP
pip install openai

# Option C: Local CLIP/SigLIP
pip install transformers
pip install torch torchvision
```

---

## Configuration

**Environment Variables**:

```bash
# .env
SEARCH_ENABLED=true
SEARCH_INDEX_NAME=resources_unified_search
CHUNKS_INDEX_NAME=chunks_unified_search

# Embeddings
TEXT_EMBEDDING_MODEL=text-embedding-3-small
TEXT_EMBEDDING_DIMENSIONS=1536

IMAGE_EMBEDDING_ENABLED=false
IMAGE_EMBEDDING_MODEL=clip-vit-base-patch32
IMAGE_EMBEDDING_DIMENSIONS=768

# OCR
OCR_ENABLED=true
TESSERACT_PATH=/usr/local/bin/tesseract

# Search tuning
SEARCH_DEFAULT_LIMIT=30
SEARCH_MAX_LIMIT=100
MONEY_TOLERANCE_PERCENT=10
```

---

## Success Criteria

✅ Search "invoice 9 USD" returns correct invoices  
✅ Search "CSV with ID X" finds exact row  
✅ Search "image of London" finds relevant images  
✅ Links open correct PDF page / CSV row / image  
✅ Search latency < 500ms  
✅ User isolation enforced (ACL)  
✅ Works with 1000+ documents per user  
✅ No hallucinations (only real data)  

---

## Timeline Summary

| Day | Phase | Tasks | Hours |
|-----|-------|-------|-------|
| 1 | Data Model | Update Resource, Create Chunk model | 4-6 |
| 2 | PDF/CSV Processing | Ingestion pipelines | 6-8 |
| 3 | Image/Text + Atlas Index | Multi-modal processing | 6-8 |
| 4 | Query Router | Classification + Search builder | 6-8 |
| 5 | Links & Viewers | Backend viewer endpoints | 4-6 |
| 6 | Frontend | Universal search UI | 6-8 |
| 7 | Testing | E2E testing & optimization | 8 |
| **Total** | | | **40-52 hours** |

**Realistic Timeline**: 5-7 working days (assuming 6-8 hours/day)

---

## Future Enhancements

1. **Reciprocal Rank Fusion** - Combine lexical + vector scores
2. **Query Auto-complete** - Suggest searches as user types
3. **Faceted Search** - Filters by date range, file type, vendor
4. **Saved Searches** - Store frequent queries
5. **Search Analytics** - Track popular queries, click-through rates
6. **Multi-language** - Support Czech, German, etc.
7. **Voice Search** - Speech-to-text query input
8. **Smart Suggestions** - "Did you mean..." corrections

---

## Rollback Plan

If issues occur:

1. Keep old simple search as fallback
2. Disable contextual search via `SEARCH_ENABLED=false`
3. Fall back to basic keyword search
4. No data loss (new fields optional)

---

## Next Steps

When ready to start:

1. ✅ Review and approve this plan
2. ✅ Confirm embedding models (Ollama vs OpenAI)
3. ✅ Set up Atlas Search indexes (manual step)
4. ✅ Start with Phase 1 (Data Model)
5. ✅ Test incrementally after each phase

---

**Status**: 📋 Comprehensive Plan Ready  
**Created**: 2025-10-31  
**Estimated Completion**: 5-7 days  

*This is a production-ready architecture following MongoDB Atlas best practices!* 🚀
