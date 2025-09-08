"""Text cleaner agent for removing special characters and normalizing text."""

import re
import time
from typing import Any, Dict, List
from mcp.types import Tool

from .base_agent import BaseAgent


class TextCleanerAgent(BaseAgent):
    """Agent for cleaning and normalizing text."""

    def get_tools(self) -> List[Tool]:
        """Return list of tools provided by this agent."""
        return [
            Tool(
                name="clean_text",
                description="Clean and normalize text by removing special characters, extra whitespace, and formatting",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "The text to clean and normalize"
                        },
                        "remove_numbers": {
                            "type": "boolean",
                            "description": "Whether to remove numbers from the text",
                            "default": False
                        },
                        "remove_punctuation": {
                            "type": "boolean",
                            "description": "Whether to remove punctuation from the text",
                            "default": False
                        },
                        "normalize_whitespace": {
                            "type": "boolean",
                            "description": "Whether to normalize whitespace (remove extra spaces, tabs, newlines)",
                            "default": True
                        },
                        "to_lowercase": {
                            "type": "boolean",
                            "description": "Whether to convert text to lowercase",
                            "default": False
                        },
                        "remove_urls": {
                            "type": "boolean",
                            "description": "Whether to remove URLs from the text",
                            "default": False
                        },
                        "remove_emails": {
                            "type": "boolean",
                            "description": "Whether to remove email addresses from the text",
                            "default": False
                        }
                    },
                    "required": ["text"]
                }
            ),
            Tool(
                name="normalize_unicode",
                description="Normalize Unicode characters in text",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "The text to normalize"
                        },
                        "form": {
                            "type": "string",
                            "description": "Unicode normalization form (NFC, NFD, NFKC, NFKD)",
                            "default": "NFC"
                        }
                    },
                    "required": ["text"]
                }
            ),
            Tool(
                name="remove_html_tags",
                description="Remove HTML tags from text",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "The text containing HTML tags to remove"
                        },
                        "preserve_content": {
                            "type": "boolean",
                            "description": "Whether to preserve the text content inside tags",
                            "default": True
                        }
                    },
                    "required": ["text"]
                }
            )
        ]

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute a tool with given arguments and return result."""
        start_time = time.time()
        
        try:
            if tool_name == "clean_text":
                result = await self._clean_text(arguments)
            elif tool_name == "normalize_unicode":
                result = await self._normalize_unicode(arguments)
            elif tool_name == "remove_html_tags":
                result = await self._remove_html_tags(arguments)
            else:
                raise ValueError(f"Unknown tool: {tool_name}")
            
            duration = time.time() - start_time
            self.log_execution(tool_name, arguments, duration)
            return result
            
        except Exception as e:
            self.logger.error(f"Error executing {tool_name}: {e}")
            raise

    async def _clean_text(self, arguments: Dict[str, Any]) -> str:
        """Clean and normalize text."""
        text = self.validate_text_input(arguments["text"])
        
        # Extract options
        remove_numbers = arguments.get("remove_numbers", False)
        remove_punctuation = arguments.get("remove_punctuation", False)
        normalize_whitespace = arguments.get("normalize_whitespace", True)
        to_lowercase = arguments.get("to_lowercase", False)
        remove_urls = arguments.get("remove_urls", False)
        remove_emails = arguments.get("remove_emails", False)
        
        # Apply cleaning operations
        if remove_urls:
            # Remove URLs
            url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
            text = re.sub(url_pattern, '', text)
        
        if remove_emails:
            # Remove email addresses
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            text = re.sub(email_pattern, '', text)
        
        if remove_numbers:
            # Remove all numbers
            text = re.sub(r'\d+', '', text)
        
        if remove_punctuation:
            # Remove punctuation (keep basic sentence structure)
            text = re.sub(r'[^\w\s]', '', text)
        
        if normalize_whitespace:
            # Normalize whitespace
            text = re.sub(r'\s+', ' ', text)
            text = text.strip()
        
        if to_lowercase:
            text = text.lower()
        
        return text

    async def _normalize_unicode(self, arguments: Dict[str, Any]) -> str:
        """Normalize Unicode characters in text."""
        import unicodedata
        
        text = self.validate_text_input(arguments["text"])
        form = arguments.get("form", "NFC").upper()
        
        if form not in ["NFC", "NFD", "NFKC", "NFKD"]:
            raise ValueError(f"Invalid normalization form: {form}")
        
        return unicodedata.normalize(form, text)

    async def _remove_html_tags(self, arguments: Dict[str, Any]) -> str:
        """Remove HTML tags from text."""
        text = self.validate_text_input(arguments["text"])
        preserve_content = arguments.get("preserve_content", True)
        
        if preserve_content:
            # Remove HTML tags but keep the content
            clean_text = re.sub(r'<[^>]+>', '', text)
        else:
            # Remove HTML tags and their content
            clean_text = re.sub(r'<[^>]*>.*?</[^>]*>', '', text, flags=re.DOTALL)
            # Also remove self-closing tags
            clean_text = re.sub(r'<[^>]*?/>', '', clean_text)
        
        # Clean up extra whitespace
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        return clean_text
