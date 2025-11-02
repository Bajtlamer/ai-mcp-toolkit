# OCR AI Agent & Improved Search Architecture

**Date**: November 1, 2025  
**Goal**: Simplify search, create OCR as AI agent, normalize all text (remove diacritics)

---

## 🎯 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                       Upload Flow                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  User uploads file                                           │
│       ↓                                                      │
│  Detect file type                                            │
│       ↓                                                      │
│  ┌────────────┬────────────┬────────────────────────┐      │
│  │   PDF      │   Image    │   CSV/Text             │      │
│  │  Agent     │   OCR      │   Processor            │      │
│  │            │   Agent    │                         │      │
│  └────────────┴────────────┴────────────────────────┘      │
│       ↓              ↓              ↓                        │
│  Extract text   Extract text   Parse content                │
│       ↓         + Describe         ↓                        │
│       ↓              ↓              ↓                        │
│  ┌──────────────────────────────────────────┐              │
│  │  Metadata Extraction (all sources)       │              │
│  │  - Keywords                               │              │
│  │  - Entities                               │              │
│  │  - Amounts/Dates                          │              │
│  │  - Image description                      │              │
│  │  - Normalize text (remove diacritics)    │              │
│  └──────────────────────────────────────────┘              │
│       ↓                                                      │
│  Generate embeddings (normalized text)                      │
│       ↓                                                      │
│  Store in MongoDB with all metadata                         │
│                                                              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                       Search Flow                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  User enters query: "datová budoucnost"                     │
│       ↓                                                      │
│  Normalize query: "datova budoucnost" (remove diacritics)   │
│       ↓                                                      │
│  ┌─────────────────────────────────────────────────┐       │
│  │            Search Mode Selector                  │       │
│  ├─────────────────────────────────────────────────┤       │
│  │  Auto    │ Semantic │ Keyword │ Hybrid          │       │
│  └─────────────────────────────────────────────────┘       │
│       ↓            ↓         ↓          ↓                   │
│  Pick best    Vector     Text      Combined                │
│  strategy     search    matching   ranking                  │
│       ↓                                                      │
│  Score = Vector similarity (60%) + Keyword match (40%)      │
│       ↓                                                      │
│  Boost by metadata:                                          │
│  - OCR text match: +50%                                      │
│  - Image description match: +30%                             │
│  - Keyword match: +20%                                       │
│       ↓                                                      │
│  Return ranked results                                       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 Implementation Plan

### Phase 1: Create OCR AI Agent ✨
**New agent**: `image_ocr_agent.py`

**Features**:
- Extract text using Tesseract OCR
- Describe image using LLaVA vision model
- Generate structured metadata
- Return both OCR text and AI description
- Normalize text (remove diacritics)

**Example output**:
```json
{
  "ocr_text": "Snowflake Summit 2025: Jak se formuje datova budoucnost",
  "normalized_ocr": "snowflake summit 2025: jak se formuje datova budoucnost",
  "description": "Screenshot of a news article header with IT trend information",
  "entities": ["Snowflake", "Summit", "2025"],
  "keywords": ["snowflake", "summit", "datova", "budoucnost", "it"],
  "image_type": "screenshot",
  "confidence": 0.95
}
```

### Phase 2: Text Normalization Service 🔤
**New utility**: `text_normalizer.py`

**Purpose**: Remove diacritics from ALL text for consistent matching

```python
def normalize_text(text: str) -> str:
    """Remove diacritics: datová → datova"""
    import unicodedata
    nfd = unicodedata.normalize('NFD', text)
    return ''.join(c for c in nfd if unicodedata.category(c) != 'Mn')

def normalize_for_search(text: str) -> str:
    """Normalize + lowercase + trim"""
    return normalize_text(text).lower().strip()
```

**Apply to**:
- All uploaded document text
- All search queries
- All metadata fields
- OCR text
- Image descriptions

### Phase 3: Update Ingestion Pipeline 📥
**Modify**: `ingestion_service.py`

**Changes**:
1. Detect file type → route to appropriate agent
2. For images: call **OCR AI Agent** instead of direct OCR service
3. Normalize all extracted text before storing
4. Store both original + normalized versions
5. Generate embeddings from normalized text

**Before**:
```python
# Direct service call
image_caption_data = await self.image_caption_service.process_image(tmp_path)
```

**After**:
```python
# Use AI agent
from ..agents.image_ocr_agent import ImageOCRAgent
ocr_agent = ImageOCRAgent()
result = await ocr_agent.process(image_path)
# result has OCR + description + normalized text
```

### Phase 4: Update Database Schema 💾
**Extend**: `ResourceChunk` model

```python
class ResourceChunk:
    # Existing fields
    text: str
    ocr_text: Optional[str]
    
    # NEW: Normalized versions (for matching)
    text_normalized: str                # All text without diacritics
    ocr_text_normalized: Optional[str]  # OCR without diacritics
    
    # NEW: Image description
    image_description: Optional[str]    # AI-generated description
    image_description_normalized: Optional[str]
    
    # NEW: Combined searchable text
    searchable_text: str                # text + ocr + description (normalized)
```

