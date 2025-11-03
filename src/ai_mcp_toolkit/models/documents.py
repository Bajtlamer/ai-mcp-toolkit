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
    """Resource document model for MCP resources with contextual search support."""
    
    # === Core identification ===
    uri: Indexed(str, unique=True)
    name: str
    description: str
    mime_type: str
    resource_type: ResourceType
    content: Optional[str] = None
    owner_id: Optional[str] = None  # User ID who owns this resource
    
    # === NEW: Extended file identifiers ===
    file_id: Optional[str] = None  # Unique file identifier (e.g., "files/2025/10/INV-1234.pdf")
    file_name: Optional[str] = None  # Original filename
    file_type: Optional[str] = None  # "pdf", "text", "csv", "image", "structured"
    
    # === NEW: Multi-tenant / ACL ===
    company_id: Optional[str] = None  # For tenant isolation (defaults to owner_id)
    
    # === NEW: File metadata ===
    size_bytes: Optional[int] = None
    tags: List[str] = Field(default_factory=list)
    summary: Optional[str] = None  # AI-generated summary or user description
    technical_metadata: Optional[str] = None  # Technical info (file size, dimensions) - separate from user description
    
    # === NEW: Structured data fields for contextual search ===
    vendor: Optional[str] = None  # Normalized vendor name (e.g., "google", "t-mobile")
    currency: Optional[str] = None  # ISO currency code ("USD", "EUR", "CZK")
    amounts_cents: List[int] = Field(default_factory=list)  # Money amounts in cents [930, 1500]
    invoice_no: Optional[str] = None  # Invoice number
    entities: List[str] = Field(default_factory=list)  # Named entities ["t-mobile", "contract"]
    keywords: List[str] = Field(default_factory=list)  # Exact searchable values (IDs, emails, phone numbers)
    dates: List[datetime] = Field(default_factory=list)  # Extracted dates
    
    # === NEW: Image-specific fields ===
    image_labels: List[str] = Field(default_factory=list)  # ["london", "bridge", "cityscape"]
    ocr_text: Optional[str] = None  # Extracted text from images
    image_width: Optional[int] = None
    image_height: Optional[int] = None
    
    # === NEW: CSV-specific fields ===
    csv_schema: Optional[Dict[str, Any]] = None  # {"columns": ["date", "amount", "vendor"]}
    csv_stats: Optional[Dict[str, Any]] = None  # {"rowCount": 123, "minAmount": 100}
    
    # === Multi-modal embeddings ===
    text_embedding: Optional[List[float]] = None  # Text semantic vector (1536 dims)
    image_embedding: Optional[List[float]] = None  # Image semantic vector (768 dims)
    embeddings_model: Optional[str] = None  # Model used for embeddings
    embeddings_created_at: Optional[datetime] = None
    embeddings_chunk_count: Optional[int] = None
    
    # === Legacy embeddings field (deprecated, use text_embedding) ===
    embeddings: Optional[List[float]] = None  # For backward compatibility
    
    # === For chunked documents ===
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
    
    # === Metadata ===
    metadata: ResourceMetadata = Field(default_factory=ResourceMetadata)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "resources"
        indexes = [
            "uri",
            "name",
            "resource_type",
            "owner_id",
            "company_id",
            "file_type",
            "vendor",
            "currency",
            "created_at",
            [("resource_type", 1), ("created_at", -1)],
            [("owner_id", 1), ("created_at", -1)],
            [("company_id", 1), ("created_at", -1)],
            [("file_type", 1), ("created_at", -1)],
            [("vendor", 1), ("created_at", -1)],
            [("currency", 1), ("amounts_cents", 1)],
            [("dates", 1), ("created_at", -1)],
        ]


