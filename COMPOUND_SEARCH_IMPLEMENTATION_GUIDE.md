# Compound Search Implementation Guide

## ✅ Can Compound Search Work with Ollama?

**YES! Absolutely.** Here's how it works:

### How Ollama Fits In

1. **During Document Upload (Ingestion)**:
   - Ollama generates embeddings using `nomic-embed-text` model
   - Embeddings are stored in MongoDB (`text_embedding` field)
   - This happens ONCE per document

2. **During Search Queries**:
   - Ollama generates embedding for the search query
   - This embedding is used to search against stored document embeddings
   - Ollama doesn't need to process every document - just the query!

3. **MongoDB Atlas Search Does the Heavy Lifting**:
   - Atlas Search performs the actual vector similarity search
   - Combines vector search + keyword search + filters in one query
   - This is **FAST** and doesn't require Ollama at all

### The Architecture

```
User Query: "invoice for $1234.56 from Google"
    ↓
Ollama (nomic-embed-text): Generate query embedding [0.123, 0.456, ...]
    ↓
MongoDB Atlas Search ($search.compound):
    - Vector search (should): Find similar embeddings
    - Keyword search (should): Match "invoice", "Google"  
    - Filters (must): amounts_cents = 123456, vendor = "Google"
    ↓
Results with scores and highlights
```

**Key Point**: Ollama is only needed to generate embeddings. The actual search is done by MongoDB Atlas, which is optimized for this.

---

## Current State Analysis

Looking at your code, here's what you have vs. what you need:

### ✅ What You Already Have

1. **QueryAnalyzer** - Extracts money, IDs, dates, entities ✅
2. **EmbeddingService** - Generates embeddings via Ollama ✅
3. **MetadataExtractor** - Extracts keywords, vendor, amounts ✅
4. **Text Normalization** - Diacritic-insensitive search ✅
5. **Keyword Search** - Working with normalized text ✅
6. **Semantic Search** - Working with Python cosine similarity ✅
7. **Hybrid Search** - Combines semantic + keyword ✅

### ❌ What's Missing for True Compound Search

1. **MongoDB Atlas Search Index** - Not deployed yet
2. **Atlas Compound Query Implementation** - Currently using Python fallback
3. **Proper `$search.compound` Aggregation** - Not implemented

### Current Problem

Your `compound_search()` method in `search_service.py` currently:
```python
async def compound_search(...):
    # Currently just calls keyword_search!
    return await self.search(query, company_id, limit, search_type="keyword")
```

It should be using MongoDB Atlas `$search.compound` instead!

---

## Implementation Plan

### Step 1: Verify MongoDB Atlas Setup

**Check if you have MongoDB Atlas with vector search enabled:**

```bash
# Check your MongoDB connection
python -c "
from motor.motor_asyncio import AsyncIOMotorClient
import os
import asyncio

async def check():
    client = AsyncIOMotorClient(os.getenv('MONGODB_URL'))
    db = client.ai_mcp_toolkit
    # List search indexes
    indexes = await db.resource_chunks.list_search_indexes()
    print('Search indexes:', [idx['name'] for idx in indexes])
    # Check if compound index exists
    for idx in indexes:
        if 'compound' in idx['name'].lower():
            print(f'✅ Found compound index: {idx["name"]} (Status: {idx.get("status")})')
            break
    else:
        print('❌ No compound index found')

asyncio.run(check())
"
```

**If you don't have Atlas with vector search:**
- MongoDB Atlas M10+ tier required for vector search
- Or use MongoDB 7.0+ self-hosted (but Atlas is easier)

### Step 2: Deploy Atlas Search Index

If index doesn't exist, create it:

