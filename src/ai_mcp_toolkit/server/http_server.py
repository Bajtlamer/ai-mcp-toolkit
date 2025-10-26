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
from fastapi import FastAPI, HTTPException, Request, Response, Cookie, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from typing import Union

from .mcp_server import MCPServer
from ..utils.config import Config
from ..utils.logger import get_logger
from ..utils.gpu_monitor import get_gpu_monitor, check_gpu_health
from ..managers.resource_manager import ResourceManager
from ..managers.user_manager import UserManager
from ..managers.session_manager import SessionManager
from ..models.documents import ResourceType, User, UserRole
from ..models.database import db_manager
from ..utils.audit import AuditLogger

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


class ResourceCreate(BaseModel):
    """Request model for creating a resource."""
    uri: str
    name: str
    description: str
    mime_type: str
    resource_type: str
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ResourceUpdate(BaseModel):
    """Request model for updating a resource."""
    name: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ResourceResponse(BaseModel):
    """Response model for a resource."""
    uri: str
    name: str
    description: str
    mime_type: str
    resource_type: str
    content: Optional[str] = None
    created_at: str
    updated_at: str


# Authentication models
class RegisterRequest(BaseModel):
    """Request model for user registration."""
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class LoginRequest(BaseModel):
    """Request model for user login."""
    username: str
    password: str


class UserResponse(BaseModel):
    """Response model for user data."""
    id: str
    username: str
    email: str
    full_name: Optional[str] = None
    role: str
    is_active: bool
    created_at: str
    last_login: Optional[str] = None


