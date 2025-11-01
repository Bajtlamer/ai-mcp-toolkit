# How Semantic Search Currently Works in Your System

Your semantic search uses **vector embeddings** to find documents based on meaning, not just keywords.

## Current Architecture

### 1. **Document Processing & Storage**
When you upload a document (PDF, text, etc.):
- The content is extracted and split into **chunks** (smaller text segments)
- Each chunk is converted to a **vector embedding** using your configured AI model (Ollama)
- These embeddings are stored in **MongoDB Atlas** with **vector search indexes**

### 2. **Search Process**
When you search for "google invoice":

```
User Query: "google invoice"
         ↓
   Query Embedding (vector)
         ↓
   MongoDB Atlas Vector Search
         ↓
   Cosine Similarity Calculation
         ↓
   Ranked Results with Scores
```

### 3. **Scoring System**
The scores you see (60%, 88%, etc.) represent **cosine similarity**:
- **80-100%**: Very high semantic similarity (same topic/context)
- **60-80%**: Moderate similarity (related concepts)
- **40-60%**: Low similarity (some shared vocabulary)
- **0-40%**: Little to no similarity

### 4. **Why "google invoice" Returns 60% for Both Documents**

Both documents contain:
- Business/commercial language
- Structured data (dates, amounts, names)
- Professional formatting context

The search finds semantic overlap even if one is an AI policy and the other is an invoice because they share:
- Corporate/business domain vocabulary
- Document structure patterns
- Professional tone and terminology

### 5. **Backend Implementation**

Your search uses two modes:

**Document-level search** (`semantic_search`):
```python
# Searches across full documents
# Returns aggregated scores per resource
# Best for: "What documents discuss AI policy?"
```

**Chunk-level search** (`semantic_search_chunks`):
```python
# Searches individual text chunks
# Returns specific matching passages
# Best for: "Find the exact section about invoices"
```

### 6. **Key Components**

- **Vector Index**: MongoDB Atlas vector search index on `resource_chunks.embedding`
- **Embedding Model**: Uses your configured Ollama model for vectorization
- **Pipeline**: Query → Embed → Search → Aggregate → Score → Rank
- **Storage**: Embeddings stored as arrays in `resource_chunks` collection

### 7. **Current Features**

✅ Real-time semantic search  
✅ Debounced input (300ms delay)  
✅ Visual similarity scores with color coding  
✅ "Find Similar" to discover related documents  
✅ Toggle between document and chunk search modes  
✅ User-specific results (only searches your documents)  

The system correctly distinguishes between documents—more specific queries like "AI usage policy" return much higher scores (88%) for the policy document, proving semantic differentiation works as designed.

---

## Search Type Modes Explained

Your system supports multiple search strategies, each optimized for different use cases:

### **Auto Mode** 🤖
**Smart query routing based on query analysis**

- Automatically selects the best search type for your query
- Analyzes query characteristics (length, specificity, keywords)
- Routes to semantic, keyword, or hybrid based on context
- **Best for**: General use when you're unsure which mode to use
- **Example**: "find AI policy" → routes to semantic; "invoice-2024-001" → routes to keyword

**Decision Logic**:
```
Short exact terms (IDs, codes) → Keyword
Natural language questions → Semantic
Mixed queries → Hybrid
```

---

### **Semantic Search** 🧠
**Meaning-based search using vector embeddings**

- Converts query to vector embedding
- Finds documents with similar semantic meaning
- Works across synonyms and related concepts
- Language and phrasing independent
- **Best for**: Conceptual searches, natural language queries
- **Examples**:
  - "documents about artificial intelligence guidelines"
  - "invoices from tech companies"
  - "policies related to data privacy"

**How it works**:
1. Query → embedding vector (1536 dimensions)
2. Vector similarity search in MongoDB Atlas
3. Returns documents with closest semantic match
4. Scores based on cosine similarity (0-100%)

**Pros**:
- Understands context and meaning
- Finds related concepts even without exact keywords
- Works with natural language

**Cons**:
- May miss exact matches if semantically distant
- Requires embeddings (preprocessing time)
- Less precise for specific IDs or codes

---

### **Keyword Search** 🔍
**Traditional text-based search using exact matching**