```bash
# Option 1: Via Atlas Console (easiest)
# 1. Go to https://cloud.mongodb.com
# 2. Navigate to your cluster → Search tab
# 3. Click "Create Search Index" → "JSON Editor"
# 4. Paste contents of atlas_indexes/resource_chunks_compound_index.json
# 5. Click "Create"

# Option 2: Via MongoDB Shell
mongosh YOUR_MONGODB_URI
use ai_mcp_toolkit

db.resource_chunks.createSearchIndex({
  "name": "resource_chunks_compound",
  "definition": {
    "mappings": {
      "dynamic": false,
      "fields": {
        "searchable_text": {
          "type": "string",
          "analyzer": "lucene.standard"
        },
        "text_embedding": {
          "type": "knnVector",
          "dimensions": 768,
          "similarity": "cosine"
        },
        "caption_embedding": {
          "type": "knnVector",
          "dimensions": 768,
          "similarity": "cosine"
        },
        "vendor": {"type": "string", "analyzer": "lucene.keyword"},
        "amounts_cents": {"type": "number"},
        "currency": {"type": "string", "analyzer": "lucene.keyword"},
        "keywords": {"type": "string", "analyzer": "lucene.keyword"},
        "company_id": {"type": "string", "analyzer": "lucene.keyword"},
        "owner_id": {"type": "string", "analyzer": "lucene.keyword"}
      }
    }
  }
})
```

**Wait for index to be READY** (can take a few minutes):
```bash
# Check status
db.resource_chunks.listSearchIndexes()
```

### Step 3: Implement True Compound Search

Here's the implementation you need to add to `SearchService`:

```python
async def compound_search_atlas(
    self,
    query: str,
    company_id: str,
    limit: int = 30,
    query_analysis: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    True MongoDB Atlas compound search using $search.compound.
    
    Combines:
    - Vector similarity search (knnBeta)
    - Keyword/text search (text)
    - Exact filters (must clauses)
    """
    from motor.motor_asyncio import AsyncIOMotorClient
    from ..models.database import db_manager
    import os
    
    # Generate query embedding (using Ollama)
    query_embedding = await self.embedding_service.embed_text(query)
    
    # Analyze query if not provided
    if query_analysis is None:
        query_analysis = await self._analyze_query(query, company_id)
    
    # Build compound query
    compound_clauses = []
    
    # 1. MUST clauses (exact filters)
    must_clauses = []
    
    # Filter by company_id (always required)
    must_clauses.append({
        "equals": {
            "value": company_id,
            "path": "company_id"
        }
    })
    
    # Exact amount matches
    if query_analysis.get('money_amounts'):
        for amount_cents in query_analysis['money_amounts']:
            must_clauses.append({
                "equals": {
                    "value": amount_cents,
                    "path": "amounts_cents"
                }
            })
    
    # Exact vendor matches
    if query_analysis.get('vendors'):
        must_clauses.append({
            "text": {
                "query": query_analysis['vendors'][0],
                "path": "vendor"
            }
        })
    
    # 2. SHOULD clauses (ranking/relevance)
    should_clauses = []
    
    # Vector similarity (semantic search)
    should_clauses.append({
        "knnBeta": {
            "vector": query_embedding,
            "path": "text_embedding",
            "k": limit * 2  # Get more candidates, then rank
        }
    })
    
    # Keyword search on normalized text
    query_normalized = normalize_query(query)
    should_clauses.append({
        "text": {
            "query": query_normalized,
            "path": ["searchable_text", "text_normalized", "ocr_text_normalized"],
            "score": {"boost": {"value": 2.0}}  # Boost keyword matches
        }
    })
    
    # Image caption search (if query mentions images)
    if query_analysis.get('file_types') and any(ft in ['image', 'jpg', 'png'] for ft in query_analysis['file_types']):
        should_clauses.append({
            "text": {
                "query": query_normalized,
                "path": ["caption", "image_labels", "ocr_text"],
                "score": {"boost": {"value": 1.5}}
            }
        })
        # Also use caption embedding if available
        if query_analysis.get('clean_text'):
            caption_embedding = await self.embedding_service.embed_text(query_analysis['clean_text'])
            should_clauses.append({
                "knnBeta": {
                    "vector": caption_embedding,
                    "path": "caption_embedding",
                    "k": limit
                }
            })
    
    # Build final compound query
    compound_query = {
        "compound": {
            "must": must_clauses if must_clauses else None,
            "should": should_clauses,
            "minimumShouldMatch": 1  # At least one should clause must match
        }
    }
    
    # Remove None values
    if compound_query["compound"]["must"] is None:
        del compound_query["compound"]["must"]
    
    # Execute Atlas Search aggregation
    try:
        client = db_manager.client
        db = client[db_manager.database_name]
        collection = db.resource_chunks
        
        pipeline = [
            {
                "$search": {
                    "index": "resource_chunks_compound",  # Your index name
                    **compound_query
                }
            },
            {
                "$addFields": {
                    "score": {"$meta": "searchScore"},
                    "highlights": {"$meta": "searchHighlights"}
                }
            },
            {
                "$lookup": {
                    "from": "resources",
                    "localField": "parent_id",
                    "foreignField": "_id",
                    "as": "resource"
                }
            },
            {
                "$unwind": {
                    "path": "$resource",
                    "preserveNullAndEmptyArrays": True
                }
            },
            {
                "$limit": limit
            },
            {
                "$project": {
                    "_id": 1,
                    "text": 1,
                    "chunk_index": 1,
                    "page_number": 1,
                    "row_index": 1,
                    "score": 1,
                    "highlights": 1,
                    "resource_id": "$parent_id",
                    "file_name": "$resource.file_name",
                    "file_id": "$resource.file_id",
                    "file_type": "$resource.file_type",
                    "mime_type": "$resource.mime_type",
                    "vendor": "$resource.vendor",
                    "summary": "$resource.summary"
                }
            }
        ]
        
        results = []
        async for doc in collection.aggregate(pipeline):
            # Determine match type
            match_type = "compound"
            if query_analysis.get('money_amounts') and doc.get('highlights'):
                match_type = "exact_amount"
            elif query_analysis.get('vendors'):
                match_type = "vendor_match"
            elif doc.get('highlights'):
                match_type = "semantic_strong" if doc['score'] > 0.7 else "hybrid"
            
            results.append({
                'id': str(doc.get('resource_id', doc['_id'])),
                'file_id': doc.get('file_id'),
                'file_name': doc.get('file_name'),
                'file_type': doc.get('file_type'),
                'mime_type': doc.get('mime_type'),
                'summary': doc.get('summary'),
                'vendor': doc.get('vendor'),
                'score': doc.get('score', 0.0),
                'match_type': match_type,
                'chunk_index': doc.get('chunk_index'),
                'chunk_preview': doc.get('text', '')[:200],
                'highlights': doc.get('highlights', []),
                'page_number': doc.get('page_number'),
                'row_index': doc.get('row_index'),
                'open_url': self._build_deep_link({
                    'id': doc.get('resource_id'),
                    'page_number': doc.get('page_number'),
                    'row_index': doc.get('row_index')
                })
            })
        
        return results
        
    except Exception as e:
        self.logger.error(f"Atlas compound search error: {e}", exc_info=True)
        # Fallback to current implementation
        self.logger.warning("Falling back to keyword search")
        return await self._keyword_search(query, company_id, limit, query_analysis)
```