### Phase 5: Simplified Search (No Compound) 🔍
**Modify**: `search_service.py`

**Remove**: All Atlas compound search complexity

**Keep**: Simple, working search modes

```python
async def search(query, mode="auto"):
    # 1. Normalize query
    query_normalized = normalize_for_search(query)
    
    # 2. Choose mode
    if mode == "auto":
        mode = detect_best_mode(query)
    
    # 3. Execute search
    if mode == "semantic":
        results = await semantic_search(query_normalized)
    elif mode == "keyword":
        results = await keyword_search(query_normalized)
    else:  # hybrid
        results = await hybrid_search(query_normalized)
    
    # 4. Boost scores by metadata
    for result in results:
        boost_score(result, query_normalized)
    
    return results
```

**Score boosting logic**:
```python
def boost_score(result, query):
    base_score = result['score']
    
    # Boost for OCR match
    if query in result.get('ocr_text_normalized', ''):
        base_score *= 1.5  # +50%
    
    # Boost for image description match
    if query in result.get('image_description_normalized', ''):
        base_score *= 1.3  # +30%
    
    # Boost for keyword match
    if any(word in result.get('keywords', []) for word in query.split()):
        base_score *= 1.2  # +20%
    
    result['score'] = min(base_score, 1.0)  # Cap at 100%
```

### Phase 6: UI for OCR Agent 🖥️
**New page**: `ui/src/routes/agents/image-ocr/+page.svelte`

**Features**:
- Upload image
- Extract text (OCR)
- Get AI description
- View extracted metadata
- Copy results
- Self-service tool

---

## 🚀 Benefits

### ✅ Advantages

1. **Diacritics handled** - "datová" matches "datova" automatically
2. **Better image search** - OCR + AI description
3. **Reusable OCR agent** - Can be used standalone or in pipeline
4. **Simple search** - No complex Atlas compound queries
5. **Better scoring** - Metadata-aware boosting
6. **Consistent** - All text normalized the same way
7. **Debuggable** - Clear flow, easy to trace

### 🎯 Results

**Your example**:
```
Query: "Jak se formuje datová budoucnost"
Normalized: "jak se formuje datova budoucnost"

article.jpg:
- OCR normalized: "jak se formuje datova budoucnost"
- Match: EXACT ✅
- Base score: 0.15 (semantic)
- OCR boost: ×1.5
- Final score: 0.225 = 23%

Wait, still low because semantic base is low...
```

**Better approach**: If OCR text matches, give it HIGH base score:

```python
# Check for exact OCR match FIRST
if exact_match_in_ocr(query_normalized, ocr_text_normalized):
    score = 0.95  # Start high!
else:
    score = semantic_similarity  # Use vector
```

### 📊 Scoring Logic (Revised)

```python
def calculate_score(query_norm, chunk):
    # Priority 1: Exact match in OCR/description
    if query_norm in chunk.ocr_text_normalized:
        return 0.95
    if query_norm in chunk.image_description_normalized:
        return 0.90
    
    # Priority 2: All words match in searchable text
    words = query_norm.split()
    if all(w in chunk.searchable_text for w in words):
        return 0.85
    
    # Priority 3: Semantic similarity
    similarity = cosine_similarity(query_embedding, chunk.embedding)
    
    # Boost semantic with metadata
    if any(w in chunk.keywords for w in words):
        similarity *= 1.2
    
    return min(similarity, 1.0)
```

---

## 📝 Implementation Order

1. ✅ **Text Normalizer** (30 min) - Simple utility
2. ✅ **Update Schema** (15 min) - Add normalized fields
3. ✅ **Create OCR Agent** (1-2 hours) - New agent with LLaVA
4. ✅ **Update Ingestion** (1 hour) - Use agent, normalize text
5. ✅ **Simplify Search** (2 hours) - Remove compound, add boosting
6. ✅ **Test** (1 hour) - Verify article.jpg ranks #1
7. ⏳ **UI for Agent** (2-3 hours) - Self-service page

**Total time**: ~8-10 hours

---

## 💡 Your Questions Answered

### Q: "Disable compound search?"
**A**: Yes! Remove all Atlas compound complexity. Use simple hybrid search with metadata boosting.

### Q: "Keep OCR?"
**A**: Yes! Make it an AI Agent with description capabilities.

### Q: "AI describe images?"
**A**: Yes! LLaVA generates: "Screenshot showing IT news article about Snowflake Summit"

### Q: "OCR as AI Agent?"
**A**: Yes! Creates reusable agent with UI.

### Q: "Ignore diacritics?"
**A**: Yes! Normalize ALL text on upload and query.

### Q: "Keep Semantic/Keyword/Hybrid modes?"
**A**: Yes! Simpler implementation with metadata boosting.

---

## 🎉 Expected Result

After implementation:

```
Query: "Jak se formuje datová budoucnost"

Results:
1. article.jpg - 95% ← OCR exact match ✅
2. ai-usage-policy.pdf - 43%
3. AKLIMA.html - 42%
```

**Perfect!** 🎯

---

**Next**: Shall I start implementing? We can do it step by step.