- MongoDB text search on indexed fields
- Matches exact words and stems (e.g., "run" matches "running")
- Boolean operators supported (AND, OR, NOT)
- Fast and deterministic
- **Best for**: Exact terms, IDs, codes, names, specific phrases
- **Examples**:
  - "invoice-2024-001"
  - "John Smith"
  - "GDPR compliance"
  - "contract-renewal-2025"

**How it works**:
1. Query → tokenized terms
2. MongoDB `$text` search on indexed fields
3. Returns documents with matching terms
4. Scores based on text relevance (term frequency, position)

**Pros**:
- Very fast (uses database indexes)
- Predictable and deterministic
- Great for exact matches

**Cons**:
- Misses synonyms and related concepts
- Sensitive to exact wording
- No understanding of meaning

---

### **Hybrid Search** ⚡
**Combines semantic and keyword search for best of both worlds**

- Runs both semantic and keyword search in parallel
- Merges and ranks results using **Reciprocal Rank Fusion (RRF)**
- Balances precision (keyword) with recall (semantic)
- **Best for**: Complex queries needing both exact matches and conceptual relevance
- **Examples**:
  - "AI policy document from 2024"
  - "Google invoice related to cloud services"
  - "GDPR data privacy guidelines"

**How it works**:
1. Query → runs both semantic and keyword searches
2. Each returns ranked results with scores
3. RRF algorithm merges results:
   ```
   score = Σ(1 / (k + rank))  where k=60 (constant)
   ```
4. Returns unified ranked list

**Example Fusion**:
```
Semantic Results:        Keyword Results:
1. doc_A (95%)          1. doc_B (exact match)
2. doc_C (87%)          2. doc_A (partial match)
3. doc_B (80%)          3. doc_D (fuzzy match)

Hybrid (RRF merged):
1. doc_A (high in both → top rank)
2. doc_B (strong in one, moderate in other)
3. doc_C (strong semantic only)
4. doc_D (keyword only)
```

**Pros**:
- Best overall relevance
- Catches both exact matches and concepts
- Robust to query type

**Cons**:
- Slower (runs two searches)
- More resource intensive
- May return more results to sort through

---

## Choosing the Right Search Type

| Query Type | Best Mode | Example |
|------------|-----------|---------|
| Natural language question | **Semantic** | "What are the AI usage guidelines?" |
| Exact ID or code | **Keyword** | "INV-2024-12345" |
| Person or company name | **Keyword** | "Acme Corp" |
| Conceptual topic | **Semantic** | "renewable energy policies" |
| Mixed (concept + specific) | **Hybrid** | "Google cloud invoice from Q4" |
| Unsure / exploratory | **Auto** | Let the system decide |

---

## Implementation Status

### Currently Implemented ✅
- Semantic search (document & chunk level)
- Vector embeddings via Ollama
- MongoDB Atlas vector search indexes
- Cosine similarity scoring
- User-specific filtering

### Planned (based on search type descriptions) 🔄
- Keyword search mode using MongoDB `$text` indexes
- Hybrid search with RRF merging
- Auto mode with intelligent routing
- Search type selector in UI

---

## Technical Details

### Vector Embeddings
- **Model**: Configured Ollama model (typically `nomic-embed-text` or similar)
- **Dimensions**: 768-1536 (model dependent)
- **Storage**: MongoDB `resource_chunks` collection
- **Index**: Atlas vector search index with cosine similarity

### Database Collections
```
resources: metadata, URI, owner_id
resource_chunks: text chunks, embeddings, parent_id
```

### Search Pipeline
```python
# Semantic Search Pipeline
query → embed(query) → vector_search(embedding) → 
  aggregate_by_resource → calculate_avg_score → rank → return
```

### Performance Considerations
- Embeddings cached in database (no re-computation)
- Vector search optimized with Atlas indexes
- Chunk-level search for precision vs document-level for overview
- User filtering applied at query level (not post-processing)

---

## Next Steps for Full Search Implementation

1. **Add MongoDB text indexes** on `resources.name`, `resources.description`, `resource_chunks.content`
2. **Implement keyword_search endpoint** using `$text` query
3. **Implement hybrid_search endpoint** with RRF merging
4. **Add auto mode** with query analysis and routing logic
5. **Update frontend UI** with search type selector dropdown
6. **Add search analytics** to track which modes users prefer

