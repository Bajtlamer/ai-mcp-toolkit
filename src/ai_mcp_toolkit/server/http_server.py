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
from fastapi import FastAPI, HTTPException, Request, Response, Cookie, Depends, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, EmailStr
from typing import Union
import io

from .mcp_server import MCPServer
from ..utils.config import Config
from ..utils.logger import get_logger
from ..utils.gpu_monitor import get_gpu_monitor, check_gpu_health
from ..managers.resource_manager import ResourceManager
from ..managers.user_manager import UserManager
from ..managers.session_manager import SessionManager
from ..managers.conversation_manager import ConversationManager
from ..managers.prompt_manager import PromptManager
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
    model: Optional[str] = None
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
    id: str
    uri: str
    name: str
    description: str
    mime_type: str
    resource_type: str
    owner_id: str
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


class ConversationCreate(BaseModel):
    """Request model for creating a conversation."""
    title: str = "New Conversation"
    messages: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None


class ConversationUpdate(BaseModel):
    """Request model for updating a conversation."""
    title: Optional[str] = None
    messages: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None
    status: Optional[str] = None


class MessageAdd(BaseModel):
    """Request model for adding a message to conversation."""
    role: str
    content: str
    timestamp: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None
    model: Optional[str] = None


class ConversationResponse(BaseModel):
    """Response model for conversation data."""
    id: str
    user_id: str
    title: str
    messages: List[Dict[str, Any]]
    status: str
    metadata: Dict[str, Any]
    created_at: str
    updated_at: str


# Prompt models
class PromptArgumentModel(BaseModel):
    """Model for prompt argument definition."""
    name: str
    description: str
    type: str = "string"
    required: bool = True
    default: Optional[Any] = None


class PromptCreate(BaseModel):
    """Request model for creating a prompt."""
    name: str
    description: str
    template: str
    arguments: Optional[List[PromptArgumentModel]] = None
    tags: Optional[List[str]] = None
    is_public: bool = True
    version: str = "1.0.0"


class PromptUpdate(BaseModel):
    """Request model for updating a prompt."""
    description: Optional[str] = None
    template: Optional[str] = None
    arguments: Optional[List[PromptArgumentModel]] = None
    tags: Optional[List[str]] = None
    is_public: Optional[bool] = None
    version: Optional[str] = None


class PromptResponse(BaseModel):
    """Response model for a prompt."""
    name: str
    description: str
    template: str
    arguments: List[PromptArgumentModel]
    tags: List[str]
    owner_id: Optional[str] = None
    is_public: bool
    version: str
    use_count: int
    created_at: str
    updated_at: str


class PromptRenderRequest(BaseModel):
    """Request model for rendering a prompt."""
    arguments: Dict[str, Any]


