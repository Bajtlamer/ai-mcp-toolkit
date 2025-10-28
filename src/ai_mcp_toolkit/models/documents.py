"""MongoDB document models for AI MCP Toolkit using Beanie ODM."""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from beanie import Document, Indexed
from pydantic import Field, BaseModel
from enum import Enum


class ResourceType(str, Enum):
    """Resource type enumeration."""
    FILE = "file"
    URL = "url"
    DATABASE = "database"
    API = "api"
    TEXT = "text"


class UserRole(str, Enum):
    """User role enumeration."""
    USER = "user"
    ADMIN = "admin"


class MessageRole(str, Enum):
    """Message role enumeration."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    AGENT = "agent"


class WorkflowStatus(str, Enum):
    """Workflow status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentStatus(str, Enum):
    """Agent status enumeration."""
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"


# Base models for MCP protocol
class ResourceMetadata(BaseModel):
    """Resource metadata."""
    size: Optional[int] = None
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list)
    properties: Dict[str, Any] = Field(default_factory=dict)


class PromptArgument(BaseModel):
    """Prompt argument definition."""
    name: str
    description: str
    type: str = "string"
    required: bool = True
    default: Optional[Any] = None


class MessageContent(BaseModel):
    """Message content structure."""
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentCapability(BaseModel):
    """Agent capability definition."""
    name: str
    description: str
    input_types: List[str] = Field(default_factory=list)
    output_types: List[str] = Field(default_factory=list)
    parameters: Dict[str, Any] = Field(default_factory=dict)


# Document models
class Session(Document):
    """Session document model for secure server-side session management."""
    
    session_id: Indexed(str, unique=True)
    user_id: Indexed(str)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    is_active: bool = True
    
    class Settings:
        name = "sessions"
        indexes = [
            "session_id",
            "user_id",
            "expires_at",
            "is_active",
            [("user_id", 1), ("is_active", 1)],
        ]


class AuditLog(Document):
    """Audit log document for tracking all user operations."""
    
    user_id: Indexed(str)
    username: str
    action: Indexed(str)  # e.g., "resource.create", "resource.update", "auth.login"
    resource_type: Optional[str] = None  # e.g., "resource", "prompt", "user"
    resource_id: Optional[str] = None
    method: str  # HTTP method: GET, POST, PUT, DELETE
    endpoint: str  # API endpoint
    status_code: int  # HTTP status code
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_data: Optional[Dict[str, Any]] = None  # Sanitized request data
    response_data: Optional[Dict[str, Any]] = None  # Sanitized response data
    error_message: Optional[str] = None
    duration_ms: Optional[float] = None  # Request duration in milliseconds
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "audit_logs"
        indexes = [
            "user_id",
            "username",
            "action",
            "resource_type",
            "timestamp",
            [("user_id", 1), ("timestamp", -1)],
            [("action", 1), ("timestamp", -1)],
        ]


class User(Document):
    """User document model for authentication and authorization."""
    
    username: Indexed(str, unique=True)
    email: Indexed(str, unique=True)
    password_hash: str
    full_name: Optional[str] = None
    role: UserRole = UserRole.USER
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    preferences: Dict[str, Any] = Field(default_factory=dict)  # UI theme, agent settings, etc.
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Settings:
        name = "users"
        indexes = [
            "username",
            "email",
            "role",
            "is_active",
            "created_at",
        ]


class Resource(Document):
    """Resource document model for MCP resources."""
    
    uri: Indexed(str, unique=True)
    name: str
    description: str
    mime_type: str
    resource_type: ResourceType
    content: Optional[str] = None
    owner_id: Optional[str] = None  # User ID who owns this resource
    metadata: ResourceMetadata = Field(default_factory=ResourceMetadata)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Vector embeddings fields for semantic search
    embeddings: Optional[List[float]] = None  # Main embedding vector (768 dims for nomic-embed-text)
    embeddings_model: Optional[str] = None  # e.g., "nomic-embed-text", "text-embedding-3-small"
    embeddings_created_at: Optional[datetime] = None
    embeddings_chunk_count: Optional[int] = None
    
    # For chunked documents (large files split into searchable chunks)
    chunks: Optional[List[Dict[str, Any]]] = None
    # chunks format: [
    #   {
    #     "index": 0,
    #     "text": "chunk content...",
    #     "embeddings": [0.1, 0.2, ...],
    #     "char_start": 0,
    #     "char_end": 1000
    #   },
    #   ...
    # ]
    
    class Settings:
        name = "resources"
        indexes = [
            "uri",
            "name",
            "resource_type",
            "owner_id",
            "created_at",
            [("resource_type", 1), ("created_at", -1)],
            [("owner_id", 1), ("created_at", -1)],
        ]


