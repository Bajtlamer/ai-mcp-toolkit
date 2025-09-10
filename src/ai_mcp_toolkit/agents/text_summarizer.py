"""Text summarizer agent using AI for generating concise summaries."""

import time
from typing import Any, Dict, List
from mcp.types import Tool

from .base_agent import BaseAgent
from ..models.ollama_client import OllamaClient, ChatMessage


class TextSummarizerAgent(BaseAgent):
    """Agent for generating concise summaries of longer texts using AI."""

    def __init__(self, config):
        """Initialize the text summarizer agent."""
        super().__init__(config)
        self.ollama_client = OllamaClient(config)

    def get_tools(self) -> List[Tool]:
        """Return list of tools provided by this agent."""
        return [
            Tool(
                name="summarize_text",
                description="Generate a concise summary of the provided text",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "The text to summarize"
                        },
                        "summary_type": {
                            "type": "string",
                            "description": "Type of summary to generate",
                            "enum": ["extractive", "abstractive", "bullet_points", "key_insights"],
                            "default": "abstractive"
                        },
                        "length": {
                            "type": "string",
                            "description": "Desired summary length",
                            "enum": ["short", "medium", "long"],
                            "default": "short"
                        },
                        "compression_ratio": {
                            "type": "string",
                            "description": "How aggressively to compress the text",
                            "enum": ["extreme", "high", "medium", "low"],
                            "default": "high"
                        },
                        "focus": {
                            "type": "string",
                            "description": "What to focus on in the summary",
                            "enum": ["main_points", "conclusions", "actions", "facts", "opinions"],
                            "default": "main_points"
                        }
                    },
                    "required": ["text"]
                }
            ),
            Tool(
                name="extract_key_points",
                description="Extract key points and main ideas from text",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "The text to extract key points from"
                        },
                        "max_points": {
                            "type": "integer",
                            "description": "Maximum number of key points to extract",
                            "default": 5
                        },
                        "include_context": {
                            "type": "boolean",
                            "description": "Whether to include context for each key point",
                            "default": True
                        }
                    },
                    "required": ["text"]
                }
            ),
            Tool(
                name="generate_headlines",
                description="Generate catchy headlines or titles for the text",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "The text to generate headlines for"
                        },
                        "count": {
                            "type": "integer",
                            "description": "Number of headline options to generate",
                            "default": 3
                        },
                        "style": {
                            "type": "string",
                            "description": "Style of headlines to generate",
                            "enum": ["neutral", "catchy", "professional", "academic"],
                            "default": "neutral"
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
            if tool_name == "summarize_text":
                result = await self._summarize_text(arguments)
            elif tool_name == "extract_key_points":
                result = await self._extract_key_points(arguments)
            elif tool_name == "generate_headlines":
                result = await self._generate_headlines(arguments)
            else:
                raise ValueError(f"Unknown tool: {tool_name}")
            
            duration = time.time() - start_time
            self.log_execution(tool_name, arguments, duration)
            return result
            
        except Exception as e:
            self.logger.error(f"Error executing {tool_name}: {e}")
            raise

    async def _summarize_text(self, arguments: Dict[str, Any]) -> str:
        """Generate a summary of the text."""
        text = self.validate_text_input(arguments["text"])
        summary_type = arguments.get("summary_type", "abstractive")
        length = arguments.get("length", "short")
        focus = arguments.get("focus", "main_points")
        compression_ratio = arguments.get("compression_ratio", "high")
        
        system_prompt = self._build_summary_system_prompt(summary_type, length, focus, compression_ratio)
        
        # For very long texts, we might need to chunk them
        if len(text) > self.config.chunk_size:
            chunks = self.chunk_text(text)
            summaries = []
            
            for i, chunk in enumerate(chunks):
                messages = [
                    ChatMessage(role="system", content=system_prompt),
                    ChatMessage(role="user", content=f"Summarize this text (part {i+1} of {len(chunks)}):\n\n{chunk}")
                ]
                
                async with self.ollama_client as client:
                    await client.ensure_model_available()
                    response = await client.chat_completion(messages=messages)
                    summaries.append(response.response.strip())
            
            # If we have multiple summaries, combine them
            if len(summaries) > 1:
                combined_summaries = "\n\n".join([f"Part {i+1}: {summary}" for i, summary in enumerate(summaries)])
                
                # Generate a final summary of the summaries
                final_prompt = f"Combine these partial summaries into one coherent {length} summary:\n\n{combined_summaries}"
                messages = [
                    ChatMessage(role="system", content=system_prompt),
                    ChatMessage(role="user", content=final_prompt)
                ]
                
                async with self.ollama_client as client:
                    response = await client.chat_completion(messages=messages)
                    return response.response.strip()
            else:
                return summaries[0]
        else:
            messages = [
                ChatMessage(role="system", content=system_prompt),
                ChatMessage(role="user", content=f"Summarize this text:\n\n{text}")
            ]
            
            async with self.ollama_client as client:
                await client.ensure_model_available()
                response = await client.chat_completion(messages=messages)
                return response.response.strip()

    async def _extract_key_points(self, arguments: Dict[str, Any]) -> str:
        """Extract key points from text."""
        text = self.validate_text_input(arguments["text"])
        max_points = arguments.get("max_points", 5)
        include_context = arguments.get("include_context", True)
        
        context_instruction = "with brief context for each point" if include_context else "as concise statements"
        
        system_prompt = f"""You are an expert at identifying key information in text. Extract the {max_points} most important key points from the provided text.

Present the key points as a numbered list {context_instruction}. Focus on the most significant ideas, findings, or conclusions that someone should know about this text."""
        
        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=f"Extract key points from this text:\n\n{text}")
        ]
        
        async with self.ollama_client as client:
            await client.ensure_model_available()
            response = await client.chat_completion(messages=messages)
            return response.response.strip()

    async def _generate_headlines(self, arguments: Dict[str, Any]) -> str:
        """Generate headlines for the text."""
        text = self.validate_text_input(arguments["text"])
        count = arguments.get("count", 3)
        style = arguments.get("style", "neutral")
        
        style_instructions = {
            "neutral": "straightforward and informative",
            "catchy": "engaging and attention-grabbing",
            "professional": "formal and business-appropriate",
            "academic": "scholarly and precise"
        }
        
        style_instruction = style_instructions.get(style, "neutral and informative")
        
        system_prompt = f"""You are a skilled headline writer. Generate {count} {style_instruction} headlines or titles that accurately capture the essence of the provided text.

Each headline should be:
- Concise and clear
- Accurately representative of the content
- {style_instruction} in tone

Present the headlines as a numbered list."""
        
        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=f"Generate headlines for this text:\n\n{text}")
        ]
        
        async with self.ollama_client as client:
            await client.ensure_model_available()
            response = await client.chat_completion(messages=messages)
            return response.response.strip()

    def _build_summary_system_prompt(self, summary_type: str, length: str, focus: str, compression_ratio: str) -> str:
        """Build system prompt for text summarization."""
        base_prompt = "You are an expert text summarizer. Your task is to create a high-quality, extremely concise summary that dramatically reduces the original text length while preserving essential information."
        
        type_instructions = {
            "extractive": "Extract and combine ONLY the most critical sentences from the original text.",
            "abstractive": "Create a new, highly compressed version that captures ONLY the core essence in your own words.",
            "bullet_points": "Summarize as the most essential bullet points only.",
            "key_insights": "Focus ONLY on the most crucial insights and conclusions."
        }
        
        # More aggressive length targets
        length_instructions = {
            "short": "Keep the summary extremely brief - maximum 1-2 sentences or 20-50 words.",
            "medium": "Create a concise summary - maximum 2-3 sentences or 50-80 words.",
            "long": "Provide a detailed but still compressed summary - maximum 1 paragraph or 80-120 words."
        }
        
        # New compression ratio instructions
        compression_instructions = {
            "extreme": "Compress to less than 5% of original length. Use only the most essential words and phrases.",
            "high": "Compress to 5-10% of original length. Be extremely selective about what to include.",
            "medium": "Compress to 10-20% of original length. Focus on core concepts only.",
            "low": "Compress to 20-30% of original length. Include main points with minimal detail."
        }
        
        focus_instructions = {
            "main_points": "Focus ONLY on the most critical central arguments and primary themes.",
            "conclusions": "Emphasize ONLY the most important conclusions, results, and final outcomes.",
            "actions": "Highlight ONLY the most essential actionable items and recommendations.",
            "facts": "Prioritize ONLY the most crucial factual information and data.",
            "opinions": "Focus ONLY on the most significant viewpoints and assessments."
        }
        
        type_instruction = type_instructions.get(summary_type, type_instructions["abstractive"])
        length_instruction = length_instructions.get(length, length_instructions["short"])
        focus_instruction = focus_instructions.get(focus, focus_instructions["main_points"])
        compression_instruction = compression_instructions.get(compression_ratio, compression_instructions["high"])
        
        return f"{base_prompt}\n\n{type_instruction}\n\n{length_instruction}\n\n{focus_instruction}\n\n{compression_instruction}\n\nIMPORTANT: Be ruthlessly concise. Every word must add significant value. Eliminate all redundancy, filler words, and minor details. Your summary should be dramatically shorter than the original while capturing its essence."
