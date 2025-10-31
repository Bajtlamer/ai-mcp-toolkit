"""Embedding service for generating vector embeddings from text and images."""

import logging
from typing import List, Optional
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Service for generating embeddings using sentence-transformers.
    
    Supports:
    - Text embeddings for semantic search
    - Image embeddings for visual search (if model supports it)
    """
    
    def __init__(
        self,
        text_model_name: str = "all-MiniLM-L6-v2",
        image_model_name: Optional[str] = "clip-ViT-B-32"
    ):
        """
        Initialize embedding models.
        
        Args:
            text_model_name: Name of sentence-transformers model for text
            image_model_name: Name of model for image embeddings (optional)
        """
        self.logger = logging.getLogger(__name__)
        
        # Load text model
        try:
            self.text_model = SentenceTransformer(text_model_name)
            self.text_dimension = self.text_model.get_sentence_embedding_dimension()
            self.logger.info(f"Loaded text embedding model: {text_model_name} (dim={self.text_dimension})")
        except Exception as e:
            self.logger.error(f"Failed to load text model {text_model_name}: {e}")
            self.text_model = None
            self.text_dimension = 384  # fallback dimension
        
        # Load image model (optional, for future multimodal search)
        self.image_model = None
        self.image_dimension = None
        
        if image_model_name:
            try:
                self.image_model = SentenceTransformer(image_model_name)
                self.image_dimension = self.image_model.get_sentence_embedding_dimension()
                self.logger.info(f"Loaded image embedding model: {image_model_name} (dim={self.image_dimension})")
            except Exception as e:
                self.logger.warning(f"Could not load image model {image_model_name}: {e}")
    
    async def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text string.
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        if not self.text_model:
            self.logger.error("Text model not loaded")
            return self._zero_embedding(self.text_dimension)
        
        try:
            # Clean text
            text = text.strip()
            if not text:
                return self._zero_embedding(self.text_dimension)
            
            # Generate embedding
            embedding = self.text_model.encode(text, convert_to_numpy=True)
            
            # Convert to list
            return embedding.tolist()
            
        except Exception as e:
            self.logger.error(f"Error generating text embedding: {e}")
            return self._zero_embedding(self.text_dimension)
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (batch processing).
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        if not self.text_model:
            self.logger.error("Text model not loaded")
            return [self._zero_embedding(self.text_dimension) for _ in texts]
        
        try:
            # Clean texts
            cleaned_texts = [t.strip() if t else "" for t in texts]
            
            # Generate embeddings in batch
            embeddings = self.text_model.encode(
                cleaned_texts,
                convert_to_numpy=True,
                show_progress_bar=len(texts) > 10
            )
            
            # Convert to list of lists
            return [emb.tolist() for emb in embeddings]
            
        except Exception as e:
            self.logger.error(f"Error generating text embeddings: {e}")
            return [self._zero_embedding(self.text_dimension) for _ in texts]
    
    async def embed_image(self, image_bytes: bytes) -> List[float]:
        """
        Generate embedding for an image.
        
        Args:
            image_bytes: Image file bytes
            
        Returns:
            List of floats representing the embedding vector
        """
        if not self.image_model:
            self.logger.warning("Image model not loaded, returning zero embedding")
            return self._zero_embedding(self.image_dimension or 512)
        
        try:
            from PIL import Image
            import io
            
            # Load image
            image = Image.open(io.BytesIO(image_bytes))
            
            # Generate embedding
            embedding = self.image_model.encode(image, convert_to_numpy=True)
            
            # Convert to list
            return embedding.tolist()
            
        except Exception as e:
            self.logger.error(f"Error generating image embedding: {e}")
            return self._zero_embedding(self.image_dimension or 512)
    
    def _zero_embedding(self, dimension: int) -> List[float]:
        """Generate a zero vector of specified dimension."""
        return [0.0] * dimension
    
    def get_text_dimension(self) -> int:
        """Get the dimension of text embeddings."""
        return self.text_dimension
    
    def get_image_dimension(self) -> Optional[int]:
        """Get the dimension of image embeddings."""
        return self.image_dimension


# Global singleton instance
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """
    Get or create the global embedding service instance.
    
    Returns:
        EmbeddingService instance
    """
    global _embedding_service
    
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    
    return _embedding_service
