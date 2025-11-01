# Compound Search Setup Instructions

This guide provides step-by-step instructions to deploy the compound hybrid search system.

---

## Prerequisites

✅ **Already installed:**
- Ollama with `llava` model pulled
- Tesseract OCR installed (`brew install tesseract` on macOS)
- MongoDB Atlas with vector search enabled
- Python 3.11+ environment

---

## Step 1: Install Python Dependencies

Add the missing `pytesseract` package:

```bash
# Add to requirements.txt and pyproject.toml
pip install pytesseract>=0.3.10
```

### Update requirements.txt
Add this line:
```
pytesseract>=0.3.10  # OCR text extraction from images
```

### Update pyproject.toml
Add to `dependencies` list:
```python
"pytesseract>=0.3.10",
```

Then install:
```bash
pip install -e .
```

---

## Step 2: Create MongoDB Atlas Search Index

### Option A: Via Atlas Console (Recommended)

1. Log in to [MongoDB Atlas](https://cloud.mongodb.com)
2. Navigate to your cluster → **Search** tab
3. Click **Create Search Index**
4. Select **JSON Editor**
5. Paste the contents of `atlas_indexes/resource_chunks_compound_index.json`
6. Click **Create Search Index**
7. Wait for index to build (Status: "Active")

### Option B: Via MongoDB CLI

```bash
# Using mongocli or Atlas API
atlas clusters search indexes create \
  --clusterName YOUR_CLUSTER \
  --file atlas_indexes/resource_chunks_compound_index.json
```

### Verify Index

```python
# In Python shell or script
from pymongo import MongoClient

client = MongoClient("YOUR_MONGODB_URI")
db = client.ai_mcp_toolkit

# List search indexes
indexes = db.resource_chunks.list_search_indexes()
for idx in indexes:
    print(f"Index: {idx['name']}, Status: {idx['status']}")
```

Expected output:
```
Index: resource_chunks_compound, Status: READY
```

---

## Step 3: Verify Dependencies

Run the verification script:

```python
# verify_compound_search.py
import asyncio
from src.ai_mcp_toolkit.services.image_caption_service import ImageCaptionService
from src.ai_mcp_toolkit.services.query_analyzer import QueryAnalyzer
from src.ai_mcp_toolkit.services.metadata_extractor import MetadataExtractor

async def verify_setup():
    print("✓ Checking components...")
    
    # Check QueryAnalyzer
    analyzer = QueryAnalyzer()
    result = analyzer.analyze("invoice for $1234.56 from Google")
    assert result['money']['cents'] == 123456
    print("✓ QueryAnalyzer working")
    
    # Check MetadataExtractor
    extractor = MetadataExtractor()
    metadata = extractor.extract("Invoice INV-2024-001 for $500 from Acme Inc")
    assert len(metadata['keywords']) > 0
    print("✓ MetadataExtractor working")
    
    # Check ImageCaptionService
    service = ImageCaptionService()
    tesseract_ok = service.check_tesseract_available()
    vision_ok = service.check_vision_model_available()
    
    print(f"{'✓' if tesseract_ok else '✗'} Tesseract OCR available")
    print(f"{'✓' if vision_ok else '✗'} LLaVA vision model available")
    
    if not vision_ok:
        print("  → Run: ollama pull llava")
    
    print("\n✓ All components verified!")

asyncio.run(verify_setup())
```

Run it:
```bash
python verify_compound_search.py
```

---

## Step 4: Test Image Processing (Optional)

Test the image caption service with a sample image:

```python
# test_image_caption.py
import asyncio
from src.ai_mcp_toolkit.services.image_caption_service import process_image_file

async def test_image():
    # Use any test image
    result = await process_image_file("path/to/test_image.jpg")
    
    print("Caption:", result['caption'])
    print("Labels:", result['image_labels'])
    print("OCR Text:", result['ocr_text'][:100] if result['ocr_text'] else "None")
    print("Embedding dims:", len(result['caption_embedding']) if result['caption_embedding'] else 0)

asyncio.run(test_image())
```

---

## Step 5: Backend Integration (Phase 5-6)

The following files need to be updated (implementation in next phases):

### Phase 5: Ingestion Pipeline
- `src/ai_mcp_toolkit/services/ingestion_service.py` - Add metadata extraction
- `src/ai_mcp_toolkit/managers/resource_manager.py` - Update chunk creation

### Phase 6: Search Endpoint
- `src/ai_mcp_toolkit/server/http_server.py` - Add `/search` compound endpoint
- `src/ai_mcp_toolkit/services/search_service.py` - Implement compound search logic

These will be implemented in subsequent phases with full code examples.

---

## Step 6: Backfill Existing Data (After Phase 5)

Once ingestion is updated, backfill metadata for existing chunks:

```bash
python scripts/backfill_compound_metadata.py
```

This script will:
1. Read all existing `resource_chunks`
2. Extract metadata (keywords, vendor, amounts, etc.)
3. Update chunks with new fields
4. Report progress

**Estimated time:** ~1-5 min per 1000 chunks (depending on content complexity)

---

## Step 7: Frontend Updates (Phase 7)

Update the search UI:
- Remove mode selector dropdown
- Add match type badges
- Add "Open" deep-link buttons
- Display highlights from Atlas

---

## Troubleshooting

### Tesseract not found
```bash
# macOS
brew install tesseract

# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# Verify
tesseract --version
```

### LLaVA model not available
```bash
ollama pull llava
ollama list  # verify it's listed
```

### MongoDB Atlas index won't build
- Check collection exists: `resource_chunks`
- Check fields exist (at least one document with new schema)
- Verify cluster tier supports vector search (M10+)
- Check index definition JSON syntax

### Python import errors
```bash
# Reinstall in editable mode
pip install -e .

# Or explicitly
pip install pytesseract pillow
```

---

## Verification Checklist

Before proceeding to implementation:

- [ ] `pytesseract` installed and importable
- [ ] Tesseract CLI accessible (`tesseract --version`)
- [ ] LLaVA model pulled in Ollama (`ollama list`)
- [ ] Atlas search index created and READY
- [ ] QueryAnalyzer tests pass
- [ ] MetadataExtractor tests pass
- [ ] ImageCaptionService can process test image

---

## Next Steps

Once setup is complete:

1. **Phase 5**: Update ingestion pipeline to extract metadata
2. **Phase 6**: Implement compound `/search` endpoint
3. **Phase 7**: Update frontend search UI
4. **Phase 9**: Run backfill script for existing data
5. **Phase 10**: Update documentation

---

## Support

If you encounter issues:
- Check logs: `tail -f logs/ai-mcp-toolkit.log`
- Verify Ollama is running: `ollama list`
- Test Atlas connection: `python test_db_connection.py`
- Review error messages in console

---

## Performance Notes

**Image processing:**
- LLaVA caption: ~2-5 sec per image (CPU) or ~1-2 sec (GPU)
- Tesseract OCR: ~0.5-2 sec per image
- Caption embedding: ~0.1-0.5 sec

**Search performance:**
- Compound queries: ~50-200ms (depends on result set size)
- Vector similarity: ~20-100ms per query
- Metadata filters: ~5-20ms

**Recommendations:**
- Process images async during upload
- Cache caption embeddings (don't regenerate)
- Use pagination for large result sets (limit: 30 default)
