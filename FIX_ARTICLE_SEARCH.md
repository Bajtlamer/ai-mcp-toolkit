# Fix article.jpg Search Issue

**Problem**: article.jpg scoring only 11% because OCR text wasn't extracted  
**Root Cause**: `pytesseract` module was not installed when image was uploaded  
**Status**: ✅ pytesseract now installed

---

## 🔧 Solution: Re-upload the Image

Since article.jpg was uploaded before pytesseract was available, it has **no OCR text** in the database. You must re-upload it.

### Option 1: Delete & Re-upload (Recommended)

1. **Navigate to Resources page** in the UI
2. **Find article.jpg** in the list
3. **Delete it** (trash icon)
4. **Go to Search page**
5. **Click "Upload" button**
6. **Select article.jpg** from your computer
7. **Upload**
8. **Wait 5-10 seconds** for processing

### Option 2: Run Backfill Script

If you have many images without OCR, run the backfill script:

```bash
cd /Users/roza/ai-mcp-toolkit
python scripts/backfill_compound_metadata.py
```

This will re-process all existing images and extract OCR text.

---

## 🧪 Verify It Worked

After re-uploading, check the backend logs for:

```
Processing image: article.jpg
Extracting OCR text...
OCR text extracted: [length] characters
Caption generated: ...
```

### Test Search Again

1. Navigate to **Search page**
2. Search: `"Jak se formuje datová budoucnost"`
3. **Expected Results**:
   - article.jpg should be **#1** with **90%+** score
   - Match type badge: "High Relevance" (blue) or "Exact ID" (green)
   - Highlights: Yellow box with Czech text excerpt
   - "Open" button visible

---

## 🔍 What Changed Behind the Scenes

### Before (11% score)
```json
{
  "file_name": "article.jpg",
  "ocr_text": null,          ❌ Missing!
  "caption": null,           ❌ Missing!
  "text": "",                ❌ Empty!
  "text_embedding": [...]    ⚠️ No text to embed
}
```
- Only semantic match on filename
- No OCR text to match Czech words
- Result: Low score (11%)

### After Re-upload (90%+ score expected)
```json
{
  "file_name": "article.jpg",
  "ocr_text": "Snowflake Summit 2025: Jak se formuje datová budoucnost...",  ✅ Extracted!
  "caption": "A screenshot of a news article about Snowflake Summit",  ✅ Generated!
  "text": "Snowflake Summit 2025: Jak se formuje datová budoucnost...",  ✅ Populated!
  "text_embedding": [...],           ✅ Embedded
  "caption_embedding": [...]         ✅ Embedded
}
```
- OCR text matches query exactly (10x boost)
- Lexical match on Czech words (5x boost)
- Caption helps ranking (10x boost)
- Result: Top score (90%+)

---

## ⚙️ New Processing Pipeline

With pytesseract installed, every new image upload now:

1. **Detects file type** → image/jpeg, image/png, etc.
2. **Runs Tesseract OCR** → Extracts text (all languages)
3. **Generates caption** → LLaVA/Moondream description (if available)
4. **Extracts metadata** → Keywords, entities, amounts, etc.
5. **Creates embeddings** → text_embedding + caption_embedding
6. **Stores in database** → ResourceChunk with all fields
7. **Indexes in Atlas** → Searchable via compound search

---

## 🎯 Ranking Breakdown

After re-upload, your search will score like this:

**Query**: "Jak se formuje datová budoucnost"

| Component | Match | Boost | Score Contribution |
|-----------|-------|-------|-------------------|
| OCR text exact match | ✅ Yes | 10x | **High** |
| Lexical match (Czech words) | ✅ Yes | 5x | **High** |
| Caption text | ✅ Partial | 10x | **Medium** |
| Text embedding | ✅ Semantic | 1.5x | **Low** |
| Caption embedding | ✅ Semantic | 1.5x | **Low** |
| **Total** | | | **90%+** |

---

## 🐛 Troubleshooting

### If article.jpg still scores low after re-upload:

#### Check 1: OCR actually ran
Look in backend logs (terminal where python main.py runs):
```
INFO: Processing image: article.jpg
INFO: OCR text extracted: 250 characters
```

If you see errors like:
```
ERROR: pytesseract not available
ERROR: Could not extract OCR
```
Then pytesseract isn't accessible to the backend process.

**Fix**: Restart the backend server:
```bash
# Stop backend (Ctrl+C)
# Start again
python main.py
```

#### Check 2: Czech language support
Tesseract should auto-detect Czech, but verify:
```bash
tesseract --list-langs
```

Should include:
- `ces` (Czech)
- `eng` (English)

If Czech is missing:
```bash
brew install tesseract-lang
```

#### Check 3: Database has OCR text
Run diagnostic:
```bash
cd /Users/roza/ai-mcp-toolkit
export MONGODB_URI="your_connection_string_from_.env"
python3 scripts/check_article.py
```

Look for:
```
OCR text length: 250
OCR preview: Snowflake Summit 2025: Jak se formuje datová budoucnost...
```

If OCR length is 0, the extraction failed.

---

## 📋 Checklist

- [x] Install pytesseract (`pip install pytesseract`)
- [x] Install Pillow (`pip install pillow`)
- [x] Verify Tesseract installed (`tesseract --version`)
- [ ] **Re-upload article.jpg** (delete old one first)
- [ ] Check backend logs for OCR extraction
- [ ] Test search again
- [ ] Verify 90%+ score for article.jpg

---

## 🎉 Expected Outcome

After completing these steps:

**Query**: "Jak se formuje datová budoucnost"

**Results**:
1. **article.jpg** - 92% - "High Relevance" - OCR: "Snowflake Summit 2025: Jak se..."
2. ai-usage-policy-template.pdf - 43% - "Hybrid Match"
3. AKLIMA Tábor.html - 42% - "Hybrid Match"

The Czech screenshot should **dominate** because:
- ✅ Exact OCR text match (10x boost)
- ✅ All Czech words match (5x boost)
- ✅ High lexical score
- ✅ Caption reinforces relevance

---

**Next Step**: Delete and re-upload article.jpg, then test search!
