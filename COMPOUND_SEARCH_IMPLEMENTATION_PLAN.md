# Compound Hybrid Search Implementation Plan

Based on analysis in `search_ingest_compound_improvement.txt`, this plan upgrades the semantic search to a **single intelligent hybrid search** with no UI mode switching.

---

## Goals

1. **Single smart search box** - no manual mode selection
2. **Structured + semantic fusion** - exact filters + vector similarity in one query
3. **Explainable results** - highlights, deep-links, match type
4. **Enhanced metadata** - IDs, amounts, vendors, entities extracted at ingest
5. **Multi-format support** - PDFs, CSVs, text, (images future)

---

## Phase 1: Schema & Index Extensions ✅ **[Priority: HIGH]**

### 1.1 Extend `resource_chunks` Model
**File**: `backend/documents.py`

Add fields to `ResourceChunk`:
```python
class ResourceChunk(Document):
    # Existing fields
    resource_id: str
    chunk_index: int
    content: str
    embedding: List[float]
    
    # NEW structured metadata fields
    keywords: List[str] = []          # IDs, emails, codes, IBANs
    currency: Optional[str] = None     # USD, EUR, GBP, etc.
    amounts: List[int] = []            # monetary values in cents
    vendor: Optional[str] = None       # normalized company name
    entities: List[str] = []           # people, orgs, locations
    
    # NEW deep-link fields
    page: Optional[int] = None         # PDF page number
    row_index: Optional[int] = None    # CSV row number
    col_index: Optional[int] = None    # CSV column index
    bbox: Optional[Dict] = None        # image region {x, y, w, h}
    
    # NEW file context
    file_type: Optional[str] = None    # pdf, csv, txt, etc.
    mime_type: Optional[str] = None
    
    # FUTURE image search fields
    image_embedding: Optional[List[float]] = None
    image_labels: List[str] = []       # captions, tags
    ocr_text: Optional[str] = None
```

**Effort**: 30 min  
**Risk**: Low (backward compatible, optional fields)

---

### 1.2 Update MongoDB Atlas Search Index
**Location**: MongoDB Atlas Console → Search Indexes → `resource_chunks`

Current index (keep this):
```json
{
  "mappings": {
    "dynamic": false,
    "fields": {
      "embedding": {
        "type": "knnVector",
        "dimensions": 768,
        "similarity": "cosine"
      }
    }
  }
}
```

**Extend to** (hybrid compound index):
```json
{
  "mappings": {
    "dynamic": false,
    "fields": {
      "content": { 
        "type": "string",
        "analyzer": "lucene.standard"
      },
      "keywords": { 
        "type": "string",
        "analyzer": "lucene.keyword"
      },
      "vendor": { 
        "type": "string",
        "analyzer": "lucene.keyword"
      },
      "currency": { 
        "type": "string",
        "analyzer": "lucene.keyword"
      },
      "amounts": { 
        "type": "number"
      },
      "file_type": { 
        "type": "string",
        "analyzer": "lucene.keyword"
      },
      "entities": {
        "type": "string",
        "analyzer": "lucene.standard"
      },
      "embedding": {
        "type": "knnVector",
        "dimensions": 768,
        "similarity": "cosine"
      },
      "image_embedding": {
        "type": "knnVector",
        "dimensions": 512,
        "similarity": "cosine"
      },
      "image_labels": {
        "type": "string"
      },
      "ocr_text": {
        "type": "string"
      }
    }
  }
}
```

**Effort**: 15 min (GUI update)  
**Risk**: Low (non-breaking, just adds fields)

---

## Phase 2: Query Analyzer & Extractor ✅ **[Priority: HIGH]**

### 2.1 Create Query Analysis Utility
**File**: `backend/query_analyzer.py` (new)

