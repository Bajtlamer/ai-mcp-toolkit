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
)

from ..agents.text_cleaner import TextCleanerAgent
from ..agents.diacritic_remover import DiacriticRemoverAgent
from ..agents.text_analyzer import TextAnalyzerAgent
from ..agents.grammar_checker import GrammarCheckerAgent
from ..agents.text_summarizer import TextSummarizerAgent
from ..agents.language_detector import LanguageDetectorAgent
from ..agents.sentiment_analyzer import SentimentAnalyzerAgent
from ..agents.text_anonymizer import TextAnonymizerAgent
from ..utils.config import Config
from ..utils.logger import get_logger

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
        
        # Initialize logger
        self.logger = get_logger(__name__, level=self.config.log_level)
        
        # Register handlers
        self._register_handlers()
        
        # Initialize and register agents
        self._initialize_agents()

    def _register_handlers(self) -> None:
        """Register MCP protocol handlers."""
        
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
        """Start the MCP server."""
        try:
            self.logger.info(f"Starting MCP server on {host}:{port}")
            await self.server.run(host=host, port=port)
        except Exception as e:
            self.logger.error(f"Error starting server: {e}", exc_info=True)
            raise

    async def stop(self) -> None:
        """Stop the MCP server."""
        try:
            self.logger.info("Stopping MCP server")
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
        """Get server statistics and status."""
        total_tools = sum(len(info.tools) for info in self.agents.values())
        
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
    await server.start(host, port)
