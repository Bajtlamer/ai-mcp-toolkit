"""Resource Manager for MCP resource operations."""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..models.documents import Resource, ResourceType, ResourceMetadata
from ..models.mcp_types import (
    Resource as MCPResource,
    ListResourcesResult,
    ReadResourceResult,
    MCPError,
    MCPErrorCode
)

logger = logging.getLogger(__name__)


class ResourceManager:
    """Manager for MCP resource operations with MongoDB Atlas storage."""
    
    def __init__(self):
        """Initialize the resource manager."""
        self.logger = logging.getLogger(__name__)
    
    async def list_resources(
        self,
        resource_type: Optional[ResourceType] = None,
        limit: int = 100,
        offset: int = 0
    ) -> ListResourcesResult:
        """
        List available resources.
        
        Args:
            resource_type: Optional filter by resource type
            limit: Maximum number of resources to return
            offset: Offset for pagination
            
        Returns:
            ListResourcesResult with available resources
        """
        try:
            # Build query
            query = {}
            if resource_type:
                query["resource_type"] = resource_type
            
            # Fetch resources from database
            resources_cursor = Resource.find(query).skip(offset).limit(limit)
            db_resources = await resources_cursor.to_list()
            
            # Convert to MCP Resource format
            mcp_resources = [
                MCPResource(
                    uri=resource.uri,
                    name=resource.name,
                    description=resource.description,
                    mimeType=resource.mime_type
                )
                for resource in db_resources
            ]
            
            self.logger.info(f"Listed {len(mcp_resources)} resources")
            return ListResourcesResult(resources=mcp_resources)
            
        except Exception as e:
            self.logger.error(f"Error listing resources: {e}", exc_info=True)
            raise
    
    async def read_resource(self, uri: str) -> ReadResourceResult:
        """
        Read a specific resource by URI.
        
        Args:
            uri: Resource URI to read
            
        Returns:
            ReadResourceResult with resource contents
            
        Raises:
            ValueError: If resource not found
        """
        try:
            # Find resource by URI
            resource = await Resource.find_one(Resource.uri == uri)
            
            if not resource:
                raise ValueError(f"Resource not found: {uri}")
            
            # Return resource contents
            contents = [
                {
                    "uri": resource.uri,
                    "mimeType": resource.mime_type,
                    "text": resource.content or ""
                }
            ]
            
            self.logger.info(f"Read resource: {uri}")
            return ReadResourceResult(contents=contents)
            
        except ValueError:
            raise
        except Exception as e:
            self.logger.error(f"Error reading resource {uri}: {e}", exc_info=True)
            raise
    
    async def create_resource(
        self,
        uri: str,
        name: str,
        description: str,
        mime_type: str,
        resource_type: ResourceType,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Resource:
        """
        Create a new resource.
        
        Args:
            uri: Unique resource URI
            name: Resource name
            description: Resource description
            mime_type: MIME type
            resource_type: Type of resource
            content: Optional resource content
            metadata: Optional metadata dictionary
            
        Returns:
            Created Resource document
            
        Raises:
            ValueError: If resource with URI already exists
        """
        try:
            # Check if resource already exists
            existing = await Resource.find_one(Resource.uri == uri)
            if existing:
                raise ValueError(f"Resource already exists: {uri}")
            
            # Create resource metadata
            resource_metadata = ResourceMetadata(
                created_at=datetime.utcnow(),
                modified_at=datetime.utcnow(),
                **(metadata or {})
            )
            
            # Create new resource
            resource = Resource(
                uri=uri,
                name=name,
                description=description,
                mime_type=mime_type,
                resource_type=resource_type,
                content=content,
                metadata=resource_metadata
            )
            
            # Save to database
            await resource.save()
            
            self.logger.info(f"Created resource: {uri}")
            return resource
            
        except ValueError:
            raise
        except Exception as e:
            self.logger.error(f"Error creating resource {uri}: {e}", exc_info=True)
            raise
    
    async def update_resource(
        self,
        uri: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Resource:
        """
        Update an existing resource.
        
        Args:
            uri: Resource URI to update
            name: Optional new name
            description: Optional new description
            content: Optional new content
            metadata: Optional metadata updates
            
        Returns:
            Updated Resource document
            
        Raises:
            ValueError: If resource not found
        """
        try:
            # Find resource
            resource = await Resource.find_one(Resource.uri == uri)
            if not resource:
                raise ValueError(f"Resource not found: {uri}")
            
            # Update fields
            if name is not None:
                resource.name = name
            if description is not None:
                resource.description = description
            if content is not None:
                resource.content = content
            if metadata is not None:
                resource.metadata.properties.update(metadata)
            
            resource.updated_at = datetime.utcnow()
            resource.metadata.modified_at = datetime.utcnow()
            
            # Save changes
            await resource.save()
            
            self.logger.info(f"Updated resource: {uri}")
            return resource
            
        except ValueError:
            raise
        except Exception as e:
            self.logger.error(f"Error updating resource {uri}: {e}", exc_info=True)
            raise
    
    async def delete_resource(self, uri: str) -> bool:
        """
        Delete a resource.
        
        Args:
            uri: Resource URI to delete
            
        Returns:
            True if deleted successfully
            
        Raises:
            ValueError: If resource not found
        """
        try:
            # Find resource
            resource = await Resource.find_one(Resource.uri == uri)
            if not resource:
                raise ValueError(f"Resource not found: {uri}")
            
            # Delete resource
            await resource.delete()
            
            self.logger.info(f"Deleted resource: {uri}")
            return True
            
        except ValueError:
            raise
        except Exception as e:
            self.logger.error(f"Error deleting resource {uri}: {e}", exc_info=True)
            raise
    
    async def get_resource_count(
        self,
        resource_type: Optional[ResourceType] = None
    ) -> int:
        """
        Get count of resources.
        
        Args:
            resource_type: Optional filter by resource type
            
        Returns:
            Number of resources
        """
        try:
            query = {}
            if resource_type:
                query["resource_type"] = resource_type
            
            count = await Resource.find(query).count()
            return count
            
        except Exception as e:
            self.logger.error(f"Error counting resources: {e}", exc_info=True)
            raise
    
    async def search_resources(
        self,
        query: str,
        limit: int = 100
    ) -> List[Resource]:
        """
        Search resources by name or description.
        
        Args:
            query: Search query string
            limit: Maximum number of results
            
        Returns:
            List of matching resources
        """
        try:
            # Search in name and description
            # Note: This is a simple implementation. For production,
            # consider using MongoDB text search or Atlas Search
            from pymongo import TEXT
            
            resources = await Resource.find(
                {
                    "$or": [
                        {"name": {"$regex": query, "$options": "i"}},
                        {"description": {"$regex": query, "$options": "i"}}
                    ]
                }
            ).limit(limit).to_list()
            
            self.logger.info(f"Search '{query}' found {len(resources)} resources")
            return resources
            
        except Exception as e:
            self.logger.error(f"Error searching resources: {e}", exc_info=True)
            raise
