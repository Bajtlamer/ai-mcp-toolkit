"""Snippet processor for raw text input, pasted content, and AI agent outputs."""

import logging
from typing import Dict, Any, List
from datetime import datetime

from .base_processor import BaseProcessor

logger = logging.getLogger(__name__)


class SnippetProcessor(BaseProcessor):
    """
    Process raw text snippets that don't come from files.
    
    Use cases:
    - Copy-pasted text from users
    - AI agent conversation outputs
    - Quick notes and annotations
    - API responses stored as text
    - Any ephemeral text content
    """
    
    async def process(self, text_content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process raw text snippet and extract metadata.
        
        Args:
            text_content: Raw text string (not file bytes)
            metadata: Initial metadata (title, source, agent_id, etc.)
            
        Returns:
            Dict with file_metadata and chunks
        """
        try:
            if not text_content or not text_content.strip():
                return {
                    'file_metadata': {
                        'file_type': 'snippet',
                        'size_bytes': 0,
                    },
                    'chunks': []
                }
            
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
            
            # Detect snippet source type
            snippet_source = metadata.get('source', 'user_input')  # user_input, ai_agent, paste, api
            
            # Build file-level metadata
            file_metadata = {
                'file_type': 'snippet',
                'snippet_source': snippet_source,
                'size_bytes': len(text_content.encode('utf-8')),
                'vendor': vendor,
                'currency': currency,
                'amounts_cents': amounts_cents,
                'entities': entities,
                'keywords': keywords,
                'dates': dates,
                'summary': self._generate_summary(text_content),
                'char_count': len(text_content),
                'line_count': text_content.count('\n') + 1,
                'word_count': len(text_content.split()),
                'created_at': metadata.get('created_at', datetime.utcnow().isoformat()),
            }
            
            # Add agent-specific metadata if this is from an AI agent
            if snippet_source == 'ai_agent':
                file_metadata['agent_id'] = metadata.get('agent_id')
                file_metadata['agent_name'] = metadata.get('agent_name')
                file_metadata['conversation_id'] = metadata.get('conversation_id')
                file_metadata['turn_number'] = metadata.get('turn_number')
            
            # Create chunks based on size
            chunks = self._create_chunks(text_content, currency, snippet_source)
            
            self.logger.info(
                f"Processed snippet ({snippet_source}): {len(text_content)} chars, "
                f"{len(chunks)} chunks, {len(keywords)} keywords"
            )
            
            return {
                'file_metadata': file_metadata,
                'chunks': chunks
            }
            
        except Exception as e:
            self.logger.error(f"Error processing snippet: {e}", exc_info=True)
            return {
                'file_metadata': {
                    'file_type': 'snippet',
                    'snippet_source': metadata.get('source', 'unknown'),
                    'size_bytes': len(text_content.encode('utf-8')) if text_content else 0,
                },
                'chunks': []
            }
    
    def _generate_summary(self, text: str, max_length: int = 200) -> str:
        """
        Generate a brief summary of the snippet.
        
        Args:
            text: Full text content
            max_length: Maximum summary length
            
        Returns:
            Summary string
        """
        # Clean and truncate
        summary = text.strip()[:max_length]
        if len(text) > max_length:
            summary += "..."
        
        # Replace newlines with spaces for summary
        summary = ' '.join(summary.split())
        
        return summary
    
    def _create_chunks(self, text: str, currency: str, source: str) -> List[Dict[str, Any]]:
        """
        Split text into semantic chunks.
        
        Strategy:
        - For short text (<500 chars): single chunk
        - For medium text (500-2000 chars): split by paragraphs
        - For long text (>2000 chars): split into overlapping windows
        
        Args:
            text: Full text content
            currency: Detected currency
            source: Source type of snippet
            
        Returns:
            List of chunk dictionaries
        """
        chunks = []
        text_length = len(text)
        
        # Short text: single chunk
        if text_length <= 500:
            chunk = self._create_chunk(text, 0, currency, source)
            chunks.append(chunk)
        
        # Medium text: split by paragraphs
        elif text_length <= 2000:
            paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
            
            # If no clear paragraphs, split by sentences
            if len(paragraphs) <= 1:
                paragraphs = self._split_by_sentences(text)
            
            for idx, para in enumerate(paragraphs):
                if not para:
                    continue
                chunk = self._create_chunk(para, idx, currency, source)
                chunks.append(chunk)
        
        # Long text: overlapping sliding windows
        else:
            chunk_size = 500
            overlap = 100
            
            start = 0
            idx = 0
            
            while start < text_length:
                end = min(start + chunk_size, text_length)
                chunk_text = text[start:end]
                
                chunk = self._create_chunk(chunk_text, idx, currency, source)
                chunks.append(chunk)
                
                start += (chunk_size - overlap)
                idx += 1
        
        return chunks[:500]  # Limit to 500 chunks max
    
    def _create_chunk(self, text: str, index: int, currency: str, source: str) -> Dict[str, Any]:
        """
        Create a single chunk with extracted metadata.
        
        Args:
            text: Chunk text
            index: Chunk index
            currency: Detected currency
            source: Source type
            
        Returns:
            Chunk dictionary
        """
        # Extract structured data from chunk
        chunk_amounts = self.extract_amounts(text)
        chunk_entities = self.extract_entities(text)
        chunk_keywords = self.extract_keywords(text)
        chunk_dates = self.extract_dates(text)
        
        return {
            'chunk_type': 'snippet_chunk',
            'chunk_index': index,
            'text': text,
            'snippet_source': source,
            'currency': currency if chunk_amounts else None,
            'amounts_cents': chunk_amounts,
            'entities': chunk_entities,
            'keywords': chunk_keywords,
            'dates': chunk_dates,
        }
    
    def _split_by_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences (rough heuristic).
        
        Args:
            text: Text to split
            
        Returns:
            List of sentences
        """
        # Simple sentence splitting
        sentences = []
        current = []
        
        for char in text:
            current.append(char)
            if char in '.!?' and len(''.join(current)) > 20:
                sentences.append(''.join(current).strip())
                current = []
        
        # Add remaining text
        if current:
            sentences.append(''.join(current).strip())
        
        return [s for s in sentences if s]