```python
import re
from typing import Dict, List, Optional
from datetime import datetime

class QueryAnalyzer:
    """Extract structured patterns from natural language queries"""
    
    # Regex patterns
    MONEY_PATTERN = re.compile(
        r'(?:USD|EUR|GBP|CHF|\$|€|£)\s*(\d{1,3}(?:[,\s]\d{3})*(?:\.\d{2})?)|'
        r'(\d{1,3}(?:[,\s]\d{3})*(?:\.\d{2})?)\s*(?:USD|EUR|GBP|CHF|dollars?|euros?)'
    )
    ID_PATTERN = re.compile(r'\b[A-Z]{2,}-\d{4,}|\b[A-Z0-9]{8,}\b')
    EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    IBAN_PATTERN = re.compile(r'\b[A-Z]{2}\d{2}[A-Z0-9]{10,30}\b')
    
    DATE_PATTERNS = [
        r'\b\d{4}-\d{2}-\d{2}\b',           # 2024-01-15
        r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',     # 01/15/2024
        r'\bQ[1-4]\s+\d{4}\b',              # Q4 2023
        r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\b'
    ]
    
    FILE_TYPES = {
        'pdf', 'csv', 'xlsx', 'xls', 'doc', 'docx', 'txt',
        'invoice', 'receipt', 'contract', 'spreadsheet', 'document'
    }
    
    def analyze(self, query: str) -> Dict:
        """Extract all structured patterns from query"""
        return {
            'money': self._extract_money(query),
            'ids': self._extract_ids(query),
            'dates': self._extract_dates(query),
            'file_types': self._extract_file_types(query),
            'entities': self._extract_entities(query),
            'clean_text': self._clean_query(query)
        }
    
    def _extract_money(self, query: str) -> Optional[Dict]:
        """Extract currency and amount"""
        match = self.MONEY_PATTERN.search(query)
        if not match:
            return None
        
        amount_str = match.group(1) or match.group(2)
        amount = float(amount_str.replace(',', '').replace(' ', ''))
        
        # Detect currency
        currency = 'USD'  # default
        if '€' in query or 'EUR' in query:
            currency = 'EUR'
        elif '£' in query or 'GBP' in query:
            currency = 'GBP'
        
        return {
            'amount': amount,
            'cents': int(amount * 100),
            'currency': currency
        }
    
    def _extract_ids(self, query: str) -> List[str]:
        """Extract IDs, emails, IBANs"""
        ids = self.ID_PATTERN.findall(query)
        emails = self.EMAIL_PATTERN.findall(query)
        ibans = self.IBAN_PATTERN.findall(query)
        return ids + emails + ibans
    
    def _extract_dates(self, query: str) -> List[str]:
        """Extract date patterns"""
        dates = []
        for pattern in self.DATE_PATTERNS:
            dates.extend(re.findall(pattern, query, re.IGNORECASE))
        return dates
    
    def _extract_file_types(self, query: str) -> List[str]:
        """Detect file type mentions"""
        query_lower = query.lower()
        return [ft for ft in self.FILE_TYPES if ft in query_lower]
    
    def _extract_entities(self, query: str) -> List[str]:
        """Extract capitalized entity candidates (simple heuristic)"""
        # Find capitalized words (not at start of sentence)
        words = query.split()
        entities = []
        for i, word in enumerate(words):
            if i > 0 and word[0].isupper() and len(word) > 2:
                entities.append(word)
        return entities
    
    def _clean_query(self, query: str) -> str:
        """Remove extracted patterns, return semantic text"""
        clean = query
        # Remove money amounts
        clean = self.MONEY_PATTERN.sub('', clean)
        # Remove IDs
        clean = self.ID_PATTERN.sub('', clean)
        return ' '.join(clean.split()).strip()
```

**Effort**: 2 hours  
**Risk**: Low (pure utility, no side effects)

---

### 2.2 Create Metadata Extractor for Ingestion
**File**: `backend/metadata_extractor.py` (new)