### Step 4: Update compound_search() Method

Replace the current `compound_search()` method:

```python
async def compound_search(
    self,
    query: str,
    owner_id: str,
    company_id: Optional[str] = None,
    limit: int = 30
) -> Dict[str, Any]:
    """
    Compound search using MongoDB Atlas $search.compound.
    
    Falls back to keyword search if Atlas Search is unavailable.
    """
    try:
        company_id = company_id or owner_id
        
        # Analyze query
        query_analysis = await self._analyze_query(query, company_id)
        
        # Try Atlas compound search first
        try:
            results = await self.compound_search_atlas(
                query=query,
                company_id=company_id,
                limit=limit,
                query_analysis=query_analysis
            )
            
            return {
                'query': query,
                'query_analysis': query_analysis,
                'results': results,
                'total': len(results),
                'search_strategy': 'compound_atlas',
                'search_type': 'compound'
            }
            
        except Exception as atlas_error:
            self.logger.warning(
                f"Atlas compound search failed: {atlas_error}. "
                f"Falling back to keyword search."
            )
            # Fallback to keyword search
            results = await self._keyword_search(
                query, company_id, limit, query_analysis
            )
            
            return {
                'query': query,
                'query_analysis': query_analysis,
                'results': results,
                'total': len(results),
                'search_strategy': 'keyword_fallback',
                'search_type': 'keyword'
            }
            
    except Exception as e:
        self.logger.error(f"Compound search error: {e}", exc_info=True)
        raise
```

### Step 5: Verify Database Connection Access

Make sure `db_manager` provides access to the raw MongoDB client:

```python
# In models/database.py or wherever db_manager is defined
class DatabaseManager:
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.database_name: str = "ai_mcp_toolkit"
    
    # ... existing methods ...
    
    @property
    def client(self):
        if self._client is None:
            raise RuntimeError("Database not connected")
        return self._client
```

