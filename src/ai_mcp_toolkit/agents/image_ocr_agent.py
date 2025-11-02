"""Image OCR AI Agent.

Extracts text from images using Tesseract OCR and generates descriptions using LLaVA.
Normalizes all extracted text by removing diacritics for consistent search matching.

Features:
- OCR text extraction (Tesseract)
- AI image description (LLaVA/Moondream)
- Text normalization (diacritic removal)
- Metadata generation (labels, keywords)
"""

import logging
from typing import Any, Dict, List, Optional
from pathlib import Path
import asyncio

from mcp.types import Tool
from .base_agent import BaseAgent
from ..services.image_caption_service import ImageCaptionService
from ..utils.text_normalizer import (
    normalize_text,
    create_searchable_text,
    tokenize_for_search
)
from ..utils.config import Config

logger = logging.getLogger(__name__)


class ImageOCRAgent(BaseAgent):
    """AI Agent for OCR extraction and image description with text normalization."""
    
    def __init__(self, config: Config):
        """Initialize the Image OCR Agent.
        
        Args:
            config: Configuration object
        """
        super().__init__(config)
        
        # Initialize image caption service
        vision_model = getattr(config, 'vision_model', 'llava')
        embedding_model = getattr(config, 'embedding_model', 'nomic-embed-text')
        
        self.caption_service = ImageCaptionService(
            vision_model=vision_model,
            embedding_model=embedding_model
        )
        
        logger.info(f"ImageOCRAgent initialized with vision={vision_model}, embedding={embedding_model}")
    
    def get_tools(self) -> List[Tool]:
        """Return list of tools provided by this agent."""
        return [
            Tool(
                name="extract_image_text",
                description=(
                    "Extract text from an image using OCR (Tesseract) and generate "
                    "an AI description (LLaVA). Returns normalized text, OCR text, "
                    "description, and metadata for search."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "image_path": {
                            "type": "string",
                            "description": "Path to the image file"
                        },
                        "extract_ocr": {
                            "type": "boolean",
                            "description": "Extract OCR text (default: true)",
                            "default": True
                        },
                        "generate_description": {
                            "type": "boolean",
                            "description": "Generate AI description (default: true)",
                            "default": True
                        },
                        "normalize_text": {
                            "type": "boolean",
                            "description": "Normalize text by removing diacritics (default: true)",
                            "default": True
                        }
                    },
                    "required": ["image_path"]
                }
            )
        ]
    
    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute a tool with given arguments.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments
            
        Returns:
            JSON string with results
        """
        if tool_name == "extract_image_text":
            return await self._extract_image_text(
                image_path=arguments["image_path"],
                extract_ocr=arguments.get("extract_ocr", True),
                generate_description=arguments.get("generate_description", True),
                normalize=arguments.get("normalize_text", True)
            )
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
    
    async def _extract_image_text(
        self,
        image_path: str,
        extract_ocr: bool = True,
        generate_description: bool = True,
        normalize: bool = True
    ) -> str:
        """Extract text and generate description from image.
        
        Args:
            image_path: Path to image file
            extract_ocr: Extract OCR text
            generate_description: Generate AI description
            normalize: Normalize text (remove diacritics)
            
        Returns:
            JSON string with extraction results
        """
        try:
            # Validate image path
            if not Path(image_path).exists():
                raise FileNotFoundError(f"Image file not found: {image_path}")
            
            logger.info(f"Processing image: {image_path}")
            
            # Process image using caption service
            result = await self.caption_service.process_image(
                image_path=image_path,
                extract_ocr=extract_ocr,
                generate_caption=generate_description
            )
            
            # Extract results
            ocr_text = result.get('ocr_text', '')
            description = result.get('caption', '')
            labels = result.get('image_labels', [])
            caption_embedding = result.get('caption_embedding')
            
            # Normalize text if requested
            ocr_text_normalized = None
            description_normalized = None
            searchable_text = None
            
            if normalize:
                if ocr_text:
                    ocr_text_normalized = normalize_text(ocr_text)
                    logger.info(f"Normalized OCR text: '{ocr_text[:50]}...' -> '{ocr_text_normalized[:50]}...'")
                
                if description:
                    description_normalized = normalize_text(description)
                    logger.info(f"Normalized description: '{description[:50]}...' -> '{description_normalized[:50]}...'")
                
                # Create combined searchable text
                searchable_text = create_searchable_text(
                    ocr_text,
                    description,
                    ' '.join(labels)
                )
                logger.info(f"Created searchable text: '{searchable_text[:100]}...'")
            
            # Generate keywords from normalized text
            keywords = []
            if searchable_text:
                keywords = tokenize_for_search(searchable_text)
                logger.info(f"Extracted {len(keywords)} keywords: {keywords[:10]}...")
            
            # Build response
            response = {
                "success": True,
                "image_path": image_path,
                "ocr_text": ocr_text,
                "ocr_text_normalized": ocr_text_normalized,
                "description": description,
                "description_normalized": description_normalized,
                "labels": labels,
                "keywords": keywords,
                "searchable_text": searchable_text,
                "has_embedding": caption_embedding is not None,
                "embedding_dimensions": len(caption_embedding) if caption_embedding else 0
            }
            
            logger.info(
                f"✅ Image processed successfully: "
                f"OCR={len(ocr_text) if ocr_text else 0} chars, "
                f"Description={len(description) if description else 0} chars, "
                f"Labels={len(labels)}, "
                f"Keywords={len(keywords)}"
            )
            
            return self.format_result(response, format_type="json")
            
        except Exception as e:
            logger.error(f"Error extracting image text: {e}", exc_info=True)
            error_response = {
                "success": False,
                "error": str(e),
                "image_path": image_path
            }
            return self.format_result(error_response, format_type="json")
    
    async def process_image_for_ingestion(
        self,
        image_path: str
    ) -> Dict[str, Any]:
        """Process image for ingestion pipeline.
        
        Convenience method for ingestion service.
        Returns normalized metadata ready for database storage.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Dictionary with normalized fields for ResourceChunk
        """
        logger.info(f"🖼️ Processing image for ingestion: {image_path}")
        
        # Process image
        result = await self.caption_service.process_image(
            image_path=image_path,
            extract_ocr=True,
            generate_caption=True
        )
        
        # Extract and normalize
        ocr_text = result.get('ocr_text', '')
        description = result.get('caption', '')
        labels = result.get('image_labels', [])
        caption_embedding = result.get('caption_embedding')
        
        # Normalize all text
        ocr_text_normalized = normalize_text(ocr_text) if ocr_text else None
        description_normalized = normalize_text(description) if description else None
        
        # Create combined searchable text
        searchable_text = create_searchable_text(
            ocr_text,
            description,
            ' '.join(labels)
        )
        
        # Generate keywords
        keywords = tokenize_for_search(searchable_text) if searchable_text else []
        
        logger.info(
            f"✅ Image ingestion metadata ready: "
            f"OCR={len(ocr_text or '')} chars, "
            f"Description={len(description or '')} chars, "
            f"Searchable={len(searchable_text or '')} chars"
        )
        
        return {
            "ocr_text": ocr_text,
            "ocr_text_normalized": ocr_text_normalized,
            "image_description": description,
            "caption": description,  # Alias for compatibility
            "text_normalized": description_normalized,
            "image_labels": labels,
            "keywords": keywords,
            "searchable_text": searchable_text,
            "caption_embedding": caption_embedding
        }


# Export
__all__ = ['ImageOCRAgent']
