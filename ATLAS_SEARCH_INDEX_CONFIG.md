# MongoDB Atlas Search Index Configuration

## Overview

This document contains the Atlas Search index configurations needed for the contextual hybrid search system. These indexes enable:

- **Vector similarity search** using embeddings
- **Keyword/lexical search** on text fields
- **Numeric filters** for amounts, dates
- **Exact matching** on IDs, vendors, entities

## Setup Instructions

1. Log into MongoDB Atlas
2. Navigate to your cluster → Search → Create Search Index
3. Choose "JSON Editor"
4. Use the configurations below

---

## Index 1: Resources Collection

**Collection:** `resources`  
**Index Name:** `resources_hybrid_search`

```json
{
  "mappings": {
    "dynamic": false,
    "fields": {
      "text_embedding": {
        "type": "knnVector",
        "dimensions": 384,
        "similarity": "cosine"
      },
      "image_embedding": {
        "type": "knnVector",
        "dimensions": 512,
        "similarity": "cosine"
      },
      "file_name": {
        "type": "string",
        "analyzer": "lucene.standard"
      },
      "file_type": {
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
      "amounts_cents": {
        "type": "number"
      },
      "summary": {
        "type": "string",
        "analyzer": "lucene.standard"
      },
      "entities": {
        "type": "string",
        "analyzer": "lucene.standard"
      },
      "keywords": {
        "type": "string",
        "analyzer": "lucene.keyword"
      },
      "tags": {
        "type": "string",
        "analyzer": "lucene.keyword"
      },
      "company_id": {
        "type": "string",
        "analyzer": "lucene.keyword"
      },
      "uploaded_by": {
        "type": "string",
        "analyzer": "lucene.keyword"
      },
      "dates": {
        "type": "date"
      },
      "created_at": {
        "type": "date"
      }
    }
  }
}
```

---

## Index 2: Resource Chunks Collection

**Collection:** `resource_chunks`  
**Index Name:** `chunks_hybrid_search`

```json
{
  "mappings": {
    "dynamic": false,
    "fields": {
      "text_embedding": {
        "type": "knnVector",
        "dimensions": 384,
        "similarity": "cosine"
      },
      "image_embedding": {
        "type": "knnVector",
        "dimensions": 512,
        "similarity": "cosine"
      },
      "text": {
        "type": "string",
        "analyzer": "lucene.standard"
      },
      "chunk_type": {
        "type": "string",
        "analyzer": "lucene.keyword"
      },
      "resource_id": {
        "type": "string",
        "analyzer": "lucene.keyword"
      },
      "company_id": {
        "type": "string",
        "analyzer": "lucene.keyword"
      },
      "file_type": {
        "type": "string",
        "analyzer": "lucene.keyword"
      },
      "page_number": {
        "type": "number"
      },
      "row_number": {
        "type": "number"
      },
      "currency": {
        "type": "string",
        "analyzer": "lucene.keyword"
      },
      "amounts_cents": {
        "type": "number"
      },
      "entities": {
        "type": "string",
        "analyzer": "lucene.standard"
      },
      "keywords": {
        "type": "string",
        "analyzer": "lucene.keyword"
      },
      "dates": {
        "type": "date"
      }
    }
  }
}
```

---

## Index Configuration Notes

### Vector Dimensions

- **text_embedding**: 384 dimensions (all-MiniLM-L6-v2)
- **image_embedding**: 512 dimensions (clip-ViT-B-32)

If you change embedding models, update the dimensions accordingly.

### Analyzers

- **lucene.standard**: Tokenizes and lowercases text, suitable for full-text search
- **lucene.keyword**: No tokenization, exact matching only

### ACL Fields

Both indexes include `company_id` for tenant isolation. All queries MUST filter by company_id.

---

## Testing the Indexes

After creating indexes, test them with:

```javascript
// Test vector search
db.resources.aggregate([
  {
    "$search": {
      "index": "resources_hybrid_search",
      "knnBeta": {
        "vector": [0.1, 0.2, ...],  // 384-dim vector
        "path": "text_embedding",
        "k": 10
      }
    }
  }
])

// Test keyword search
db.resources.aggregate([
  {
    "$search": {
      "index": "resources_hybrid_search",
      "compound": {
        "must": [
          { "text": { "query": "invoice", "path": "file_name" } }
        ],
        "filter": [
          { "equals": { "path": "company_id", "value": "user123" } }
        ]
      }
    }
  }
])
```

---

## Maintenance

- Indexes update automatically as documents are inserted/updated
- Monitor index size in Atlas Search metrics
- Rebuild indexes if you change field mappings

---

## Future Enhancements

- Add autocomplete analyzer for type-ahead search
- Add language-specific analyzers for multilingual support
- Implement faceted search on tags, vendors, file types
