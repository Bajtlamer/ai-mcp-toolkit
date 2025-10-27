"""Prompt Manager for AI MCP Toolkit - handles prompt template operations."""

from typing import List, Optional, Dict, Any
from datetime import datetime
import re
import logging

from ..models.documents import Prompt, PromptArgument
from beanie import PydanticObjectId

logger = logging.getLogger(__name__)


class PromptManager:
    """Manager class for prompt template operations."""
    
    @staticmethod
    async def create_prompt(
        name: str,
        description: str,
        template: str,
        arguments: List[Dict[str, Any]] = None,
        tags: List[str] = None,
        owner_id: Optional[str] = None,
        is_public: bool = True,
        version: str = "1.0.0"
    ) -> Prompt:
        """
        Create a new prompt template.
        
        Args:
            name: Unique name for the prompt
            description: Description of what the prompt does
            template: The prompt template with {{variable}} placeholders
            arguments: List of argument definitions
            tags: Tags for categorization
            owner_id: User ID of the creator
            is_public: Whether the prompt is publicly visible
            version: Version string
            
        Returns:
            Created Prompt document
            
        Raises:
            ValueError: If prompt name already exists or template is invalid
        """
        # Check if prompt with this name already exists
        existing = await Prompt.find_one(Prompt.name == name)
        if existing:
            raise ValueError(f"Prompt with name '{name}' already exists")
        
        # Validate template
        PromptManager._validate_template(template, arguments or [])
        
        # Parse arguments
        prompt_arguments = []
        if arguments:
            for arg in arguments:
                prompt_arguments.append(PromptArgument(**arg))
        
        # Create prompt document
        prompt = Prompt(
            name=name,
            description=description,
            template=template,
            arguments=prompt_arguments,
            tags=tags or [],
            owner_id=owner_id,
            is_public=is_public,
            version=version,
            use_count=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        await prompt.insert()
        logger.info(f"Created prompt: {name}")
        return prompt
    
    @staticmethod
    async def get_prompt(name: str, user_id: Optional[str] = None) -> Optional[Prompt]:
        """
        Get a prompt by name.
        
        Args:
            name: Prompt name
            user_id: User ID for permission checking
            
        Returns:
            Prompt document or None if not found/no access
        """
        prompt = await Prompt.find_one(Prompt.name == name)
        
        if not prompt:
            return None
        
        # Check access permissions
        if not prompt.is_public:
            if not user_id or prompt.owner_id != user_id:
                return None  # No access to private prompt
        
        return prompt
    
    @staticmethod
    async def list_prompts(
        user_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Prompt]:
        """
        List prompts with optional filtering.
        
        Args:
            user_id: Filter by owner or show public prompts
            tags: Filter by tags
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of Prompt documents
        """
        query = {}
        
        # Build query
        filters = []
        
        # Show public prompts OR owned prompts
        if user_id:
            filters.append({"$or": [
                {"is_public": True},
                {"owner_id": user_id}
            ]})
        else:
            filters.append({"is_public": True})
        
        # Filter by tags
        if tags:
            filters.append({"tags": {"$in": tags}})
        
        if filters:
            if len(filters) == 1:
                query = filters[0]
            else:
                query = {"$and": filters}
        
        prompts = await Prompt.find(query).skip(skip).limit(limit).sort("-created_at").to_list()
        return prompts
    
    @staticmethod
    async def update_prompt(
        name: str,
        user_id: Optional[str] = None,
        description: Optional[str] = None,
        template: Optional[str] = None,
        arguments: Optional[List[Dict[str, Any]]] = None,
        tags: Optional[List[str]] = None,
        is_public: Optional[bool] = None,
        version: Optional[str] = None
    ) -> Optional[Prompt]:
        """
        Update an existing prompt.
        
        Args:
            name: Prompt name to update
            user_id: User ID for permission checking
            description: New description
            template: New template
            arguments: New arguments
            tags: New tags
            is_public: New visibility setting
            version: New version string
            
        Returns:
            Updated Prompt document or None if not found/no access
            
        Raises:
            ValueError: If template is invalid
            PermissionError: If user doesn't have permission to update
        """
        prompt = await Prompt.find_one(Prompt.name == name)
        
        if not prompt:
            return None
        
        # Check update permissions (only owner can update)
        if prompt.owner_id and user_id != prompt.owner_id:
            raise PermissionError(f"User {user_id} cannot update prompt '{name}'")
        
        # Update fields
        if description is not None:
            prompt.description = description
        
        if template is not None:
            # Validate new template
            args_to_validate = arguments if arguments is not None else [arg.dict() for arg in prompt.arguments]
            PromptManager._validate_template(template, args_to_validate)
            prompt.template = template
        
        if arguments is not None:
            prompt.arguments = [PromptArgument(**arg) for arg in arguments]
        
        if tags is not None:
            prompt.tags = tags
        
        if is_public is not None:
            prompt.is_public = is_public
        
        if version is not None:
            prompt.version = version
        
        prompt.updated_at = datetime.utcnow()
        
        await prompt.save()
        logger.info(f"Updated prompt: {name}")
        return prompt
    
    @staticmethod
    async def delete_prompt(name: str, user_id: Optional[str] = None) -> bool:
        """
        Delete a prompt.
        
        Args:
            name: Prompt name to delete
            user_id: User ID for permission checking
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            PermissionError: If user doesn't have permission to delete
        """
        prompt = await Prompt.find_one(Prompt.name == name)
        
        if not prompt:
            return False
        
        # Check delete permissions (only owner can delete)
        if prompt.owner_id and user_id != prompt.owner_id:
            raise PermissionError(f"User {user_id} cannot delete prompt '{name}'")
        
        await prompt.delete()
        logger.info(f"Deleted prompt: {name}")
        return True
    
    @staticmethod
    async def count_prompts(user_id: Optional[str] = None, tags: Optional[List[str]] = None) -> int:
        """
        Count prompts with optional filtering.
        
        Args:
            user_id: Filter by owner or public prompts
            tags: Filter by tags
            
        Returns:
            Count of matching prompts
        """
        query = {}
        filters = []
        
        # Show public prompts OR owned prompts
        if user_id:
            filters.append({"$or": [
                {"is_public": True},
                {"owner_id": user_id}
            ]})
        else:
            filters.append({"is_public": True})
        
        # Filter by tags
        if tags:
            filters.append({"tags": {"$in": tags}})
        
        if filters:
            if len(filters) == 1:
                query = filters[0]
            else:
                query = {"$and": filters}
        
        count = await Prompt.find(query).count()
        return count
    
    @staticmethod
    def render_prompt(prompt: Prompt, values: Dict[str, Any]) -> str:
        """
        Render a prompt template with provided values.
        
        Args:
            prompt: Prompt document
            values: Dictionary of argument name -> value
            
        Returns:
            Rendered prompt string
            
        Raises:
            ValueError: If required arguments are missing or invalid
        """
        # Validate required arguments
        for arg in prompt.arguments:
            if arg.required and arg.name not in values:
                if arg.default is not None:
                    values[arg.name] = arg.default
                else:
                    raise ValueError(f"Required argument '{arg.name}' is missing")
        
        # Replace placeholders
        rendered = prompt.template
        for key, value in values.items():
            placeholder = f"{{{{{key}}}}}"  # {{key}}
            rendered = rendered.replace(placeholder, str(value))
        
        return rendered
    
    @staticmethod
    async def increment_use_count(name: str) -> None:
        """Increment the use count for a prompt."""
        prompt = await Prompt.find_one(Prompt.name == name)
        if prompt:
            prompt.use_count += 1
            await prompt.save()
    
    @staticmethod
    def _validate_template(template: str, arguments: List[Dict[str, Any]]) -> None:
        """
        Validate a prompt template.
        
        Args:
            template: Template string with {{variable}} placeholders
            arguments: List of argument definitions
            
        Raises:
            ValueError: If template is invalid
        """
        # Find all placeholders in template
        placeholders = set(re.findall(r'\{\{(\w+)\}\}', template))
        
        # Check if all required placeholders have corresponding arguments
        arg_names = {arg.get('name') for arg in arguments}
        
        # Undefined placeholders (in template but not in arguments)
        undefined = placeholders - arg_names
        if undefined:
            logger.warning(f"Template has placeholders without argument definitions: {undefined}")
            # Don't raise error - allow flexible templates
        
        # Unused arguments (defined but not in template)
        unused = arg_names - placeholders
        if unused:
            logger.warning(f"Arguments defined but not used in template: {unused}")
            # Don't raise error - allow extra arguments
        
        # Basic template validation
        if not template or not template.strip():
            raise ValueError("Template cannot be empty")
    
    @staticmethod
    async def search_prompts(
        query: str,
        user_id: Optional[str] = None,
        limit: int = 20
    ) -> List[Prompt]:
        """
        Search prompts by name, description, or tags.
        
        Args:
            query: Search query string
            user_id: User ID for permission filtering
            limit: Maximum results
            
        Returns:
            List of matching Prompt documents
        """
        # Build search query
        filters = []
        
        # Text search in name, description, and tags
        text_filter = {
            "$or": [
                {"name": {"$regex": query, "$options": "i"}},
                {"description": {"$regex": query, "$options": "i"}},
                {"tags": {"$regex": query, "$options": "i"}}
            ]
        }
        filters.append(text_filter)
        
        # Access control
        if user_id:
            filters.append({"$or": [
                {"is_public": True},
                {"owner_id": user_id}
            ]})
        else:
            filters.append({"is_public": True})
        
        search_query = {"$and": filters}
        
        prompts = await Prompt.find(search_query).limit(limit).sort("-use_count").to_list()
        return prompts
