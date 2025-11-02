# Search Match Types & Scoring

This document explains all the match types used in the AI MCP Toolkit search system and how they're scored.

## Match Types (Highest to Lowest Score)

### 1. ✨ Exact Phrase (100% - 93%)
**Trigger:** Query text appears as an exact phrase in document content

**Score by field:**
- `searchable_text` (normalized content): **100%** (1.0)
- `ocr_text_normalized` (OCR from images): **98%** (0.98)
- `text_normalized` (regular text): **95%** (0.95)
- `image_description`: **93%** (0.93)

**Examples:**
- `"google invoice"` → Finds documents containing the exact phrase "google invoice"
- `"t-mobile contract"` → Finds documents with that exact phrase
- Works with diacritics: `"Michal"` matches "Michál" or "Michal"

**Badge:** Green "✨ Exact Phrase"

---

### 2. Exact Keyword (100%)
**Trigger:** Query matches an exact keyword/tag stored in document metadata

**Score:** **100%** (1.0)

**Examples:**
- Document tagged with `"INV-12345"` → Searching `"INV-12345"` returns exact match
- Document with keyword `"urgent"` → Searching `"urgent"` finds it

**Badge:** Blue "Exact Keyword"

---

### 3. Vendor Filter (88%)
**Trigger:** Query is primarily about a vendor (≤1 non-vendor word)

**Score:** **88%** (0.88)

**Vendor list:**
- google
- t-mobile / tmobile
- amazon / aws
- microsoft
- apple
- adobe
- salesforce
- zoom
- slack

**Ignored words:** invoice, invoices, bill, bills, payment, payments

**Examples:**
- ✅ `"google"` → Vendor match (0 non-vendor words)
- ✅ `"google invoice"` → Vendor match (invoice is ignored)
- ✅ `"t-mobile payment"` → Vendor match
- ✅ `"google czech"` → Vendor match (1 non-vendor word)
- ❌ `"google tag manager"` → NO vendor match (2 non-vendor words: tag, manager)

**Badge:** Yellow "Vendor Match"

**Note:** If the phrase also appears in content, Exact Phrase wins (100% > 88%)

---

### 4. Partial Words (50-60%)
**Trigger:** Some query words found in content, but not as exact phrase

**Score calculation:**
- `overlap_ratio = matching_words / total_query_words`
- `score = base_score × overlap_ratio`
- **Minimum 50% overlap required** for multi-word queries

**Base scores by field:**
- `searchable_text`: **50%** (0.5)
- `ocr_text_normalized`: **45%** (0.45)
- `text_normalized`: **40%** (0.4)

**Examples:**
- `"google cloud invoice"` might match document with "google" and "invoice" but not "cloud"
- Score depends on how many words match

**Badge:** Gray "Partial Match"

**Note:** Results below 50% score are filtered out to reduce noise

---

### 5. Semantic (Variable %)
**Trigger:** Vector similarity search (semantic meaning)

**Score:** Cosine similarity between query and document embeddings (0-100%)

**Types:**
- `semantic_document`: Document-level embedding match
- `semantic_chunk`: Chunk-level embedding match (more granular)

**Examples:**
- `"invoices from cloud providers"` → Finds Google/AWS invoices semantically
- `"renewable energy contracts"` → Finds related documents by meaning

**Badge:** Blue "Semantic" or "High Relevance"

---

### 6. Hybrid (Combined)
**Trigger:** Combines semantic + keyword approaches

**Score:** `(semantic_score × 0.6) + (keyword_score × 0.4)`

**Badge:** Gray "Hybrid Match"

---

## Search Strategy Selection

The system automatically chooses the best search strategy:

### Keyword Search
- Queries with exact IDs (e.g., `"INV-12345"`)
- Simple 1-2 word queries (e.g., `"google"`, `"invoice"`)
- **Uses:** Exact phrase matching + vendor filtering

### Hybrid Search  
- Queries with money amounts (e.g., `"$1,234.56 invoice"`)
- Queries with dates (e.g., `"2024-01-15 contract"`)
- Queries with vendors (e.g., `"google invoice"`)
- **Uses:** Combines semantic + keyword + filters

### Semantic Search
- Complex natural language queries (e.g., `"show me recent cloud infrastructure expenses"`)
- **Uses:** Vector similarity only

---

## Deduplication Logic

When multiple matches exist for the same document:

1. **Prefer higher score** (>5% difference)
2. **If scores close (±5%):** Prefer content match over vendor_filter
3. **Display highest scoring match type** as badge
4. **Vendor badge always shows separately** (from document metadata)

---

## Adding New Vendors

To add vendors to the detection list:

1. Edit `src/ai_mcp_toolkit/services/search_service.py`
2. Find the `vendor_patterns` list (line ~142)
3. Add vendor name in lowercase
4. Restart backend server

```python
vendor_patterns = [
    'google', 't-mobile', 'tmobile', 'amazon', 'aws', 'microsoft',
    'apple', 'adobe', 'salesforce', 'zoom', 'slack',
    'yourvendor'  # Add here
]
```

---

## Special Query Features

### Money Amounts
- Pattern: `$1,234.56`, `1234.56 USD`, `€500`, `1000 CZK`
- Triggers hybrid search
- Future: Will filter by exact amounts

### IDs
- Pattern: `INV-12345`, `ABC123`, `123456` (6+ digits)
- Triggers exact keyword search
- Score: 100%

### Dates
- Pattern: `2024-01-15`, `01/15/2024`
- Triggers hybrid search
- Future: Will filter by date ranges

### File Types
- Future feature: Filter by file extension
- Example: `"invoice pdf"`, `"contract.docx"`

---

## Tips for Better Search

1. **For exact documents:** Use specific phrases like `"google invoice march 2024"`
2. **For vendor documents:** Just use vendor name + type: `"google invoice"`
3. **For semantic search:** Use natural language: `"show me cloud expenses from last quarter"`
4. **For IDs:** Type the exact ID: `"INV-12345"`
5. **Diacritics don't matter:** `"Michal"` finds `"Michál"` automatically
