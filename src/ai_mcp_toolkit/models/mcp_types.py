"""MCP Protocol types and utilities."""

from mcp.types import (
    Resource,
    ListResourcesResult,
    ReadResourceResult,
    JSONRPCError
)

# Re-export MCP types for convenience
# Note: MCPError and MCPErrorCode don't exist in mcp.types
# Using JSONRPCError instead, or standard Python exceptions
MCPError = JSONRPCError  # Alias for compatibility
MCPErrorCode = int  # Error codes are integers

__all__ = [
    "Resource",
    "ListResourcesResult",
    "ReadResourceResult",
    "MCPError",
    "MCPErrorCode",
    "JSONRPCError"
]