class ResourceChunk(Document):
    """Chunk/part of a larger resource (PDF pages, CSV rows, image regions).
    
    Enhanced with compound search metadata for intelligent hybrid search:
    - Structured data extraction (money, IDs, vendors, entities)
    - Image caption embeddings for visual search
    - Deep-link support (page/row/bbox coordinates)
    """
    
    # === Parent reference ===
    parent_id: Indexed(str)  # Reference to Resource._id
    resource_uri: Optional[str] = None  # For easy lookup
    
    # === Chunk identification ===
    chunk_type: str  # "text", "page", "row", "cell", "region", "image"
    chunk_index: int  # Sequential index within parent
    
    # === Location metadata (for deep-linking) ===
    page_number: Optional[int] = None  # For PDFs (renamed from page_number for clarity)
    row_index: Optional[int] = None  # For CSVs
    col_index: Optional[int] = None  # For CSV cells
    bbox: Optional[List[float]] = None  # [x, y, width, height] for images/PDFs
    
    # === Content ===
    text: Optional[str] = None  # Extracted text (was 'content' in old schema)
    content: Optional[str] = None  # Alias for backward compatibility
    
    # === NEW: Normalized text for diacritic-insensitive search ===
    text_normalized: Optional[str] = None  # Text with diacritics removed
    ocr_text_normalized: Optional[str] = None  # OCR text with diacritics removed
    searchable_text: Optional[str] = None  # Combined normalized text from all sources
    image_description: Optional[str] = None  # AI-generated image description (LLaVA)
    
    # === Multi-modal embeddings ===
    text_embedding: Optional[List[float]] = None  # Text semantic vector (768 dims with nomic-embed-text)
    image_embedding: Optional[List[float]] = None  # Image semantic vector (future: for actual images)
    caption_embedding: Optional[List[float]] = None  # Caption+OCR text embedding (768 dims, same model)
    embedding: Optional[List[float]] = None  # Alias for backward compatibility (points to text_embedding)
    
    # === Structured fields (inherited from parent for search) ===
    company_id: str  # ACL - copied from parent
    owner_id: str  # Owner - copied from parent
    file_type: Optional[str] = None  # "pdf", "csv", "txt", "image" - copied from parent
    mime_type: Optional[str] = None  # MIME type (e.g., "application/pdf", "image/jpeg")
    file_name: Optional[str] = None  # Filename - copied from parent
    
    # === Compound search metadata (extracted at ingest) ===
    # Exact match fields
    keywords: List[str] = Field(default_factory=list)  # IDs, emails, IBANs, long numbers (exact phrase match)
    vendor: Optional[str] = None  # Normalized vendor/company name (lowercase)
    
    # Numeric/structured fields
    currency: Optional[str] = None  # ISO currency ("USD", "EUR", "CZK")
    amounts_cents: List[int] = Field(default_factory=list)  # Monetary amounts in cents for range queries
    dates: List[datetime] = Field(default_factory=list)  # Extracted dates
    
    # Entity recognition
    entities: List[str] = Field(default_factory=list)  # Named entities (people, orgs, locations)
    
    # === Image search fields (Ollama-only with LLaVA + Tesseract) ===
    caption: Optional[str] = None  # AI-generated image caption (from LLaVA/Moondream)
    image_labels: List[str] = Field(default_factory=list)  # Tags extracted from caption (e.g., ["london", "bridge"])
    ocr_text: Optional[str] = None  # Text extracted from image via Tesseract
    
    # === Metadata ===
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "resource_chunks"
        indexes = [
            "parent_id",
            "company_id",
            "owner_id",
            "chunk_type",
            "file_type",
            "page_number",
            "row_index",
            "created_at",
            [("parent_id", 1), ("chunk_index", 1)],
            [("company_id", 1), ("created_at", -1)],
            [("chunk_type", 1), ("created_at", -1)],
            [("currency", 1), ("amounts_cents", 1)],
            [("dates", 1)],
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
    messages: List[Dict[str, Any]] = Field(default_factory=list)  # Store messages directly
    status: str = "active"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)  # total_time, total_tokens, avg_tokens_per_second, etc.
    
    class Settings:
        name = "conversations"
        indexes = [
            "user_id",
            "title",
            "status",
            "created_at",
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
