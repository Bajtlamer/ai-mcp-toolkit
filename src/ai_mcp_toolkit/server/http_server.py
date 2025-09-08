"""HTTP server wrapper for MCP functionality."""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .mcp_server import MCPServer
from ..utils.config import Config
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ToolRequest(BaseModel):
    """Request model for tool execution."""
    name: str
    arguments: Dict[str, Any]


class ToolResponse(BaseModel):
    """Response model for tool execution."""
    result: str
    success: bool = True
    error: Optional[str] = None


class ServerStatus(BaseModel):
    """Server status response model."""
    status: str
    version: str
    agents_count: int
    total_tools: int
    agents: Dict[str, Any]


class HTTPServer:
    """HTTP server that wraps MCP functionality."""

    def __init__(self, config: Optional[Config] = None):
        """Initialize the HTTP server with MCP backend."""
        self.config = config or Config()
        self.mcp_server = None
        self.app = None
        self.logger = get_logger(__name__, level=self.config.log_level)

    async def initialize(self):
        """Initialize the MCP server and create FastAPI app."""
        try:
            # Initialize MCP server
            self.mcp_server = MCPServer(self.config)
            self.logger.info("MCP server initialized successfully")
            
            # Create FastAPI app
            self.app = await self._create_app()
            self.logger.info("FastAPI app created successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing HTTP server: {e}", exc_info=True)
            raise

    async def _create_app(self) -> FastAPI:
        """Create and configure FastAPI application."""
        
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            """Application lifespan manager."""
            self.logger.info("Starting HTTP server")
            yield
            self.logger.info("Shutting down HTTP server")

        app = FastAPI(
            title="AI MCP Toolkit HTTP Server",
            description="HTTP API wrapper for MCP-based text processing agents",
            version="1.0.0",
            lifespan=lifespan
        )

        # Add CORS middleware
        if self.config.enable_cors:
            app.add_middleware(
                CORSMiddleware,
                allow_origins=self.config.cors_origins.split(",") if isinstance(self.config.cors_origins, str) else ["*"],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )

        # Health check endpoint
        @app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {"status": "healthy", "timestamp": asyncio.get_event_loop().time()}

        # List available tools
        @app.get("/tools", response_model=List[Dict[str, Any]])
        async def list_tools():
            """List all available tools."""
            try:
                if not self.mcp_server:
                    raise HTTPException(status_code=500, detail="MCP server not initialized")
                
                all_tools = []
                for agent_info in self.mcp_server.agents.values():
                    for tool in agent_info.tools:
                        all_tools.append({
                            "name": tool.name,
                            "description": tool.description,
                            "agent": agent_info.name,
                            "input_schema": tool.inputSchema if hasattr(tool, 'inputSchema') else {}
                        })
                
                self.logger.info(f"Listed {len(all_tools)} tools")
                return all_tools
                
            except Exception as e:
                self.logger.error(f"Error listing tools: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))

        # Execute a tool
        @app.post("/tools/execute", response_model=ToolResponse)
        async def execute_tool(request: ToolRequest):
            """Execute a specific tool."""
            try:
                if not self.mcp_server:
                    raise HTTPException(status_code=500, detail="MCP server not initialized")
                
                self.logger.info(f"Executing tool: {request.name} with args: {request.arguments}")
                
                # Find the agent that owns this tool
                agent_info = None
                tool = None
                
                for info in self.mcp_server.agents.values():
                    for t in info.tools:
                        if t.name == request.name:
                            agent_info = info
                            tool = t
                            break
                    if agent_info:
                        break
                
                if not agent_info:
                    raise HTTPException(status_code=404, detail=f"Tool '{request.name}' not found")
                
                # Execute the tool
                result = await agent_info.agent.execute_tool(request.name, request.arguments)
                
                self.logger.info(f"Tool {request.name} executed successfully")
                return ToolResponse(result=result, success=True)
                
            except HTTPException:
                raise
            except Exception as e:
                error_msg = f"Error executing tool '{request.name}': {str(e)}"
                self.logger.error(error_msg, exc_info=True)
                return ToolResponse(result="", success=False, error=error_msg)

        # Get server status
        @app.get("/status", response_model=ServerStatus)
        async def get_status():
            """Get server status and statistics."""
            try:
                if not self.mcp_server:
                    raise HTTPException(status_code=500, detail="MCP server not initialized")
                
                stats = self.mcp_server.get_server_stats()
                
                return ServerStatus(
                    status="running",
                    version="1.0.0",
                    agents_count=stats["agents_count"],
                    total_tools=stats["total_tools"],
                    agents=stats["agents"]
                )
                
            except Exception as e:
                self.logger.error(f"Error getting server status: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))

        # List agents
        @app.get("/agents")
        async def list_agents():
            """List all registered agents."""
            try:
                if not self.mcp_server:
                    raise HTTPException(status_code=500, detail="MCP server not initialized")
                
                agents = []
                for name, info in self.mcp_server.agents.items():
                    agents.append({
                        "name": name,
                        "description": info.description,
                        "tools_count": len(info.tools),
                        "tools": [tool.name for tool in info.tools]
                    })
                
                return {"agents": agents}
                
            except Exception as e:
                self.logger.error(f"Error listing agents: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))

        # Root endpoint with API info
        @app.get("/")
        async def root():
            """Root endpoint with API information."""
            return {
                "name": "AI MCP Toolkit HTTP Server",
                "version": "1.0.0",
                "description": "HTTP API wrapper for MCP-based text processing agents",
                "endpoints": {
                    "health": "/health",
                    "tools": "/tools",
                    "execute": "/tools/execute",
                    "status": "/status",
                    "agents": "/agents",
                    "docs": "/docs"
                }
            }

        return app

    async def start(self, host: str = "localhost", port: int = 8000):
        """Start the HTTP server."""
        try:
            if not self.app:
                await self.initialize()
            
            self.logger.info(f"Starting HTTP server on {host}:{port}")
            
            config = uvicorn.Config(
                app=self.app,
                host=host,
                port=port,
                log_level=self.config.log_level.lower(),
                access_log=True
            )
            
            server = uvicorn.Server(config)
            await server.serve()
            
        except Exception as e:
            self.logger.error(f"Error starting HTTP server: {e}", exc_info=True)
            raise

    async def stop(self):
        """Stop the HTTP server."""
        try:
            self.logger.info("Stopping HTTP server")
            if self.mcp_server:
                await self.mcp_server.stop()
        except Exception as e:
            self.logger.error(f"Error stopping server: {e}", exc_info=True)


# Convenience functions
async def create_http_server(config: Optional[Config] = None) -> HTTPServer:
    """Create and initialize HTTP server."""
    server = HTTPServer(config)
    await server.initialize()
    return server


async def run_http_server(
    host: str = "localhost", 
    port: int = 8000, 
    config: Optional[Config] = None
) -> None:
    """Run the HTTP server with the given configuration."""
    server = await create_http_server(config)
    await server.start(host, port)
