# MongoDB Atlas Vector Search Index Setup

**Date**: 2025-10-28  
**Status**: ⏸️ Manual Setup Required

## Overview

This guide explains how to create vector search indexes in MongoDB Atlas to enable semantic search for resources.

## Prerequisites

- MongoDB Atlas cluster (already configured)
- Admin access to Atlas UI
- Database: Your project database
- Collection: `resources`

## Index 1: Resource-Level Vector Search

This index enables semantic search across entire documents using the main `embeddings` field.

### Steps

1. Go to MongoDB Atlas UI
2. Navigate to: **Cluster** → **Search** tab
3. Click **"Create Search Index"**
4. Select **"JSON Editor"**
5. Paste the following configuration:

```json
{
  "name": "resource_vector_index",
  "type": "vectorSearch",
  "definition": {
    "fields": [
      {
        "type": "vector",
        "path": "embeddings",
        "numDimensions": 768,
        "similarity": "cosine"
      },
      {
        "type": "filter",
        "path": "owner_id"
      },
      {
        "type": "filter",
        "path": "resource_type"
      },
      {
        "type": "filter",
        "path": "mime_type"
      }
    ]
  }
}
```

6. Select **database** and **collection**: `resources`
7. Click **"Create Search Index"**
8. Wait for index to build (usually 1-2 minutes)

### Index Details

- **Name**: `resource_vector_index`
- **Type**: Vector Search
- **Dimensions**: 768 (for Ollama `nomic-embed-text` model)
- **Similarity**: Cosine (best for normalized embeddings)
- **Filters**: User isolation (`owner_id`), resource filtering

### Usage

This index is used for:
- Semantic search across all documents
- "Find similar resources" feature
- High-level document matching

## Index 2: Chunk-Level Vector Search

This index enables precise search within document chunks for large documents.

### Steps

1. Go to MongoDB Atlas UI
2. Navigate to: **Cluster** → **Search** tab
3. Click **"Create Search Index"**
4. Select **"JSON Editor"**
5. Paste the following configuration:

```json
{
  "name": "resource_chunks_vector_index",
  "type": "vectorSearch",
  "definition": {
    "fields": [
      {
        "type": "vector",
        "path": "chunks.embeddings",
        "numDimensions": 768,
        "similarity": "cosine"
      },
      {
        "type": "filter",
        "path": "owner_id"
      },
      {
        "type": "filter",
        "path": "resource_type"
      }
    ]
  }
}
```

6. Select **database** and **collection**: `resources`
7. Click **"Create Search Index"**
8. Wait for index to build

### Index Details

- **Name**: `resource_chunks_vector_index`
- **Type**: Vector Search
- **Path**: `chunks.embeddings` (nested array)
- **Dimensions**: 768
- **Similarity**: Cosine

### Usage

This index is used for:
- Precise search within large documents
- RAG (Retrieval Augmented Generation) context extraction
- Finding specific paragraphs/sections
- Better accuracy for long documents

## Verification

After creating indexes, verify they're active:

```bash
# In MongoDB shell or Atlas UI
db.resources.getIndexes()
```

You should see both vector search indexes listed with status "READY".

## Index Build Time

- Small collections (< 1000 docs): ~1-2 minutes
- Medium collections (1000-10000 docs): ~5-10 minutes
- Large collections (> 10000 docs): ~15-30 minutes

## If Using OpenAI Embeddings

If you switch to OpenAI `text-embedding-3-small` (1536 dimensions), update both indexes:

```json
{
  "numDimensions": 1536
}
```

## Troubleshooting

### Index Build Fails
- Check cluster tier supports vector search (M10+)
- Verify collection exists and has documents
- Check JSON syntax is valid

### Search Returns No Results
- Verify index status is "READY"
- Check embeddings field exists in documents
- Verify embedding dimensions match (768 for Ollama)
- Check filter conditions (owner_id, etc.)

### Slow Search Performance
- Increase `numCandidates` in search pipeline
- Add more filters to narrow search space
- Consider upgrading Atlas cluster tier

## Cost Considerations

**MongoDB Atlas Vector Search Pricing**:
- M10+ clusters support vector search
- No additional cost for vector search itself
- Storage costs apply for embedding data (~4KB per document with 768 dims)
- Estimate: 1000 documents × 4KB = ~4MB storage

## Next Steps

After creating indexes:
1. ✅ Continue to Phase 2: Embedding Generation Service
2. Test semantic search with sample documents
3. Monitor query performance in Atlas
4. Adjust `numCandidates` based on result quality

---

**Status**: ⏸️ Waiting for manual Atlas UI setup  
**Expected Time**: 5-10 minutes  
**Required**: Admin access to MongoDB Atlas
