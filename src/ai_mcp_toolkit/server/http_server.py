"""HTTP server wrapper for MCP functionality."""

import asyncio
import json
import logging
import time
import uuid
import aiohttp
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Union

from .mcp_server import MCPServer
from ..utils.config import Config
from ..utils.logger import get_logger
from ..utils.gpu_monitor import get_gpu_monitor, check_gpu_health

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


class ChatMessage(BaseModel):
    """Chat message model."""
    role: str  # "user", "assistant", "system"
    content: str


class ChatCompletionRequest(BaseModel):
    """Chat completion request model."""
    messages: List[ChatMessage]
    model: Optional[str] = "qwen2.5:14b"
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2000
    stream: Optional[bool] = False


class ChatCompletionResponse(BaseModel):
    """Chat completion response model."""
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Optional[Dict[str, Union[int, float]]] = None


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

        # GPU health check endpoint
        @app.get("/gpu/health")
        async def gpu_health():
            """Get GPU health and status information."""
            try:
                health_info = await check_gpu_health()
                return health_info
            except Exception as e:
                self.logger.error(f"Error checking GPU health: {e}", exc_info=True)
                return {"error": str(e), "gpu_available": False}

        # GPU performance metrics endpoint
        @app.get("/gpu/metrics")
        async def gpu_metrics():
            """Get current GPU performance metrics."""
            try:
                gpu_monitor = get_gpu_monitor()
                await gpu_monitor.update_metrics()
                
                return {
                    "performance_summary": gpu_monitor.get_performance_summary(),
                    "current_metrics": {
                        "timestamp": gpu_monitor.current_metrics.timestamp,
                        "gpu_utilization": gpu_monitor.current_metrics.gpu_utilization,
                        "gpu_memory_usage": gpu_monitor.current_metrics.gpu_memory_usage,
                        "ollama_memory_usage": gpu_monitor.current_metrics.ollama_memory_usage,
                        "inference_speed": gpu_monitor.current_metrics.inference_speed,
                        "total_requests": gpu_monitor.current_metrics.request_count,
                        "total_tokens_processed": gpu_monitor.current_metrics.total_tokens_processed
                    }
                }
            except Exception as e:
                self.logger.error(f"Error getting GPU metrics: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))

        # GPU optimization recommendations endpoint
        @app.get("/gpu/recommendations")
        async def gpu_recommendations():
            """Get GPU optimization recommendations."""
            try:
                gpu_monitor = get_gpu_monitor()
                recommendations = await gpu_monitor.get_optimization_recommendations()
                
                return {
                    "recommendations": recommendations,
                    "timestamp": time.time()
                }
            except Exception as e:
                self.logger.error(f"Error getting GPU recommendations: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))

        # Chat completions endpoint
        @app.post("/chat/completions", response_model=ChatCompletionResponse)
        async def chat_completions(request: ChatCompletionRequest):
            """Handle chat completion requests via Ollama."""
            try:
                start_time = time.time()
                self.logger.info(f"Processing chat completion request with {len(request.messages)} messages")
                
                # Build the prompt from messages
                prompt_parts = []
                for message in request.messages:
                    if message.role == "user":
                        prompt_parts.append(f"Human: {message.content}")
                    elif message.role == "assistant":
                        prompt_parts.append(f"Assistant: {message.content}")
                    elif message.role == "system":
                        prompt_parts.append(f"System: {message.content}")
                
                # Add final assistant prompt
                prompt = "\n\n".join(prompt_parts) + "\n\nAssistant:"
                
                # Make request to Ollama
                ollama_url = self.config.get_ollama_url()
                async with aiohttp.ClientSession() as session:
                    ollama_request = {
                        "model": request.model or self.config.ollama_model,
                        "prompt": prompt,
                        "stream": False,
                        "keep_alive": "30m",  # Keep model loaded for 30 minutes
                        "options": {
                            "temperature": request.temperature or self.config.temperature,
                            "num_predict": request.max_tokens or self.config.max_tokens
                        }
                    }
                    
                    async with session.post(
                        f"{ollama_url}/api/generate",
                        json=ollama_request,
                        timeout=aiohttp.ClientTimeout(total=120)
                    ) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            self.logger.error(f"Ollama API error: {response.status} - {error_text}")
                            raise HTTPException(
                                status_code=502, 
                                detail=f"Ollama API error: {response.status}"
                            )
                        
                        result = await response.json()
                        
                        # Calculate timing metrics
                        end_time = time.time()
                        total_time = end_time - start_time
                        
                        # Extract metrics from Ollama response
                        prompt_eval_count = result.get("prompt_eval_count", 0)
                        eval_count = result.get("eval_count", 0)
                        prompt_eval_duration = result.get("prompt_eval_duration", 0) / 1e9  # Convert to seconds
                        eval_duration = result.get("eval_duration", 0) / 1e9  # Convert to seconds
                        
                        # Calculate tokens per second
                        tokens_per_second = eval_count / eval_duration if eval_duration > 0 else 0
                        
                        # Format response in OpenAI-compatible format
                        response_id = str(uuid.uuid4())
                        created_time = int(time.time())
                        
                        chat_response = ChatCompletionResponse(
                            id=response_id,
                            created=created_time,
                            model=request.model or self.config.ollama_model,
                            choices=[
                                {
                                    "index": 0,
                                    "message": {
                                        "role": "assistant",
                                        "content": result.get("response", "")
                                    },
                                    "finish_reason": "stop"
                                }
                            ],
                            usage={
                                "prompt_tokens": int(prompt_eval_count),
                                "completion_tokens": int(eval_count),
                                "total_tokens": int(prompt_eval_count + eval_count),
                                "prompt_eval_duration": round(prompt_eval_duration, 3),
                                "eval_duration": round(eval_duration, 3),
                                "total_duration": round(total_time, 3),
                                "tokens_per_second": round(tokens_per_second, 2)
                            }
                        )
                        
                        self.logger.info(
                            f"Chat completion successful: {len(result.get('response', ''))} chars, "
                            f"{eval_count} tokens in {total_time:.2f}s ({tokens_per_second:.1f} t/s)"
                        )
                        return chat_response
                        
            except aiohttp.ClientError as e:
                self.logger.error(f"Error connecting to Ollama: {e}")
                raise HTTPException(status_code=502, detail="Failed to connect to Ollama service")
            except Exception as e:
                self.logger.error(f"Error processing chat completion: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))

        # Root endpoint with API info
        @app.get("/")
        async def root():
            """Root endpoint with API information."""
            return {
                "name": "AI MCP Toolkit HTTP Server",
                "version": "1.0.0",
                "description": "HTTP API wrapper for MCP-based text processing agents with GPU acceleration",
                "endpoints": {
                    "health": "/health",
                    "tools": "/tools",
                    "execute": "/tools/execute",
                    "status": "/status",
                    "agents": "/agents",
                    "chat": "/chat/completions",
                    "gpu_health": "/gpu/health",
                    "gpu_metrics": "/gpu/metrics", 
                    "gpu_recommendations": "/gpu/recommendations",
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
