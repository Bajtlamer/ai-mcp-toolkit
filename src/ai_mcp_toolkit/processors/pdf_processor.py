"""PDF processor for extracting text and metadata from PDF files."""

import io
import logging
from typing import Dict, Any, List
from datetime import datetime
from pypdf import PdfReader

from .base_processor import BaseProcessor

logger = logging.getLogger(__name__)


class PDFProcessor(BaseProcessor):
    """Process PDF files and extract structured metadata."""
    
    async def process(self, file_bytes: bytes, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process PDF file and extract metadata and page-level chunks.
        
        Args:
            file_bytes: PDF file content
            metadata: Initial metadata (filename, mime_type, etc.)
            
        Returns:
            Dict with file_metadata and chunks
        """
        try:
            # Parse PDF
            pdf_file = io.BytesIO(file_bytes)
            reader = PdfReader(pdf_file)
            
            # Extract all text
            all_text = ""
            page_texts = []
            
            for page_num, page in enumerate(reader.pages):
                try:
                    page_text = page.extract_text()
                    page_texts.append(page_text)
                    all_text += f"\n{page_text}"
                except Exception as e:
                    self.logger.warning(f"Could not extract text from page {page_num + 1}: {e}")
                    page_texts.append("")
            
            # Extract PDF metadata
            pdf_metadata = {}
            if reader.metadata:
                pdf_metadata = {
                    'pdf_title': reader.metadata.get('/Title', ''),
                    'pdf_author': reader.metadata.get('/Author', ''),
                    'pdf_subject': reader.metadata.get('/Subject', ''),
                    'pdf_creator': reader.metadata.get('/Creator', ''),
                }
            
            # Extract structured data from all text
            amounts_cents = self.extract_amounts(all_text)
            currency = self.extract_currency(all_text)
            dates = self.extract_dates(all_text)
            entities = self.extract_entities(all_text)
            keywords = self.extract_keywords(all_text)
            
            # Try to identify vendor from entities
            vendor = None
            if entities:
                vendor = self.normalize_vendor(entities[0])
            
            # Build file-level metadata
            file_metadata = {
                'file_type': 'pdf',
                'size_bytes': len(file_bytes),
                'vendor': vendor,
                'currency': currency,
                'amounts_cents': amounts_cents,
                'entities': entities,
                'keywords': keywords,
                'dates': dates,
                'summary': self._generate_summary(all_text, pdf_metadata),
                **pdf_metadata,
                'pdf_pages': len(reader.pages),
            }
            
            # Create page-level chunks
            chunks = []
            for page_num, page_text in enumerate(page_texts):
                if not page_text.strip():
                    continue
                
                # Extract structured data from this page
                page_amounts = self.extract_amounts(page_text)
                page_entities = self.extract_entities(page_text)
                page_keywords = self.extract_keywords(page_text)
                page_dates = self.extract_dates(page_text)
                
                chunk = {
                    'chunk_type': 'page',
                    'chunk_index': page_num,
                    'page_number': page_num + 1,  # 1-indexed for users
                    'text': page_text,
                    'currency': currency if page_amounts else None,
                    'amounts_cents': page_amounts,
                    'entities': page_entities,
                    'keywords': page_keywords,
                    'dates': page_dates,
                }
                
                chunks.append(chunk)
            
            self.logger.info(
                f"Processed PDF: {len(reader.pages)} pages, "
                f"{len(amounts_cents)} amounts, {len(keywords)} keywords"
            )
            
            return {
                'file_metadata': file_metadata,
                'chunks': chunks
            }
            
        except Exception as e:
            self.logger.error(f"Error processing PDF: {e}", exc_info=True)
            # Return minimal metadata on error
            return {
                'file_metadata': {
                    'file_type': 'pdf',
                    'size_bytes': len(file_bytes),
                },
                'chunks': []
            }
    
    def _generate_summary(self, text: str, pdf_metadata: Dict[str, Any]) -> str:
        """
        Generate a brief summary of the PDF.
        
        Args:
            text: Full text content
            pdf_metadata: PDF metadata
            
        Returns:
            Summary string
        """
        # Use PDF title if available
        if pdf_metadata.get('pdf_title'):
            summary = pdf_metadata['pdf_title']
        else:
            # Use first 200 characters
            summary = text.strip()[:200]
            if len(text) > 200:
                summary += "..."
        
        return summary
