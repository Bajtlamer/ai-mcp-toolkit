"""Diacritic remover agent for removing accents and diacritical marks from text."""

import time
from typing import Any, Dict, List
from mcp.types import Tool
import unidecode

from .base_agent import BaseAgent


class DiacriticRemoverAgent(BaseAgent):
    """Agent for removing diacritical marks and accents from text."""

    def get_tools(self) -> List[Tool]:
        """Return list of tools provided by this agent."""
        return [
            Tool(
                name="remove_diacritics",
                description="Remove diacritical marks and accents from text",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "The text from which to remove diacritics"
                        },
                        "method": {
                            "type": "string",
                            "description": "Method to use for diacritic removal (unicode, unidecode)",
                            "enum": ["unicode", "unidecode"],
                            "default": "unidecode"
                        },
                        "preserve_case": {
                            "type": "boolean",
                            "description": "Whether to preserve the original case",
                            "default": True
                        }
                    },
                    "required": ["text"]
                }
            ),
            Tool(
                name="transliterate_text",
                description="Transliterate text to ASCII characters",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "The text to transliterate"
                        },
                        "preserve_spacing": {
                            "type": "boolean",
                            "description": "Whether to preserve original spacing",
                            "default": True
                        }
                    },
                    "required": ["text"]
                }
            ),
            Tool(
                name="normalize_text",
                description="Normalize text by removing diacritics and applying various transformations",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "The text to normalize"
                        },
                        "remove_diacritics": {
                            "type": "boolean",
                            "description": "Whether to remove diacritical marks",
                            "default": True
                        },
                        "to_lowercase": {
                            "type": "boolean",
                            "description": "Whether to convert to lowercase",
                            "default": False
                        },
                        "replace_spaces": {
                            "type": "boolean",
                            "description": "Whether to replace spaces with underscores",
                            "default": False
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
            if tool_name == "remove_diacritics":
                result = await self._remove_diacritics(arguments)
            elif tool_name == "transliterate_text":
                result = await self._transliterate_text(arguments)
            elif tool_name == "normalize_text":
                result = await self._normalize_text(arguments)
            else:
                raise ValueError(f"Unknown tool: {tool_name}")
            
            duration = time.time() - start_time
            self.log_execution(tool_name, arguments, duration)
            return result
            
        except Exception as e:
            self.logger.error(f"Error executing {tool_name}: {e}")
            raise

    async def _remove_diacritics(self, arguments: Dict[str, Any]) -> str:
        """Remove diacritical marks from text."""
        text = self.validate_text_input(arguments["text"])
        method = arguments.get("method", "unidecode")
        preserve_case = arguments.get("preserve_case", True)
        
        original_case = None
        if preserve_case:
            # Store case information
            original_case = [c.isupper() for c in text]
        
        if method == "unidecode":
            # Use unidecode for comprehensive transliteration
            result = unidecode.unidecode(text)
        elif method == "unicode":
            # Use Unicode normalization to remove diacritics
            import unicodedata
            # Normalize to decomposed form (NFD) and remove combining characters
            normalized = unicodedata.normalize('NFD', text)
            result = ''.join(
                char for char in normalized
                if unicodedata.category(char) != 'Mn'  # Remove combining marks
            )
        else:
            raise ValueError(f"Unknown method: {method}")
        
        if preserve_case and original_case:
            # Restore original case
            result_chars = list(result)
            for i, (char, was_upper) in enumerate(zip(result_chars, original_case)):
                if i < len(result_chars):
                    if was_upper:
                        result_chars[i] = char.upper()
                    else:
                        result_chars[i] = char.lower()
            result = ''.join(result_chars)
        
        return result

    async def _transliterate_text(self, arguments: Dict[str, Any]) -> str:
        """Transliterate text to ASCII characters."""
        text = self.validate_text_input(arguments["text"])
        preserve_spacing = arguments.get("preserve_spacing", True)
        
        # Use unidecode for transliteration
        result = unidecode.unidecode(text)
        
        if not preserve_spacing:
            # Normalize spacing
            import re
            result = re.sub(r'\s+', ' ', result).strip()
        
        return result

    async def _normalize_text(self, arguments: Dict[str, Any]) -> str:
        """Normalize text with multiple transformations."""
        text = self.validate_text_input(arguments["text"])
        
        remove_diacritics = arguments.get("remove_diacritics", True)
        to_lowercase = arguments.get("to_lowercase", False)
        replace_spaces = arguments.get("replace_spaces", False)
        
        result = text
        
        if remove_diacritics:
            result = unidecode.unidecode(result)
        
        if to_lowercase:
            result = result.lower()
        
        if replace_spaces:
            result = result.replace(' ', '_')
        
        return result
