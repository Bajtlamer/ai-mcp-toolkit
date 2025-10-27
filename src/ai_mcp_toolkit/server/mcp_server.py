"""Core MCP Server implementation for AI text processing toolkit."""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
import json

from mcp.server import Server
from mcp.types import (
    Tool,
    TextContent,
    CallToolRequestParams,
    CallToolResult,
    ListToolsResult,
    Resource,
    ListResourcesResult,
    ReadResourceResult,
    Prompt,
    PromptArgument,
    PromptMessage,
    ListPromptsResult,
    GetPromptResult,
)

from ..agents.text_cleaner import TextCleanerAgent
from ..agents.diacritic_remover import DiacriticRemoverAgent
from ..agents.text_analyzer import TextAnalyzerAgent
from ..agents.grammar_checker import GrammarCheckerAgent
from ..agents.text_summarizer import TextSummarizerAgent
from ..agents.language_detector import LanguageDetectorAgent
from ..agents.sentiment_analyzer import SentimentAnalyzerAgent
from ..agents.text_anonymizer import TextAnonymizerAgent
from ..agents.pdf_extractor import PDFExtractorAgent
from ..utils.config import Config
from ..utils.logger import get_logger
from ..utils.gpu_monitor import get_gpu_monitor
from ..models.database import db_manager
from ..managers.resource_manager import ResourceManager
from ..managers.prompt_manager import PromptManager

logger = get_logger(__name__)


@dataclass
class AgentInfo:
    """Information about a registered agent."""
    name: str
    description: str
    agent: Any
    tools: List[Tool]


