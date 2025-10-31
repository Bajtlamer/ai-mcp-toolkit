"""Text processor for plain text files (.txt, .md, .ini, .json, etc.)"""

import json
import logging
import configparser
from typing import Dict, Any, List

from .base_processor import BaseProcessor

logger = logging.getLogger(__name__)


class TextProcessor(BaseProcessor):
    """Process text files and extract structured metadata."""
    
    async def process(self, file_bytes: bytes, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process text file and extract metadata and paragraph-level chunks.
        
        Args:
            file_bytes: Text file content
            metadata: Initial metadata (filename, mime_type, etc.)
            
        Returns:
            Dict with file_metadata and chunks
        """
        try:
            # Decode text
            text_content = file_bytes.decode('utf-8', errors='replace')
            
            # Determine file type from extension or mime
            file_type = self._detect_file_type(metadata, text_content)
            
            # Extract structured data
            amounts_cents = self.extract_amounts(text_content)
            currency = self.extract_currency(text_content)
            dates = self.extract_dates(text_content)
            entities = self.extract_entities(text_content)
            keywords = self.extract_keywords(text_content)
            
            # Try to identify vendor
            vendor = None
            if entities:
                vendor = self.normalize_vendor(entities[0])
            
            # Special handling for structured formats
            structured_data = {}
            if file_type == 'json':
                structured_data = self._extract_json_schema(text_content)
            elif file_type == 'ini':
                structured_data = self._extract_ini_sections(text_content)
            
            # Build file-level metadata
            file_metadata = {
                'file_type': file_type,
                'size_bytes': len(file_bytes),
                'vendor': vendor,
                'currency': currency,
                'amounts_cents': amounts_cents,
                'entities': entities,
                'keywords': keywords,
                'dates': dates,
                'summary': self._generate_summary(text_content),
                'char_count': len(text_content),
                'line_count': text_content.count('\n') + 1,
                **structured_data,
            }
            
            # Create paragraph/section-level chunks
            chunks = self._create_chunks(text_content, currency)
            
            self.logger.info(
                f"Processed {file_type}: {len(text_content)} chars, "
                f"{len(chunks)} chunks, {len(keywords)} keywords"
            )
            
            return {
                'file_metadata': file_metadata,
                'chunks': chunks
            }
            
        except Exception as e:
            self.logger.error(f"Error processing text file: {e}", exc_info=True)
            return {
                'file_metadata': {
                    'file_type': 'text',
                    'size_bytes': len(file_bytes),
                },
                'chunks': []
            }
    
    def _detect_file_type(self, metadata: Dict[str, Any], content: str) -> str:
        """Detect specific text file type."""
        filename = metadata.get('filename', '').lower()
        
        if filename.endswith('.json'):
            return 'json'
        elif filename.endswith('.ini') or filename.endswith('.cfg'):
            return 'ini'
        elif filename.endswith('.md'):
            return 'markdown'
        elif filename.endswith('.yaml') or filename.endswith('.yml'):
            return 'yaml'
        elif filename.endswith('.xml'):
            return 'xml'
        else:
            return 'text'
    
    def _extract_json_schema(self, content: str) -> Dict[str, Any]:
        """Extract schema information from JSON file."""
        try:
            data = json.loads(content)
            
            # Extract top-level keys as schema
            if isinstance(data, dict):
                schema = {
                    'json_keys': list(data.keys()),
                    'json_structure': 'object',
                }
            elif isinstance(data, list):
                schema = {
                    'json_structure': 'array',
                    'json_array_length': len(data),
                }
                # Get keys from first object if array of objects
                if data and isinstance(data[0], dict):
                    schema['json_keys'] = list(data[0].keys())
            else:
                schema = {'json_structure': 'primitive'}
            
            return schema
        except json.JSONDecodeError:
            return {}
    
    def _extract_ini_sections(self, content: str) -> Dict[str, Any]:
        """Extract section information from INI file."""
        try:
            config = configparser.ConfigParser()
            config.read_string(content)
            
            sections = list(config.sections())
            return {
                'ini_sections': sections,
                'ini_section_count': len(sections),
            }
        except Exception:
            return {}
    
    def _generate_summary(self, text: str) -> str:
        """Generate a brief summary of the text."""
        # Use first 200 characters
        summary = text.strip()[:200]
        if len(text) > 200:
            summary += "..."
        return summary
    
    def _create_chunks(self, text: str, currency: str) -> List[Dict[str, Any]]:
        """
        Split text into chunks by paragraphs or fixed size.
        
        Args:
            text: Full text content
            currency: Detected currency
            
        Returns:
            List of chunk dictionaries
        """
        chunks = []
        
        # Split by double newlines (paragraphs)
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        # If no clear paragraphs, split by single newlines
        if len(paragraphs) <= 1:
            paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
        
        # If still too few, split by fixed size
        if len(paragraphs) <= 1:
            chunk_size = 500
            paragraphs = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
        
        for idx, para in enumerate(paragraphs[:500]):  # Limit to 500 chunks
            if not para:
                continue
            
            # Extract structured data from paragraph
            para_amounts = self.extract_amounts(para)
            para_entities = self.extract_entities(para)
            para_keywords = self.extract_keywords(para)
            para_dates = self.extract_dates(para)
            
            chunk = {
                'chunk_type': 'paragraph',
                'chunk_index': idx,
                'text': para,
                'currency': currency if para_amounts else None,
                'amounts_cents': para_amounts,
                'entities': para_entities,
                'keywords': para_keywords,
                'dates': para_dates,
            }
            
            chunks.append(chunk)
        
        return chunks