class HTTPServer:
    """HTTP server that wraps MCP functionality."""

    def __init__(self, config: Optional[Config] = None):
        """Initialize the HTTP server with MCP backend."""
        self.config = config or Config()
        self.mcp_server = None
        self.resource_manager = ResourceManager()
        self.user_manager = UserManager()
        self.session_manager = SessionManager()
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
            
            # Initialize database connections
            try:
                self.logger.info("Connecting to databases...")
                await db_manager.connect()
                self.logger.info("Database connections established")
            except Exception as e:
                self.logger.error(f"Failed to connect to databases: {e}", exc_info=True)
                raise
            
            yield
            
            # Cleanup: disconnect from databases
            self.logger.info("Shutting down HTTP server")
            try:
                await db_manager.disconnect()
                self.logger.info("Database connections closed")
            except Exception as e:
                self.logger.error(f"Error closing databases: {e}", exc_info=True)

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
        
        # Authentication dependency
        async def get_current_user(
            request: Request,
            session_id: Optional[str] = Cookie(None, alias="session_id")
        ) -> Optional[User]:
            """Get current authenticated user from session cookie."""
            if not session_id:
                return None
            
            user = await self.session_manager.get_user_from_session(session_id)
            return user
        
        async def require_auth(
            user: Optional[User] = Depends(get_current_user)
        ) -> User:
            """Require authentication (raise 401 if not authenticated)."""
            if not user:
                raise HTTPException(
                    status_code=401,
                    detail="Authentication required"
                )
            return user
        
        async def require_admin(
            user: User = Depends(require_auth)
        ) -> User:
            """Require admin role (raise 403 if not admin)."""
            if user.role != UserRole.ADMIN:
                raise HTTPException(
                    status_code=403,
                    detail="Admin access required"
                )
            return user

        # Authentication endpoints
        @app.post("/auth/register", response_model=UserResponse)
        async def register(request: RegisterRequest):
            """Register a new user."""
            try:
                user = await self.user_manager.register(
                    username=request.username,
                    email=request.email,
                    password=request.password,
                    full_name=request.full_name
                )
                
                self.logger.info(f"User registered: {user.username}")
                
                return UserResponse(
                    id=str(user.id),
                    username=user.username,
                    email=user.email,
                    full_name=user.full_name,
                    role=user.role.value,
                    is_active=user.is_active,
                    created_at=user.created_at.isoformat(),
                    last_login=user.last_login.isoformat() if user.last_login else None
                )
                
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                self.logger.error(f"Error during registration: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail="Registration failed")
        
        @app.post("/auth/login")
        async def login(request_data: LoginRequest, request: Request, response: Response):
            """Login and create session."""
            try:
                # Authenticate user
                user = await self.user_manager.authenticate(
                    username=request_data.username,
                    password=request_data.password
                )
                
                if not user:
                    raise HTTPException(
                        status_code=401,
                        detail="Invalid username or password"
                    )
                
                # Create session
                client_ip = request.client.host if request.client else None
                user_agent = request.headers.get("user-agent")
                
                session = await self.session_manager.create_session(
                    user_id=str(user.id),
                    ip_address=client_ip,
                    user_agent=user_agent
                )
                
                # Set HTTP-only cookie
                response.set_cookie(
                    key="session_id",
                    value=session.session_id,
                    httponly=True,
                    secure=False,  # Set to True in production with HTTPS
                    samesite="lax",
                    max_age=86400  # 24 hours
                )
                
                self.logger.info(f"User logged in: {user.username}")
                
                return {
                    "message": "Login successful",
                    "user": UserResponse(
                        id=str(user.id),
                        username=user.username,
                        email=user.email,
                        full_name=user.full_name,
                        role=user.role.value,
                        is_active=user.is_active,
                        created_at=user.created_at.isoformat(),
                        last_login=user.last_login.isoformat() if user.last_login else None
                    )
                }
                
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Error during login: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail="Login failed")
        
        @app.post("/auth/logout")
        async def logout(
            response: Response,
            session_id: Optional[str] = Cookie(None, alias="session_id")
        ):
            """Logout and delete session."""
            if session_id:
                await self.session_manager.delete_session(session_id)
            
            # Clear cookie
            response.delete_cookie(key="session_id")
            
            return {"message": "Logout successful"}
        
        @app.get("/auth/me", response_model=UserResponse)
        async def get_current_user_info(user: User = Depends(require_auth)):
            """Get current user information."""
            return UserResponse(
                id=str(user.id),
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                role=user.role.value,
                is_active=user.is_active,
                created_at=user.created_at.isoformat(),
                last_login=user.last_login.isoformat() if user.last_login else None
            )

        # Health check endpoint
        @app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {"status": "healthy", "timestamp": asyncio.get_event_loop().time()}
        
        # Database health check endpoint
        @app.get("/health/database")
        async def database_health_check():
            """Database health check endpoint."""
            try:
                health = await db_manager.health_check()
                return {
                    "status": "healthy" if health["overall"] else "unhealthy",
                    "mongodb": health["mongodb"],
                    "redis": health["redis"],
                    "timestamp": asyncio.get_event_loop().time()
                }
            except Exception as e:
                self.logger.error(f"Database health check failed: {e}", exc_info=True)
                return {
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": asyncio.get_event_loop().time()
                }

        # List available tools (requires auth)
        @app.get("/tools", response_model=List[Dict[str, Any]])
        async def list_tools(user: User = Depends(require_auth)):
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

        # Execute a tool (requires auth)
        @app.post("/tools/execute", response_model=ToolResponse)
        async def execute_tool(request: ToolRequest, user: User = Depends(require_auth)):
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

        # Get server status (requires auth)
        @app.get("/status", response_model=ServerStatus)
        async def get_status(user: User = Depends(require_auth)):
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

        # List agents (requires auth)
        @app.get("/agents")
        async def list_agents(user: User = Depends(require_auth)):
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

        # GPU health check endpoint (requires auth)
        @app.get("/gpu/health")
        async def gpu_health(user: User = Depends(require_auth)):
            """Get GPU health and status information."""
            try:
                health_info = await check_gpu_health()
                return health_info
            except Exception as e:
                self.logger.error(f"Error checking GPU health: {e}", exc_info=True)
                return {"error": str(e), "gpu_available": False}

        # GPU performance metrics endpoint (requires auth)
        @app.get("/gpu/metrics")
        async def gpu_metrics(user: User = Depends(require_auth)):
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

        # GPU optimization recommendations endpoint (requires auth)
        @app.get("/gpu/recommendations")
        async def gpu_recommendations(user: User = Depends(require_auth)):
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

        # Chat completions endpoint (requires auth, model selection admin-only)
        @app.post("/chat/completions", response_model=ChatCompletionResponse)
        async def chat_completions(
            request: ChatCompletionRequest,
            user: User = Depends(require_auth),
            req: Request = None
        ):
            """Handle chat completion requests via Ollama."""
            # Only admins can override the model
            if request.model and request.model != self.config.ollama_model:
                if user.role != UserRole.ADMIN:
                    raise HTTPException(
                        status_code=403,
                        detail="Only administrators can change the model"
                    )
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

        # Resource Management Endpoints (all require auth)
        
        @app.get("/resources", response_model=List[Dict[str, Any]])
        async def list_resources(
            user: User = Depends(require_auth),
            resource_type: Optional[str] = None,
            limit: int = 100,
            offset: int = 0
        ):
            """List resources (users see only their own, admins see all)."""
            try:
                # Convert resource_type string to enum if provided
                type_filter = None
                if resource_type:
                    try:
                        type_filter = ResourceType(resource_type)
                    except ValueError:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Invalid resource_type. Must be one of: {[t.value for t in ResourceType]}"
                        )
                
                result = await self.resource_manager.list_resources(
                    resource_type=type_filter,
                    limit=limit,
                    offset=offset
                )
                
                # Convert to dict format
                resources = [
                    {
                        "uri": r.uri,
                        "name": r.name,
                        "description": r.description,
                        "mimeType": r.mimeType
                    }
                    for r in result.resources
                ]
                
                self.logger.info(f"Listed {len(resources)} resources")
                return resources
                
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Error listing resources: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.get("/resources/{uri:path}", response_model=Dict[str, Any])
        async def get_resource(uri: str, user: User = Depends(require_auth)):
            """Get a specific resource by URI (ownership checked)."""
            try:
                result = await self.resource_manager.read_resource(uri)
                
                if not result.contents:
                    raise HTTPException(status_code=404, detail=f"Resource not found: {uri}")
                
                self.logger.info(f"Retrieved resource: {uri}")
                return result.contents[0]
                
            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except Exception as e:
                self.logger.error(f"Error getting resource {uri}: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.post("/resources", response_model=ResourceResponse, status_code=201)
        async def create_resource(request: ResourceCreate, user: User = Depends(require_auth)):
            """Create a new resource (owner set to current user)."""
            try:
                # Convert resource_type string to enum
                try:
                    resource_type_enum = ResourceType(request.resource_type)
                except ValueError:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid resource_type. Must be one of: {[t.value for t in ResourceType]}"
                    )
                
                resource = await self.resource_manager.create_resource(
                    uri=request.uri,
                    name=request.name,
                    description=request.description,
                    mime_type=request.mime_type,
                    resource_type=resource_type_enum,
                    content=request.content,
                    metadata=request.metadata
                )
                
                self.logger.info(f"Created resource: {resource.uri}")
                
                return ResourceResponse(
                    uri=resource.uri,
                    name=resource.name,
                    description=resource.description,
                    mime_type=resource.mime_type,
                    resource_type=resource.resource_type.value,
                    content=resource.content,
                    created_at=resource.created_at.isoformat(),
                    updated_at=resource.updated_at.isoformat()
                )
                
            except ValueError as e:
                raise HTTPException(status_code=409, detail=str(e))
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Error creating resource: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.put("/resources/{uri:path}", response_model=ResourceResponse)
        async def update_resource(uri: str, request: ResourceUpdate, user: User = Depends(require_auth)):
            """Update an existing resource (ownership checked)."""
            try:
                resource = await self.resource_manager.update_resource(
                    uri=uri,
                    name=request.name,
                    description=request.description,
                    content=request.content,
                    metadata=request.metadata
                )
                
                self.logger.info(f"Updated resource: {uri}")
                
                return ResourceResponse(
                    uri=resource.uri,
                    name=resource.name,
                    description=resource.description,
                    mime_type=resource.mime_type,
                    resource_type=resource.resource_type.value,
                    content=resource.content,
                    created_at=resource.created_at.isoformat(),
                    updated_at=resource.updated_at.isoformat()
                )
                
            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except Exception as e:
                self.logger.error(f"Error updating resource {uri}: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.delete("/resources/{uri:path}", status_code=204)
        async def delete_resource(uri: str):
            """Delete a resource."""
            try:
                await self.resource_manager.delete_resource(uri)
                self.logger.info(f"Deleted resource: {uri}")
                return None
                
            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except Exception as e:
                self.logger.error(f"Error deleting resource {uri}: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.get("/resources/search/{query}")
        async def search_resources(query: str, limit: int = 100):
            """Search resources by name or description."""
            try:
                resources = await self.resource_manager.search_resources(
                    query=query,
                    limit=limit
                )
                
                results = [
                    {
                        "uri": r.uri,
                        "name": r.name,
                        "description": r.description,
                        "mime_type": r.mime_type,
                        "resource_type": r.resource_type.value
                    }
                    for r in resources
                ]
                
                self.logger.info(f"Search '{query}' found {len(results)} resources")
                return {"query": query, "results": results, "count": len(results)}
                
            except Exception as e:
                self.logger.error(f"Error searching resources: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.get("/resources/stats/count")
        async def get_resource_count(resource_type: Optional[str] = None):
            """Get count of resources."""
            try:
                type_filter = None
                if resource_type:
                    try:
                        type_filter = ResourceType(resource_type)
                    except ValueError:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Invalid resource_type. Must be one of: {[t.value for t in ResourceType]}"
                        )
                
                count = await self.resource_manager.get_resource_count(
                    resource_type=type_filter
                )
                
                return {"count": count, "resource_type": resource_type}
                
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Error counting resources: {e}", exc_info=True)
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
                    "database_health": "/health/database",
                    "tools": "/tools",
                    "execute": "/tools/execute",
                    "status": "/status",
                    "agents": "/agents",
                    "chat": "/chat/completions",
                    "resources": "/resources",
                    "resources_create": "/resources (POST)",
                    "resources_get": "/resources/{uri} (GET)",
                    "resources_update": "/resources/{uri} (PUT)",
                    "resources_delete": "/resources/{uri} (DELETE)",
                    "resources_search": "/resources/search/{query}",
                    "resources_count": "/resources/stats/count",
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
