"""
ASGI application factory for running with uvicorn.

Usage:
    uvicorn ai_mcp_toolkit.main:app --reload --port 8000
"""

import asyncio
from .server.http_server import HTTPServer
from .utils.config import Config

# Create server instance
_server = None
app = None


def get_app():
    """Get or create the FastAPI app instance."""
    global _server, app
    
    if app is None:
        # Create server synchronously
        _server = HTTPServer()
        
        # Initialize and get app
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_server.initialize())
        app = _server.app
    
    return app


# Create app on module import
app = get_app()
