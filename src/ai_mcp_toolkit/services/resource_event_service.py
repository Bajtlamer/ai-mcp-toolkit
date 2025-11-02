"""Resource event service for handling creation, updates, and deletions."""

import logging
import asyncio
from enum import Enum
from typing import Optional, List

from ..models.documents import Resource
from .reindexing_service import get_reindexing_service

logger = logging.getLogger(__name__)


class ResourceEventType(str, Enum):
    """Types of resource events."""
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"


class ResourceEventService:
    """
    Service for handling resource change events and triggering reindexing.
    
    Coordinates background tasks when resources are:
    - Created (new upload)
    - Updated (metadata/content changed)
    - Deleted (removed from system)
    """
    
    def __init__(self):
        """Initialize resource event service."""
        self.logger = logging.getLogger(__name__)
        self.reindexing_service = get_reindexing_service()
        self.logger.info("✅ ResourceEventService initialized")
    
    async def on_resource_created(
        self,
        resource: Resource,
        skip_embeddings: bool = False
    ) -> None:
        """
        Handle resource creation event.
        
        Triggers full reindexing in background:
        - Keywords and entities extraction
        - Embedding generation
        - Redis suggestion indexing
        
        Args:
            resource: Newly created resource
            skip_embeddings: Skip embedding generation (if already done during upload)
        """
        try:
            self.logger.info(f"📥 Resource created event: {resource.file_name} (id={resource.id})")
            
            # Full reindex for new resources
            # Note: Embeddings might already be generated during upload, so can skip if needed
            await self.reindexing_service.reindex_resource(
                resource,
                reindex_keywords=True,
                reindex_embeddings=not skip_embeddings,
                reindex_suggestions=True
            )
            
        except Exception as e:
            self.logger.error(f"Error in resource created handler: {e}", exc_info=True)
    
    async def on_resource_updated(
        self,
        resource: Resource,
        changed_fields: Optional[List[str]] = None
    ) -> None:
        """
        Handle resource update event.
        
        Selectively reindexes based on what changed:
        - If content/summary changed: regenerate keywords, entities, embeddings
        - If metadata changed (file_name, vendor): update Redis suggestions
        - If only minor fields changed: skip expensive operations
        
        Args:
            resource: Updated resource
            changed_fields: List of fields that changed (optional, for selective reindexing)
        """
        try:
            self.logger.info(f"📝 Resource updated event: {resource.file_name} (id={resource.id})")
            
            if changed_fields:
                self.logger.info(f"  Changed fields: {', '.join(changed_fields)}")
            
            # Determine what needs reindexing
            needs_keyword_reindex = False
            needs_embedding_reindex = False
            needs_suggestion_reindex = False
            
            if changed_fields:
                # Selective reindexing based on changed fields
                content_fields = {'content', 'summary', 'text'}
                metadata_fields = {'file_name', 'vendor', 'keywords', 'entities'}
                
                if any(field in content_fields for field in changed_fields):
                    needs_keyword_reindex = True
                    needs_embedding_reindex = True
                    needs_suggestion_reindex = True
                elif any(field in metadata_fields for field in changed_fields):
                    needs_suggestion_reindex = True
            else:
                # No field info, reindex everything to be safe
                needs_keyword_reindex = True
                needs_embedding_reindex = True
                needs_suggestion_reindex = True
            
            # Perform selective reindexing
            await self.reindexing_service.reindex_resource(
                resource,
                reindex_keywords=needs_keyword_reindex,
                reindex_embeddings=needs_embedding_reindex,
                reindex_suggestions=needs_suggestion_reindex
            )
            
        except Exception as e:
            self.logger.error(f"Error in resource updated handler: {e}", exc_info=True)
    
    async def on_resource_deleted(
        self,
        resource_id: str,
        company_id: str
    ) -> None:
        """
        Handle resource deletion event.
        
        Removes resource from all indexes:
        - Redis suggestions
        - (MongoDB documents already deleted)
        
        Args:
            resource_id: ID of deleted resource
            company_id: Company ID for multi-tenancy
        """
        try:
            self.logger.info(f"🗑️ Resource deleted event: {resource_id}")
            
            # Remove from indexes
            await self.reindexing_service.remove_resource_from_indexes(
                resource_id=resource_id,
                company_id=company_id
            )
            
        except Exception as e:
            self.logger.error(f"Error in resource deleted handler: {e}", exc_info=True)
    
    def trigger_background_reindex(
        self,
        resource: Resource,
        event_type: ResourceEventType,
        changed_fields: Optional[List[str]] = None
    ) -> asyncio.Task:
        """
        Trigger reindexing in background task.
        
        This creates an asyncio task that runs without blocking.
        The task will complete in the background.
        
        Args:
            resource: Resource to reindex
            event_type: Type of event (created/updated/deleted)
            changed_fields: Fields that changed (for updates)
            
        Returns:
            asyncio.Task that can be awaited if needed
        """
        if event_type == ResourceEventType.CREATED:
            task = asyncio.create_task(self.on_resource_created(resource))
        elif event_type == ResourceEventType.UPDATED:
            task = asyncio.create_task(self.on_resource_updated(resource, changed_fields))
        elif event_type == ResourceEventType.DELETED:
            task = asyncio.create_task(
                self.on_resource_deleted(str(resource.id), resource.company_id)
            )
        else:
            raise ValueError(f"Unknown event type: {event_type}")
        
        self.logger.debug(f"🚀 Background reindex task created for {event_type.value}")
        return task


# Global singleton
_resource_event_service: Optional[ResourceEventService] = None


def get_resource_event_service() -> ResourceEventService:
    """Get or create the global resource event service instance."""
    global _resource_event_service
    if _resource_event_service is None:
        _resource_event_service = ResourceEventService()
    return _resource_event_service
