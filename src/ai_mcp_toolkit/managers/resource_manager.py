"""Resource Manager for MCP resource operations."""

import logging
import aiohttp
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
        user_id: Optional[str] = None,
        is_admin: bool = False,
        resource_type: Optional[ResourceType] = None,
        limit: int = 100,
        offset: int = 0
    ) -> ListResourcesResult:
        """
        List available resources.
        
        Args:
            user_id: User ID for ownership filtering (required for non-admins)
            is_admin: Whether the user is an admin (admins see all resources)
            resource_type: Optional filter by resource type
            limit: Maximum number of resources to return
            offset: Offset for pagination
            
        Returns:
            ListResourcesResult with available resources
        """
        try:
            # Build query
            query = {}
            
            # Ownership filtering: regular users see only their resources, admins see all
            if not is_admin and user_id:
                query["owner_id"] = user_id
            
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
    
    async def read_resource(
        self,
        uri: str,
        user_id: Optional[str] = None,
        is_admin: bool = False
    ) -> ReadResourceResult:
        """
        Read a specific resource by URI.
        
        Args:
            uri: Resource URI to read
            user_id: User ID for ownership check (required for non-admins)
            is_admin: Whether the user is an admin (admins can read all resources)
            
        Returns:
            ReadResourceResult with resource contents
            
        Raises:
            ValueError: If resource not found or access denied
        """
        try:
            # Find resource by URI
            resource = await Resource.find_one(Resource.uri == uri)
            
            if not resource:
                raise ValueError(f"Resource not found: {uri}")
            
            # Ownership check: regular users can only read their own resources
            if not is_admin and user_id and resource.owner_id != user_id:
                raise ValueError(f"Access denied: Resource not found: {uri}")
            
            # Fetch/extract content based on resource type
            content = resource.content or ""
            
            # Debug logging
            self.logger.info(f"=== DEBUG READ RESOURCE ===")
            self.logger.info(f"URI: {uri}")
            self.logger.info(f"Resource mime_type: {resource.mime_type}")
            self.logger.info(f"Resource content preview: {content[:100] if content else 'None'}")
            self.logger.info(f"Resource has metadata: {resource.metadata is not None}")
            if resource.metadata:
                self.logger.info(f"Metadata type: {type(resource.metadata)}")
                self.logger.info(f"Metadata dict: {resource.metadata.dict() if hasattr(resource.metadata, 'dict') else 'N/A'}")
                if hasattr(resource.metadata, 'properties'):
                    self.logger.info(f"Metadata properties keys: {list(resource.metadata.properties.keys())}")
                    self.logger.info(f"Has pdf_bytes: {'pdf_bytes' in resource.metadata.properties}")
                else:
                    self.logger.info(f"Metadata has no properties attribute")
            self.logger.info(f"=== END DEBUG ===")
            
            # Extract text from PDF files
            if resource.mime_type == 'application/pdf' and resource.metadata and 'pdf_bytes' in resource.metadata.properties:
                try:
                    import base64
                    from pypdf import PdfReader
                    import io
                    
                    self.logger.info(f"Extracting text from PDF resource: {resource.uri}")
                    pdf_bytes_b64 = resource.metadata.properties.get('pdf_bytes')
                    if pdf_bytes_b64:
                        pdf_bytes = base64.b64decode(pdf_bytes_b64)
                        pdf_file = io.BytesIO(pdf_bytes)
                        reader = PdfReader(pdf_file)
                        
                        extracted_text = []
                        for page_num in range(len(reader.pages)):
                            page = reader.pages[page_num]
                            text = page.extract_text()
                            if text.strip():
                                extracted_text.append(f"--- Page {page_num + 1} ---\n{text}")
                        
                        if extracted_text:
                            content = "\n\n".join(extracted_text)
                            self.logger.info(f"Extracted {len(content)} characters from PDF ({len(reader.pages)} pages)")
                        else:
                            content = "[No text content found in PDF]"
                except Exception as e:
                    content = f"[Error extracting PDF text: {str(e)}]"
                    self.logger.error(f"Error extracting PDF text from {resource.uri}: {e}")
            
            # Fetch content from URL resources
            elif resource.resource_type == ResourceType.URL and resource.uri.startswith(('http://', 'https://')):
                try:
                    self.logger.info(f"Fetching URL content: {resource.uri}")
                    async with aiohttp.ClientSession() as session:
                        async with session.get(
                            resource.uri,
                            timeout=aiohttp.ClientTimeout(total=30),
                            headers={'User-Agent': 'AI-MCP-Toolkit/1.0'}
                        ) as response:
                            if response.status == 200:
                                # Check if content is text
                                content_type = response.headers.get('Content-Type', '')
                                if 'text' in content_type or 'json' in content_type or 'xml' in content_type:
                                    content = await response.text()
                                    self.logger.info(f"Fetched {len(content)} chars from URL")
                                else:
                                    content = f"[Binary content from URL: {resource.uri}, Content-Type: {content_type}]"
                            else:
                                content = f"[Error fetching URL: HTTP {response.status}]"
                                self.logger.warning(f"Failed to fetch URL {resource.uri}: {response.status}")
                except aiohttp.ClientError as e:
                    content = f"[Error fetching URL: {str(e)}]"
                    self.logger.error(f"Error fetching URL {resource.uri}: {e}")
                except Exception as e:
                    content = f"[Error fetching URL: {str(e)}]"
                    self.logger.error(f"Unexpected error fetching URL {resource.uri}: {e}")
            
            # Return resource contents
            contents = [
                {
                    "uri": resource.uri,
                    "mimeType": resource.mime_type,
                    "text": content
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
        owner_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        embeddings: Optional[List[float]] = None,
        chunks: Optional[List[Dict[str, Any]]] = None
    ) -> Resource:
        """
        Create a new resource with optional vector embeddings.
        
        Args:
            uri: Unique resource URI
            name: Resource name
            description: Resource description
            mime_type: MIME type
            resource_type: Type of resource
            owner_id: User ID who owns this resource
            content: Optional resource content
            metadata: Optional metadata dictionary
            embeddings: Optional embedding vector for semantic search
            chunks: Optional document chunks with embeddings
            
        Returns:
            Created Resource document
            
        Raises:
            ValueError: If resource with URI already exists
        """
        try:
            # Note: We allow duplicate URIs now since each upload gets a unique UUID
            # Users can upload multiple versions of the same file
            
            # Create resource metadata
            resource_metadata = ResourceMetadata(
                created_at=datetime.utcnow(),
                modified_at=datetime.utcnow(),
                properties=metadata or {}
            )
            
            # Create new resource with embeddings
            resource = Resource(
                uri=uri,
                name=name,
                description=description,
                mime_type=mime_type,
                resource_type=resource_type,
                owner_id=owner_id,
                content=content,
                metadata=resource_metadata,
                embeddings=embeddings,
                chunks=chunks,
                embeddings_model=metadata.get('embeddings_model') if metadata else None,
                embeddings_created_at=datetime.utcnow() if embeddings else None,
                embeddings_chunk_count=len(chunks) if chunks else 0
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
        user_id: Optional[str] = None,
        is_admin: bool = False,
        name: Optional[str] = None,
        description: Optional[str] = None,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Resource:
        """
        Update an existing resource.
        
        Args:
            uri: Resource URI to update
            user_id: User ID for ownership check (required for non-admins)
            is_admin: Whether the user is an admin (admins can update all resources)
            name: Optional new name
            description: Optional new description
            content: Optional new content
            metadata: Optional metadata updates
            
        Returns:
            Updated Resource document
            
        Raises:
            ValueError: If resource not found or access denied
        """
        try:
            # Find resource
            resource = await Resource.find_one(Resource.uri == uri)
            if not resource:
                raise ValueError(f"Resource not found: {uri}")
            
            # Ownership check: regular users can only update their own resources
            if not is_admin and user_id and resource.owner_id != user_id:
                raise ValueError(f"Access denied: Resource not found: {uri}")
            
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
            
            # Trigger background reindexing if searchable fields changed
            searchable_fields_changed = any([
                name is not None,
                description is not None,
                content is not None
            ])
            
            if searchable_fields_changed:
                import asyncio
                from ..services.reindexing_service import get_reindexing_service
                
                # Fire reindexing task in background (non-blocking)
                asyncio.create_task(
                    get_reindexing_service().reindex_resource(
                        resource=resource,
                        reindex_keywords=False,  # Don't regenerate keywords on every edit
                        reindex_embeddings=content is not None,  # Only if content changed
                        reindex_suggestions=True,  # Always update autocomplete
                        update_chunks=True  # Always update chunk searchable_text
                    )
                )
                self.logger.info(f"🔄 Triggered background reindexing for: {uri}")
            
            return resource
            
        except ValueError:
            raise
        except Exception as e:
            self.logger.error(f"Error updating resource {uri}: {e}", exc_info=True)
            raise
    
    async def delete_resource(
        self,
        uri: str,
        user_id: Optional[str] = None,
        is_admin: bool = False
    ) -> bool:
        """
        Delete a resource.
        
        Args:
            uri: Resource URI to delete
            user_id: User ID for ownership check (required for non-admins)
            is_admin: Whether the user is an admin (admins can delete all resources)
            
        Returns:
            True if deleted successfully
            
        Raises:
            ValueError: If resource not found or access denied
        """
        try:
            # Find resource
            resource = await Resource.find_one(Resource.uri == uri)
            if not resource:
                raise ValueError(f"Resource not found: {uri}")
            
            # Ownership check: regular users can only delete their own resources
            if not is_admin and user_id and resource.owner_id != user_id:
                raise ValueError(f"Access denied: Resource not found: {uri}")
            
            # 🐞 FIX: Delete associated chunks first
            from ..models.documents import ResourceChunk
            resource_id = str(resource.id)
            company_id = resource.company_id or resource.owner_id
            
            chunks_deleted = await ResourceChunk.find(
                ResourceChunk.parent_id == resource_id
            ).delete()
            
            if chunks_deleted.deleted_count > 0:
                self.logger.info(f"Deleted {chunks_deleted.deleted_count} chunks for resource {uri}")
            
            # Remove from Redis suggestions before deleting
            try:
                from ..services.reindexing_service import get_reindexing_service
                await get_reindexing_service().remove_resource_from_indexes(
                    resource_id=resource_id,
                    company_id=company_id
                )
            except Exception as e:
                self.logger.warning(f"Could not remove from indexes: {e}")
            
            # Delete resource
            await resource.delete()
            
            self.logger.info(f"✅ Deleted resource {uri} and all associated data")
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
