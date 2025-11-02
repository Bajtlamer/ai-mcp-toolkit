# Diacritic Normalization Implementation Progress

## Overview

This document tracks the implementation of diacritic-insensitive search for the AI MCP Toolkit. The goal is to enable accurate search results for queries containing Czech, Slovak, and other European language diacritics (č, š, ž, á, é, etc.) by normalizing both stored text and search queries.

**Status**: Phase 5 of 8 Complete ✅ (62.5%)

---

## Problem Statement

### Original Issue
When searching for Czech text like **"Jak se formuje datov\u00e1 budoucnost"**, the system failed to find images containing OCR-extracted text like **"datova budoucnost"** because:
1. Tesseract OCR extracts text without diacritics
2. MongoDB Atlas text search is diacritic-sensitive by default
3. Compound search with `knnBeta` is unsupported in some Atlas tiers

### Solution Approach
1. Create text normalizer utility to remove diacritics consistently
2. Store both original and normalized text fields
3. Normalize all search queries before searching
4. Simplify search to use normalized text fields (no complex compound search)
5. Boost scores for matches in OCR text and image descriptions

---

## Implementation Phases

### \u2705 Phase 1: Text Normalizer Utility (COMPLETED)

**Files**: `src/ai_mcp_toolkit/utils/text_normalizer.py`

**Functions Created**:
- `remove_diacritics(text: str) -> str`
  - Uses Unicode NFD decomposition to separate diacritics
  - Filters out combining characters (category Mn)
  - Returns NFC normalized text
  - Example: "datov\u00e1" \u2192 "datova"

- `normalize_text(text: str, lowercase: bool = True) -> str`
  - Removes diacritics
  - Converts to lowercase
  - Normalizes whitespace
  - Example: "Jak se formuje datov\u00e1 budoucnost" \u2192 "jak se formuje datova budoucnost"

- `normalize_query(query: str) -> str`
  - Wrapper for `normalize_text` specifically for search queries
  - Always uses lowercase

- `create_searchable_text(*text_parts: Optional[str]) -> str`
  - Combines multiple text sources (text, OCR, caption, labels)
  - Normalizes the combined result
  - Returns single searchable field

- `tokenize_for_search(text: str) -> list[str]`
  - Splits normalized text into search tokens
  - Filters out very short tokens (< 2 chars)
  - Used for keyword extraction

**Test Results**:
```
datov\u00e1                     \u2192 datova
Jak se formuje datov\u00e1 budoucnost \u2192 jak se formuje datova budoucnost
\u0160koda                     \u2192 skoda
caf\u00e9                      \u2192 cafe
Z\u00fcrich                    \u2192 zurich
```

---

### \u2705 Phase 2: ResourceChunk Schema Extension (COMPLETED)

**Files**: `src/ai_mcp_toolkit/models/documents.py`

**New Fields Added to ResourceChunk**:
```python
# Normalized text for diacritic-insensitive search
text_normalized: Optional[str] = None           # Text with diacritics removed
ocr_text_normalized: Optional[str] = None       # OCR text with diacritics removed
searchable_text: Optional[str] = None           # Combined normalized text from all sources
image_description: Optional[str] = None         # AI-generated image description (LLaVA)
```

**Purpose**:
- Store both original text (with diacritics) and normalized text (without)
- Enable fast lexical search on `searchable_text` field
- Preserve original text for display purposes
- Support multi-source search (text + OCR + description + labels)

---

### \u2705 Phase 3: Image OCR AI Agent (COMPLETED)

**Files**: `src/ai_mcp_toolkit/agents/image_ocr_agent.py`

**Features**:
- Extends `BaseAgent` with MCP tool interface
- Wraps `ImageCaptionService` for OCR and LLaVA
- **Automatically normalizes all extracted text**
- Generates combined searchable text from multiple sources
- Extracts keywords from normalized text

**Key Method**: `process_image_for_ingestion(image_path: str) -> Dict`
Returns:
```python
{
    "ocr_text": str,                    # Original OCR text
    "ocr_text_normalized": str,         # Normalized OCR text
    "image_description": str,           # AI description (LLaVA)
    "text_normalized": str,             # Normalized description
    "image_labels": List[str],          # Tags from description
    "keywords": List[str],              # Extracted keywords
    "searchable_text": str,             # Combined normalized text
    "caption_embedding": List[float]    # Semantic embedding
}
```

**Example Output**:
```
Original OCR:    "Jak se formuje datova budoucnost"
Normalized OCR:  "jak se formuje datova budoucnost"
Description:     "A newspaper article about data and future"
Searchable:      "jak se formuje datova budoucnost newspaper article about data future"
Keywords:        ["jak", "se", "formuje", "datova", "budoucnost", "newspaper", "article", ...]
```

---

### \u2705 Phase 4: Ingestion Service Update (COMPLETED)

**Files**: `src/ai_mcp_toolkit/services/ingestion_service.py`

**Changes**:
1. **Added imports**:
   - `ImageOCRAgent` for normalized image processing
   - `normalize_text`, `create_searchable_text`, `tokenize_for_search` from text_normalizer
   - `Config` for agent initialization

2. **Updated `__init__`**:
   - Initialize `ImageOCRAgent` with config
   - Log initialization with OCR Agent

3. **Updated image processing**:
   - Route images through `ocr_agent.process_image_for_ingestion()`
   - Log OCR, description, and searchable text lengths
   - Clean up temp files

4. **Updated `_ingest_chunks`**:
   - Normalize `text`, `ocr_text`, and `caption` for every chunk
   - Create `searchable_text` from all sources
   - Extract keywords from normalized searchable text
   - Populate new fields: `text_normalized`, `ocr_text_normalized`, `searchable_text`, `image_description`
   - Log normalization stats for each chunk

