# Vector Embeddings & Semantic Search Implementation Plan

**Date Created**: 2025-10-27  
**Status**: 📋 Planning Phase  
**Priority**: 🟡 High (Future Enhancement)  
**Estimated Time**: 2-3 days

## Overview

Implement automatic vectorization of uploaded resources to enable:
- ✅ Semantic search across user's documents
- ✅ AI-powered Q&A about stored resources
- ✅ Smart document recommendations
- ✅ Content similarity detection
- ✅ RAG (Retrieval Augmented Generation) capabilities

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      File Upload Flow                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  User uploads file                                           │
│         ↓                                                    │
│  Extract text content (PDF, DOC, TXT, etc.)                 │
│         ↓                                                    │
│  Chunk text (1000 chars per chunk)                          │
│         ↓                                                    │
│  Generate embeddings (Ollama/OpenAI)                        │
│         ↓                                                    │
│  Store in MongoDB with vector index                         │
│         ↓                                                    │
│  User can now search semantically!                          │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Phase 1: Database Schema Updates (30 min)

### Task 1.1: Update Resource Model

**File**: `src/ai_mcp_toolkit/models/documents.py`

```python
class Resource(Document):
    # ... existing fields ...
    
    # NEW: Vector embeddings fields
    embeddings: Optional[List[float]] = None
    embeddings_model: Optional[str] = None  # "nomic-embed-text", "text-embedding-3-small"
    embeddings_created_at: Optional[datetime] = None
    embeddings_chunk_count: Optional[int] = None
    
    # For chunked documents (large files)
    chunks: Optional[List[Dict[str, Any]]] = None
    # chunks = [
    #   {
    #     "index": 0,
    #     "text": "chunk content...",
    #     "embeddings": [0.1, 0.2, ...],
    #     "char_start": 0,
    #     "char_end": 1000
    #   },
    #   ...
    # ]
    
    class Settings:
        name = "resources"
        indexes = [
            # ... existing indexes ...
            # Vector search index (created in Atlas UI)
        ]
```

### Task 1.2: Create Vector Search Index in MongoDB Atlas

**Manual Step** (via MongoDB Atlas UI):

1. Go to Atlas → Your Cluster → Search
2. Create Search Index
3. Use JSON configuration:

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
      }
    ]
  }
}
```

**For chunked search**:
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
      }
    ]
  }
}
```

## Phase 2: Embedding Generation Service (1-2 hours)

### Task 2.1: Create Embedding Manager

**File**: `src/ai_mcp_toolkit/managers/embedding_manager.py` (NEW)

