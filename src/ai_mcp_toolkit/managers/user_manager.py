"""User Manager for user authentication and management."""

import logging
from typing import Optional, List
from datetime import datetime

from ..models.documents import User, UserRole
from ..utils.auth import hash_password, verify_password

logger = logging.getLogger(__name__)


class UserManager:
    """Manager for user operations with authentication."""
    
    def __init__(self):
        """Initialize the user manager."""
        self.logger = logging.getLogger(__name__)
    
    async def register(
        self,
        username: str,
        email: str,
        password: str,
        full_name: Optional[str] = None,
        role: UserRole = UserRole.USER
    ) -> User:
        """
        Register a new user.
        
        Args:
            username: Unique username
            email: User email
            password: Plain text password
            full_name: Optional full name
            role: User role (default: USER)
            
        Returns:
            Created User document
            
        Raises:
            ValueError: If username or email already exists
        """
        try:
            # Check if username exists
            existing_user = await User.find_one(User.username == username)
            if existing_user:
                raise ValueError(f"Username '{username}' already exists")
            
            # Check if email exists
            existing_email = await User.find_one(User.email == email)
            if existing_email:
                raise ValueError(f"Email '{email}' already exists")
            
            # Hash the password
            password_hash = hash_password(password)
            
            # Create user
            user = User(
                username=username,
                email=email,
                password_hash=password_hash,
                full_name=full_name,
                role=role,
                is_active=True
            )
            
            # Save to database
            await user.save()
            
            self.logger.info(f"User registered: {username}")
            return user
            
        except ValueError:
            raise
        except Exception as e:
            self.logger.error(f"Error registering user {username}: {e}", exc_info=True)
            raise
    
    async def authenticate(self, username: str, password: str) -> Optional[User]:
        """
        Authenticate a user with username and password.
        
        Args:
            username: Username
            password: Plain text password
            
        Returns:
            User if authentication successful, None otherwise
        """
        try:
            # Find user by username
            user = await User.find_one(User.username == username)
            
            if not user:
                self.logger.warning(f"Authentication failed: user not found: {username}")
                return None
            
            # Check if user is active
            if not user.is_active:
                self.logger.warning(f"Authentication failed: user inactive: {username}")
                return None
            
            # Verify password
            if not verify_password(password, user.password_hash):
                self.logger.warning(f"Authentication failed: invalid password: {username}")
                return None
            
            # Update last login
            user.last_login = datetime.utcnow()
            await user.save()
            
            self.logger.info(f"User authenticated: {username}")
            return user
            
        except Exception as e:
            self.logger.error(f"Error authenticating user {username}: {e}", exc_info=True)
            return None
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User document if found, None otherwise
        """
        try:
            from beanie import PydanticObjectId
            user = await User.get(PydanticObjectId(user_id))
            return user
        except Exception as e:
            self.logger.error(f"Error getting user by ID {user_id}: {e}", exc_info=True)
            return None
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Get user by username.
        
        Args:
            username: Username
            
        Returns:
            User document if found, None otherwise
        """
        try:
            user = await User.find_one(User.username == username)
            return user
        except Exception as e:
            self.logger.error(f"Error getting user by username {username}: {e}", exc_info=True)
            return None
    
    async def update_user(
        self,
        user_id: str,
        email: Optional[str] = None,
        full_name: Optional[str] = None,
        password: Optional[str] = None
    ) -> Optional[User]:
        """
        Update user information.
        
        Args:
            user_id: User ID
            email: Optional new email
            full_name: Optional new full name
            password: Optional new password
            
        Returns:
            Updated User document if successful, None otherwise
        """
        try:
            user = await self.get_user_by_id(user_id)
            if not user:
                return None
            
            # Update fields
            if email:
                # Check if email already exists for another user
                existing = await User.find_one(User.email == email)
                if existing and str(existing.id) != user_id:
                    raise ValueError(f"Email '{email}' already exists")
                user.email = email
            
            if full_name:
                user.full_name = full_name
            
            if password:
                user.password_hash = hash_password(password)
            
            user.updated_at = datetime.utcnow()
            await user.save()
            
            self.logger.info(f"User updated: {user.username}")
            return user
            
        except ValueError:
            raise
        except Exception as e:
            self.logger.error(f"Error updating user {user_id}: {e}", exc_info=True)
            return None
    
    async def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
        role: Optional[UserRole] = None
    ) -> List[User]:
        """
        List users (admin only).
        
        Args:
            skip: Number of users to skip
            limit: Maximum number of users to return
            role: Optional role filter
            
        Returns:
            List of User documents
        """
        try:
            query = {}
            if role:
                query["role"] = role
            
            users_cursor = User.find(query).skip(skip).limit(limit)
            users = await users_cursor.to_list()
            
            self.logger.info(f"Listed {len(users)} users")
            return users
            
        except Exception as e:
            self.logger.error(f"Error listing users: {e}", exc_info=True)
            return []
    
    async def get_user_count(self, role: Optional[UserRole] = None) -> int:
        """
        Get count of users.
        
        Args:
            role: Optional role filter
            
        Returns:
            Count of users
        """
        try:
            query = {}
            if role:
                query["role"] = role
            
            count = await User.find(query).count()
            return count
            
        except Exception as e:
            self.logger.error(f"Error counting users: {e}", exc_info=True)
            return 0
    
    async def delete_user(self, user_id: str) -> bool:
        """
        Delete a user (admin only).
        
        Args:
            user_id: User ID
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            user = await self.get_user_by_id(user_id)
            if not user:
                return False
            
            await user.delete()
            self.logger.info(f"User deleted: {user.username}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting user {user_id}: {e}", exc_info=True)
            return False
    
    async def toggle_user_status(self, user_id: str) -> Optional[User]:
        """
        Toggle user active status (admin only).
        
        Args:
            user_id: User ID
            
        Returns:
            Updated User document if successful, None otherwise
        """
        try:
            user = await self.get_user_by_id(user_id)
            if not user:
                return None
            
            user.is_active = not user.is_active
            user.updated_at = datetime.utcnow()
            await user.save()
            
            status = "activated" if user.is_active else "deactivated"
            self.logger.info(f"User {status}: {user.username}")
            return user
            
        except Exception as e:
            self.logger.error(f"Error toggling user status {user_id}: {e}", exc_info=True)
            return None