```python
import re
from typing import Dict, List

class MetadataExtractor:
    """Extract structured metadata from document chunks during ingestion"""
    
    def extract(self, content: str, file_type: str = None) -> Dict:
        """Extract all metadata from chunk content"""
        analyzer = QueryAnalyzer()
        
        result = analyzer.analyze(content)
        
        return {
            'keywords': self._extract_keywords(content),
            'currency': result['money']['currency'] if result['money'] else None,
            'amounts': [result['money']['cents']] if result['money'] else [],
            'vendor': self._extract_vendor(content),
            'entities': result['entities'],
            'file_type': file_type
        }
    
    def _extract_keywords(self, content: str) -> List[str]:
        """Extract exact match keywords (IDs, codes, long numbers)"""
        keywords = []
        
        # IDs like INV-2024-001
        keywords.extend(re.findall(r'\b[A-Z]{2,}-\d{4,}\b', content))
        
        # Long numbers (8+ digits, likely IDs/account numbers)
        keywords.extend(re.findall(r'\b\d{8,}\b', content))
        
        # Emails
        keywords.extend(re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content))
        
        # IBANs
        keywords.extend(re.findall(r'\b[A-Z]{2}\d{2}[A-Z0-9]{10,30}\b', content))
        
        return list(set(keywords))  # deduplicate
    
    def _extract_vendor(self, content: str) -> Optional[str]:
        """Heuristic vendor/company detection"""
        # Look for "From:", "Vendor:", "Company:" patterns
        patterns = [
            r'(?:From|Vendor|Company|Supplier):\s*([A-Z][A-Za-z\s&]+)',
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Inc|LLC|Ltd|Corp|GmbH))\b'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1).strip().lower()
        
        return None
```

**Effort**: 2 hours  
**Risk**: Low

---

## Phase 3: Compound Search Endpoint ✅ **[Priority: HIGH]**

### 3.1 Implement Unified `/search` Endpoint
**File**: `backend/http_server.py`

Replace existing semantic/keyword endpoints with:

```python
from query_analyzer import QueryAnalyzer

@app.post("/search")
async def unified_search(
    request: SearchRequest,
    user: User = Depends(require_auth)
):
    """Single intelligent search endpoint - no mode selection needed"""
    
    # Analyze query
    analyzer = QueryAnalyzer()
    analysis = analyzer.analyze(request.query)
    
    # Build compound search query
    must_clauses = [
        {"equals": {"path": "owner_id", "value": str(user.id)}}
    ]
    
    should_clauses = []
    
    # MUST: Exact filters
    if analysis['money']:
        money = analysis['money']
        must_clauses.append({
            "equals": {"path": "currency", "value": money['currency']}
        })
        # Range ±10% for fuzzy amount matching
        cents = money['cents']
        must_clauses.append({
            "range": {
                "path": "amounts",
                "gte": int(cents * 0.9),
                "lte": int(cents * 1.1)
            }
        })
    
    for exact_id in analysis['ids']:
        must_clauses.append({
            "phrase": {"path": "keywords", "query": exact_id}
        })
    
    if analysis['file_types']:
        must_clauses.append({
            "equals": {"path": "file_type", "value": analysis['file_types'][0]}
        })
    
    # SHOULD: Semantic + Lexical
    if analysis['clean_text']:
        # Semantic vector search
        query_embedding = await generate_embedding(analysis['clean_text'])
        should_clauses.append({
            "knnBeta": {
                "path": "embedding",
                "vector": query_embedding,
                "k": 64
            }
        })
        
        # Lexical text search
        should_clauses.append({
            "text": {
                "path": ["content", "vendor", "entities"],
                "query": analysis['clean_text'],
                "score": {"boost": {"value": 2}}
            }
        })
    
    # Execute compound search
    pipeline = [
        {
            "$search": {
                "index": "chunks_compound",
                "compound": {
                    "must": must_clauses,
                    "should": should_clauses,
                    "minimumShouldMatch": 1
                }
            }
        },
        {"$limit": 30},
        {
            "$project": {
                "resource_id": 1,
                "content": 1,
                "page": 1,
                "row_index": 1,
                "vendor": 1,
                "currency": 1,
                "amounts": 1,
                "file_type": 1,
                "score": {"$meta": "searchScore"},
                "highlights": {"$meta": "searchHighlights"}
            }
        }
    ]
    
    chunks_collection = ResourceChunk.get_pymongo_collection()
    results = await chunks_collection.aggregate(pipeline).to_list(length=30)
    
    # Add explainability
    for result in results:
        result['match_type'] = _determine_match_type(result, analysis)
        result['open_url'] = _build_deep_link(result)
    
    return {"results": results, "analysis": analysis}


def _determine_match_type(result: Dict, analysis: Dict) -> str:
    """Determine why this result matched"""
    if analysis['money'] and result.get('currency'):
        return 'exact_amount'
    elif analysis['ids'] and any(id in result.get('keywords', []) for id in analysis['ids']):
        return 'exact_id'
    elif result['score'] > 0.8:
        return 'semantic_strong'
    else:
        return 'hybrid'


def _build_deep_link(result: Dict) -> str:
    """Generate open URL for PDF page, CSV row, or image region"""
    resource_id = result['resource_id']
    
    if result.get('page'):
        return f"/resources/{resource_id}?page={result['page']}"
    elif result.get('row_index'):
        return f"/resources/{resource_id}?row={result['row_index']}"
    else:
        return f"/resources/{resource_id}"
```