class HTTPServer:
    """HTTP server that wraps MCP functionality."""

    def __init__(self, config: Optional[Config] = None):
        """Initialize the HTTP server with MCP backend."""
        self.config = config or Config()
        self.mcp_server = None
        self.resource_manager = ResourceManager()
        self.user_manager = UserManager()
        self.session_manager = SessionManager()
        self.conversation_manager = ConversationManager()
        self.prompt_manager = PromptManager()
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
        
        # Current model configuration (public)
        @app.get("/model/current")
        async def get_current_model():
            """Get currently configured model (public endpoint)."""
            return {
                "model": self.config.ollama_model,
                "gpu_backend": self.config.gpu_backend
            }
        
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

        # Get server status (public - no auth required)
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

        # GPU health check endpoint (public - no auth required)
        @app.get("/gpu/health")
        async def gpu_health():
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
        
        # Ollama models endpoint (all authenticated users can view)
        @app.get("/ollama/models")
        async def list_ollama_models(user: User = Depends(require_auth)):
            """List available Ollama models (all authenticated users can view)."""
            try:
                from ..models.ollama_client import OllamaClient
                
                async with OllamaClient(self.config) as client:
                    models = await client.list_models()
                    
                    return {
                        "success": True,
                        "current_model": self.config.ollama_model,
                        "available_models": models,
                        "count": len(models)
                    }
            except Exception as e:
                self.logger.error(f"Error listing Ollama models: {e}", exc_info=True)
                return {
                    "success": False,
                    "error": str(e),
                    "current_model": self.config.ollama_model,
                    "available_models": [],
                    "count": 0
                }
        
        # GPU backend configuration endpoint (admin only)
        @app.get("/gpu/backend")
        async def get_gpu_backend(user: User = Depends(require_admin)):
            """Get current GPU backend configuration (admin only)."""
            return {
                "success": True,
                "gpu_backend": self.config.gpu_backend,
                "available_backends": ["auto", "cuda", "metal", "cpu"],
                "description": {
                    "auto": "Auto-detect (tries CUDA first, then Metal, fallback to CPU)",
                    "cuda": "NVIDIA CUDA (requires CUDA-capable GPU and drivers)",
                    "metal": "Apple Metal (for Apple Silicon Macs)",
                    "cpu": "CPU only (no GPU acceleration)"
                }
            }
        
        @app.post("/gpu/backend")
        async def set_gpu_backend(
            request: Dict[str, Any],
            user: User = Depends(require_admin)
        ):
            """Set GPU backend configuration (admin only)."""
            try:
                backend = request.get("backend")
                valid_backends = ["auto", "cuda", "metal", "cpu"]
                
                if not backend:
                    raise HTTPException(status_code=400, detail="Backend is required")
                
                if backend not in valid_backends:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid backend '{backend}'. Must be one of: {', '.join(valid_backends)}"
                    )
                
                old_backend = self.config.gpu_backend
                self.config.gpu_backend = backend
                
                self.logger.info(f"Admin {user.username} changed GPU backend from {old_backend} to {backend}")
                
                # Log audit event
                await AuditLogger.log(
                    user=user,
                    action="gpu.backend.change",
                    method="POST",
                    endpoint="/gpu/backend",
                    status_code=200,
                    resource_type="configuration",
                    resource_id="gpu_backend",
                    request_data={"backend": backend, "previous_backend": old_backend}
                )
                
                return {
                    "success": True,
                    "message": f"GPU backend changed to: {backend}",
                    "previous_backend": old_backend,
                    "current_backend": backend,
                    "note": "Backend changed in memory. To persist across restarts, update GPU_BACKEND environment variable. Ollama will automatically use the appropriate backend."
                }
                
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Error setting GPU backend: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))
        
        # Switch Ollama model endpoint (admin only)
        @app.post("/ollama/models/switch")
        async def switch_ollama_model(
            request: Dict[str, Any],
            user: User = Depends(require_admin)
        ):
            """Switch active Ollama model (admin only) - physically unloads old model and loads new one."""
            try:
                model_name = request.get("model")
                if not model_name:
                    raise HTTPException(status_code=400, detail="Model name is required")
                
                from ..models.ollama_client import OllamaClient
                
                # Verify model exists
                async with OllamaClient(self.config) as client:
                    models = await client.list_models()
                    # Extract model names from OllamaModel dataclass objects
                    model_names = [m.name for m in models]
                    
                    if model_name not in model_names:
                        raise HTTPException(
                            status_code=404,
                            detail=f"Model '{model_name}' not found. Available models: {', '.join(model_names)}"
                        )
                
                old_model = self.config.ollama_model
                
                # Step 1: Physically unload the old model from Ollama (like 'ollama stop')
                ollama_url = self.config.get_ollama_url()
                async with aiohttp.ClientSession() as session:
                    try:
                        self.logger.info(f"Unloading old model: {old_model}")
                        # Send a request with keep_alive=0 to immediately unload the old model
                        unload_response = await session.post(
                            f"{ollama_url}/api/generate",
                            json={
                                "model": old_model,
                                "prompt": "",
                                "keep_alive": 0  # Unload immediately
                            },
                            timeout=aiohttp.ClientTimeout(total=10)
                        )
                        if unload_response.status == 200:
                            self.logger.info(f"Successfully unloaded old model: {old_model}")
                        else:
                            self.logger.warning(f"Old model unload returned status {unload_response.status}")
                    except Exception as e:
                        self.logger.warning(f"Could not unload old model {old_model}: {e}")
                    
                    # Step 2: Pre-load and warm up the new model (like 'echo Hello | ollama run')
                    try:
                        self.logger.info(f"Loading and warming up new model: {model_name}")
                        warmup_response = await session.post(
                            f"{ollama_url}/api/generate",
                            json={
                                "model": model_name,
                                "prompt": "Hello",  # Simple warmup prompt
                                "stream": False,
                                "keep_alive": "30m"  # Keep loaded for 30 minutes
                            },
                            timeout=aiohttp.ClientTimeout(total=120)  # Allow time for model loading
                        )
                        if warmup_response.status == 200:
                            warmup_data = await warmup_response.json()
                            self.logger.info(f"Successfully loaded and warmed up model: {model_name}")
                        else:
                            error_text = await warmup_response.text()
                            self.logger.error(f"Warmup failed with status {warmup_response.status}: {error_text}")
                            raise HTTPException(
                                status_code=500,
                                detail=f"Failed to load new model: HTTP {warmup_response.status}"
                            )
                    except aiohttp.ClientError as e:
                        self.logger.error(f"Failed to warm up new model {model_name}: {e}", exc_info=True)
                        raise HTTPException(
                            status_code=500,
                            detail=f"Failed to load new model: {str(e)}"
                        )
                
                # Step 3: Update config in memory (only after successful model load)
                self.config.ollama_model = model_name
                
                # Log the change
                self.logger.info(f"Admin {user.username} switched model from {old_model} to {model_name}")
                
                # Log audit event
                await AuditLogger.log(
                    user=user,
                    action="model.switch",
                    method="POST",
                    endpoint="/ollama/models/switch",
                    status_code=200,
                    resource_type="model",
                    resource_id=model_name,
                    request_data={"model": model_name, "previous_model": old_model}
                )
                
                return {
                    "success": True,
                    "message": f"Successfully switched to model: {model_name}",
                    "previous_model": old_model,
                    "current_model": model_name,
                    "note": "Model physically unloaded and reloaded in Ollama. No server restart needed. To persist across restarts, update OLLAMA_MODEL environment variable."
                }
                
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Error switching model: {e}", exc_info=True)
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
                
                # Pass user context for ownership filtering
                is_admin = user.role == UserRole.ADMIN
                result = await self.resource_manager.list_resources(
                    user_id=str(user.id),
                    is_admin=is_admin,
                    resource_type=type_filter,
                    limit=limit,
                    offset=offset
                )
                
                # Fetch resources from database to get owner info
                from ..models.documents import Resource
                resources_list = []
                
                for mcp_resource in result.resources:
                    # Get full resource document
                    db_resource = await Resource.find_one(Resource.uri == mcp_resource.uri)
                    if db_resource:
                        # Get owner username if admin
                        owner_username = None
                        if is_admin and db_resource.owner_id:
                            self.logger.debug(f"Admin viewing resource {db_resource.uri}, owner_id: {db_resource.owner_id}")
                            owner = await self.user_manager.get_user_by_id(db_resource.owner_id)
                            if owner:
                                owner_username = owner.username
                                self.logger.debug(f"Found owner: {owner_username}")
                            else:
                                owner_username = "Unknown"
                                self.logger.warning(f"Could not find user with ID: {db_resource.owner_id}")
                        
                        resources_list.append({
                            "id": str(db_resource.id),
                            "uri": db_resource.uri,
                            "name": db_resource.name,
                            "description": db_resource.description,
                            "mimeType": db_resource.mime_type,
                            "resourceType": db_resource.resource_type.value,
                            "ownerId": db_resource.owner_id,
                            "ownerUsername": owner_username,  # Only populated for admins
                            "createdAt": db_resource.created_at.isoformat(),
                            "updatedAt": db_resource.updated_at.isoformat()
                        })
                
                self.logger.info(f"Listed {len(resources_list)} resources")
                return resources_list
                
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Error listing resources: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.post("/resources/upload", response_model=ResourceResponse, status_code=201)
        async def upload_resource(
            file: UploadFile = File(...),
            name: str = Form(None),
            description: str = Form(...),
            user: User = Depends(require_auth)
        ):
            """Upload a file as a resource."""
            try:
                # Read file content
                content_bytes = await file.read()
                
                # Detect resource type based on MIME type
                mime_type = file.content_type or 'application/octet-stream'
                
                # Determine if it's a text file we can store directly
                is_text = mime_type.startswith('text/') or mime_type in [
                    'application/json', 'application/xml', 'application/javascript'
                ]
                
                # For text files under 10MB, store content directly
                # For binary files or large files, store base64 encoded or reference
                content_str = None
                if is_text and len(content_bytes) < 10 * 1024 * 1024:  # 10MB limit
                    try:
                        content_str = content_bytes.decode('utf-8')
                    except UnicodeDecodeError:
                        # If decode fails, treat as binary
                        is_text = False
                
                if not is_text or content_str is None:
                    # For binary files, store metadata only
                    # For PDFs, store the bytes for later text extraction
                    import base64
                    metadata = {
                        'original_filename': file.filename,
                        'file_size': len(content_bytes),
                        'is_binary': not is_text
                    }
                    
                    if mime_type == 'application/pdf':
                        # Store PDF bytes as base64 for later extraction
                        metadata['pdf_bytes'] = base64.b64encode(content_bytes).decode('utf-8')
                        content_str = f"[PDF file: {file.filename}, {len(content_bytes)} bytes - text will be extracted on access]"
                    else:
                        content_str = f"[Binary file: {file.filename}, {len(content_bytes)} bytes, {mime_type}]"
                else:
                    metadata = {
                        'original_filename': file.filename,
                        'file_size': len(content_bytes),
                        'is_binary': False
                    }
                
                # Generate URI
                uri = f"file:///{file.filename}"
                
                # Use provided name or filename
                resource_name = name or file.filename
                
                # Create resource with owner_id
                resource = await self.resource_manager.create_resource(
                    uri=uri,
                    name=resource_name,
                    description=description,
                    mime_type=mime_type,
                    resource_type=ResourceType.FILE,
                    owner_id=str(user.id),
                    content=content_str,
                    metadata=metadata
                )
                
                self.logger.info(f"User {user.username} uploaded file: {file.filename} ({len(content_bytes)} bytes)")
                
                # Log audit event
                await AuditLogger.log(
                    user=user,
                    action="resource.upload",
                    method="POST",
                    endpoint="/resources/upload",
                    status_code=201,
                    resource_type="resource",
                    resource_id=resource.uri,
                    request_data={
                        'filename': file.filename,
                        'size': len(content_bytes),
                        'mime_type': mime_type
                    }
                )
                
                return ResourceResponse(
                    id=str(resource.id),
                    uri=resource.uri,
                    name=resource.name,
                    description=resource.description,
                    mime_type=resource.mime_type,
                    resource_type=resource.resource_type.value,
                    owner_id=resource.owner_id,
                    content=resource.content if is_text else None,
                    created_at=resource.created_at.isoformat(),
                    updated_at=resource.updated_at.isoformat()
                )
                
            except ValueError as e:
                raise HTTPException(status_code=409, detail=str(e))
            except Exception as e:
                self.logger.error(f"Error uploading file: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.get("/resources/{uri:path}", response_model=Dict[str, Any])
        async def get_resource(uri: str, user: User = Depends(require_auth)):
            """Get a specific resource by URI (ownership checked)."""
            try:
                is_admin = user.role == UserRole.ADMIN
                result = await self.resource_manager.read_resource(
                    uri,
                    user_id=str(user.id),
                    is_admin=is_admin
                )
                
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
                    owner_id=str(user.id),
                    content=request.content,
                    metadata=request.metadata
                )
                
                self.logger.info(f"Created resource: {resource.uri}")
                
                return ResourceResponse(
                    id=str(resource.id),
                    uri=resource.uri,
                    name=resource.name,
                    description=resource.description,
                    mime_type=resource.mime_type,
                    resource_type=resource.resource_type.value,
                    owner_id=resource.owner_id,
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
                is_admin = user.role == UserRole.ADMIN
                resource = await self.resource_manager.update_resource(
                    uri=uri,
                    user_id=str(user.id),
                    is_admin=is_admin,
                    name=request.name,
                    description=request.description,
                    content=request.content,
                    metadata=request.metadata
                )
                
                self.logger.info(f"Updated resource: {uri}")
                
                return ResourceResponse(
                    id=str(resource.id),
                    uri=resource.uri,
                    name=resource.name,
                    description=resource.description,
                    mime_type=resource.mime_type,
                    resource_type=resource.resource_type.value,
                    owner_id=resource.owner_id,
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
        async def delete_resource(uri: str, user: User = Depends(require_auth)):
            """Delete a resource (ownership checked)."""
            try:
                is_admin = user.role == UserRole.ADMIN
                await self.resource_manager.delete_resource(
                    uri,
                    user_id=str(user.id),
                    is_admin=is_admin
                )
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
        
        # Prompt Management Endpoints
        
        @app.get("/prompts", response_model=List[PromptResponse])
        async def list_prompts(
            user: User = Depends(require_auth),
            tags: Optional[str] = None,
            limit: int = 100,
            offset: int = 0
        ):
            """List prompts (public + user's private prompts)."""
            try:
                tag_list = tags.split(",") if tags else None
                
                prompts = await self.prompt_manager.list_prompts(
                    user_id=str(user.id),
                    tags=tag_list,
                    skip=offset,
                    limit=limit
                )
                
                return [
                    PromptResponse(
                        name=p.name,
                        description=p.description,
                        template=p.template,
                        arguments=[PromptArgumentModel(**arg.dict()) for arg in p.arguments],
                        tags=p.tags,
                        owner_id=p.owner_id,
                        is_public=p.is_public,
                        version=p.version,
                        use_count=p.use_count,
                        created_at=p.created_at.isoformat(),
                        updated_at=p.updated_at.isoformat()
                    )
                    for p in prompts
                ]
                
            except Exception as e:
                self.logger.error(f"Error listing prompts: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.get("/prompts/{name}", response_model=PromptResponse)
        async def get_prompt(
            name: str,
            user: User = Depends(require_auth)
        ):
            """Get a specific prompt by name."""
            try:
                prompt = await self.prompt_manager.get_prompt(name, user_id=str(user.id))
                
                if not prompt:
                    raise HTTPException(status_code=404, detail=f"Prompt '{name}' not found")
                
                return PromptResponse(
                    name=prompt.name,
                    description=prompt.description,
                    template=prompt.template,
                    arguments=[PromptArgumentModel(**arg.dict()) for arg in prompt.arguments],
                    tags=prompt.tags,
                    owner_id=prompt.owner_id,
                    is_public=prompt.is_public,
                    version=prompt.version,
                    use_count=prompt.use_count,
                    created_at=prompt.created_at.isoformat(),
                    updated_at=prompt.updated_at.isoformat()
                )
                
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Error getting prompt {name}: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.post("/prompts", response_model=PromptResponse, status_code=201)
        async def create_prompt(
            request: PromptCreate,
            user: User = Depends(require_auth)
        ):
            """Create a new prompt template."""
            try:
                arguments = [arg.dict() for arg in request.arguments] if request.arguments else []
                
                prompt = await self.prompt_manager.create_prompt(
                    name=request.name,
                    description=request.description,
                    template=request.template,
                    arguments=arguments,
                    tags=request.tags or [],
                    owner_id=str(user.id),
                    is_public=request.is_public,
                    version=request.version
                )
                
                self.logger.info(f"User {user.username} created prompt: {prompt.name}")
                
                # Log audit event
                await AuditLogger.log(
                    user=user,
                    action="prompt.create",
                    method="POST",
                    endpoint="/prompts",
                    status_code=201,
                    resource_type="prompt",
                    resource_id=prompt.name
                )
                
                return PromptResponse(
                    name=prompt.name,
                    description=prompt.description,
                    template=prompt.template,
                    arguments=[PromptArgumentModel(**arg.dict()) for arg in prompt.arguments],
                    tags=prompt.tags,
                    owner_id=prompt.owner_id,
                    is_public=prompt.is_public,
                    version=prompt.version,
                    use_count=prompt.use_count,
                    created_at=prompt.created_at.isoformat(),
                    updated_at=prompt.updated_at.isoformat()
                )
                
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                self.logger.error(f"Error creating prompt: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.put("/prompts/{name}", response_model=PromptResponse)
        async def update_prompt(
            name: str,
            request: PromptUpdate,
            user: User = Depends(require_auth)
        ):
            """Update an existing prompt (only owner can update)."""
            try:
                arguments = [arg.dict() for arg in request.arguments] if request.arguments else None
                
                prompt = await self.prompt_manager.update_prompt(
                    name=name,
                    user_id=str(user.id),
                    description=request.description,
                    template=request.template,
                    arguments=arguments,
                    tags=request.tags,
                    is_public=request.is_public,
                    version=request.version
                )
                
                if not prompt:
                    raise HTTPException(status_code=404, detail=f"Prompt '{name}' not found")
                
                self.logger.info(f"User {user.username} updated prompt: {name}")
                
                # Log audit event
                await AuditLogger.log(
                    user=user,
                    action="prompt.update",
                    method="PUT",
                    endpoint=f"/prompts/{name}",
                    status_code=200,
                    resource_type="prompt",
                    resource_id=name
                )
                
                return PromptResponse(
                    name=prompt.name,
                    description=prompt.description,
                    template=prompt.template,
                    arguments=[PromptArgumentModel(**arg.dict()) for arg in prompt.arguments],
                    tags=prompt.tags,
                    owner_id=prompt.owner_id,
                    is_public=prompt.is_public,
                    version=prompt.version,
                    use_count=prompt.use_count,
                    created_at=prompt.created_at.isoformat(),
                    updated_at=prompt.updated_at.isoformat()
                )
                
            except PermissionError as e:
                raise HTTPException(status_code=403, detail=str(e))
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Error updating prompt {name}: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.delete("/prompts/{name}", status_code=204)
        async def delete_prompt(
            name: str,
            user: User = Depends(require_auth)
        ):
            """Delete a prompt (only owner can delete)."""
            try:
                success = await self.prompt_manager.delete_prompt(name, user_id=str(user.id))
                
                if not success:
                    raise HTTPException(status_code=404, detail=f"Prompt '{name}' not found")
                
                self.logger.info(f"User {user.username} deleted prompt: {name}")
                
                # Log audit event
                await AuditLogger.log(
                    user=user,
                    action="prompt.delete",
                    method="DELETE",
                    endpoint=f"/prompts/{name}",
                    status_code=204,
                    resource_type="prompt",
                    resource_id=name
                )
                
                return None
                
            except PermissionError as e:
                raise HTTPException(status_code=403, detail=str(e))
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Error deleting prompt {name}: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.post("/prompts/{name}/render")
        async def render_prompt(
            name: str,
            request: PromptRenderRequest,
            user: User = Depends(require_auth)
        ):
            """Render a prompt template with provided arguments."""
            try:
                prompt = await self.prompt_manager.get_prompt(name, user_id=str(user.id))
                
                if not prompt:
                    raise HTTPException(status_code=404, detail=f"Prompt '{name}' not found")
                
                rendered = self.prompt_manager.render_prompt(prompt, request.arguments)
                
                # Increment use count
                await self.prompt_manager.increment_use_count(name)
                
                return {
                    "prompt_name": name,
                    "rendered": rendered,
                    "arguments": request.arguments
                }
                
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Error rendering prompt {name}: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.get("/prompts/search/{query}")
        async def search_prompts(
            query: str,
            user: User = Depends(require_auth),
            limit: int = 20
        ):
            """Search prompts by name, description, or tags."""
            try:
                prompts = await self.prompt_manager.search_prompts(
                    query=query,
                    user_id=str(user.id),
                    limit=limit
                )
                
                results = [
                    {
                        "name": p.name,
                        "description": p.description,
                        "tags": p.tags,
                        "version": p.version,
                        "use_count": p.use_count
                    }
                    for p in prompts
                ]
                
                return {"query": query, "results": results, "count": len(results)}
                
            except Exception as e:
                self.logger.error(f"Error searching prompts: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.get("/prompts/stats/count")
        async def get_prompt_count(
            user: User = Depends(require_auth),
            tags: Optional[str] = None
        ):
            """Get count of prompts."""
            try:
                tag_list = tags.split(",") if tags else None
                
                count = await self.prompt_manager.count_prompts(
                    user_id=str(user.id),
                    tags=tag_list
                )
                
                return {"count": count, "tags": tags}
                
            except Exception as e:
                self.logger.error(f"Error counting prompts: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))
        
        # Conversation Management Endpoints (all require auth)
        
        @app.get("/conversations", response_model=List[ConversationResponse])
        async def list_conversations(
            user: User = Depends(require_auth),
            limit: int = 100,
            offset: int = 0
        ):
            """List all conversations for the authenticated user."""
            try:
                conversations = await self.conversation_manager.list_conversations(
                    user_id=str(user.id),
                    limit=limit,
                    offset=offset
                )
                
                # Log audit event
                await AuditLogger.log(
                    user=user,
                    action="conversations.list",
                    method="GET",
                    endpoint="/conversations",
                    status_code=200,
                    resource_type="conversations"
                )
                
                return [
                    ConversationResponse(
                        id=str(c.id),
                        user_id=c.user_id,
                        title=c.title,
                        messages=c.messages,
                        status=c.status,
                        metadata=c.metadata,
                        created_at=c.created_at.isoformat(),
                        updated_at=c.updated_at.isoformat()
                    )
                    for c in conversations
                ]
                
            except Exception as e:
                self.logger.error(f"Error listing conversations: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.get("/conversations/{conversation_id}", response_model=ConversationResponse)
        async def get_conversation(
            conversation_id: str,
            user: User = Depends(require_auth)
        ):
            """Get a specific conversation by ID."""
            try:
                conversation = await self.conversation_manager.get_conversation(
                    conversation_id=conversation_id,
                    user_id=str(user.id)
                )
                
                if not conversation:
                    raise HTTPException(status_code=404, detail="Conversation not found")
                
                # Log audit event
                await AuditLogger.log(
                    user=user,
                    action="conversations.get",
                    method="GET",
                    endpoint=f"/conversations/{conversation_id}",
                    status_code=200,
                    resource_type="conversation",
                    resource_id=conversation_id
                )
                
                return ConversationResponse(
                    id=str(conversation.id),
                    user_id=conversation.user_id,
                    title=conversation.title,
                    messages=conversation.messages,
                    status=conversation.status,
                    metadata=conversation.metadata,
                    created_at=conversation.created_at.isoformat(),
                    updated_at=conversation.updated_at.isoformat()
                )
                
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Error getting conversation {conversation_id}: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.post("/conversations", response_model=ConversationResponse, status_code=201)
        async def create_conversation(
            request: ConversationCreate,
            user: User = Depends(require_auth)
        ):
            """Create a new conversation."""
            try:
                conversation = await self.conversation_manager.create_conversation(
                    user_id=str(user.id),
                    title=request.title,
                    messages=request.messages,
                    metadata=request.metadata
                )
                
                # Log audit event
                await AuditLogger.log(
                    user=user,
                    action="conversations.create",
                    method="POST",
                    endpoint="/conversations",
                    status_code=201,
                    resource_type="conversation",
                    resource_id=str(conversation.id),
                    request_data={"title": request.title}
                )
                
                self.logger.info(f"Created conversation {conversation.id} for user {user.username}")
                
                return ConversationResponse(
                    id=str(conversation.id),
                    user_id=conversation.user_id,
                    title=conversation.title,
                    messages=conversation.messages,
                    status=conversation.status,
                    metadata=conversation.metadata,
                    created_at=conversation.created_at.isoformat(),
                    updated_at=conversation.updated_at.isoformat()
                )
                
            except Exception as e:
                self.logger.error(f"Error creating conversation: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.put("/conversations/{conversation_id}", response_model=ConversationResponse)
        async def update_conversation(
            conversation_id: str,
            request: ConversationUpdate,
            user: User = Depends(require_auth)
        ):
            """Update an existing conversation."""
            try:
                conversation = await self.conversation_manager.update_conversation(
                    conversation_id=conversation_id,
                    user_id=str(user.id),
                    title=request.title,
                    messages=request.messages,
                    metadata=request.metadata,
                    status=request.status
                )
                
                if not conversation:
                    raise HTTPException(status_code=404, detail="Conversation not found")
                
                # Log audit event
                await AuditLogger.log(
                    user=user,
                    action="conversations.update",
                    method="PUT",
                    endpoint=f"/conversations/{conversation_id}",
                    status_code=200,
                    resource_type="conversation",
                    resource_id=conversation_id
                )
                
                self.logger.info(f"Updated conversation {conversation_id}")
                
                return ConversationResponse(
                    id=str(conversation.id),
                    user_id=conversation.user_id,
                    title=conversation.title,
                    messages=conversation.messages,
                    status=conversation.status,
                    metadata=conversation.metadata,
                    created_at=conversation.created_at.isoformat(),
                    updated_at=conversation.updated_at.isoformat()
                )
                
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Error updating conversation {conversation_id}: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.delete("/conversations/{conversation_id}", status_code=204)
        async def delete_conversation(
            conversation_id: str,
            user: User = Depends(require_auth)
        ):
            """Delete a conversation."""
            try:
                success = await self.conversation_manager.delete_conversation(
                    conversation_id=conversation_id,
                    user_id=str(user.id)
                )
                
                if not success:
                    raise HTTPException(status_code=404, detail="Conversation not found")
                
                # Log audit event
                await AuditLogger.log(
                    user=user,
                    action="conversations.delete",
                    method="DELETE",
                    endpoint=f"/conversations/{conversation_id}",
                    status_code=204,
                    resource_type="conversation",
                    resource_id=conversation_id
                )
                
                self.logger.info(f"Deleted conversation {conversation_id}")
                return None
                
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Error deleting conversation {conversation_id}: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.delete("/conversations", status_code=200)
        async def delete_all_conversations(user: User = Depends(require_auth)):
            """Delete all conversations for the current user (bulk operation)."""
            try:
                deleted_count = await self.conversation_manager.delete_all_conversations(
                    user_id=str(user.id)
                )
                
                # Log audit event
                await AuditLogger.log(
                    user=user,
                    action="conversations.delete_all",
                    method="DELETE",
                    endpoint="/conversations",
                    status_code=200,
                    resource_type="conversation",
                    response_data={"deleted_count": deleted_count}
                )
                
                self.logger.info(f"Deleted {deleted_count} conversations for user {user.username}")
                return {"deleted_count": deleted_count, "message": f"Successfully deleted {deleted_count} conversations"}
                
            except Exception as e:
                self.logger.error(f"Error deleting all conversations: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.post("/conversations/{conversation_id}/messages", response_model=ConversationResponse)
        async def add_message(
            conversation_id: str,
            message: MessageAdd,
            user: User = Depends(require_auth)
        ):
            """Add a message to a conversation."""
            try:
                message_dict = {
                    "role": message.role,
                    "content": message.content,
                    "timestamp": message.timestamp
                }
                
                # Preserve metrics and model if provided
                if message.metrics:
                    message_dict["metrics"] = message.metrics
                if message.model:
                    message_dict["model"] = message.model
                
                conversation = await self.conversation_manager.add_message(
                    conversation_id=conversation_id,
                    user_id=str(user.id),
                    message=message_dict
                )
                
                if not conversation:
                    raise HTTPException(status_code=404, detail="Conversation not found")
                
                # Log audit event
                await AuditLogger.log(
                    user=user,
                    action="conversations.add_message",
                    method="POST",
                    endpoint=f"/conversations/{conversation_id}/messages",
                    status_code=200,
                    resource_type="conversation",
                    resource_id=conversation_id
                )
                
                return ConversationResponse(
                    id=str(conversation.id),
                    user_id=conversation.user_id,
                    title=conversation.title,
                    messages=conversation.messages,
                    status=conversation.status,
                    metadata=conversation.metadata,
                    created_at=conversation.created_at.isoformat(),
                    updated_at=conversation.updated_at.isoformat()
                )
                
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Error adding message to conversation {conversation_id}: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.get("/conversations/stats/count")
        async def get_conversation_count(user: User = Depends(require_auth)):
            """Get count of conversations for the user."""
            try:
                count = await self.conversation_manager.get_conversation_count(
                    user_id=str(user.id)
                )
                
                return {"count": count}
                
            except Exception as e:
                self.logger.error(f"Error counting conversations: {e}", exc_info=True)
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
                    "conversations": "/conversations",
                    "conversations_create": "/conversations (POST)",
                    "conversations_get": "/conversations/{id} (GET)",
                    "conversations_update": "/conversations/{id} (PUT)",
                    "conversations_delete": "/conversations/{id} (DELETE)",
                    "conversations_add_message": "/conversations/{id}/messages (POST)",
                    "conversations_count": "/conversations/stats/count",
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
                    "ollama_models": "/ollama/models (GET, admin only)",
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