class MCPServer:
    """Main MCP Server for AI text processing toolkit."""

    def __init__(self, config: Optional[Config] = None):
        """Initialize the MCP server with configuration."""
        self.config = config or Config()
        self.server = Server("ai-mcp-toolkit")
        self.agents: Dict[str, AgentInfo] = {}
        self.db_manager = db_manager
        self._db_connected = False
        self.resource_manager = ResourceManager()
        self.prompt_manager = PromptManager()
        
        # Initialize logger
        self.logger = get_logger(__name__, level=self.config.log_level)
        
        # Register handlers
        self._register_handlers()
        
        # Initialize GPU monitoring
        self.gpu_monitor = get_gpu_monitor()
        
        # Initialize and register agents
        self._initialize_agents()

    def _register_handlers(self) -> None:
        """Register MCP protocol handlers."""
        
        @self.server.list_resources()
        async def list_resources() -> ListResourcesResult:
            """List all available resources."""
            try:
                if not self._db_connected:
                    self.logger.warning("Database not connected, returning empty resource list")
                    return ListResourcesResult(resources=[])
                
                result = await self.resource_manager.list_resources()
                self.logger.info(f"Listed {len(result.resources)} resources")
                return result
            except Exception as e:
                self.logger.error(f"Error listing resources: {e}", exc_info=True)
                return ListResourcesResult(resources=[])
        
        @self.server.read_resource()
        async def read_resource(uri: str) -> ReadResourceResult:
            """Read a specific resource by URI."""
            try:
                if not self._db_connected:
                    raise ValueError("Database not connected")
                
                result = await self.resource_manager.read_resource(uri)
                self.logger.info(f"Read resource: {uri}")
                return result
            except ValueError as e:
                self.logger.error(f"Resource not found: {uri}")
                raise
            except Exception as e:
                self.logger.error(f"Error reading resource {uri}: {e}", exc_info=True)
                raise
        
        @self.server.list_prompts()
        async def list_prompts() -> ListPromptsResult:
            """List all available prompt templates."""
            try:
                if not self._db_connected:
                    self.logger.warning("Database not connected, returning empty prompt list")
                    return ListPromptsResult(prompts=[])
                
                # Get all public prompts (no user_id since MCP doesn't have auth context)
                db_prompts = await self.prompt_manager.list_prompts(user_id=None, limit=100)
                
                # Convert to MCP Prompt objects
                mcp_prompts = []
                for db_prompt in db_prompts:
                    # Convert arguments
                    arguments = []
                    for arg in db_prompt.arguments:
                        arguments.append(PromptArgument(
                            name=arg.name,
                            description=arg.description,
                            required=arg.required
                        ))
                    
                    mcp_prompts.append(Prompt(
                        name=db_prompt.name,
                        description=db_prompt.description,
                        arguments=arguments
                    ))
                
                self.logger.info(f"Listed {len(mcp_prompts)} prompts")
                return ListPromptsResult(prompts=mcp_prompts)
                
            except Exception as e:
                self.logger.error(f"Error listing prompts: {e}", exc_info=True)
                return ListPromptsResult(prompts=[])
        
        @self.server.get_prompt()
        async def get_prompt(name: str, arguments: Optional[Dict[str, str]] = None) -> GetPromptResult:
            """Get a specific prompt template and optionally render it with arguments."""
            try:
                if not self._db_connected:
                    raise ValueError("Database not connected")
                
                # Get the prompt from database
                db_prompt = await self.prompt_manager.get_prompt(name, user_id=None)
                if not db_prompt:
                    raise ValueError(f"Prompt '{name}' not found or not accessible")
                
                # Render the prompt if arguments provided
                rendered_template = db_prompt.template
                if arguments:
                    rendered_template = self.prompt_manager.render_prompt(db_prompt, arguments)
                    # Increment use count when prompt is actually used
                    await self.prompt_manager.increment_use_count(name)
                
                # Return the rendered prompt as a message
                messages = [PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=rendered_template
                    )
                )]
                
                self.logger.info(f"Got prompt: {name}")
                return GetPromptResult(
                    description=db_prompt.description,
                    messages=messages
                )
                
            except ValueError as e:
                self.logger.error(f"Prompt not found: {name}")
                raise
            except Exception as e:
                self.logger.error(f"Error getting prompt {name}: {e}", exc_info=True)
                raise
        
        @self.server.list_tools()
        async def list_tools() -> ListToolsResult:
            """List all available tools from registered agents."""
            all_tools = []
            for agent_info in self.agents.values():
                all_tools.extend(agent_info.tools)
            
            self.logger.info(f"Listed {len(all_tools)} tools")
            return ListToolsResult(tools=all_tools)

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> CallToolResult:
            """Handle tool calls by routing to appropriate agents."""
            self.logger.info(f"Tool called: {name} with args: {arguments}")
            
            try:
                # Find the agent that owns this tool
                agent_info = None
                tool = None
                
                for info in self.agents.values():
                    for t in info.tools:
                        if t.name == name:
                            agent_info = info
                            tool = t
                            break
                    if agent_info:
                        break
                
                if not agent_info:
                    error_msg = f"Tool '{name}' not found"
                    self.logger.error(error_msg)
                    return CallToolResult(
                        content=[TextContent(type="text", text=error_msg)],
                        isError=True
                    )
                
                # Call the agent's method
                result = await agent_info.agent.execute_tool(name, arguments)
                
                self.logger.info(f"Tool {name} executed successfully")
                return CallToolResult(
                    content=[TextContent(type="text", text=result)]
                )
                
            except Exception as e:
                error_msg = f"Error executing tool '{name}': {str(e)}"
                self.logger.error(error_msg, exc_info=True)
                return CallToolResult(
                    content=[TextContent(type="text", text=error_msg)],
                    isError=True
                )

    def _initialize_agents(self) -> None:
        """Initialize and register all available agents."""
        try:
            # Text Cleaner Agent
            text_cleaner = TextCleanerAgent(self.config)
            self._register_agent(
                "text_cleaner",
                "Clean and normalize text by removing special characters and formatting",
                text_cleaner
            )
            
            # Diacritic Remover Agent
            diacritic_remover = DiacriticRemoverAgent(self.config)
            self._register_agent(
                "diacritic_remover", 
                "Remove diacritical marks and accents from text",
                diacritic_remover
            )
            
            # Text Analyzer Agent
            text_analyzer = TextAnalyzerAgent(self.config)
            self._register_agent(
                "text_analyzer",
                "Analyze text for statistics, readability, and linguistic properties",
                text_analyzer
            )
            
            # Grammar Checker Agent
            grammar_checker = GrammarCheckerAgent(self.config)
            self._register_agent(
                "grammar_checker",
                "Check and correct grammar, spelling, and style issues",
                grammar_checker
            )
            
            # Text Summarizer Agent
            text_summarizer = TextSummarizerAgent(self.config)
            self._register_agent(
                "text_summarizer",
                "Generate concise summaries of longer texts",
                text_summarizer
            )
            
            # Language Detector Agent
            language_detector = LanguageDetectorAgent(self.config)
            self._register_agent(
                "language_detector",
                "Detect the language of input text",
                language_detector
            )
            
            # Sentiment Analyzer Agent
            sentiment_analyzer = SentimentAnalyzerAgent(self.config)
            self._register_agent(
                "sentiment_analyzer",
                "Analyze emotional tone and sentiment of text",
                sentiment_analyzer
            )
            
            # Text Anonymizer Agent
            text_anonymizer = TextAnonymizerAgent(self.config)
            self._register_agent(
                "text_anonymizer",
                "Anonymize sensitive information in text for privacy protection",
                text_anonymizer
            )
            
            # PDF Extractor Agent
            pdf_extractor = PDFExtractorAgent(self.config)
            self._register_agent(
                "pdf_extractor",
                "Extract text content from PDF files",
                pdf_extractor
            )
            
            self.logger.info(f"Initialized {len(self.agents)} agents")
            
        except Exception as e:
            self.logger.error(f"Error initializing agents: {e}", exc_info=True)
            raise

    def _register_agent(self, name: str, description: str, agent: Any) -> None:
        """Register an agent with the server."""
        try:
            tools = agent.get_tools()
            agent_info = AgentInfo(
                name=name,
                description=description,
                agent=agent,
                tools=tools
            )
            self.agents[name] = agent_info
            self.logger.debug(f"Registered agent '{name}' with {len(tools)} tools")
            
        except Exception as e:
            self.logger.error(f"Error registering agent '{name}': {e}")
            raise

    async def start(self, host: str = "localhost", port: int = 8000) -> None:
        """Start the MCP server with database connections and GPU monitoring."""
        try:
            self.logger.info(f"Starting MCP server on {host}:{port}")
            
            # Connect to databases
            try:
                await self.db_manager.connect()
                self._db_connected = True
                
                # Perform health check
                health = await self.db_manager.health_check()
                self.logger.info(f"Database health check: {health}")
                
                if health["overall"]:
                    self.logger.info("✅ All database connections established successfully")
                else:
                    self.logger.warning(f"⚠️ Some database connections failed: {health}")
                    
            except Exception as e:
                self.logger.error(f"Failed to connect to databases: {e}")
                # Continue without database if connection fails
                self._db_connected = False
            
            # Start GPU monitoring
            await self.gpu_monitor.start_monitoring(interval=10.0)  # Monitor every 10 seconds
            self.logger.info("GPU monitoring started")
            
            await self.server.run(host=host, port=port)
        except Exception as e:
            self.logger.error(f"Error starting server: {e}", exc_info=True)
            raise

    async def stop(self) -> None:
        """Stop the MCP server, database connections, and GPU monitoring."""
        try:
            self.logger.info("Stopping MCP server")
            
            # Disconnect from databases
            if self._db_connected:
                await self.db_manager.disconnect()
                self._db_connected = False
                self.logger.info("Database connections closed")
            
            # Stop GPU monitoring
            await self.gpu_monitor.stop_monitoring()
            self.logger.info("GPU monitoring stopped")
            
            await self.server.close()
        except Exception as e:
            self.logger.error(f"Error stopping server: {e}", exc_info=True)

    def get_agent_info(self, agent_name: str) -> Optional[AgentInfo]:
        """Get information about a specific agent."""
        return self.agents.get(agent_name)

    def list_agents(self) -> List[str]:
        """List all registered agent names."""
        return list(self.agents.keys())

    def get_server_stats(self) -> Dict[str, Any]:
        """Get server statistics and status including GPU metrics and database health."""
        total_tools = sum(len(info.tools) for info in self.agents.values())
        
        # Get GPU performance summary
        gpu_summary = self.gpu_monitor.get_performance_summary()
        
        return {
            "agents_count": len(self.agents),
            "total_tools": total_tools,
            "agents": {
                name: {
                    "description": info.description,
                    "tools_count": len(info.tools),
                    "tools": [tool.name for tool in info.tools]
                }
                for name, info in self.agents.items()
            },
            "config": {
                "log_level": self.config.log_level,
                "ollama_host": self.config.ollama_host,
                "ollama_port": self.config.ollama_port,
                "ollama_model": self.config.ollama_model,
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature
            },
            "gpu_performance": gpu_summary,
            "database": {
                "connected": self._db_connected,
                "manager": "MongoDB Atlas + Redis"
            }
        }


# Convenience functions for standalone usage
async def create_server(config: Optional[Config] = None) -> MCPServer:
    """Create and return a configured MCP server instance."""
    return MCPServer(config)


async def run_server(
    host: str = "localhost", 
    port: int = 8000, 
    config: Optional[Config] = None
) -> None:
    """Run the MCP server with the given configuration."""
    server = await create_server(config)
    try:
        await server.start(host, port)
    finally:
        await server.stop()
