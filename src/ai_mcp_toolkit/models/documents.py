"""Beanie Document models for AI MCP Toolkit."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from beanie import Document, PydanticObjectId
from pydantic import Field, EmailStr, BaseModel, field_validator, ConfigDict


# Enums
class UserRole(str, Enum):
    """User role enumeration."""
    USER = "USER"
    ADMIN = "ADMIN"


class ResourceType(str, Enum):
    """Resource type enumeration."""
    FILE = "file"
    URL = "url"
    TEXT = "text"
    SNIPPET = "snippet"


# Pydantic models for nested structures
class ResourceMetadata(BaseModel):
    """Metadata for resources."""
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    file_type: Optional[str] = None
    mime_type: Optional[str] = None
    vendor: Optional[str] = None
    summary: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    entities: List[str] = Field(default_factory=list)
    amounts_cents: List[int] = Field(default_factory=list)
    currency: Optional[str] = None
    technical_metadata: Dict[str, Any] = Field(default_factory=dict)
    file_storage: Optional[Dict[str, Any]] = None


class PromptArgument(BaseModel):
    """Argument definition for prompt templates."""
    name: str
    description: str
    required: bool = False
    default_value: Optional[str] = None


# Document Models
class User(Document):
    """User document model."""
    model_config = ConfigDict(
        extra="allow",
        use_enum_values=True,
        validate_assignment=True
    )
    
    username: str = Field(..., unique=True)
    email: EmailStr = Field(..., unique=True)
    password_hash: str
    full_name: Optional[str] = None
    role: UserRole = UserRole.USER
    is_active: bool = True
    last_login: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    preferences: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @field_validator('role', mode='before')
    @classmethod
    def validate_role(cls, v):
        """Convert role string to enum, handling lowercase values."""
        if isinstance(v, str):
            # Convert lowercase to uppercase
            v_upper = v.upper()
            try:
                return UserRole(v_upper)
            except ValueError:
                # If not a valid enum value, default to USER
                return UserRole.USER
        return v
    
    class Settings:
        name = "users"
        indexes = ["username", "email"]


class Session(Document):
    """User session document model."""
    user_id: PydanticObjectId = Field(..., alias="user_id")
    session_id: str = Field(..., unique=True)
    expires_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    is_active: bool = True
    last_activity: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "sessions"
        indexes = ["session_id", "user_id", "expires_at"]


class AuditLog(Document):
    """Audit log document model."""
    user_id: Optional[PydanticObjectId] = None
    username: Optional[str] = None
    action: str
    method: str
    endpoint: str
    status_code: int
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    request_data: Optional[Dict[str, Any]] = None
    response_data: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "audit_logs"
        indexes = ["user_id", "action", "timestamp"]


class Resource(Document):
    """Resource document model."""
    uri: str = Field(..., unique=True)
    name: str
    description: Optional[str] = None
    mime_type: Optional[str] = None
    resource_type: ResourceType = ResourceType.FILE
    owner_id: PydanticObjectId
    company_id: PydanticObjectId
    metadata: ResourceMetadata = Field(default_factory=ResourceMetadata)
    
    # Content and embeddings
    content: Optional[str] = None
    text_embedding: Optional[List[float]] = None
    image_embedding: Optional[List[float]] = None
    embeddings: Optional[List[float]] = None
    embeddings_model: Optional[str] = None
    embeddings_created_at: Optional[datetime] = None
    embeddings_chunk_count: Optional[int] = None
    chunks: Optional[List[Dict[str, Any]]] = None
    
    # File information
    file_id: Optional[str] = None
    file_name: Optional[str] = None
    file_type: Optional[str] = None
    file_path: Optional[str] = None
    file_data_base64: Optional[str] = None
    size_bytes: Optional[int] = None
    
    # Extracted metadata
    vendor: Optional[str] = None
    summary: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    entities: List[str] = Field(default_factory=list)
    amounts_cents: List[int] = Field(default_factory=list)
    currency: Optional[str] = None
    dates: List[Any] = Field(default_factory=list)  # Can be strings or datetime objects
    invoice_no: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    
    # OCR and image data
    ocr_text: Optional[str] = None
    image_labels: List[str] = Field(default_factory=list)
    image_width: Optional[int] = None
    image_height: Optional[int] = None
    
    # CSV data
    csv_schema: Optional[Dict[str, Any]] = None
    csv_stats: Optional[Dict[str, Any]] = None
    
    # Technical metadata
    technical_metadata: Optional[Dict[str, Any]] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "resources"
        indexes = [
            "uri",
            "owner_id",
            "company_id",
            [("owner_id", 1), ("resource_type", 1)],
            [("company_id", 1), ("created_at", -1)]
        ]
    


class ResourceChunk(Document):
    """Resource chunk document model for search."""
    parent_id: PydanticObjectId  # Reference to Resource
    owner_id: PydanticObjectId
    company_id: PydanticObjectId
    chunk_type: str = Field(default="text")  # text, image, csv_row
    chunk_index: int = 0
    
    # Text content
    text: Optional[str] = None
    text_normalized: Optional[str] = None
    searchable_text: Optional[str] = None
    
    # OCR and image content
    ocr_text: Optional[str] = None
    ocr_text_normalized: Optional[str] = None
    caption: Optional[str] = None
    image_labels: List[str] = Field(default_factory=list)
    image_description: Optional[str] = None
    
    # Embeddings
    text_embedding: Optional[List[float]] = None
    caption_embedding: Optional[List[float]] = None
    embedding: Optional[List[float]] = None  # Alias for text_embedding
    
    # Metadata for compound search
    keywords: List[str] = Field(default_factory=list)
    vendor: Optional[str] = None
    entities: List[str] = Field(default_factory=list)
    currency: Optional[str] = None
    amounts_cents: List[int] = Field(default_factory=list)
    
    # Deep linking
    page_number: Optional[int] = None
    row_index: Optional[int] = None
    col_index: Optional[int] = None
    
    # File metadata
    file_name: Optional[str] = None
    file_type: Optional[str] = None
    mime_type: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "resource_chunks"
        indexes = [
            "parent_id",
            "owner_id",
            "company_id",
            [("parent_id", 1), ("chunk_index", 1)],
            [("company_id", 1), ("created_at", -1)]
        ]
    


class Conversation(Document):
    """Conversation document model."""
    user_id: PydanticObjectId
    title: str
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    status: str = Field(default="active")  # active, archived, deleted
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "conversations"
        indexes = [
            "user_id",
            [("user_id", 1), ("created_at", -1)]
        ]


class Message(Document):
    """Message document model (for future use)."""
    conversation_id: PydanticObjectId
    role: str  # user, assistant
    content: str
    model: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "messages"
        indexes = [
            "conversation_id",
            [("conversation_id", 1), ("timestamp", 1)]
        ]


class Prompt(Document):
    """Prompt template document model."""
    name: str
    description: Optional[str] = None
    arguments: List[PromptArgument] = Field(default_factory=list)
    template: str
    owner_id: Optional[PydanticObjectId] = None
    is_public: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "prompts"
        indexes = [
            "owner_id",
            "name",
            "is_public"
        ]