**Effort**: 4 hours  
**Risk**: Medium (core search logic)

---

## Phase 4: Enhanced Ingestion Pipeline ✅ **[Priority: HIGH]**

### 4.1 Update Resource Upload Handler
**File**: `backend/http_server.py` → `/resources/upload`

```python
from metadata_extractor import MetadataExtractor

async def process_uploaded_file(...):
    # ... existing chunking logic ...
    
    extractor = MetadataExtractor()
    
    for chunk_index, chunk_text in enumerate(chunks):
        # Generate text embedding (existing)
        embedding = await generate_embedding(chunk_text)
        
        # NEW: Extract structured metadata
        metadata = extractor.extract(chunk_text, file_type=file.content_type)
        
        chunk = ResourceChunk(
            resource_id=str(resource.id),
            chunk_index=chunk_index,
            content=chunk_text,
            embedding=embedding,
            # NEW metadata fields
            keywords=metadata['keywords'],
            currency=metadata['currency'],
            amounts=metadata['amounts'],
            vendor=metadata['vendor'],
            entities=metadata['entities'],
            file_type=metadata['file_type']
        )
        
        await chunk.insert()
```

**Effort**: 2 hours  
**Risk**: Low (extends existing flow)

---

### 4.2 Add CSV Row-Level Chunking
**File**: `backend/csv_processor.py` (new)

```python
import csv
from io import StringIO

class CSVProcessor:
    """Process CSV files at row granularity"""
    
    async def process_csv(self, file_content: str, resource_id: str):
        """Create one chunk per CSV row with column metadata"""
        reader = csv.DictReader(StringIO(file_content))
        
        chunks = []
        for row_index, row in enumerate(reader):
            # Convert row to text representation
            chunk_text = ' | '.join(f"{k}: {v}" for k, v in row.items())
            
            # Extract metadata
            metadata = MetadataExtractor().extract(chunk_text, 'csv')
            
            # Generate embedding
            embedding = await generate_embedding(chunk_text)
            
            chunk = ResourceChunk(
                resource_id=resource_id,
                chunk_index=row_index,
                content=chunk_text,
                embedding=embedding,
                row_index=row_index,
                **metadata
            )
            
            chunks.append(chunk)
        
        await ResourceChunk.insert_many(chunks)
```

**Effort**: 3 hours  
**Risk**: Medium

