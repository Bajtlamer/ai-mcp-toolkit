"""Image processor for extracting visual content and metadata from images."""

import io
import logging
from typing import Dict, Any, List
from PIL import Image
from PIL.ExifTags import TAGS

from .base_processor import BaseProcessor

logger = logging.getLogger(__name__)


class ImageProcessor(BaseProcessor):
    """Process image files and extract visual metadata."""
    
    async def process(self, file_bytes: bytes, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process image file and extract metadata.
        
        Args:
            file_bytes: Image file content
            metadata: Initial metadata (filename, mime_type, etc.)
            
        Returns:
            Dict with file_metadata and chunks (usually single chunk for images)
        """
        try:
            # Open image
            image = Image.open(io.BytesIO(file_bytes))
            
            # Extract basic image info
            width, height = image.size
            image_format = image.format
            image_mode = image.mode
            
            # Extract EXIF data if available
            exif_data = self._extract_exif(image)
            
            # Extract location from EXIF if available
            location_tags = []
            if exif_data:
                # Check for GPS info
                gps_info = exif_data.get('GPSInfo', {})
                if gps_info:
                    location_tags.append('geotagged')
                
                # Check for location keywords
                keywords = exif_data.get('Keywords', '')
                if keywords:
                    location_tags.extend([k.lower() for k in keywords.split(',') if k.strip()])
            
            # Build file-level metadata
            # Store technical info separately from user description
            technical_info = f"{image_format} image ({width}x{height})"
            
            file_metadata = {
                'file_type': 'image',
                'size_bytes': len(file_bytes),
                'image_format': image_format,
                'image_mode': image_mode,
                'width': width,
                'height': height,
                'aspect_ratio': round(width / height, 2) if height > 0 else 0,
                'image_labels': location_tags,  # Can be enriched with vision AI later
                'exif': exif_data,
                'technical_metadata': technical_info,
                # Only set summary if user hasn't provided a description
                'summary': metadata.get('description') or technical_info,
            }
            
            # For images, create single chunk representing whole image
            # Note: actual image embeddings would be generated separately
            chunks = [{
                'chunk_type': 'image',
                'chunk_index': 0,
                'text': f"{metadata.get('filename', 'image')} - {image_format} {width}x{height}",
                'width': width,
                'height': height,
                'image_labels': location_tags,
            }]
            
            self.logger.info(
                f"Processed image: {image_format} {width}x{height}, "
                f"{len(file_bytes)} bytes"
            )
            
            return {
                'file_metadata': file_metadata,
                'chunks': chunks
            }
            
        except Exception as e:
            self.logger.error(f"Error processing image: {e}", exc_info=True)
            return {
                'file_metadata': {
                    'file_type': 'image',
                    'size_bytes': len(file_bytes),
                },
                'chunks': []
            }
    
    def _extract_exif(self, image: Image.Image) -> Dict[str, Any]:
        """
        Extract EXIF metadata from image.
        
        Args:
            image: PIL Image object
            
        Returns:
            Dictionary of EXIF data
        """
        exif_data = {}
        
        try:
            exif_raw = image.getexif()
            if not exif_raw:
                return {}
            
            for tag_id, value in exif_raw.items():
                tag_name = TAGS.get(tag_id, tag_id)
                
                # Convert bytes to string if needed
                if isinstance(value, bytes):
                    try:
                        value = value.decode('utf-8', errors='replace')
                    except Exception:
                        value = str(value)
                
                exif_data[tag_name] = value
            
            return exif_data
            
        except Exception as e:
            self.logger.warning(f"Could not extract EXIF data: {e}")
            return {}
