"""Base agent class for all text processing agents."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from mcp.types import Tool, TextContent
from ..utils.config import Config
from ..utils.logger import get_logger


class BaseAgent(ABC):
    """Abstract base class for all text processing agents."""

    def __init__(self, config: Config):
        """Initialize the base agent."""
        self.config = config
        self.logger = get_logger(self.__class__.__name__, level=config.log_level)
        self.name = self.__class__.__name__.replace("Agent", "").lower()
        
    @abstractmethod
    def get_tools(self) -> List[Tool]:
        """Return list of tools provided by this agent."""
        pass
    
    @abstractmethod
    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute a tool with given arguments and return result."""
        pass
    
    def validate_text_input(self, text: str, max_length: Optional[int] = None) -> str:
        """Validate and sanitize text input."""
        if not isinstance(text, str):
            raise ValueError("Input must be a string")
        
        if not text.strip():
            raise ValueError("Input text cannot be empty")
        
        max_len = max_length or self.config.max_text_length
        if len(text) > max_len:
            raise ValueError(f"Text too long. Maximum length is {max_len} characters")
        
        return text.strip()
    
    def chunk_text(self, text: str, chunk_size: Optional[int] = None) -> List[str]:
        """Split text into chunks for processing."""
        chunk_size = chunk_size or self.config.chunk_size
        
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        words = text.split()
        current_chunk = []
        current_length = 0
        
        for word in words:
            word_length = len(word) + 1  # +1 for space
            
            if current_length + word_length > chunk_size and current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_length = len(word)
            else:
                current_chunk.append(word)
                current_length += word_length
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks
    
    def format_result(self, result: Any, format_type: str = "text") -> str:
        """Format result for output."""
        if format_type == "json":
            import json
            return json.dumps(result, indent=2, ensure_ascii=False)
        elif format_type == "yaml":
            import yaml
            return yaml.dump(result, default_flow_style=False, allow_unicode=True)
        else:
            return str(result)
    
    def log_execution(self, tool_name: str, arguments: Dict[str, Any], duration: float) -> None:
        """Log tool execution details."""
        self.logger.info(
            f"Executed tool '{tool_name}' in {duration:.3f}s with args: "
            f"{str(arguments)[:100]}{'...' if len(str(arguments)) > 100 else ''}"
        )