```python
"""Embedding generation and management for semantic search."""

import logging
from typing import List, Optional, Dict, Any
import ollama
from openai import OpenAI

logger = logging.getLogger(__name__)


class EmbeddingManager:
    """Manages embedding generation for resources."""
    
    def __init__(self, provider: str = "ollama", model: str = None):
        """
        Initialize embedding manager.
        
        Args:
            provider: "ollama" or "openai"
            model: Model name (default: nomic-embed-text for ollama,
                   text-embedding-3-small for openai)
        """
        self.provider = provider
        
        if provider == "ollama":
            self.model = model or "nomic-embed-text"
            self.dimensions = 768
        elif provider == "openai":
            self.model = model or "text-embedding-3-small"
            self.dimensions = 1536
            self.client = OpenAI()
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed (max 8000 tokens)
            
        Returns:
            List of floats (embedding vector)
        """
        try:
            if self.provider == "ollama":
                return await self._generate_ollama(text)
            elif self.provider == "openai":
                return await self._generate_openai(text)
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    async def _generate_ollama(self, text: str) -> List[float]:
        """Generate embedding using Ollama."""
        response = ollama.embeddings(
            model=self.model,
            prompt=text[:8000]  # Limit to avoid token limits
        )
        return response['embedding']
    
    async def _generate_openai(self, text: str) -> List[float]:
        """Generate embedding using OpenAI."""
        response = self.client.embeddings.create(
            model=self.model,
            input=text[:8000]
        )
        return response.data[0].embedding
    
    async def generate_batch_embeddings(
        self, 
        texts: List[str]
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        if self.provider == "openai":
            # OpenAI supports batch processing
            response = self.client.embeddings.create(
                model=self.model,
                input=[t[:8000] for t in texts]
            )
            return [item.embedding for item in response.data]
        else:
            # Ollama: process one by one
            embeddings = []
            for text in texts:
                emb = await self.generate_embedding(text)
                embeddings.append(emb)
            return embeddings
    
    def chunk_text(
        self, 
        text: str, 
        chunk_size: int = 1000,
        overlap: int = 200
    ) -> List[Dict[str, Any]]:
        """
        Split text into overlapping chunks.
        
        Args:
            text: Text to chunk
            chunk_size: Characters per chunk
            overlap: Overlap between chunks
            
        Returns:
            List of chunk dictionaries with metadata
        """
        chunks = []
        start = 0
        index = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk_text = text[start:end]
            
            chunks.append({
                "index": index,
                "text": chunk_text,
                "char_start": start,
                "char_end": end,
                "embeddings": None  # Will be filled later
            })
            
            start += (chunk_size - overlap)
            index += 1
        
        return chunks
    
    async def embed_document(
        self,
        text: str,
        chunk_if_large: bool = True,
        chunk_size: int = 1000
    ) -> Dict[str, Any]:
        """
        Embed a document (with chunking for large docs).
        
        Args:
            text: Document text
            chunk_if_large: Whether to chunk large documents
            chunk_size: Size of chunks if chunking
            
        Returns:
            Dict with embeddings and chunks
        """
        # For short documents, single embedding
        if len(text) <= chunk_size or not chunk_if_large:
            embedding = await self.generate_embedding(text)
            return {
                "embeddings": embedding,
                "chunks": None,
                "chunk_count": 0
            }
        
        # For long documents, chunk and embed each chunk
        chunks = self.chunk_text(text, chunk_size=chunk_size)
        chunk_texts = [c["text"] for c in chunks]
        chunk_embeddings = await self.generate_batch_embeddings(chunk_texts)
        
        # Attach embeddings to chunks
        for chunk, embedding in zip(chunks, chunk_embeddings):
            chunk["embeddings"] = embedding
        
        # Also create a summary embedding (first chunk or average)
        summary_embedding = chunk_embeddings[0]
        
        return {
            "embeddings": summary_embedding,
            "chunks": chunks,
            "chunk_count": len(chunks)
        }


# Singleton instance
embedding_manager = EmbeddingManager(provider="ollama")
```

### Task 2.2: Add Configuration

**File**: `src/ai_mcp_toolkit/utils/config.py`

Add to Config class:
```python
# Embedding configuration
embedding_provider: str = "ollama"  # "ollama" or "openai"
embedding_model: Optional[str] = None  # Auto-detected per provider
embedding_chunk_size: int = 1000
embedding_enabled: bool = True
```

## Phase 3: Update Upload Endpoint (1 hour)

### Task 3.1: Modify Upload to Generate Embeddings

**File**: `src/ai_mcp_toolkit/server/http_server.py`

Add after file processing:

```python
from ..managers.embedding_manager import embedding_manager

# ... in upload_resource function ...

# After content extraction, before saving to database:
if self.config.embedding_enabled and content_str:
    try:
        self.logger.info(f"Generating embeddings for {file.filename}...")
        
        # Generate embeddings
        embedding_result = await embedding_manager.embed_document(
            text=content_str,
            chunk_if_large=True,
            chunk_size=self.config.embedding_chunk_size
        )
        
        # Add to metadata
        metadata['embeddings_model'] = embedding_manager.model
        metadata['embeddings_created_at'] = datetime.utcnow().isoformat()
        metadata['embeddings_chunk_count'] = embedding_result['chunk_count']
        
        # Store embeddings in resource
        resource = await self.resource_manager.create_resource(
            # ... existing params ...
            embeddings=embedding_result['embeddings'],
            chunks=embedding_result['chunks']
        )
        
        self.logger.info(f"Embeddings generated: {embedding_result['chunk_count']} chunks")
        
    except Exception as e:
        # Don't fail upload if embeddings fail
        self.logger.warning(f"Failed to generate embeddings: {e}")
        # Continue with normal upload (without embeddings)
```

### Task 3.2: Update ResourceManager

**File**: `src/ai_mcp_toolkit/managers/resource_manager.py`

Update `create_resource` method to accept embeddings:

