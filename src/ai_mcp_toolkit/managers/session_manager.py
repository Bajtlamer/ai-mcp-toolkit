"""Session Manager for secure server-side session management."""

import secrets
import logging
from typing import Optional
from datetime import datetime, timedelta

from ..models.documents import Session, User

logger = logging.getLogger(__name__)

# Session configuration
SESSION_EXPIRE_HOURS = 24  # Sessions expire after 24 hours
SESSION_ID_LENGTH = 32  # Length of session ID in bytes (64 hex chars)


class SessionManager:
    """Manager for server-side session operations."""
    
    def __init__(self):
        """Initialize the session manager."""
        self.logger = logging.getLogger(__name__)
    
    def generate_session_id(self) -> str:
        """
        Generate a cryptographically secure session ID.
        
        Returns:
            Secure random session ID
        """
        return secrets.token_hex(SESSION_ID_LENGTH)
    
    async def create_session(
        self,
        user_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Session:
        """
        Create a new session for a user.
        
        Args:
            user_id: User ID
            ip_address: Client IP address
            user_agent: Client user agent string
            
        Returns:
            Created Session document
        """
        try:
            session_id = self.generate_session_id()
            expires_at = datetime.utcnow() + timedelta(hours=SESSION_EXPIRE_HOURS)
            
            session = Session(
                session_id=session_id,
                user_id=user_id,
                expires_at=expires_at,
                ip_address=ip_address,
                user_agent=user_agent,
                is_active=True
            )
            
            await session.save()
            
            self.logger.info(f"Session created for user: {user_id}")
            return session
            
        except Exception as e:
            self.logger.error(f"Error creating session for user {user_id}: {e}", exc_info=True)
            raise
    
    async def get_session(self, session_id: str) -> Optional[Session]:
        """
        Get session by session ID.
        
        Args:
            session_id: Session ID
            
        Returns:
            Session document if found and valid, None otherwise
        """
        try:
            session = await Session.find_one(Session.session_id == session_id)
            
            if not session:
                return None
            
            # Check if session is expired
            if session.expires_at < datetime.utcnow():
                self.logger.info(f"Session expired: {session_id[:8]}...")
                await self.delete_session(session_id)
                return None
            
            # Check if session is active
            if not session.is_active:
                self.logger.info(f"Session inactive: {session_id[:8]}...")
                return None
            
            # Update last activity
            session.last_activity = datetime.utcnow()
            await session.save()
            
            return session
            
        except Exception as e:
            self.logger.error(f"Error getting session: {e}", exc_info=True)
            return None
    
    async def get_user_from_session(self, session_id: str) -> Optional[User]:
        """
        Get user from session ID.
        
        Args:
            session_id: Session ID
            
        Returns:
            User document if session is valid, None otherwise
        """
        try:
            session = await self.get_session(session_id)
            if not session:
                return None
            
            from beanie import PydanticObjectId
            user = await User.get(PydanticObjectId(session.user_id))
            
            if not user or not user.is_active:
                return None
            
            return user
            
        except Exception as e:
            self.logger.error(f"Error getting user from session: {e}", exc_info=True)
            return None
    
    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a session (logout).
        
        Args:
            session_id: Session ID to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            session = await Session.find_one(Session.session_id == session_id)
            if not session:
                return False
            
            await session.delete()
            self.logger.info(f"Session deleted: {session_id[:8]}...")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting session: {e}", exc_info=True)
            return False
    
    async def delete_user_sessions(self, user_id: str) -> int:
        """
        Delete all sessions for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Number of sessions deleted
        """
        try:
            sessions = await Session.find(Session.user_id == user_id).to_list()
            count = 0
            
            for session in sessions:
                await session.delete()
                count += 1
            
            self.logger.info(f"Deleted {count} sessions for user: {user_id}")
            return count
            
        except Exception as e:
            self.logger.error(f"Error deleting user sessions: {e}", exc_info=True)
            return 0
    
    async def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions from database.
        
        Returns:
            Number of sessions cleaned up
        """
        try:
            now = datetime.utcnow()
            expired_sessions = await Session.find(Session.expires_at < now).to_list()
            count = 0
            
            for session in expired_sessions:
                await session.delete()
                count += 1
            
            if count > 0:
                self.logger.info(f"Cleaned up {count} expired sessions")
            
            return count
            
        except Exception as e:
            self.logger.error(f"Error cleaning up expired sessions: {e}", exc_info=True)
            return 0
    
    async def extend_session(self, session_id: str, hours: int = SESSION_EXPIRE_HOURS) -> bool:
        """
        Extend session expiration time.
        
        Args:
            session_id: Session ID
            hours: Hours to extend (default: SESSION_EXPIRE_HOURS)
            
        Returns:
            True if extended successfully, False otherwise
        """
        try:
            session = await Session.find_one(Session.session_id == session_id)
            if not session:
                return False
            
            session.expires_at = datetime.utcnow() + timedelta(hours=hours)
            session.last_activity = datetime.utcnow()
            await session.save()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error extending session: {e}", exc_info=True)
            return False
    
    async def get_user_sessions(self, user_id: str) -> list[Session]:
        """
        Get all active sessions for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of active Session documents
        """
        try:
            sessions = await Session.find(
                Session.user_id == user_id,
                Session.is_active == True
            ).to_list()
            
            # Filter out expired sessions
            valid_sessions = []
            now = datetime.utcnow()
            
            for session in sessions:
                if session.expires_at > now:
                    valid_sessions.append(session)
                else:
                    # Clean up expired session
                    await session.delete()
            
            return valid_sessions
            
        except Exception as e:
            self.logger.error(f"Error getting user sessions: {e}", exc_info=True)
            return []
