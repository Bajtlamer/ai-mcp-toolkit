"""Image caption and OCR service for visual search.

Ollama-only implementation using:
- LLaVA/Moondream for image captioning
- Tesseract for OCR text extraction
- nomic-embed-text for caption embeddings (same as text embeddings)

Enables searching images via caption + OCR text without external APIs.
"""

import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import base64

try:
    import pytesseract
    from PIL import Image
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    logging.warning("pytesseract or Pillow not installed. OCR will be disabled.")

import ollama

logger = logging.getLogger(__name__)


class ImageCaptionService:
    """Generate captions and extract OCR text from images using local models."""
    
    def __init__(
        self,
        vision_model: str = "llava",
        embedding_model: str = "nomic-embed-text"
    ):
        """Initialize image caption service.
        
        Args:
            vision_model: Ollama vision model (llava, moondream, bakllava)
            embedding_model: Text embedding model for caption embeddings
        """
        self.vision_model = vision_model or "llava"
        self.embedding_model = embedding_model or "nomic-embed-text"
        
        # Validate models are not None
        if not self.vision_model:
            logger.error("Vision model is None or empty! Using default 'llava'")
            self.vision_model = "llava"
        if not self.embedding_model:
            logger.error("Embedding model is None or empty! Using default 'nomic-embed-text'")
            self.embedding_model = "nomic-embed-text"
        
        logger.info(f"ImageCaptionService initialized: vision={self.vision_model}, embedding={self.embedding_model}")
        logger.info(f"Tesseract available: {TESSERACT_AVAILABLE}")
    
    async def process_image(
        self,
        image_path: str,
        extract_ocr: bool = True,
        generate_caption: bool = True
    ) -> Dict:
        """Process image: generate caption, extract OCR, create embedding.
        
        Args:
            image_path: Path to image file
            extract_ocr: Whether to extract OCR text
            generate_caption: Whether to generate AI caption
            
        Returns:
            Dict with:
            {
                'caption': str,                  # AI-generated caption
                'image_labels': List[str],       # Tags extracted from caption
                'ocr_text': str,                 # OCR extracted text
                'caption_embedding': List[float] # Text embedding of caption+OCR
            }
        """
        result = {
            'caption': None,
            'image_labels': [],
            'ocr_text': None,
            'caption_embedding': None
        }
        
        # Generate caption with LLaVA
        if generate_caption:
            caption, labels = await self._generate_caption(image_path)
            result['caption'] = caption
            result['image_labels'] = labels
        
        # Extract OCR text
        if extract_ocr and TESSERACT_AVAILABLE:
            logger.info(f"Starting OCR extraction for: {image_path}")
            ocr_text = await self._extract_ocr(image_path)
            result['ocr_text'] = ocr_text
            if ocr_text:
                logger.info(f"OCR extracted {len(ocr_text)} characters")
            else:
                logger.warning(f"OCR returned no text for {image_path}")
        elif extract_ocr and not TESSERACT_AVAILABLE:
            logger.error("OCR requested but Tesseract is NOT available!")
        
        # Generate caption embedding (combines caption + OCR text)
        combined_text = ' '.join(filter(None, [result['caption'], result['ocr_text']]))
        if combined_text.strip():
            result['caption_embedding'] = await self._generate_embedding(combined_text)
        
        logger.info(f"Processed image: caption={bool(result['caption'])}, ocr={bool(result['ocr_text'])}, embedding={bool(result['caption_embedding'])}")
        return result
    
    async def _generate_caption(self, image_path: str) -> Tuple[Optional[str], List[str]]:
        """Generate image caption using LLaVA/Moondream.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Tuple of (caption_text, [labels])
        """
        try:
            # Read and encode image
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            # Generate caption using Ollama vision model
            response = ollama.chat(
                model=self.vision_model,
                messages=[{
                    'role': 'user',
                    'content': 'Describe this image concisely in one sentence, then list 3-5 key visual tags (objects, places, concepts). Format: CAPTION: [sentence]. TAGS: [tag1, tag2, ...]',
                    'images': [image_data]
                }]
            )
            
            caption_full = response['message']['content']
            
            # Parse caption and tags
            caption, labels = self._parse_caption_response(caption_full)
            
            logger.debug(f"Generated caption: {caption[:100]}... with {len(labels)} labels")
            return caption, labels
            
        except Exception as e:
            # Check if it's a missing model error
            error_str = str(e)
            if 'not found' in error_str or '404' in error_str:
                logger.warning(f"Vision model '{self.vision_model}' not installed. Install with: ollama pull {self.vision_model}")
            else:
                logger.error(f"Error generating caption: {e}", exc_info=True)
            return None, []
    
    def _parse_caption_response(self, response: str) -> Tuple[str, List[str]]:
        """Parse LLaVA response to extract caption and tags.
        
        Expected format: "CAPTION: description. TAGS: tag1, tag2, tag3"
        """
        caption = ""
        labels = []
        
        # Try to parse structured response
        if "CAPTION:" in response and "TAGS:" in response:
            parts = response.split("TAGS:")
            caption = parts[0].replace("CAPTION:", "").strip()
            tags_str = parts[1].strip()
            labels = [t.strip().lower() for t in tags_str.split(",") if t.strip()]
        else:
            # Fallback: use entire response as caption, extract nouns heuristically
            caption = response.strip()
            # Simple tag extraction: capitalized words
            words = response.split()
            labels = [w.lower().strip('.,;:!?') for w in words if w and w[0].isupper() and len(w) > 2]
            labels = list(set(labels))[:5]  # dedupe and limit
        
        return caption, labels
    
    async def _extract_ocr(self, image_path: str) -> Optional[str]:
        """Extract text from image using Tesseract OCR.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Extracted text or None
        """
        if not TESSERACT_AVAILABLE:
            logger.warning("Tesseract not available, skipping OCR")
            return None
        
        try:
            # Open image
            image = Image.open(image_path)
            
            # Extract text
            ocr_text = pytesseract.image_to_string(image)
            
            # Clean up text
            ocr_text = ocr_text.strip()
            
            if ocr_text:
                logger.info(f"✅ OCR SUCCESS: Extracted {len(ocr_text)} chars")
                logger.info(f"OCR preview: {ocr_text[:100]}...")
                return ocr_text
            else:
                logger.warning("OCR returned empty string")
                return None
                
        except Exception as e:
            logger.error(f"Error extracting OCR: {e}", exc_info=True)
            return None
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate text embedding for caption+OCR text.
        
        Uses same embedding model as text chunks (nomic-embed-text).
        
        Args:
            text: Combined caption + OCR text
            
        Returns:
            Embedding vector (768 dims)
        """
        try:
            # Ensure text is a string and not None
            if not text or not isinstance(text, str):
                logger.warning(f"Invalid text type for embedding: {type(text)}")
                return []
            
            # Validate embedding model is set
            if not self.embedding_model:
                logger.error(f"Embedding model is None! Cannot generate embeddings.")
                return []
            
            # Truncate to avoid token limits
            truncated_text = str(text)[:8000]
            
            response = ollama.embeddings(
                model=self.embedding_model,
                prompt=truncated_text
            )
            
            embedding = response.get('embedding', [])
            
            if not embedding:
                raise ValueError(f"Ollama returned empty embedding for caption")
            
            logger.debug(f"Generated caption embedding: {len(embedding)} dimensions")
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating caption embedding: {e}", exc_info=True)
            return []
    
    def check_tesseract_available(self) -> bool:
        """Check if Tesseract is installed and accessible."""
        if not TESSERACT_AVAILABLE:
            return False
        
        try:
            version = pytesseract.get_tesseract_version()
            logger.info(f"Tesseract version: {version}")
            return True
        except Exception as e:
            logger.warning(f"Tesseract not accessible: {e}")
            return False
    
    def check_vision_model_available(self) -> bool:
        """Check if vision model is available in Ollama."""
        try:
            response = ollama.list()
            
            # Handle ListResponse object with 'models' attribute
            if hasattr(response, 'models'):
                models_list = response.models
            elif isinstance(response, dict):
                models_list = response.get('models', [])
            else:
                models_list = response
            
            # Extract model names from Model objects
            model_names = []
            for m in models_list:
                if hasattr(m, 'model'):
                    model_names.append(m.model)
                elif hasattr(m, 'name'):
                    model_names.append(m.name)
                elif isinstance(m, dict):
                    model_names.append(m.get('model') or m.get('name', ''))
            
            # Check if vision model is available (handle model:tag format)
            available = any(
                self.vision_model in name or name.startswith(f"{self.vision_model}:")
                for name in model_names if name
            )
            
            if available:
                logger.info(f"Vision model '{self.vision_model}' is available")
            else:
                logger.warning(f"Vision model '{self.vision_model}' not found. Available: {model_names}")
            
            return available
        except Exception as e:
            logger.error(f"Error checking vision model: {e}", exc_info=True)
            return False


# Convenience function for quick image processing
async def process_image_file(
    image_path: str,
    vision_model: str = "llava",
    embedding_model: str = "nomic-embed-text"
) -> Dict:
    """Process a single image file (convenience function).
    
    Args:
        image_path: Path to image file
        vision_model: Ollama vision model
        embedding_model: Text embedding model
        
    Returns:
        Processed image metadata dict
    """
    service = ImageCaptionService(vision_model, embedding_model)
    return await service.process_image(image_path)