---

## Phase 5: Frontend Updates ✅ **[Priority: MEDIUM]**

### 5.1 Simplify Search UI
**File**: `frontend/src/routes/search/+page.svelte`

**Changes**:
- ✅ Remove mode selector dropdown (Auto/Semantic/Keyword/Hybrid)
- ✅ Keep single search input
- ✅ Add result explainability:
  - Match type badge (exact/semantic/hybrid)
  - Highlights from Atlas
  - "Open" button with deep-link
- ✅ Optional: "Why this result?" expander

**Effort**: 2 hours  
**Risk**: Low

---

### 5.2 Add Deep-Link Viewer
**File**: `frontend/src/routes/resources/[id]/+page.svelte`

Support query params:
- `?page=5` → scroll to PDF page 5
- `?row=42` → highlight CSV row 42
- `?bbox=x,y,w,h` → highlight image region

**Effort**: 3 hours  
**Risk**: Medium (depends on PDF/CSV viewers)

---

## Phase 6: Advanced Features (Future) 🔄

### 6.1 Image Search with Vision Models
- CLIP embeddings for images
- OCR text extraction (Tesseract)
- Caption generation (BLIP)
- Bounding box annotations

**Effort**: 8+ hours  
**Risk**: High (requires additional model infrastructure)  
**Dependency**: Vision model service separate from Ollama

---

### 6.2 Advanced NER for Entities
Replace heuristic entity extraction with:
- spaCy NER pipeline
- Or cloud NER (Google Cloud NLP, AWS Comprehend)

**Effort**: 4 hours  
**Risk**: Medium (adds dependency)

---

## Summary: What to Build First

### Immediate (Phase 1-3) - **Week 1**
1. ✅ Extend `ResourceChunk` schema with metadata fields
2. ✅ Update Atlas search index (hybrid compound)
3. ✅ Build `QueryAnalyzer` + `MetadataExtractor` utilities
4. ✅ Implement unified `/search` endpoint with compound queries
5. ✅ Update ingestion to extract metadata

**Outcome**: Single search box that intelligently routes and fuses results

### Near-term (Phase 4-5) - **Week 2**
6. ✅ Add CSV row-level processing
7. ✅ Simplify frontend (remove mode selector)
8. ✅ Add result explainability UI (highlights, match types)
9. ✅ Implement deep-link viewer

**Outcome**: Professional search experience with explainability

### Future (Phase 6) - **Month 2+**
10. 🔄 Image search (CLIP + OCR + captions)
11. 🔄 Advanced NER with spaCy
12. 🔄 Search analytics and relevance tuning

---

## Migration Strategy

### For Existing Data
Run migration script to backfill metadata:
```python
# backend/scripts/backfill_metadata.py
async def backfill_metadata():
    """Add metadata to existing chunks"""
    extractor = MetadataExtractor()
    
    async for chunk in ResourceChunk.find_all():
        metadata = extractor.extract(chunk.content)
        chunk.keywords = metadata['keywords']
        chunk.currency = metadata['currency']
        chunk.amounts = metadata['amounts']
        chunk.vendor = metadata['vendor']
        chunk.entities = metadata['entities']
        await chunk.save()
```

### Index Update
- Atlas index updates are non-breaking
- Existing `embedding` field works unchanged
- New fields populate as data is backfilled

---

## Success Metrics

1. **Zero mode switches needed** - user just types, system handles routing
2. **Top-1 accuracy improvement** - correct result ranks first more often
3. **Explainability** - users understand why results matched
4. **Deep-links work** - clicking opens exact page/row/region

---

## Questions to Answer Before Starting

1. **Current embedding dimensions?** (need for Atlas index)
2. **Do you want CSV support immediately or later?**
3. **Image search priority?** (high effort, can defer)
4. **Existing data volume?** (affects backfill strategy)

Let me know and I can start implementing Phase 1 immediately!