**Impact**:
- All new uploads will have normalized text fields
- Images will have rich searchable metadata
- Existing data will need backfill (Phase 6)

---

## Next Steps

### ✅ Phase 5: Simplify Search Service (COMPLETED)

**Files**: `src/ai_mcp_toolkit/services/search_service.py`

**Implementation**:
1. **Added imports**: `normalize_query`, `normalize_text`, `tokenize_for_search`
2. **Updated initialization**: Log diacritic-insensitive search support
3. **Rewrote `_keyword_search()` method**:
   - Normalize query using `normalize_query()`
   - Tokenize query for partial matching
   - 5-level priority matching system:

**Priority Levels** (highest to lowest):
1. **Priority 1 (score=1.0)**: Match in `searchable_text` (combined normalized field)
2. **Priority 2 (score=0.98)**: Match in `ocr_text_normalized` (OCR-specific, high value for images)
3. **Priority 3 (score=0.95)**: Match in `text_normalized` (regular text)
4. **Priority 4 (score=0.93)**: Match in `image_description` (AI-generated description)
5. **Priority 5 (score=0.7-0.9)**: Token overlap ≥50% (partial matching)

**Features**:
- Diacritic-insensitive matching throughout
- Per-document deduplication (keeps highest-scoring chunk)
- Debug logging for match tracking
- Preserves semantic and hybrid search modes

**Example Flow**:
```
Query: "Jak se formuje datová budoucnost"
↓
Normalize: "jak se formuje datova budoucnost"
↓
Search in searchable_text field
↓
Match article.jpg OCR: "jak se formuje datova budoucnost"
↓
Score: 1.0 (perfect match)
```

---

### Phase 6: Test with article.jpg (PENDING)

**Goals**:
1. Clear cache of existing article.jpg data
2. Re-upload article.jpg to trigger new ingestion with normalization
3. Search for "Jak se formuje datov\u00e1 budoucnost"
4. Verify article.jpg appears with \u226590% score
5. Test various diacritic combinations

---

### Phase 7: OCR Agent UI (PENDING)

**Files**: `ui/src/routes/agents/image-ocr/+page.svelte`

**Features**:
- Self-service OCR tool at `/agents/image-ocr`
- File upload for image processing
- Display OCR text, description, normalized text
- Show extracted keywords and searchable text
- Copy-to-clipboard functionality

---

### Phase 8: Documentation Update (PENDING)

**Files**: 
- `ENHANCEMENT_TASKS.md` (update progress)
- `DIACRITIC_NORMALIZATION_COMPLETE.md` (completion report)
- `README.md` (feature announcement)

---

## Technical Details

### Unicode Normalization

We use **NFD (Normalized Form Decomposed)** to separate base characters from diacritics:

```python
import unicodedata

# NFD decomposes "\u00e1" (single character) into "a" + "\u0301" (combining acute)
nfd = unicodedata.normalize('NFD', 'datov\u00e1')  # -> 'datova\u0301'

# Filter out combining characters (category Mn)
without_diacritics = ''.join(
    char for char in nfd 
    if unicodedata.category(char) != 'Mn'
)  # -> 'datova'

# NFC recomposes to standard form
result = unicodedata.normalize('NFC', without_diacritics)  # -> 'datova'
```

### Search Architecture

**Before** (Complex Compound Search):
```
Query: "datov\u00e1"
\u2192 Compound search with knnBeta (unsupported)
\u2192 Fallback to legacy search
\u2192 Low scores, duplicates, missing results
```

**After** (Normalized Lexical Search):
```
Query: "datov\u00e1"
\u2192 Normalize: "datova"
\u2192 Lexical search on searchable_text
\u2192 Boost OCR/description matches
\u2192 High scores, no duplicates, accurate results
```

---

## Files Modified

1. ✅ `src/ai_mcp_toolkit/utils/text_normalizer.py` (NEW)
2. ✅ `src/ai_mcp_toolkit/models/documents.py` (UPDATED)
3. ✅ `src/ai_mcp_toolkit/agents/image_ocr_agent.py` (NEW)
4. ✅ `src/ai_mcp_toolkit/services/ingestion_service.py` (UPDATED)
5. ✅ `src/ai_mcp_toolkit/services/search_service.py` (UPDATED)
6. ⚠️ `ui/src/routes/agents/image-ocr/+page.svelte` (PENDING)
7. ✅ `ENHANCEMENT_TASKS.md` (UPDATED)
8. ✅ `DIACRITIC_NORMALIZATION_PROGRESS.md` (UPDATED)

---

## Dependencies

No new external dependencies required. All functionality uses Python standard library (`unicodedata`, `re`) and existing dependencies (`pytesseract`, `ollama`, `pillow`).

---

## Performance Considerations

- Text normalization is fast (microseconds per text)
- Searchable text field enables efficient lexical search
- No impact on semantic search (embeddings remain unchanged)
- Slight storage increase (~10-20%) for normalized fields

---

## Testing Strategy

1. Unit tests for text normalizer functions
2. Integration test for OCR agent
3. End-to-end test for image ingestion with normalization
4. Search accuracy test with diacritic variations
5. Performance benchmark for normalization overhead

---

## Rollback Plan

If issues arise:
1. Ingestion still stores original text fields
2. Search can fall back to original fields
3. Normalized fields are optional (can be null)
4. No breaking changes to existing API

---

**Last Updated**: 2025-01-XX  
**Status**: 62.5% Complete (5/8 phases done)  
**Next Action**: Phase 6 - Test with article.jpg or Phase 7 - Create OCR Agent UI
