"""Background reindexing service for resources."""

import logging
import os
from typing import Optional
from bson import ObjectId

from ..models.documents import Resource, ResourceChunk
from .embedding_service import get_embedding_service
from .suggestion_service import SuggestionService

logger = logging.getLogger(__name__)


class ReindexingService:
    """
    Service for background reindexing of resources.
    
    Handles regeneration of:
    - Keywords and entities
    - Embeddings (resource and chunks)
    - Redis suggestions
    - Searchable text normalization
    """
    
    def __init__(self):
        """Initialize reindexing service."""
        self.logger = logging.getLogger(__name__)
        self.embedding_service = get_embedding_service()
        self.suggestion_service = SuggestionService()
        
        # Configuration from environment
        self.enable_keywords = os.getenv("REINDEX_KEYWORDS", "true").lower() == "true"
        self.enable_embeddings = os.getenv("REINDEX_EMBEDDINGS", "true").lower() == "true"
        self.enable_suggestions = os.getenv("REINDEX_SUGGESTIONS", "true").lower() == "true"
        
        self.logger.info(
            f"ReindexingService initialized: "
            f"keywords={self.enable_keywords}, "
            f"embeddings={self.enable_embeddings}, "
            f"suggestions={self.enable_suggestions}"
        )
    
    async def reindex_resource(
        self,
        resource: Resource,
        reindex_keywords: bool = True,
        reindex_embeddings: bool = True,
        reindex_suggestions: bool = True,
        update_chunks: bool = True
    ) -> None:
        """
        Reindex a resource completely.
        
        Args:
            resource: Resource to reindex
            reindex_keywords: Whether to regenerate keywords/entities
            reindex_embeddings: Whether to regenerate embeddings
            reindex_suggestions: Whether to update Redis suggestions
            update_chunks: Whether to update chunk searchable_text with new metadata
        """
        try:
            self.logger.info(f"🔄 Starting reindex for resource: {resource.file_name} (id={resource.id})")
            
            # Update chunks with new resource metadata (most important for search!)
            if update_chunks:
                await self.update_chunk_searchable_text(resource)
            
            # Keywords and entities
            if reindex_keywords and self.enable_keywords:
                await self.reindex_resource_keywords(resource)
            
            # Embeddings
            if reindex_embeddings and self.enable_embeddings:
                await self.reindex_resource_embeddings(resource)
            
            # Redis suggestions
            if reindex_suggestions and self.enable_suggestions:
                await self.reindex_redis_suggestions(resource)
            
            self.logger.info(f"✅ Reindex complete for resource: {resource.file_name}")
            
        except Exception as e:
            self.logger.error(f"❌ Error reindexing resource {resource.id}: {e}", exc_info=True)
    
    async def update_chunk_searchable_text(self, resource: Resource) -> None:
        """
        Update searchable_text in all chunks with current resource metadata.
        
        This ensures search finds resources even after metadata changes.
        
        Args:
            resource: Resource with updated metadata
        """
        try:
            self.logger.info(f"🔍 Updating chunk searchable_text for: {resource.file_name}")
            
            # Import text normalizer
            from ..utils.text_normalizer import create_searchable_text, normalize_text
            
            # Fetch all chunks
            chunks = await ResourceChunk.find(
                ResourceChunk.parent_id == str(resource.id)
            ).to_list()
            
            if not chunks:
                self.logger.warning(f"No chunks found for resource {resource.file_name}")
                return
            
            updated_count = 0
            for chunk in chunks:
                # Regenerate searchable_text with current resource metadata
                searchable_text = create_searchable_text(
                    resource.name,
                    resource.description or resource.summary,
                    ' '.join(resource.tags) if resource.tags else None,
                    ' '.join(resource.keywords) if resource.keywords else None,
                    chunk.text,
                    chunk.ocr_text,
                    separator=' '
                )
                
                # Only update if changed
                if searchable_text != chunk.searchable_text:
                    chunk.searchable_text = searchable_text
                    
                    # Also update normalized fields
                    if chunk.text:
                        chunk.text_normalized = normalize_text(chunk.text)
                    if chunk.ocr_text:
                        chunk.ocr_text_normalized = normalize_text(chunk.ocr_text)
                    
                    await chunk.save()
                    updated_count += 1
            
            self.logger.info(f"✅ Updated searchable_text in {updated_count}/{len(chunks)} chunks")
            
        except Exception as e:
            self.logger.error(f"Error updating chunk searchable_text: {e}", exc_info=True)
    
    async def reindex_resource_keywords(self, resource: Resource) -> None:
        """
        Regenerate keywords and entities for a resource.
        
        Uses Ollama to extract:
        - Keywords: Important terms from content
        - Entities: Names, places, organizations
        
        Args:
            resource: Resource to update
        """
        try:
            self.logger.info(f"📝 Regenerating keywords for: {resource.file_name}")
            
            # Import here to avoid circular dependency
            from .ingestion_service import IngestionService
            
            ingestion = IngestionService()
            
            # Get text to analyze
            text = resource.content or resource.summary or ""
            if not text:
                self.logger.warning(f"No content to extract keywords from: {resource.file_name}")
                return
            
            # Extract keywords
            keywords = await ingestion._extract_keywords(text)
            if keywords:
                resource.keywords = keywords
                self.logger.info(f"  Keywords: {', '.join(keywords[:5])}...")
            
            # Extract entities
            entities = await ingestion._extract_entities(text)
            if entities:
                resource.entities = entities
                self.logger.info(f"  Entities: {', '.join(entities[:5])}...")
            
            # Save changes
            await resource.save()
            self.logger.info(f"✅ Keywords updated for: {resource.file_name}")
            
        except Exception as e:
            self.logger.error(f"Error regenerating keywords: {e}", exc_info=True)
    
    async def reindex_resource_embeddings(self, resource: Resource) -> None:
        """
        Regenerate embeddings for resource and its chunks.
        
        Args:
            resource: Resource to update
        """
        try:
            self.logger.info(f"🧠 Regenerating embeddings for: {resource.file_name}")
            
            # Regenerate resource-level embedding
            if resource.content or resource.summary:
                text = resource.content or resource.summary
                embedding = await self.embedding_service.embed_text(text)
                resource.text_embedding = embedding
                await resource.save()
                self.logger.info(f"  ✅ Resource embedding updated")
            
            # Regenerate chunk embeddings
            chunks = await ResourceChunk.find(
                ResourceChunk.parent_id == resource.id
            ).to_list()
            
            if chunks:
                self.logger.info(f"  Updating {len(chunks)} chunk embeddings...")
                for i, chunk in enumerate(chunks):
                    if chunk.text:
                        embedding = await self.embedding_service.embed_text(chunk.text)
                        chunk.text_embedding = embedding
                        await chunk.save()
                        
                        if (i + 1) % 10 == 0:
                            self.logger.info(f"    Progress: {i + 1}/{len(chunks)} chunks")
                
                self.logger.info(f"  ✅ All {len(chunks)} chunk embeddings updated")
            
            self.logger.info(f"✅ Embeddings updated for: {resource.file_name}")
            
        except Exception as e:
            self.logger.error(f"Error regenerating embeddings: {e}", exc_info=True)
    
    async def reindex_redis_suggestions(self, resource: Resource) -> None:
        """
        Update Redis suggestion indexes for a resource.
        
        Adds:
        - File name
        - Vendor (if exists)
        - Entities (names, places, etc.)
        - Keywords
        
        Args:
            resource: Resource to index
        """
        try:
            self.logger.info(f"📊 Updating Redis suggestions for: {resource.file_name}")
            
            # Remove old suggestions for this resource (if tracking is implemented)
            # For now, we'll just add new suggestions
            # Note: This means old suggestions might remain, but they'll have lower scores over time
            
            # Index the resource
            await self.suggestion_service.index_resource(resource)
            
            self.logger.info(f"✅ Redis suggestions updated for: {resource.file_name}")
            
        except Exception as e:
            self.logger.error(f"Error updating Redis suggestions: {e}", exc_info=True)
    
    async def remove_resource_from_indexes(self, resource_id: str, company_id: str) -> None:
        """
        Remove a deleted resource from all indexes.
        
        Args:
            resource_id: ID of deleted resource
            company_id: Company ID for multi-tenancy
        """
        try:
            self.logger.info(f"🗑️ Removing resource {resource_id} from indexes")
            
            # Remove from Redis suggestions
            if self.enable_suggestions:
                await self.suggestion_service.remove_resource_suggestions(
                    resource_id=resource_id,
                    company_id=company_id
                )
            
            self.logger.info(f"✅ Resource {resource_id} removed from indexes")
            
        except Exception as e:
            self.logger.error(f"Error removing resource from indexes: {e}", exc_info=True)


# Global singleton
_reindexing_service: Optional[ReindexingService] = None


def get_reindexing_service() -> ReindexingService:
    """Get or create the global reindexing service instance."""
    global _reindexing_service
    if _reindexing_service is None:
        _reindexing_service = ReindexingService()
    return _reindexing_service
