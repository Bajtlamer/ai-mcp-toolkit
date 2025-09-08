"""Grammar checker agent using Ollama for AI-powered grammar and style checking."""

import time
from typing import Any, Dict, List
from mcp.types import Tool

from .base_agent import BaseAgent
from ..models.ollama_client import OllamaClient, ChatMessage


class GrammarCheckerAgent(BaseAgent):
    """Agent for checking and correcting grammar, spelling, and style issues using AI."""

    def __init__(self, config):
        """Initialize the grammar checker agent."""
        super().__init__(config)
        self.ollama_client = OllamaClient(config)

    def get_tools(self) -> List[Tool]:
        """Return list of tools provided by this agent."""
        return [
            Tool(
                name="check_grammar",
                description="Check and correct grammar, spelling, and basic style issues in text",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "The text to check for grammar and spelling issues"
                        },
                        "correction_level": {
                            "type": "string",
                            "description": "Level of corrections to apply",
                            "enum": ["basic", "standard", "advanced"],
                            "default": "standard"
                        },
                        "style": {
                            "type": "string",
                            "description": "Writing style to optimize for",
                            "enum": ["formal", "casual", "academic", "business"],
                            "default": "standard"
                        },
                        "preserve_tone": {
                            "type": "boolean",
                            "description": "Whether to preserve the original tone and voice",
                            "default": True
                        }
                    },
                    "required": ["text"]
                }
            ),
            Tool(
                name="suggest_improvements",
                description="Suggest style and clarity improvements for text",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "The text to analyze for improvement suggestions"
                        },
                        "focus_areas": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Specific areas to focus on for improvements",
                            "default": ["clarity", "conciseness", "flow"]
                        }
                    },
                    "required": ["text"]
                }
            ),
            Tool(
                name="explain_corrections",
                description="Explain grammar rules and corrections made to text",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "original_text": {
                            "type": "string",
                            "description": "The original text before corrections"
                        },
                        "corrected_text": {
                            "type": "string",
                            "description": "The corrected version of the text"
                        }
                    },
                    "required": ["original_text", "corrected_text"]
                }
            )
        ]

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute a tool with given arguments and return result."""
        start_time = time.time()
        
        try:
            if tool_name == "check_grammar":
                result = await self._check_grammar(arguments)
            elif tool_name == "suggest_improvements":
                result = await self._suggest_improvements(arguments)
            elif tool_name == "explain_corrections":
                result = await self._explain_corrections(arguments)
            else:
                raise ValueError(f"Unknown tool: {tool_name}")
            
            duration = time.time() - start_time
            self.log_execution(tool_name, arguments, duration)
            return result
            
        except Exception as e:
            self.logger.error(f"Error executing {tool_name}: {e}")
            raise

    async def _check_grammar(self, arguments: Dict[str, Any]) -> str:
        """Check and correct grammar in text using AI."""
        text = self.validate_text_input(arguments["text"])
        correction_level = arguments.get("correction_level", "standard")
        style = arguments.get("style", "standard")
        preserve_tone = arguments.get("preserve_tone", True)
        
        # Build system prompt based on parameters
        system_prompt = self._build_grammar_system_prompt(correction_level, style, preserve_tone)
        
        # Use chat format for better control
        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=f"Please check and correct this text:\n\n{text}")
        ]
        
        async with self.ollama_client as client:
            await client.ensure_model_available()
            response = await client.chat_completion(messages=messages)
            
            # Clean up response
            corrected_text = response.response.strip()
            
            # If the AI included explanations, try to extract just the corrected text
            if "\n\n" in corrected_text:
                # Look for patterns that might indicate the corrected text
                lines = corrected_text.split("\n")
                for i, line in enumerate(lines):
                    if line.strip() and not line.startswith(("Corrected", "Here", "The", "I've", "Changes")):
                        # This might be the start of the corrected text
                        corrected_text = "\n".join(lines[i:])
                        break
            
            return corrected_text

    async def _suggest_improvements(self, arguments: Dict[str, Any]) -> str:
        """Suggest improvements for text clarity and style."""
        text = self.validate_text_input(arguments["text"])
        focus_areas = arguments.get("focus_areas", ["clarity", "conciseness", "flow"])
        
        focus_str = ", ".join(focus_areas)
        
        system_prompt = f"""You are a writing improvement specialist. Analyze the provided text and suggest specific improvements focusing on {focus_str}.

Provide your suggestions in the following format:
1. **Improvement Area**: [Brief description]
   - **Issue**: [What could be improved]
   - **Suggestion**: [How to improve it]
   - **Example**: [Show the improvement if applicable]

Focus on practical, actionable suggestions that will make the writing more effective."""
        
        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=f"Please analyze this text and suggest improvements:\n\n{text}")
        ]
        
        async with self.ollama_client as client:
            await client.ensure_model_available()
            response = await client.chat_completion(messages=messages)
            return response.response

    async def _explain_corrections(self, arguments: Dict[str, Any]) -> str:
        """Explain the corrections made to text."""
        original_text = self.validate_text_input(arguments["original_text"])
        corrected_text = self.validate_text_input(arguments["corrected_text"])
        
        system_prompt = """You are a grammar and writing expert. Compare the original and corrected texts and explain the changes made.

Provide explanations in this format:
1. **Change**: [Describe what was changed]
   - **Rule/Reason**: [Grammar rule or writing principle that applies]
   - **Example**: Show the before and after

Focus on educational explanations that help the user understand the reasoning behind each correction."""
        
        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=f"Original text:\n{original_text}\n\nCorrected text:\n{corrected_text}\n\nPlease explain the corrections made.")
        ]
        
        async with self.ollama_client as client:
            await client.ensure_model_available()
            response = await client.chat_completion(messages=messages)
            return response.response

    def _build_grammar_system_prompt(self, correction_level: str, style: str, preserve_tone: bool) -> str:
        """Build system prompt for grammar checking based on parameters."""
        base_prompt = "You are an expert grammar checker and editor. Your task is to correct grammar, spelling, and punctuation errors in the provided text."
        
        if correction_level == "basic":
            level_instruction = "Focus only on obvious grammar, spelling, and punctuation errors. Make minimal changes."
        elif correction_level == "standard":
            level_instruction = "Correct grammar, spelling, punctuation, and basic style issues. Improve clarity where needed."
        else:  # advanced
            level_instruction = "Provide comprehensive corrections including grammar, spelling, punctuation, style, word choice, and sentence structure improvements."
        
        style_instruction = ""
        if style != "standard":
            style_map = {
                "formal": "Ensure the text maintains a formal, professional tone with proper grammar and sophisticated vocabulary.",
                "casual": "Keep the text conversational and approachable while maintaining correctness.",
                "academic": "Use precise, scholarly language appropriate for academic writing with proper citations format if applicable.",
                "business": "Optimize for business communication - clear, concise, and professional."
            }
            style_instruction = style_map.get(style, "")
        
        tone_instruction = "Preserve the original author's voice and tone while making corrections." if preserve_tone else "Feel free to adjust tone and voice as needed for better communication."
        
        return f"{base_prompt}\n\n{level_instruction}\n\n{style_instruction}\n\n{tone_instruction}\n\nProvide only the corrected text without explanations unless specifically requested."
