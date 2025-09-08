"""Sentiment analyzer agent using AI for emotional tone analysis."""

import time
from typing import Any, Dict, List
from mcp.types import Tool

from .base_agent import BaseAgent
from ..models.ollama_client import OllamaClient, ChatMessage


class SentimentAnalyzerAgent(BaseAgent):
    """Agent for analyzing emotional tone and sentiment of text using AI."""

    def __init__(self, config):
        """Initialize the sentiment analyzer agent."""
        super().__init__(config)
        self.ollama_client = OllamaClient(config)

    def get_tools(self) -> List[Tool]:
        """Return list of tools provided by this agent."""
        return [
            Tool(
                name="analyze_sentiment",
                description="Analyze the emotional tone and sentiment of text",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "The text to analyze for sentiment"
                        },
                        "detail_level": {
                            "type": "string",
                            "description": "Level of analysis detail",
                            "enum": ["basic", "detailed", "comprehensive"],
                            "default": "detailed"
                        },
                        "include_emotions": {
                            "type": "boolean",
                            "description": "Whether to include specific emotion detection",
                            "default": True
                        }
                    },
                    "required": ["text"]
                }
            ),
            Tool(
                name="sentiment_comparison",
                description="Compare sentiment between multiple texts",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "texts": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of texts to compare sentiment"
                        },
                        "labels": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Optional labels for each text",
                            "default": []
                        }
                    },
                    "required": ["texts"]
                }
            )
        ]

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute a tool with given arguments and return result."""
        start_time = time.time()
        
        try:
            if tool_name == "analyze_sentiment":
                result = await self._analyze_sentiment(arguments)
            elif tool_name == "sentiment_comparison":
                result = await self._sentiment_comparison(arguments)
            else:
                raise ValueError(f"Unknown tool: {tool_name}")
            
            duration = time.time() - start_time
            self.log_execution(tool_name, arguments, duration)
            return self.format_result(result, "json")
            
        except Exception as e:
            self.logger.error(f"Error executing {tool_name}: {e}")
            raise

    async def _analyze_sentiment(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze sentiment of text using AI."""
        text = self.validate_text_input(arguments["text"])
        detail_level = arguments.get("detail_level", "detailed")
        include_emotions = arguments.get("include_emotions", True)
        
        system_prompt = self._build_sentiment_system_prompt(detail_level, include_emotions)
        
        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=f"Analyze the sentiment of this text:\n\n{text}")
        ]
        
        async with self.ollama_client as client:
            await client.ensure_model_available()
            response = await client.chat_completion(messages=messages)
            
            # Parse the AI response to extract structured data
            return self._parse_sentiment_response(response.response)

    async def _sentiment_comparison(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Compare sentiment between multiple texts."""
        texts = arguments["texts"]
        labels = arguments.get("labels", [])
        
        if not texts:
            raise ValueError("At least one text must be provided")
        
        # Ensure we have labels for all texts
        if len(labels) < len(texts):
            labels.extend([f"Text {i+1}" for i in range(len(labels), len(texts))])
        
        system_prompt = """You are a sentiment analysis expert. Compare the sentiment across multiple texts and provide:
1. Individual sentiment for each text (positive/negative/neutral with confidence)
2. Overall comparison summary
3. Key differences in emotional tone

Format your response as structured data that can be parsed."""
        
        # Build comparison text
        comparison_text = "Compare the sentiment of these texts:\n\n"
        for i, (text, label) in enumerate(zip(texts, labels)):
            comparison_text += f"{label}:\n{text}\n\n"
        
        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=comparison_text)
        ]
        
        async with self.ollama_client as client:
            await client.ensure_model_available()
            response = await client.chat_completion(messages=messages)
            
            return {
                "comparison_analysis": response.response,
                "texts_analyzed": len(texts),
                "labels": labels[:len(texts)]
            }

    def _build_sentiment_system_prompt(self, detail_level: str, include_emotions: bool) -> str:
        """Build system prompt for sentiment analysis."""
        base_prompt = "You are an expert sentiment analyst. Analyze the emotional tone and sentiment of the provided text."
        
        if detail_level == "basic":
            analysis_instruction = "Provide a simple sentiment classification (positive, negative, or neutral) with a brief explanation."
        elif detail_level == "detailed":
            analysis_instruction = "Provide detailed sentiment analysis including polarity, intensity, and key sentiment indicators."
        else:  # comprehensive
            analysis_instruction = "Provide comprehensive sentiment analysis including polarity, intensity, subjectivity, emotional indicators, and contextual factors."
        
        emotion_instruction = ""
        if include_emotions:
            emotion_instruction = "Also identify specific emotions present (joy, anger, sadness, fear, surprise, disgust, etc.) with intensity levels."
        
        format_instruction = """Format your response with clear sections:
- Overall Sentiment: [positive/negative/neutral]
- Confidence: [0-100%]
- Intensity: [low/medium/high]
- Key Indicators: [words/phrases that indicate sentiment]
- Explanation: [brief reasoning]"""
        
        if include_emotions:
            format_instruction += "\n- Emotions Detected: [list with intensity levels]"
        
        return f"{base_prompt}\n\n{analysis_instruction}\n\n{emotion_instruction}\n\n{format_instruction}"

    def _parse_sentiment_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response into structured sentiment data."""
        # This is a simplified parser - in a production system, you might want more sophisticated parsing
        lines = response.strip().split('\n')
        result = {
            "overall_sentiment": "neutral",
            "confidence": 0.5,
            "intensity": "medium",
            "key_indicators": [],
            "explanation": response,
            "emotions_detected": []
        }
        
        for line in lines:
            line = line.strip()
            if line.startswith("Overall Sentiment:"):
                sentiment = line.split(":", 1)[1].strip().lower()
                if "positive" in sentiment:
                    result["overall_sentiment"] = "positive"
                elif "negative" in sentiment:
                    result["overall_sentiment"] = "negative"
                else:
                    result["overall_sentiment"] = "neutral"
            elif line.startswith("Confidence:"):
                try:
                    conf_str = line.split(":", 1)[1].strip().replace("%", "")
                    result["confidence"] = float(conf_str) / 100
                except:
                    pass
            elif line.startswith("Intensity:"):
                intensity = line.split(":", 1)[1].strip().lower()
                result["intensity"] = intensity
            elif line.startswith("Key Indicators:"):
                indicators = line.split(":", 1)[1].strip()
                result["key_indicators"] = [ind.strip() for ind in indicators.split(",") if ind.strip()]
        
        return result
