"""AI MCP Toolkit - Text processing agents with MCP protocol support."""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .server.mcp_server import MCPServer
from .agents import *
from .utils import *

__all__ = [
    "MCPServer",
    "__version__",
    "__author__",
    "__email__",
]