class Prompt(Document):
    """Prompt document model for MCP prompts."""
    
    name: Indexed(str, unique=True)
    description: str
    template: str
    arguments: List[PromptArgument] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    owner_id: Optional[str] = None  # User ID who created this prompt
    is_public: bool = True  # Public prompts visible to all users
    version: str = "1.0.0"
    use_count: int = 0  # Track how many times the prompt was used
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "prompts"
        indexes = [
            "name",
            "tags",
            "owner_id",
            "is_public",
            "created_at",
            [("tags", 1), ("created_at", -1)],
            [("owner_id", 1), ("created_at", -1)],
            [("is_public", 1), ("created_at", -1)],
        ]


class Message(Document):
    """Message document model for MCP messages."""
    
    conversation_id: Indexed(str)
    role: MessageRole
    content: MessageContent
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    agent_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Settings:
        name = "messages"
        indexes = [
            "conversation_id",
            "timestamp",
            "role",
            "agent_id",
            [("conversation_id", 1), ("timestamp", 1)],
        ]


class Conversation(Document):
    """Conversation document model."""
    
    user_id: Indexed(str)  # Owner of the conversation
    title: str
    description: Optional[str] = None
    messages: List[Dict[str, Any]] = Field(default_factory=list)  # Store messages directly
    participants: List[str] = Field(default_factory=list)
    status: str = "active"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)  # thinking_times, response_count, etc.
    
    class Settings:
        name = "conversations"
        indexes = [
            "user_id",
            "title",
            "status",
            "created_at",
            "participants",
            [("user_id", 1), ("created_at", -1)],
            [("status", 1), ("created_at", -1)],
        ]


class AgentState(Document):
    """Agent state document model."""
    
    agent_id: Indexed(str, unique=True)
    agent_name: str
    status: AgentStatus = AgentStatus.IDLE
    capabilities: List[AgentCapability] = Field(default_factory=list)
    current_task: Optional[str] = None
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    performance_metrics: Dict[str, Any] = Field(default_factory=dict)
    configuration: Dict[str, Any] = Field(default_factory=dict)
    
    class Settings:
        name = "agent_states"
        indexes = [
            "agent_id",
            "status",
            "last_activity",
            [("status", 1), ("last_activity", -1)],
        ]


class WorkflowStep(BaseModel):
    """Workflow step definition."""
    step_id: str
    agent_id: str
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_data: Dict[str, Any] = Field(default_factory=dict)
    status: WorkflowStatus = WorkflowStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    dependencies: List[str] = Field(default_factory=list)


class Workflow(Document):
    """Workflow document model."""
    
    name: str
    description: str
    steps: List[WorkflowStep] = Field(default_factory=list)
    status: WorkflowStatus = WorkflowStatus.PENDING
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Settings:
        name = "workflows"
        indexes = [
            "name",
            "status",
            "created_by",
            "created_at",
            [("status", 1), ("created_at", -1)],
        ]


# Shared context models
class SharedContext(Document):
    """Shared context document for agent cooperation."""
    
    context_id: Indexed(str, unique=True)
    name: str
    description: str
    data: Dict[str, Any] = Field(default_factory=dict)
    access_level: str = "public"  # public, private, restricted
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    
    class Settings:
        name = "shared_contexts"
        indexes = [
            "context_id",
            "access_level",
            "created_by",
            "created_at",
            [("access_level", 1), ("created_at", -1)],
        ]


# Event system models
class Event(Document):
    """Event document model for event-driven architecture."""
    
    event_id: Indexed(str, unique=True)
    event_type: str
    source: str
    data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    processed: bool = False
    subscribers: List[str] = Field(default_factory=list)
    
    class Settings:
        name = "events"
        indexes = [
            "event_id",
            "event_type",
            "timestamp",
            "processed",
            [("event_type", 1), ("timestamp", -1)],
        ]


# Cache models for Redis
class CacheEntry(BaseModel):
    """Cache entry model."""
    key: str
    value: Any
    ttl: int  # Time to live in seconds
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(default_factory=datetime.utcnow)
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        return datetime.utcnow() > self.expires_at
