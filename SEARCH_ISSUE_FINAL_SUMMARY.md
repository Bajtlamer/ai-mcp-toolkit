# Search Accuracy Issue - Final Summary

**Date**: November 1, 2025  
**Issue**: Czech screenshot (article.jpg) with text "Jak se formuje datová budoucnost" scoring only 11% instead of ranking #1

---

## ✅ What We Fixed

1. **Installed pytesseract** - OCR extraction now works
2. **OCR text IS being extracted** - Verified in database: "Jak se formuje datova budoucnost"
3. **Removed Python cache** - Multiple times to ensure code updates apply
4. **Fixed Atlas compound search syntax** - Removed unsupported knnBeta nesting
5. **Added fuzzy matching** - To handle diacritics (á vs a)
6. **Fixed duplicate results** - Added grouping by parent_id
7. **Normalized scores** - Divided by 10 for 0-100% range
8. **Added OCR text to keyword search** - With diacritic-insensitive matching

---

## ❌ Remaining Problem

**OCR text extracted**: `"Jak se formuje datova budoucnost"` (without accent on 'á')  
**User searches for**: `"Jak se formuje datová budoucnost"` (with accent)

**Result**: Only 11% match (semantic similarity), not the expected 98% (keyword match)

---

## 🔍 Root Cause

The OCR-aware keyword search code **might not be executing** or there's a logical issue preventing it from matching.

### Possible Issues:

1. **Code not reloading** - Despite clearing cache, old code may be running
2. **Logic error** - The `chunk_matches` dict might not be populating results correctly
3. **Hybrid search merging** - OCR matches might be getting lost in the merge logic
4. **Company ID mismatch** - ACL filtering might be excluding the result

---

## 🧪 What We Know Works

### Direct Database Query (Works!):
```python
# Individual word searches find article.jpg ✅
- "Snowflake" → article.jpg found
- "Summit" → article.jpg found  
- "formuje" → article.jpg found
- "budoucnost" → article.jpg found
```

### Atlas Text Search (Works!):
```python
# Simple text search finds it with score 0.41
pipeline = [
    {"$search": {"text": {"query": query, "path": "ocr_text"}}}
]
# Result: article.jpg appears ✅
```

### Backend Code (Works!):
- OCR extraction: ✅ Working
- Database storage: ✅ OCR text present
- Atlas index: ✅ Deployed and working

---

## 💡 Why It's Still Failing

The **legacy hybrid search** that's currently active combines:
1. Semantic search (vector similarity) → 11% match
2. Keyword search (text matching) → Should be 98% but isn't working

**Hypothesis**: The keyword search function either:
- Isn't finding the chunk (despite code saying it should)
- Isn't properly weighting the OCR match
- Has the OCR match overridden by lower semantic score in merge logic

---

## 📋 Code Added (Should Work But Doesn't)

### In `_keyword_search` function (line ~336-356):

```python
# Normalize query (remove diacritics)
query_normalized = ''.join(
    c for c in unicodedata.normalize('NFD', query.lower())
    if unicodedata.category(c) != 'Mn'
)

for chunk in chunks:
    # Check OCR text with diacritic-insensitive matching
    if chunk.ocr_text:
        ocr_normalized = ''.join(
            c for c in unicodedata.normalize('NFD', chunk.ocr_text.lower())
            if unicodedata.category(c) != 'Mn'
        )
        ocr_match = query_normalized in ocr_normalized
    
    if ocr_match:
        score = 0.98  # High score for OCR match
```

**This should work** but article.jpg still scores 11%.

---

## 🎯 Recommended Next Steps

### Option 1: Debug Logging
Add explicit logging to see if OCR matching code is executing:

```python
if chunk.ocr_text:
    self.logger.info(f"Checking OCR in {chunk.file_name}: {chunk.ocr_text[:50]}")
    if ocr_match:
        self.logger.info(f"✅ OCR MATCH in {chunk.file_name}!")
```

### Option 2: Simplify Further
Replace entire `compound_search` with a direct database query that we know works:

```python
async def compound_search(...):
    # Direct MongoDB text search (bypass all complexity)
    chunks = await ResourceChunk.find(
        ResourceChunk.owner_id == owner_id,
        {"$text": {"$search": query}}
    ).to_list(limit)
    # Format and return
```

### Option 3: Use MongoDB Text Index
Create a MongoDB text index on `ocr_text` field:

```python
db.resource_chunks.create_index([("ocr_text", "text")])
```

Then use `$text` search which handles diacritics automatically.

---

## 📊 Current State

### What's Working:
- ✅ OCR extraction (pytesseract)
- ✅ OCR text in database
- ✅ Atlas search index
- ✅ Direct Atlas queries find article.jpg
- ✅ No duplicates
- ✅ Normalized scores

### What's NOT Working:
- ❌ article.jpg ranking at top
- ❌ OCR text boosting not applying
- ❌ Score stuck at 11% (semantic only)

---

## 🔧 Quick Fix to Test

To verify if the problem is code execution vs. logic, add this at the very start of `_keyword_search`:

```python
async def _keyword_search(...):
    self.logger.info(f"🔍 KEYWORD SEARCH CALLED with query: {query}")
    
    # ... rest of function
    
    self.logger.info(f"🔍 KEYWORD SEARCH returning {len(results)} results")
    return results
```

Then check logs when searching. If you DON'T see these messages, the function isn't being called at all.

---

## 💭 Final Thoughts

We've spent significant time on this and made many improvements:
- Installed missing dependencies
- Fixed Atlas syntax errors
- Added OCR text support
- Handled diacritics
- Removed duplicates

The core infrastructure is now correct. The remaining issue is likely:
1. A subtle bug in the search merge logic
2. Or the code still not reloading despite cache clears

**Recommendation**: 
- Add debug logging to confirm code execution
- Or use the simple MongoDB `$text` search as a quick working solution
- Come back to optimize compound search later once basic functionality works

---

## 📝 Files Modified

- `src/ai_mcp_toolkit/services/search_service.py` - Multiple iterations
- `src/ai_mcp_toolkit/services/image_caption_service.py` - Added logging
- `src/ai_mcp_toolkit/services/ingestion_service.py` - Already had OCR support

## 🎯 Success Criteria

- [ ] article.jpg appears in search results for "Jak se formuje datová budoucnost"
- [ ] article.jpg scores 80%+ (OCR keyword match)
- [ ] article.jpg ranks in top 3 results
- [ ] No duplicate results
- [ ] Scores normalized (0-100%)

**Current**: 11% score, not in top results ❌

---

**Status**: Issue partially resolved (OCR works, but not boosting score)  
**Next**: Add debug logging or use simpler MongoDB text search
