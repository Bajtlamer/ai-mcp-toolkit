"""Database connection and initialization for MongoDB with Beanie ODM."""

import os
import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

logger = logging.getLogger(__name__)

# Global Redis client
_redis_client: Optional[redis.Redis] = None


class DatabaseManager:
    """Manages MongoDB connection and Beanie initialization."""
    
    def __init__(self):
        """Initialize database manager."""
        self.client: Optional[AsyncIOMotorClient] = None
        self.database_name: str = os.getenv("MONGODB_DATABASE", "ai_mcp_toolkit")
        self.mongodb_url: str = os.getenv(
            "MONGODB_URL",
            "mongodb://localhost:27017"
        )
        self._connected = False
        self.logger = logging.getLogger(__name__)
    
    async def connect(self) -> None:
        """Connect to MongoDB and initialize Beanie."""
        if self._connected:
            self.logger.warning("Database already connected")
            return
        
        try:
            # Create Motor client
            self.client = AsyncIOMotorClient(
                self.mongodb_url,
                serverSelectionTimeoutMS=5000
            )
            
            # Test connection
            await self.client.admin.command('ping')
            self.logger.info(f"✅ Connected to MongoDB: {self.database_name}")
            
            # Initialize Beanie with document models
            from .documents import (
                User, Session, AuditLog, Resource, ResourceChunk,
                Conversation, Message, Prompt
            )
            from .search_config import SearchCategory
            
            await init_beanie(
                database=self.client[self.database_name],
                document_models=[
                    User,
                    Session,
                    AuditLog,
                    Resource,
                    ResourceChunk,
                    Conversation,
                    Message,
                    Prompt,
                    SearchCategory
                ]
            )
            
            self.logger.info("✅ Beanie initialized with document models")
            self._connected = True
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            self.logger.error(f"❌ Failed to connect to MongoDB: {e}")
            self.client = None
            raise
        except Exception as e:
            self.logger.error(f"❌ Database initialization error: {e}", exc_info=True)
            self.client = None
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from MongoDB."""
        if self.client:
            self.client.close()
            self.client = None
            self._connected = False
            self.logger.info("Disconnected from MongoDB")
    
    async def health_check(self) -> dict:
        """Check database health."""
        if not self.client:
            return {
                "mongodb": False,
                "overall": False,
                "error": "Not connected"
            }
        
        try:
            await self.client.admin.command('ping')
            return {
                "mongodb": True,
                "overall": True,
                "database": self.database_name
            }
        except Exception as e:
            return {
                "mongodb": False,
                "overall": False,
                "error": str(e)
            }
    
    @property
    def is_connected(self) -> bool:
        """Check if database is connected."""
        return self._connected and self.client is not None


# Global database manager instance
db_manager = DatabaseManager()


async def get_redis_client():
    """Get or create Redis client."""
    global _redis_client
    
    if not REDIS_AVAILABLE:
        logger.warning("Redis library not installed, suggestions disabled")
        return None
    
    if _redis_client is not None:
        return _redis_client
    
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    redis_db = int(os.getenv("REDIS_DB", "0"))
    
    try:
        _redis_client = redis.from_url(
            redis_url,
            db=redis_db,
            decode_responses=True,
            socket_connect_timeout=5
        )
        # Test connection
        await _redis_client.ping()
        logger.info(f"✅ Connected to Redis: {redis_url}")
        return _redis_client
    except Exception as e:
        logger.warning(f"⚠️ Redis connection failed: {e}. Suggestions will be disabled.")
        _redis_client = None
        return None


async def close_redis():
    """Close Redis connection."""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
        logger.info("Closed Redis connection")

