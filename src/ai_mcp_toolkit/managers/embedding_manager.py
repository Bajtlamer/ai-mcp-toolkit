"""Embedding generation and management for semantic search.

This module provides functionality to generate vector embeddings for text documents
using either Ollama (local) or OpenAI (cloud) embedding models.
"""

import logging
from typing import List, Optional, Dict, Any
import ollama
from datetime import datetime

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
            # Note: OpenAI client initialization deferred until needed
            self._openai_client = None
        else:
            raise ValueError(f"Unknown provider: {provider}")
        
        logger.info(f"EmbeddingManager initialized: provider={provider}, model={self.model}, dims={self.dimensions}")
    
    @property
    def openai_client(self):
        """Lazy initialization of OpenAI client."""
        if self._openai_client is None and self.provider == "openai":
            from openai import OpenAI
            self._openai_client = OpenAI()
        return self._openai_client
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed (max 8000 chars for safety)
            
        Returns:
            List of floats (embedding vector)
            
        Raises:
            Exception: If embedding generation fails
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding")
            return []
        
        try:
            if self.provider == "ollama":
                return await self._generate_ollama(text)
            elif self.provider == "openai":
                return await self._generate_openai(text)
        except Exception as e:
            logger.error(f"Error generating embedding: {e}", exc_info=True)
            raise
    
    async def _generate_ollama(self, text: str) -> List[float]:
        """
        Generate embedding using Ollama.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector as list of floats
        """
        # Truncate to avoid token limits (roughly 8000 chars ~ 2000 tokens)
        truncated_text = text[:8000]
        
        try:
            response = ollama.embeddings(
                model=self.model,
                prompt=truncated_text
            )
            embedding = response.get('embedding', [])
            
            if not embedding:
                raise ValueError("Ollama returned empty embedding")
            
            logger.debug(f"Generated Ollama embedding: {len(embedding)} dimensions")
            return embedding
            
        except Exception as e:
            logger.error(f"Ollama embedding error: {e}", exc_info=True)
            raise
    
    async def _generate_openai(self, text: str) -> List[float]:
        """
        Generate embedding using OpenAI.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector as list of floats
        """
        truncated_text = text[:8000]
        
        try:
            response = self.openai_client.embeddings.create(
                model=self.model,
                input=truncated_text
            )
            embedding = response.data[0].embedding
            
            logger.debug(f"Generated OpenAI embedding: {len(embedding)} dimensions")
            return embedding
            
        except Exception as e:
            logger.error(f"OpenAI embedding error: {e}", exc_info=True)
            raise
    
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
        if not texts:
            return []
        
        logger.info(f"Generating batch embeddings for {len(texts)} texts")
        
        if self.provider == "openai":
            # OpenAI supports efficient batch processing
            try:
                response = self.openai_client.embeddings.create(
                    model=self.model,
                    input=[t[:8000] for t in texts]
                )
                embeddings = [item.embedding for item in response.data]
                logger.info(f"Generated {len(embeddings)} OpenAI embeddings in batch")
                return embeddings
            except Exception as e:
                logger.error(f"OpenAI batch embedding error: {e}", exc_info=True)
                raise
        else:
            # Ollama: process one by one
            embeddings = []
            for i, text in enumerate(texts):
                try:
                    emb = await self.generate_embedding(text)
                    embeddings.append(emb)
                    
                    if (i + 1) % 10 == 0:
                        logger.debug(f"Progress: {i + 1}/{len(texts)} embeddings generated")
                        
                except Exception as e:
                    logger.error(f"Failed to generate embedding for text {i}: {e}")
                    # Append empty embedding to maintain index alignment
                    embeddings.append([])
            
            logger.info(f"Generated {len(embeddings)} Ollama embeddings sequentially")
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
            overlap: Overlap between chunks (preserves context)
            
        Returns:
            List of chunk dictionaries with metadata
        """
        if not text:
            return []
        
        chunks = []
        start = 0
        index = 0
        text_length = len(text)
        
        while start < text_length:
            end = min(start + chunk_size, text_length)
            chunk_text = text[start:end]
            
            # Skip very small chunks at the end
            if len(chunk_text.strip()) < 50:
                break
            
            chunks.append({
                "index": index,
                "text": chunk_text,
                "char_start": start,
                "char_end": end,
                "embeddings": None  # Will be filled later
            })
            
            start += (chunk_size - overlap)
            index += 1
        
        logger.info(f"Split text into {len(chunks)} chunks (size={chunk_size}, overlap={overlap})")
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
            Dict with embeddings and chunks:
            {
                "embeddings": [0.1, 0.2, ...],  # Main embedding
                "chunks": [{...}, ...],          # Chunk objects with embeddings
                "chunk_count": 5
            }
        """
        if not text or not text.strip():
            logger.warning("Empty document provided for embedding")
            return {
                "embeddings": [],
                "chunks": None,
                "chunk_count": 0
            }
        
        text = text.strip()
        
        # For short documents, single embedding
        if len(text) <= chunk_size or not chunk_if_large:
            logger.info(f"Generating single embedding for document ({len(text)} chars)")
            embedding = await self.generate_embedding(text)
            return {
                "embeddings": embedding,
                "chunks": None,
                "chunk_count": 0
            }
        
        # For long documents, chunk and embed each chunk
        logger.info(f"Chunking large document ({len(text)} chars)")
        chunks = self.chunk_text(text, chunk_size=chunk_size)
        
        if not chunks:
            # Fallback: single embedding
            embedding = await self.generate_embedding(text)
            return {
                "embeddings": embedding,
                "chunks": None,
                "chunk_count": 0
            }
        
        # Generate embeddings for all chunks
        chunk_texts = [c["text"] for c in chunks]
        chunk_embeddings = await self.generate_batch_embeddings(chunk_texts)
        
        # Attach embeddings to chunks
        for chunk, embedding in zip(chunks, chunk_embeddings):
            chunk["embeddings"] = embedding
        
        # Use first chunk's embedding as the main document embedding
        # (Alternative: could use average of all chunks)
        summary_embedding = chunk_embeddings[0] if chunk_embeddings else []
        
        logger.info(f"Document embedded: {len(chunks)} chunks created")
        return {
            "embeddings": summary_embedding,
            "chunks": chunks,
            "chunk_count": len(chunks)
        }


# Singleton instance
_embedding_manager_instance = None


def get_embedding_manager(provider: str = "ollama", model: str = None) -> EmbeddingManager:
    """
    Get or create the singleton embedding manager instance.
    
    Args:
        provider: "ollama" or "openai"
        model: Model name (optional)
        
    Returns:
        EmbeddingManager instance
    """
    global _embedding_manager_instance
    
    if _embedding_manager_instance is None:
        _embedding_manager_instance = EmbeddingManager(provider=provider, model=model)
    
    return _embedding_manager_instance
