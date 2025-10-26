"""AI MCP Toolkit Models Module."""

from .ollama_client import OllamaClient, ChatMessage, CompletionResponse, OllamaModel
from .database import DatabaseManager, db_manager, get_database, get_mongodb_client, get_redis_client
from .documents import (
    Resource, Prompt, Message, Conversation, AgentState, Workflow,
    SharedContext, Event, CacheEntry,
    ResourceType, MessageRole, WorkflowStatus, AgentStatus
)
from .mcp_types import (
    MCPError, MCPErrorCode, Resource as MCPResource, Prompt as MCPPrompt,
    Message as MCPMessage, Tool, AgentMessage, Workflow as MCPWorkflow,
    SharedContext as MCPSharedContext, Event as MCPEvent, Pipeline,
    MemoryEntry, MCPResponse, HealthCheckResult
)

__all__ = [
    # Database
    "DatabaseManager", "db_manager", "get_database", "get_mongodb_client", "get_redis_client",
    
    # Documents
    "Resource", "Prompt", "Message", "Conversation", "AgentState", "Workflow",
    "SharedContext", "Event", "CacheEntry",
    "ResourceType", "MessageRole", "WorkflowStatus", "AgentStatus",
    
    # MCP Types
    "MCPError", "MCPErrorCode", "MCPResource", "MCPPrompt", "MCPMessage",
    "Tool", "AgentMessage", "MCPWorkflow", "MCPSharedContext", "MCPEvent",
    "Pipeline", "MemoryEntry", "MCPResponse", "HealthCheckResult",
    
    # Existing
    "OllamaClient", "ChatMessage", "CompletionResponse", "OllamaModel"
]
