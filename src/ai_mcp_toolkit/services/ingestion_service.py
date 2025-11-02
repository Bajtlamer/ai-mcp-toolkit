"""Resource ingestion service for processing and storing resources with embeddings."""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from bson import ObjectId

from ..models.documents import Resource, ResourceChunk, ResourceType
from ..processors import (
    PDFProcessor,
    CSVProcessor,
    ImageProcessor,
    TextProcessor,
    SnippetProcessor,
)
from .embedding_service import get_embedding_service
from .metadata_extractor import MetadataExtractor
from .image_caption_service import ImageCaptionService
from ..agents.image_ocr_agent import ImageOCRAgent
from ..utils.text_normalizer import (
    normalize_text,
    create_searchable_text,
    tokenize_for_search
)
from ..utils.config import Config

logger = logging.getLogger(__name__)


class IngestionService:
    """
    Service for ingesting resources: processing, embedding, and storing.
    
    Orchestrates:
    1. File type detection and routing to appropriate processor
    2. Metadata extraction and chunk creation
    3. Embedding generation for file and chunks
    4. Storage in MongoDB with proper relationships
    """
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize ingestion service with processors and embedding service.
        
        Args:
            config: Optional config object (will use default if not provided)
        """
        self.logger = logging.getLogger(__name__)
        
        # Initialize processors
        self.pdf_processor = PDFProcessor()
        self.csv_processor = CSVProcessor()
        self.image_processor = ImageProcessor()
        self.text_processor = TextProcessor()
        self.snippet_processor = SnippetProcessor()
        
        # Get embedding service
        self.embedding_service = get_embedding_service()
        
        # Initialize compound search utilities
        self.metadata_extractor = MetadataExtractor()
        self.image_caption_service = ImageCaptionService(
            vision_model="llava",
            embedding_model="nomic-embed-text"
        )
        
        # Initialize OCR AI Agent for image processing with text normalization
        if config is None:
            config = Config()
        self.ocr_agent = ImageOCRAgent(config)
        
        self.logger.info("✅ IngestionService initialized with OCR Agent and text normalization")
    
    async def ingest_file(
        self,
        file_bytes: bytes,
        filename: str,
        mime_type: str,
        company_id: str,
        user_id: str,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Resource:
        """
        Ingest a file: process, embed, and store.
        
        Args:
            file_bytes: File content
            filename: Original filename
            mime_type: MIME type
            company_id: Company ID for ACL
            user_id: User ID who uploaded
            tags: Optional tags
            metadata: Optional additional metadata
            
        Returns:
            Created Resource document
        """
        try:
            self.logger.info(f"Ingesting file: {filename} ({mime_type})")
            
            # Select processor based on MIME type
            processor = self._select_processor(mime_type, filename)
            
            # Process file
            initial_metadata = {
                'filename': filename,
                'mime_type': mime_type,
                **(metadata or {})
            }
            
            result = await processor.process(file_bytes, initial_metadata)
            file_metadata = result['file_metadata']
            chunks_data = result['chunks']
            
            # Generate file-level text embedding
            file_text = file_metadata.get('summary', '') or filename
            file_embedding = await self.embedding_service.embed_text(file_text)
            
            # Generate image embedding and process image-specific metadata
            image_embedding = None
            image_caption_data = None
            
            if file_metadata.get('file_type') == 'image' or 'image' in mime_type.lower():
                # Generate image embedding
                image_embedding = await self.embedding_service.embed_image(file_bytes)
                
                # ✨ Process image with OCR Agent (includes normalization)
                try:
                    # Save temp file for OCR agent
                    import tempfile
                    import os
                    with tempfile.NamedTemporaryFile(suffix=f".{filename.split('.')[-1]}", delete=False) as tmp:
                        tmp.write(file_bytes)
                        tmp_path = tmp.name
                    
                    try:
                        # Use OCR Agent which automatically normalizes text
                        image_caption_data = await self.ocr_agent.process_image_for_ingestion(tmp_path)
                        self.logger.info(
                            f"✅ OCR Agent processed {filename}: "
                            f"OCR={len(image_caption_data.get('ocr_text', '') or '')} chars, "
                            f"Description={len(image_caption_data.get('image_description', '') or '')} chars, "
                            f"Searchable={len(image_caption_data.get('searchable_text', '') or '')} chars"
                        )
                    finally:
                        os.unlink(tmp_path)  # Clean up temp file
                except Exception as e:
                    self.logger.warning(f"Could not process image with OCR Agent for {filename}: {e}")
                    image_caption_data = None
            
            # Create Resource document with BOTH old (MCP) and new (search) fields
            file_id = f"files/{datetime.utcnow().strftime('%Y/%m')}/{filename}"
            uri = f"file:///{user_id}/{filename}"  # MCP-compatible URI
            summary_text = file_metadata.get('summary', '') or f"Uploaded file: {filename}"
            
            resource = Resource(
                # OLD/Required MCP fields
                uri=uri,
                name=filename,
                description=summary_text,
                mime_type=mime_type,
                resource_type=ResourceType.FILE,
                owner_id=user_id,
                
                # NEW contextual search fields
                file_id=file_id,
                file_name=filename,
                file_type=file_metadata.get('file_type', 'unknown'),
                company_id=company_id,
                size_bytes=file_metadata.get('size_bytes', len(file_bytes)),
                tags=tags or [],
                vendor=file_metadata.get('vendor'),
                currency=file_metadata.get('currency'),
                amounts_cents=file_metadata.get('amounts_cents', []),
                entities=file_metadata.get('entities', []),
                keywords=file_metadata.get('keywords', []),
                dates=file_metadata.get('dates', []),
                summary=summary_text,
                text_embedding=file_embedding,
                image_embedding=image_embedding,
                image_labels=image_caption_data.get('image_labels', []) if image_caption_data else [],
                ocr_text=image_caption_data.get('ocr_text') if image_caption_data else None,
                metadata=file_metadata,
            )
            
            # Save resource
            await resource.insert()
            
            self.logger.info(f"Created resource: {resource.id}")
            
            # Process and save chunks (pass image caption data if available)
            await self._ingest_chunks(resource, chunks_data, image_caption_data=image_caption_data)
            
            # Index terms for search suggestions in Redis
            await self._index_suggestions(resource)
            
            return resource
            
        except Exception as e:
            self.logger.error(f"Error ingesting file {filename}: {e}", exc_info=True)
            raise
    
    async def ingest_snippet(
        self,
        text_content: str,
        title: str,
        company_id: str,
        user_id: str,
        snippet_source: str = 'user_input',
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Resource:
        """
        Ingest a text snippet (raw text, AI output, etc.).
        
        Args:
            text_content: Raw text content
            title: Title or summary of snippet
            company_id: Company ID for ACL
            user_id: User ID who created
            snippet_source: Source type (user_input, ai_agent, etc.)
            tags: Optional tags
            metadata: Optional additional metadata (agent_id, conversation_id, etc.)
            
        Returns:
            Created Resource document
        """
        try:
            self.logger.info(f"Ingesting snippet: {title} (source: {snippet_source})")
            
            # Process snippet
            initial_metadata = {
                'source': snippet_source,
                'title': title,
                **(metadata or {})
            }
            
            result = await self.snippet_processor.process(text_content, initial_metadata)
            file_metadata = result['file_metadata']
            chunks_data = result['chunks']
            
            # Generate file-level text embedding
            file_text = file_metadata.get('summary', '') or title
            file_embedding = await self.embedding_service.embed_text(file_text)
            
            # Create Resource document with BOTH old (MCP) and new (search) fields
            file_id = f"snippets/{datetime.utcnow().strftime('%Y/%m')}/{ObjectId()}"
            uri = f"text:///{user_id}/{title.replace(' ', '-')}"
            summary_text = file_metadata.get('summary', '') or title
            
            resource = Resource(
                # OLD/Required MCP fields
                uri=uri,
                name=title,
                description=summary_text,
                mime_type='text/plain',
                resource_type=ResourceType.TEXT,
                owner_id=user_id,
                content=text_content[:10000],  # Store first 10k chars
                
                # NEW contextual search fields
                file_id=file_id,
                file_name=title,
                file_type='snippet',
                company_id=company_id,
                size_bytes=file_metadata.get('size_bytes', 0),
                tags=tags or [],
                vendor=file_metadata.get('vendor'),
                currency=file_metadata.get('currency'),
                amounts_cents=file_metadata.get('amounts_cents', []),
                entities=file_metadata.get('entities', []),
                keywords=file_metadata.get('keywords', []),
                dates=file_metadata.get('dates', []),
                summary=summary_text,
                text_embedding=file_embedding,
                metadata=file_metadata,
            )
            
            # Save resource
            await resource.insert()
            
            self.logger.info(f"Created snippet resource: {resource.id}")
            
            # Process and save chunks
            await self._ingest_chunks(resource, chunks_data)
            
            # Index terms for search suggestions in Redis
            await self._index_suggestions(resource)
            
            return resource
            
        except Exception as e:
            self.logger.error(f"Error ingesting snippet {title}: {e}", exc_info=True)
            raise
    
    async def _ingest_chunks(
        self,
        resource: Resource,
        chunks_data: List[Dict[str, Any]],
        image_caption_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Process and save chunks for a resource with compound search metadata extraction.
        
        Args:
            resource: Parent Resource document
            chunks_data: List of chunk dictionaries from processor
            image_caption_data: Optional image caption/OCR data for images
        """
        if not chunks_data:
            self.logger.info(f"No chunks to process for resource {resource.id}")
            return
        
        self.logger.info(f"Processing {len(chunks_data)} chunks for resource {resource.id}")
        
        # Extract texts for batch embedding
        chunk_texts = [chunk.get('text', '') for chunk in chunks_data]
        
        # Generate embeddings in batch
        embeddings = await self.embedding_service.embed_texts(chunk_texts)
        
        # Create and save chunks
        chunks_to_insert = []
        
        for chunk_data, embedding in zip(chunks_data, embeddings):
            # Extract compound search metadata from chunk text
            chunk_text = chunk_data.get('text', '')
            extracted_metadata = self.metadata_extractor.extract(
                chunk_text,
                file_type=resource.file_type
            )
            
            # Image-specific fields (from processor or image caption service)
            caption = chunk_data.get('caption') or (image_caption_data.get('caption') if image_caption_data else None)
            image_labels = chunk_data.get('image_labels', []) or (image_caption_data.get('image_labels', []) if image_caption_data else [])
            ocr_text = chunk_data.get('ocr_text') or (image_caption_data.get('ocr_text') if image_caption_data else None)
            caption_embedding = chunk_data.get('caption_embedding') or (image_caption_data.get('caption_embedding') if image_caption_data else None)
            
            # ✨ NEW: Normalize all text for diacritic-insensitive search
            text_normalized = normalize_text(chunk_text) if chunk_text else None
            ocr_text_normalized = normalize_text(ocr_text) if ocr_text else None
            image_description = caption  # Use caption as image description
            
            # Create combined searchable text from all sources
            searchable_text = create_searchable_text(
                chunk_text,
                ocr_text,
                caption,
                ' '.join(image_labels)
            )
            
            # Extract additional keywords from searchable text
            normalized_keywords = tokenize_for_search(searchable_text) if searchable_text else []
            all_keywords = list(set(
                (chunk_data.get('keywords', []) or extracted_metadata.get('keywords', [])) +
                normalized_keywords
            ))
            
            self.logger.debug(
                f"Chunk {chunk_data.get('chunk_index', 0)}: "
                f"text={len(chunk_text)} chars, "
                f"normalized={len(text_normalized or '')} chars, "
                f"searchable={len(searchable_text or '')} chars, "
                f"keywords={len(all_keywords)}"
            )
            
            # Merge processor metadata with extracted metadata
            # Processor metadata takes precedence if present
            chunk = ResourceChunk(
                parent_id=str(resource.id),
                resource_uri=resource.uri,
                company_id=resource.company_id,
                owner_id=resource.owner_id,
                file_name=resource.file_name,
                file_type=resource.file_type,
                mime_type=resource.mime_type,
                chunk_type=chunk_data.get('chunk_type', 'text'),
                chunk_index=chunk_data.get('chunk_index', 0),
                
                # Content and embeddings
                text=chunk_text,
                content=chunk_text,  # Backward compatibility alias
                text_embedding=embedding,
                embedding=embedding,  # Backward compatibility alias
                
                # ✨ NEW: Normalized text fields
                text_normalized=text_normalized,
                ocr_text_normalized=ocr_text_normalized,
                searchable_text=searchable_text,
                image_description=image_description,
                
                # Deep-linking fields
                page_number=chunk_data.get('page_number'),
                row_index=chunk_data.get('row_number') or chunk_data.get('row_index'),
                col_index=chunk_data.get('col_index'),
                bbox=chunk_data.get('bbox'),
                
                # Compound search metadata (extracted + normalized)
                keywords=all_keywords,
                vendor=chunk_data.get('vendor') or extracted_metadata.get('vendor'),
                currency=chunk_data.get('currency') or extracted_metadata.get('currency'),
                amounts_cents=chunk_data.get('amounts_cents', []) or extracted_metadata.get('amounts_cents', []),
                entities=chunk_data.get('entities', []) or extracted_metadata.get('entities', []),
                dates=chunk_data.get('dates', []),
                
                # Image-specific fields (from processor or image caption service)
                caption=caption,
                image_labels=image_labels,
                ocr_text=ocr_text,
                caption_embedding=caption_embedding,
            )
            
            chunks_to_insert.append(chunk)
        
        # Batch insert chunks
        if chunks_to_insert:
            await ResourceChunk.insert_many(chunks_to_insert)
            self.logger.info(f"Inserted {len(chunks_to_insert)} chunks for resource {resource.id} with metadata extraction")
    
    def _select_processor(self, mime_type: str, filename: str):
        """
        Select appropriate processor based on MIME type and filename.
        
        Args:
            mime_type: MIME type of file
            filename: Filename (for extension detection)
            
        Returns:
            Processor instance
        """
        # Check MIME type first
        if 'pdf' in mime_type.lower():
            return self.pdf_processor
        elif 'image' in mime_type.lower():
            return self.image_processor
        elif 'csv' in mime_type.lower() or mime_type == 'text/csv':
            return self.csv_processor
        elif 'text' in mime_type.lower():
            return self.text_processor
        
        # Check filename extension as fallback
        filename_lower = filename.lower()
        if filename_lower.endswith('.pdf'):
            return self.pdf_processor
        elif filename_lower.endswith(('.csv', '.tsv')):
            return self.csv_processor
        elif filename_lower.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')):
            return self.image_processor
        elif filename_lower.endswith(('.txt', '.md', '.json', '.ini', '.yaml', '.yml', '.xml')):
            return self.text_processor
        
        # Default to text processor
        return self.text_processor
    
    async def _index_suggestions(self, resource: Resource) -> None:
        """Index resource terms in Redis for search suggestions.
        
        Args:
            resource: Resource to index
        """
        try:
            from .suggestion_service import SuggestionService
            
            suggestion_service = SuggestionService()
            
            # Collect content from all chunks for term extraction
            chunks = await ResourceChunk.find(
                ResourceChunk.parent_id == str(resource.id)
            ).to_list()
            
            # Combine all chunk text
            combined_content = ' '.join(
                chunk.text for chunk in chunks if chunk.text
            )
            
            # Index terms in Redis
            await suggestion_service.add_document_terms(
                file_name=resource.file_name,
                entities=resource.entities,
                keywords=resource.keywords,
                vendor=resource.vendor,
                content=combined_content,
                company_id=resource.company_id
            )
            
            self.logger.debug(f"Indexed suggestions for resource: {resource.file_name}")
            
        except Exception as e:
            # Non-critical: log but don't fail ingestion
            self.logger.warning(f"Could not index suggestions for {resource.file_name}: {e}")


# Global singleton instance
_ingestion_service: Optional[IngestionService] = None


def get_ingestion_service() -> IngestionService:
    """
    Get or create the global ingestion service instance.
    
    Returns:
        IngestionService instance
    """
    global _ingestion_service
    
    if _ingestion_service is None:
        _ingestion_service = IngestionService()
    
    return _ingestion_service
