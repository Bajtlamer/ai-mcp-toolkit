"""Database configuration and connection management for AI MCP Toolkit."""

import os
import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""
    
    # MongoDB Atlas configuration
    mongodb_url: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    mongodb_database: str = os.getenv("MONGODB_DATABASE", "ai_mcp_toolkit")
    
    # Redis configuration
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    redis_db: int = int(os.getenv("REDIS_DB", "0"))
    
    # Connection settings
    max_pool_size: int = int(os.getenv("MONGODB_MAX_POOL_SIZE", "100"))
    min_pool_size: int = int(os.getenv("MONGODB_MIN_POOL_SIZE", "10"))
    max_idle_time_ms: int = int(os.getenv("MONGODB_MAX_IDLE_TIME_MS", "30000"))
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore"  # Ignore extra fields from environment
    }


class DatabaseManager:
    """Database connection manager for MongoDB and Redis."""
    
    def __init__(self):
        self.settings = DatabaseSettings()
        self.mongodb_client: Optional[AsyncIOMotorClient] = None
        self.redis_client = None
        self._is_connected = False
    
    async def connect(self) -> None:
        """Initialize database connections."""
        try:
            # Connect to MongoDB Atlas
            self.mongodb_client = AsyncIOMotorClient(
                self.settings.mongodb_url,
                maxPoolSize=self.settings.max_pool_size,
                minPoolSize=self.settings.min_pool_size,
                maxIdleTimeMS=self.settings.max_idle_time_ms,
                serverSelectionTimeoutMS=5000,
            )
            
            # Test MongoDB connection
            await self.mongodb_client.admin.command('ping')
            logger.info(f"Connected to MongoDB Atlas: {self.settings.mongodb_database}")
            
            # Initialize Beanie with all document models
            await self._init_beanie()
            
            # Connect to Redis
            await self._connect_redis()
            
            self._is_connected = True
            logger.info("Database connections established successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to databases: {e}")
            raise
    
    async def _init_beanie(self) -> None:
        """Initialize Beanie with document models."""
        from .documents import (
            User, Session, AuditLog, 
            Resource, ResourceChunk,
            Prompt, Message, Conversation, 
            AgentState, Workflow
        )
        from .search_config import SearchCategory
        
        # List of all document models
        document_models = [
            User,
            Session,
            AuditLog,
            Resource,
            ResourceChunk,  # NEW: For contextual search chunks
            SearchCategory,  # NEW: For dynamic search configuration
            Prompt,
            Message,
            Conversation,
            AgentState,
            Workflow,
        ]
        
        await init_beanie(
            database=self.mongodb_client[self.settings.mongodb_database],
            document_models=document_models
        )
        logger.info("Beanie initialized with document models")
    
    async def _connect_redis(self) -> None:
        """Connect to Redis."""
        try:
            import redis.asyncio as redis
            
            self.redis_client = redis.from_url(
                self.settings.redis_url,
                db=self.settings.redis_db,
                decode_responses=True
            )
            
            # Test Redis connection
            await self.redis_client.ping()
            logger.info(f"Connected to Redis: {self.settings.redis_url}")
            
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Continuing without Redis.")
            self.redis_client = None
    
    async def disconnect(self) -> None:
        """Close database connections."""
        try:
            if self.mongodb_client:
                self.mongodb_client.close()
                logger.info("MongoDB connection closed")
            
            if self.redis_client:
                await self.redis_client.close()
                logger.info("Redis connection closed")
            
            self._is_connected = False
            
        except Exception as e:
            logger.error(f"Error closing database connections: {e}")
    
    @property
    def is_connected(self) -> bool:
        """Check if database connections are active."""
        return self._is_connected
    
    async def health_check(self) -> dict:
        """Perform health check on all database connections."""
        health = {
            "mongodb": False,
            "redis": False,
            "overall": False
        }
        
        try:
            # Check MongoDB
            if self.mongodb_client:
                await self.mongodb_client.admin.command('ping')
                health["mongodb"] = True
            
            # Check Redis
            if self.redis_client:
                await self.redis_client.ping()
                health["redis"] = True
            
            # Overall health is OK if MongoDB is connected (Redis is optional)
            health["overall"] = health["mongodb"]
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
        
        return health


# Global database manager instance
db_manager = DatabaseManager()


async def get_database() -> DatabaseManager:
    """Get the database manager instance."""
    if not db_manager.is_connected:
        await db_manager.connect()
    return db_manager


async def get_mongodb_client() -> AsyncIOMotorClient:
    """Get the MongoDB client."""
    if not db_manager.is_connected:
        await db_manager.connect()
    return db_manager.mongodb_client


async def get_redis_client():
    """Get the Redis client."""
    if not db_manager.is_connected:
        await db_manager.connect()
    return db_manager.redis_client
