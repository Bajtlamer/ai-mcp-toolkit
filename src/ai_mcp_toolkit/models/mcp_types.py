"""MCP protocol types and data structures."""

from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field as PydanticField
from datetime import datetime
from enum import Enum


class MCPErrorCode(str, Enum):
    """MCP error codes."""
    INVALID_REQUEST = "invalid_request"
    METHOD_NOT_FOUND = "method_not_found"
    INVALID_PARAMS = "invalid_params"
    INTERNAL_ERROR = "internal_error"
    RESOURCE_NOT_FOUND = "resource_not_found"
    PROMPT_NOT_FOUND = "prompt_not_found"
    MESSAGE_NOT_FOUND = "message_not_found"


class MCPError(BaseModel):
    """MCP error response."""
    code: MCPErrorCode
    message: str
    data: Optional[Dict[str, Any]] = None


# Resource types
class Resource(BaseModel):
    """MCP Resource type."""
    uri: str
    name: str
    description: str
    mimeType: Optional[str] = None


class ListResourcesResult(BaseModel):
    """Result of list_resources request."""
    resources: List[Resource]


class ReadResourceResult(BaseModel):
    """Result of read_resource request."""
    contents: List[Dict[str, Any]]


# Prompt types
class PromptArgument(BaseModel):
    """Prompt argument definition."""
    name: str
    description: str
    required: bool = True


class Prompt(BaseModel):
    """MCP Prompt type."""
    name: str
    description: str
    arguments: List[PromptArgument] = PydanticField(default_factory=list)


class ListPromptsResult(BaseModel):
    """Result of list_prompts request."""
    prompts: List[Prompt]


class GetPromptResult(BaseModel):
    """Result of get_prompt request."""
    description: str
    messages: List[Dict[str, Any]]


# Message types
class Message(BaseModel):
    """MCP Message type."""
    role: str
    content: Dict[str, Any]
    timestamp: Optional[datetime] = None


class ListMessagesResult(BaseModel):
    """Result of list_messages request."""
    messages: List[Message]


class SendMessageResult(BaseModel):
    """Result of send_message request."""
    message: Message


# Tool types
class Tool(BaseModel):
    """MCP Tool type."""
    name: str
    description: str
    inputSchema: Dict[str, Any]


class ListToolsResult(BaseModel):
    """Result of list_tools request."""
    tools: List[Tool]


class CallToolResult(BaseModel):
    """Result of call_tool request."""
    content: List[Dict[str, Any]]
    isError: bool = False


# Agent communication types
class AgentMessage(BaseModel):
    """Message for inter-agent communication."""
    from_agent: str
    to_agent: str
    message_type: str
    content: Dict[str, Any]
    timestamp: datetime = PydanticField(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = None


class AgentCapability(BaseModel):
    """Agent capability definition."""
    name: str
    description: str
    input_types: List[str] = PydanticField(default_factory=list)
    output_types: List[str] = PydanticField(default_factory=list)
    parameters: Dict[str, Any] = PydanticField(default_factory=dict)


class AgentRegistration(BaseModel):
    """Agent registration information."""
    agent_id: str
    agent_name: str
    capabilities: List[AgentCapability]
    status: str = "idle"
    last_heartbeat: datetime = PydanticField(default_factory=datetime.utcnow)


# Workflow types
class WorkflowStep(BaseModel):
    """Workflow step definition."""
    step_id: str
    agent_id: str
    input_data: Dict[str, Any] = PydanticField(default_factory=dict)
    output_data: Dict[str, Any] = PydanticField(default_factory=dict)
    status: str = "pending"
    dependencies: List[str] = PydanticField(default_factory=list)


class Workflow(BaseModel):
    """Workflow definition."""
    workflow_id: str
    name: str
    description: str
    steps: List[WorkflowStep]
    status: str = "pending"
    created_at: datetime = PydanticField(default_factory=datetime.utcnow)


class WorkflowExecutionResult(BaseModel):
    """Result of workflow execution."""
    workflow_id: str
    status: str
    results: Dict[str, Any] = PydanticField(default_factory=dict)
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


# Shared context types
class SharedContext(BaseModel):
    """Shared context for agent cooperation."""
    context_id: str
    name: str
    description: str
    data: Dict[str, Any] = PydanticField(default_factory=dict)
    access_level: str = "public"
    created_by: str
    created_at: datetime = PydanticField(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None


class ContextUpdate(BaseModel):
    """Context update notification."""
    context_id: str
    updates: Dict[str, Any]
    updated_by: str
    timestamp: datetime = PydanticField(default_factory=datetime.utcnow)


# Event types
class Event(BaseModel):
    """Event for event-driven architecture."""
    event_id: str
    event_type: str
    source: str
    data: Dict[str, Any] = PydanticField(default_factory=dict)
    timestamp: datetime = PydanticField(default_factory=datetime.utcnow)


class EventSubscription(BaseModel):
    """Event subscription."""
    subscriber_id: str
    event_types: List[str]
    callback_url: Optional[str] = None


# Pipeline types
class PipelineStep(BaseModel):
    """Pipeline processing step."""
    step_id: str
    agent_id: str
    input_mapping: Dict[str, str] = PydanticField(default_factory=dict)
    output_mapping: Dict[str, str] = PydanticField(default_factory=dict)
    parameters: Dict[str, Any] = PydanticField(default_factory=dict)


class Pipeline(BaseModel):
    """Pipeline definition."""
    pipeline_id: str
    name: str
    description: str
    steps: List[PipelineStep]
    status: str = "inactive"
    created_at: datetime = PydanticField(default_factory=datetime.utcnow)


class PipelineExecutionResult(BaseModel):
    """Result of pipeline execution."""
    pipeline_id: str
    execution_id: str
    status: str
    results: Dict[str, Any] = PydanticField(default_factory=dict)
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


# Memory types
class MemoryEntry(BaseModel):
    """Memory entry for persistent storage."""
    memory_id: str
    key: str
    value: Any
    metadata: Dict[str, Any] = PydanticField(default_factory=dict)
    created_at: datetime = PydanticField(default_factory=datetime.utcnow)
    accessed_at: datetime = PydanticField(default_factory=datetime.utcnow)
    access_count: int = 0


class MemoryQuery(BaseModel):
    """Memory query for retrieval."""
    query: str
    filters: Dict[str, Any] = PydanticField(default_factory=dict)
    limit: int = 100
    offset: int = 0


class MemorySearchResult(BaseModel):
    """Result of memory search."""
    entries: List[MemoryEntry]
    total_count: int
    query: str


# Configuration types
class MCPConfig(BaseModel):
    """MCP server configuration."""
    server_name: str
    server_version: str
    capabilities: Dict[str, Any] = PydanticField(default_factory=dict)
    resources: List[str] = PydanticField(default_factory=list)
    prompts: List[str] = PydanticField(default_factory=list)
    tools: List[str] = PydanticField(default_factory=list)


# Response types
class MCPResponse(BaseModel):
    """Generic MCP response."""
    success: bool
    data: Optional[Any] = None
    error: Optional[MCPError] = None
    timestamp: datetime = PydanticField(default_factory=datetime.utcnow)


class HealthCheckResult(BaseModel):
    """Health check result."""
    status: str
    services: Dict[str, bool] = PydanticField(default_factory=dict)
    timestamp: datetime = PydanticField(default_factory=datetime.utcnow)
    version: str
    uptime: float