```python
async def create_resource(
    self,
    # ... existing params ...
    embeddings: Optional[List[float]] = None,
    chunks: Optional[List[Dict[str, Any]]] = None
) -> Resource:
    """Create a new resource with optional embeddings."""
    
    # ... existing code ...
    
    resource = Resource(
        # ... existing fields ...
        embeddings=embeddings,
        chunks=chunks,
        embeddings_model=metadata.get('embeddings_model'),
        embeddings_created_at=datetime.utcnow() if embeddings else None,
        embeddings_chunk_count=metadata.get('embeddings_chunk_count', 0)
    )
    
    await resource.save()
    return resource
```

## Phase 4: Semantic Search API (1-2 hours)

### Task 4.1: Create Search Endpoints

**File**: `src/ai_mcp_toolkit/server/http_server.py`

```python
@app.post("/resources/search/semantic")
async def semantic_search_resources(
    query: str,
    limit: int = 10,
    min_score: float = 0.5,
    user: User = Depends(require_auth)
):
    """
    Search resources using semantic similarity.
    
    Args:
        query: Natural language search query
        limit: Maximum results to return
        min_score: Minimum similarity score (0-1)
    
    Returns:
        List of resources with similarity scores
    """
    try:
        # Generate query embedding
        query_embedding = await embedding_manager.generate_embedding(query)
        
        # Vector search pipeline
        pipeline = [
            {
                "$vectorSearch": {
                    "index": "resource_vector_index",
                    "path": "embeddings",
                    "queryVector": query_embedding,
                    "numCandidates": 100,
                    "limit": limit,
                    "filter": {
                        "owner_id": str(user.id)  # User isolation
                    }
                }
            },
            {
                "$addFields": {
                    "score": {"$meta": "vectorSearchScore"}
                }
            },
            {
                "$match": {
                    "score": {"$gte": min_score}
                }
            },
            {
                "$project": {
                    "uri": 1,
                    "name": 1,
                    "description": 1,
                    "mime_type": 1,
                    "created_at": 1,
                    "score": 1
                }
            }
        ]
        
        # Execute search
        results = await Resource.aggregate(pipeline).to_list()
        
        self.logger.info(
            f"Semantic search by {user.username}: '{query}' "
            f"returned {len(results)} results"
        )
        
        return {
            "query": query,
            "results": results,
            "count": len(results)
        }
        
    except Exception as e:
        self.logger.error(f"Semantic search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/resources/search/chunks")
async def search_resource_chunks(
    query: str,
    limit: int = 10,
    user: User = Depends(require_auth)
):
    """
    Search within document chunks for precise matches.
    
    For large documents that were chunked, this searches
    within individual chunks for more precise results.
    """
    try:
        query_embedding = await embedding_manager.generate_embedding(query)
        
        pipeline = [
            {
                "$vectorSearch": {
                    "index": "resource_chunks_vector_index",
                    "path": "chunks.embeddings",
                    "queryVector": query_embedding,
                    "numCandidates": 100,
                    "limit": limit,
                    "filter": {
                        "owner_id": str(user.id)
                    }
                }
            },
            {
                "$addFields": {
                    "score": {"$meta": "vectorSearchScore"}
                }
            },
            {
                "$unwind": "$chunks"
            },
            {
                "$project": {
                    "uri": 1,
                    "name": 1,
                    "chunk": "$chunks",
                    "score": 1
                }
            }
        ]
        
        results = await Resource.aggregate(pipeline).to_list()
        
        return {
            "query": query,
            "chunks": results,
            "count": len(results)
        }
        
    except Exception as e:
        self.logger.error(f"Chunk search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

## Phase 5: AI Chat with Resources (1-2 hours)

### Task 5.1: RAG Endpoint

**File**: `src/ai_mcp_toolkit/server/http_server.py`

```python
@app.post("/chat/with-resources")
async def chat_with_resources(
    question: str,
    model: str = "llama3.2",
    max_context_chunks: int = 5,
    user: User = Depends(require_auth)
):
    """
    Ask AI questions about your uploaded resources.
    Uses RAG (Retrieval Augmented Generation).
    
    Args:
        question: Question to ask
        model: Ollama model to use
        max_context_chunks: Number of relevant chunks to include
    
    Returns:
        AI answer with source citations
    """
    try:
        # 1. Find relevant resources via semantic search
        query_embedding = await embedding_manager.generate_embedding(question)
        
        # Search in chunks for more precise context
        pipeline = [
            {
                "$vectorSearch": {
                    "index": "resource_chunks_vector_index",
                    "path": "chunks.embeddings",
                    "queryVector": query_embedding,
                    "numCandidates": 50,
                    "limit": max_context_chunks,
                    "filter": {"owner_id": str(user.id)}
                }
            },
            {"$addFields": {"score": {"$meta": "vectorSearchScore"}}},
            {"$unwind": "$chunks"},
            {
                "$project": {
                    "name": 1,
                    "uri": 1,
                    "chunk_text": "$chunks.text",
                    "score": 1
                }
            }
        ]
        
        relevant_chunks = await Resource.aggregate(pipeline).to_list()
        
        if not relevant_chunks:
            return {
                "answer": "I couldn't find any relevant documents to answer your question.",
                "sources": [],
                "confidence": "none"
            }
        
        # 2. Build context from relevant chunks
        context_parts = []
        sources = []
        
        for i, chunk in enumerate(relevant_chunks):
            context_parts.append(
                f"[Document {i+1}: {chunk['name']}]\n{chunk['chunk_text']}\n"
            )
            sources.append({
                "name": chunk['name'],
                "uri": chunk['uri'],
                "score": chunk['score']
            })
        
        context = "\n".join(context_parts)
        
        # 3. Create RAG prompt
        system_prompt = """You are a helpful AI assistant. Answer the user's question based ONLY on the provided documents. 

If the documents don't contain enough information to answer the question, say so clearly.
Always cite which document(s) you used for your answer."""

        user_prompt = f"""Based on these documents:

{context}

Question: {question}

Answer:"""

        # 4. Get AI response
        response = ollama.chat(
            model=model,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ]
        )
        
        answer = response['message']['content']
        
        # 5. Return answer with sources
        return {
            "answer": answer,
            "sources": sources,
            "question": question,
            "model": model,
            "context_chunks_used": len(relevant_chunks)
        }
        
    except Exception as e:
        self.logger.error(f"RAG chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/resources/{uri:path}/similar")