---

## Testing the Implementation

### Test 1: Verify Atlas Index

```python
# test_atlas_index.py
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os

async def test_index():
    client = AsyncIOMotorClient(os.getenv('MONGODB_URL'))
    db = client.ai_mcp_toolkit
    
    # List indexes
    indexes = await db.resource_chunks.list_search_indexes()
    print("Search indexes:")
    for idx in indexes:
        print(f"  - {idx['name']}: {idx.get('status', 'unknown')}")
    
    # Check if compound index exists and is ready
    compound_idx = [idx for idx in indexes if 'compound' in idx['name'].lower()]
    if compound_idx:
        idx = compound_idx[0]
        if idx.get('status') == 'READY':
            print(f"\n✅ Compound index is READY: {idx['name']}")
        else:
            print(f"\n⏳ Compound index is {idx.get('status')}: {idx['name']}")
    else:
        print("\n❌ No compound index found. Create it first!")

asyncio.run(test_index())
```

### Test 2: Test Compound Search

```python
# test_compound_search.py
import asyncio
from src.ai_mcp_toolkit.services.search_service import get_search_service

async def test_compound():
    service = get_search_service()
    
    # Test queries
    queries = [
        "invoice for $1234.56",
        "Google invoice",
        "PDF from last month",
        "receipt from Acme Corp"
    ]
    
    for query in queries:
        print(f"\n🔍 Query: '{query}'")
        result = await service.compound_search(
            query=query,
            owner_id="test_user_id",
            company_id="test_company_id",
            limit=5
        )
        
        print(f"  Strategy: {result.get('search_strategy')}")
        print(f"  Results: {result['total']}")
        for i, res in enumerate(result['results'][:3], 1):
            print(f"    {i}. {res.get('file_name')} (score: {res.get('score', 0):.2f}, type: {res.get('match_type')})")

asyncio.run(test_compound())
```

---

## Performance Comparison

### Current Implementation (Python)
- **Semantic Search**: Loads all chunks, calculates cosine similarity in Python
- **Speed**: ~500ms - 2s for 1000 chunks
- **Scaling**: Poor - gets slower as data grows

### Atlas Compound Search
- **Vector Search**: Optimized C++ implementation
- **Speed**: ~50-200ms for millions of documents
- **Scaling**: Excellent - constant time regardless of data size
- **Features**: Built-in highlights, scoring, filtering

---

## Checklist

Before implementing:
- [ ] MongoDB Atlas cluster with M10+ tier (or self-hosted 7.0+)
- [ ] Atlas Search index created and status is "READY"
- [ ] Verify index name matches code (`resource_chunks_compound`)
- [ ] Test database connection and access to `db_manager.client`
- [ ] Verify Ollama `nomic-embed-text` model is available
- [ ] Test embedding generation works

After implementing:
- [ ] Test compound search with various queries
- [ ] Verify results include highlights
- [ ] Check match types are correct
- [ ] Test fallback to keyword search when Atlas fails
- [ ] Monitor performance (should be <200ms)

---

## Troubleshooting

### "Index not found" error
- Check index name matches exactly
- Verify index status is "READY" (not "BUILDING")
- Wait a few minutes after creating index

### "Vector dimensions mismatch"
- Verify embeddings are 768 dimensions (nomic-embed-text default)
- Check `text_embedding` field has 768 values

### "No results returned"
- Check `company_id` filter is correct
- Verify documents exist in `resource_chunks` collection
- Check documents have `text_embedding` field populated

### Slow performance
- Ensure index is created (not just defined)
- Check if using appropriate Atlas tier (M10+)
- Verify compound query structure is correct

---

## Summary

**Yes, compound search works perfectly with Ollama!** The key points:

1. ✅ Ollama generates embeddings (once per document, once per query)
2. ✅ MongoDB Atlas performs the actual search (fast, scalable)
3. ✅ Compound queries combine vector + keyword + filters
4. ✅ Your current code just needs to use Atlas Search instead of Python fallback

The implementation above will give you true compound search that:
- Finds documents by semantic similarity (vector search)
- Matches exact keywords and phrases (text search)
- Filters by exact values (money, vendor, etc.)
- Returns highlighted results with relevance scores

All while using Ollama for embedding generation, which it's perfect for!

