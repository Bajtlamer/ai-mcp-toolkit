"""Conversation Manager for per-user conversation storage."""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..models.documents import Conversation

logger = logging.getLogger(__name__)


class ConversationManager:
    """Manager for user conversation operations."""
    
    def __init__(self):
        """Initialize the conversation manager."""
        self.logger = logging.getLogger(__name__)
    
    async def list_conversations(
        self,
        user_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Conversation]:
        """
        List all conversations for a user.
        
        Args:
            user_id: User ID
            limit: Maximum number of conversations to return
            offset: Offset for pagination
            
        Returns:
            List of Conversation documents
        """
        try:
            conversations = await Conversation.find(
                Conversation.user_id == user_id
            ).sort(-Conversation.updated_at).skip(offset).limit(limit).to_list()
            
            self.logger.info(f"Listed {len(conversations)} conversations for user {user_id}")
            return conversations
            
        except Exception as e:
            self.logger.error(f"Error listing conversations: {e}", exc_info=True)
            return []
    
    async def get_conversation(
        self,
        conversation_id: str,
        user_id: str
    ) -> Optional[Conversation]:
        """
        Get a specific conversation by ID.
        
        Args:
            conversation_id: Conversation ID
            user_id: User ID (for ownership verification)
            
        Returns:
            Conversation document if found and owned by user, None otherwise
        """
        try:
            from beanie import PydanticObjectId
            conversation = await Conversation.get(PydanticObjectId(conversation_id))
            
            if not conversation:
                return None
            
            # Verify ownership
            if conversation.user_id != user_id:
                self.logger.warning(f"User {user_id} attempted to access conversation {conversation_id} owned by {conversation.user_id}")
                return None
            
            return conversation
            
        except Exception as e:
            self.logger.error(f"Error getting conversation {conversation_id}: {e}", exc_info=True)
            return None
    
    async def create_conversation(
        self,
        user_id: str,
        title: str = "New Conversation",
        messages: List[Dict[str, Any]] = None,
        metadata: Dict[str, Any] = None
    ) -> Conversation:
        """
        Create a new conversation.
        
        Args:
            user_id: User ID
            title: Conversation title
            messages: Initial messages
            metadata: Additional metadata
            
        Returns:
            Created Conversation document
        """
        try:
            conversation = Conversation(
                user_id=user_id,
                title=title,
                messages=messages or [],
                status="active",
                metadata=metadata or {}
            )
            
            await conversation.save()
            
            self.logger.info(f"Created conversation {conversation.id} for user {user_id}")
            return conversation
            
        except Exception as e:
            self.logger.error(f"Error creating conversation: {e}", exc_info=True)
            raise
    
    async def update_conversation(
        self,
        conversation_id: str,
        user_id: str,
        title: Optional[str] = None,
        messages: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        status: Optional[str] = None
    ) -> Optional[Conversation]:
        """
        Update a conversation.
        
        Args:
            conversation_id: Conversation ID
            user_id: User ID (for ownership verification)
            title: New title
            messages: Updated messages
            metadata: Updated metadata
            status: Updated status
            
        Returns:
            Updated Conversation document if successful, None otherwise
        """
        try:
            conversation = await self.get_conversation(conversation_id, user_id)
            
            if not conversation:
                return None
            
            # Update fields
            if title is not None:
                conversation.title = title
            
            if messages is not None:
                conversation.messages = messages
            
            if metadata is not None:
                conversation.metadata = metadata
            
            if status is not None:
                conversation.status = status
            
            conversation.updated_at = datetime.utcnow()
            await conversation.save()
            
            self.logger.info(f"Updated conversation {conversation_id}")
            return conversation
            
        except Exception as e:
            self.logger.error(f"Error updating conversation {conversation_id}: {e}", exc_info=True)
            return None
    
    async def delete_conversation(
        self,
        conversation_id: str,
        user_id: str
    ) -> bool:
        """
        Delete a conversation.
        
        Args:
            conversation_id: Conversation ID
            user_id: User ID (for ownership verification)
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            conversation = await self.get_conversation(conversation_id, user_id)
            
            if not conversation:
                return False
            
            await conversation.delete()
            
            self.logger.info(f"Deleted conversation {conversation_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting conversation {conversation_id}: {e}", exc_info=True)
            return False
    
    async def delete_all_conversations(
        self,
        user_id: str
    ) -> int:
        """
        Delete all conversations for a user (bulk operation).
        
        Args:
            user_id: User ID
            
        Returns:
            Number of conversations deleted
        """
        try:
            result = await Conversation.find(
                Conversation.user_id == user_id
            ).delete()
            
            deleted_count = result.deleted_count if hasattr(result, 'deleted_count') else 0
            self.logger.info(f"Deleted {deleted_count} conversations for user {user_id}")
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"Error deleting all conversations for user {user_id}: {e}", exc_info=True)
            return 0
    
    async def add_message(
        self,
        conversation_id: str,
        user_id: str,
        message: Dict[str, Any]
    ) -> Optional[Conversation]:
        """
        Add a message to a conversation.
        
        Args:
            conversation_id: Conversation ID
            user_id: User ID (for ownership verification)
            message: Message to add
            
        Returns:
            Updated Conversation document if successful, None otherwise
        """
        try:
            conversation = await self.get_conversation(conversation_id, user_id)
            
            if not conversation:
                return None
            
            # Add timestamp if not present
            if 'timestamp' not in message:
                message['timestamp'] = datetime.utcnow().isoformat()
            
            conversation.messages.append(message)
            conversation.updated_at = datetime.utcnow()
            await conversation.save()
            
            self.logger.info(f"Added message to conversation {conversation_id}")
            return conversation
            
        except Exception as e:
            self.logger.error(f"Error adding message to conversation {conversation_id}: {e}", exc_info=True)
            return None
    
    async def get_conversation_count(self, user_id: str) -> int:
        """
        Get count of conversations for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Count of conversations
        """
        try:
            count = await Conversation.find(
                Conversation.user_id == user_id
            ).count()
            
            return count
            
        except Exception as e:
            self.logger.error(f"Error counting conversations: {e}", exc_info=True)
            return 0