async def find_similar_resources(
    uri: str,
    limit: int = 5,
    user: User = Depends(require_auth)
):
    """
    Find resources similar to a given resource.
    
    Useful for:
    - "More like this" recommendations
    - Duplicate detection
    - Content clustering
    """
    try:
        # Get the source resource
        resource = await Resource.find_one(
            Resource.uri == uri,
            Resource.owner_id == str(user.id)
        )
        
        if not resource or not resource.embeddings:
            raise HTTPException(
                status_code=404,
                detail="Resource not found or has no embeddings"
            )
        
        # Find similar resources
        pipeline = [
            {
                "$vectorSearch": {
                    "index": "resource_vector_index",
                    "path": "embeddings",
                    "queryVector": resource.embeddings,
                    "numCandidates": 50,
                    "limit": limit + 1,  # +1 because it includes itself
                    "filter": {"owner_id": str(user.id)}
                }
            },
            {"$addFields": {"score": {"$meta": "vectorSearchScore"}}},
            {
                "$match": {
                    "uri": {"$ne": uri}  # Exclude the source document
                }
            },
            {"$limit": limit},
            {
                "$project": {
                    "uri": 1,
                    "name": 1,
                    "description": 1,
                    "created_at": 1,
                    "score": 1
                }
            }
        ]
        
        similar = await Resource.aggregate(pipeline).to_list()
        
        return {
            "source": {
                "uri": resource.uri,
                "name": resource.name
            },
            "similar_resources": similar,
            "count": len(similar)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        self.logger.error(f"Similar resources error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

## Phase 6: Background Processing (1 hour)

### Task 6.1: Embed Existing Resources

**File**: `src/ai_mcp_toolkit/scripts/embed_existing_resources.py` (NEW)

```python
"""Script to generate embeddings for existing resources."""

import asyncio
from ai_mcp_toolkit.models.database import db_manager
from ai_mcp_toolkit.models.documents import Resource
from ai_mcp_toolkit.managers.embedding_manager import embedding_manager


async def embed_existing_resources():
    """Generate embeddings for all resources that don't have them."""
    
    # Connect to database
    await db_manager.connect()
    
    try:
        # Find resources without embeddings
        resources = await Resource.find(
            Resource.embeddings == None
        ).to_list()
        
        print(f"Found {len(resources)} resources without embeddings")
        
        for i, resource in enumerate(resources):
            try:
                print(f"[{i+1}/{len(resources)}] Processing: {resource.name}")
                
                # Get text content
                if not resource.content:
                    print(f"  ⚠️  Skipping (no content)")
                    continue
                
                # Generate embeddings
                embedding_result = await embedding_manager.embed_document(
                    text=resource.content,
                    chunk_if_large=True
                )
                
                # Update resource
                resource.embeddings = embedding_result['embeddings']
                resource.chunks = embedding_result['chunks']
                resource.embeddings_model = embedding_manager.model
                resource.embeddings_chunk_count = embedding_result['chunk_count']
                
                await resource.save()
                
                print(f"  ✅ Generated {embedding_result['chunk_count']} chunks")
                
            except Exception as e:
                print(f"  ❌ Error: {e}")
                continue
        
        print("\n✅ Done!")
        
    finally:
        await db_manager.disconnect()


if __name__ == "__main__":
    asyncio.run(embed_existing_resources())
```

**Run with**:
```bash
python -m src.ai_mcp_toolkit.scripts.embed_existing_resources
```

## Phase 7: Frontend Integration (2-3 hours)

### Task 7.1: Semantic Search UI

**File**: `ui/src/routes/resources/+page.svelte`

Add semantic search input:

```svelte
<script>
  let semanticQuery = '';
  let semanticResults = [];
  
  async function semanticSearch() {
    const response = await fetch('/resources/search/semantic', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({
        query: semanticQuery,
        limit: 10
      })
    });
    
    const data = await response.json();
    semanticResults = data.results;
  }
</script>

<!-- Semantic search box -->
<div class="mb-6">
  <label class="block text-sm font-medium mb-2">
    🔍 Semantic Search
  </label>
  <input
    type="text"
    bind:value={semanticQuery}
    on:keydown={(e) => e.key === 'Enter' && semanticSearch()}
    placeholder="Ask a question or describe what you're looking for..."
    class="w-full px-4 py-2 border rounded-lg"
  />
  <button
    on:click={semanticSearch}
    class="mt-2 px-4 py-2 bg-blue-600 text-white rounded-lg"
  >
    Search by Meaning
  </button>
</div>

<!-- Results with scores -->
{#each semanticResults as result}
  <div class="p-4 border rounded-lg mb-2">
    <div class="flex justify-between">
      <h3 class="font-semibold">{result.name}</h3>
      <span class="text-sm text-gray-500">
        {(result.score * 100).toFixed(1)}% match
      </span>
    </div>
    <p class="text-sm text-gray-600">{result.description}</p>
  </div>
{/each}
```

### Task 7.2: AI Chat with Resources UI

**File**: `ui/src/routes/chat-with-docs/+page.svelte` (NEW)

```svelte
<script>
  let question = '';
  let answer = null;
  let loading = false;
  
  async function askQuestion() {
    loading = true;
    try {
      const response = await fetch('/chat/with-resources', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ question })
      });
      
      answer = await response.json();
    } finally {
      loading = false;
    }
  }
</script>

<div class="max-w-4xl mx-auto p-6">
  <h1 class="text-3xl font-bold mb-6">
    💬 Chat with Your Documents
  </h1>
  
  <div class="mb-6">
    <textarea
      bind:value={question}
      placeholder="Ask a question about your uploaded documents..."
      class="w-full px-4 py-3 border rounded-lg"
      rows="3"
    />
    
    <button
      on:click={askQuestion}
      disabled={loading || !question}
      class="mt-2 px-6 py-3 bg-blue-600 text-white rounded-lg"
    >
      {loading ? 'Thinking...' : 'Ask AI'}
    </button>
  </div>
  
  {#if answer}
    <div class="bg-white rounded-lg shadow p-6">
      <h2 class="font-semibold mb-2">Answer:</h2>
      <p class="text-gray-800 mb-4">{answer.answer}</p>
      
      <h3 class="font-semibold text-sm mb-2">Sources:</h3>
      <ul class="text-sm text-gray-600">
        {#each answer.sources as source}
          <li>
            📄 {source.name} ({(source.score * 100).toFixed(0)}% relevant)
          </li>
        {/each}
      </ul>
    </div>
  {/if}
</div>
```

## Phase 8: Testing & Optimization (1 day)

### Task 8.1: Test Scenarios

```bash
# 1. Upload documents
curl -X POST http://localhost:8000/resources/upload \
  -F "file=@document1.pdf" \
  -F "description=Product manual"

# 2. Semantic search
curl -X POST http://localhost:8000/resources/search/semantic \
  -H "Content-Type: application/json" \
  -d '{"query": "how to install the product?"}'

# 3. Chat with docs
curl -X POST http://localhost:8000/chat/with-resources \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the system requirements?"}'

# 4. Find similar documents
curl http://localhost:8000/resources/file:///user/uuid.pdf/similar
```

### Task 8.2: Performance Optimization

- Add caching for frequently searched queries
- Batch embedding generation
- Optimize chunk size based on document type
- Add background job queue for large uploads

## Dependencies

### Required

```bash
# Ollama (local embeddings)
ollama pull nomic-embed-text

# Or OpenAI (cloud embeddings)
pip install openai
```

### Optional

```bash
# For better chunking
pip install tiktoken  # OpenAI tokenizer

# For semantic chunking
pip install langchain
```

## Configuration

**Environment Variables**:

```bash
# .env
EMBEDDING_PROVIDER=ollama  # or "openai"
EMBEDDING_MODEL=nomic-embed-text  # or "text-embedding-3-small"
EMBEDDING_CHUNK_SIZE=1000
EMBEDDING_ENABLED=true

# For OpenAI
OPENAI_API_KEY=sk-...
```

## Monitoring & Metrics

### Metrics to Track

- Embedding generation time
- Search latency
- RAG response time
- Cache hit rate
- User satisfaction with search results

### Logging

```python
logger.info(f"Embedding generated: {len(text)} chars → {len(embedding)} dims in {duration}s")
logger.info(f"Semantic search: '{query}' → {len(results)} results in {latency}ms")
logger.info(f"RAG answer: {len(answer)} chars using {chunk_count} context chunks")
```

## Cost Estimation

### Ollama (Local) - FREE
- ✅ No API costs
- ✅ Unlimited embeddings
- ⚠️ Requires local GPU/CPU

### OpenAI (Cloud) - PAID
- text-embedding-3-small: $0.00002 / 1K tokens
- Example: 1000 documents × 1000 tokens = $0.02
- ⚠️ API rate limits apply

## Success Criteria

✅ All uploaded resources auto-generate embeddings  
✅ Semantic search returns relevant results  
✅ AI chat provides accurate answers with sources  
✅ Response time < 2s for searches  
✅ User isolation maintained (can't search others' docs)  
✅ System handles 1000+ documents per user  

## Future Enhancements

1. **Hybrid Search**: Combine vector + keyword search
2. **Query Expansion**: Auto-expand user queries
3. **Result Re-ranking**: ML-based result ordering
4. **Conversation Memory**: Multi-turn chat context
5. **Document Summarization**: Auto-generate summaries
6. **Topic Clustering**: Group similar documents
7. **Trend Analysis**: Track content over time

## Rollback Plan

If issues occur:

1. Disable embeddings via config: `EMBEDDING_ENABLED=false`
2. System continues working without semantic search
3. Old keyword search remains functional
4. No data loss (embeddings stored separately)

## Timeline

| Phase | Tasks | Time | Status |
|-------|-------|------|--------|
| 1 | Database Schema | 30 min | ⏸️ Pending |
| 2 | Embedding Service | 1-2 hours | ⏸️ Pending |
| 3 | Upload Integration | 1 hour | ⏸️ Pending |
| 4 | Search API | 1-2 hours | ⏸️ Pending |
| 5 | RAG Chat | 1-2 hours | ⏸️ Pending |
| 6 | Background Jobs | 1 hour | ⏸️ Pending |
| 7 | Frontend | 2-3 hours | ⏸️ Pending |
| 8 | Testing | 1 day | ⏸️ Pending |
| **Total** | | **2-3 days** | |

## Next Steps

When ready to implement:

1. Review this plan
2. Confirm embedding provider (Ollama vs OpenAI)
3. Set up MongoDB Atlas vector search index
4. Start with Phase 1 (Database Schema)
5. Test incrementally after each phase

---

**Status**: 📋 Ready for Implementation  
**Created**: 2025-10-27  
**Estimated Completion**: TBD  

*This is a comprehensive plan. We can implement in phases or all at once when ready!* 🚀
