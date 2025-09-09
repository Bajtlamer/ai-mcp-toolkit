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
- Confidence: [0-100%] (Use 95-100% for very clear sentiment, 85-94% for clear sentiment, 70-84% for moderate sentiment, below 70% for ambiguous sentiment)
- Intensity: [low/medium/high]
- Key Indicators: [words/phrases that indicate sentiment]
- Explanation: [brief reasoning]"""
        
        if include_emotions:
            format_instruction += "\n- Emotions Detected: [list with intensity levels]"
        
        return f"{base_prompt}\n\n{analysis_instruction}\n\n{emotion_instruction}\n\n{format_instruction}"

    def _parse_sentiment_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response into structured sentiment data."""
        import re
        
        result = {
            "overall_sentiment": "neutral",
            "confidence": 0.5,
            "intensity": "medium",
            "key_indicators": [],
            "explanation": response,
            "emotions_detected": []
        }
        
        # Parse Overall Sentiment with multiple pattern variations
        sentiment_patterns = [
            r'\*\*Overall Sentiment:\*\*\s*([^\n]+)',
            r'Overall Sentiment:\s*([^\n]+)',
            r'Sentiment:\s*([^\n]+)',
            r'\*\*Sentiment:\*\*\s*([^\n]+)'
        ]
        
        sentiment_found = None
        for pattern in sentiment_patterns:
            sentiment_match = re.search(pattern, response, re.IGNORECASE)
            if sentiment_match:
                sentiment_found = sentiment_match.group(1).strip().lower()
                break
        
        if sentiment_found:
            # Check for negative indicators first (more specific)
            if any(neg_word in sentiment_found for neg_word in ["negative", "very negative", "extremely negative", "highly negative", "strongly negative"]):
                result["overall_sentiment"] = "negative"
            elif any(pos_word in sentiment_found for pos_word in ["positive", "very positive", "extremely positive", "highly positive", "strongly positive"]):
                result["overall_sentiment"] = "positive"
            else:
                result["overall_sentiment"] = "neutral"
        
        # Parse Confidence
        confidence_match = re.search(r'\*\*Confidence:\*\*\s*(\d+(?:\.\d+)?)%?', response, re.IGNORECASE)
        if confidence_match:
            try:
                conf_value = float(confidence_match.group(1))
                # If the value is greater than 1, it's likely a percentage (e.g., 95)
                # Convert to decimal (e.g., 0.95)
                result["confidence"] = conf_value / 100 if conf_value > 1 else conf_value
            except ValueError:
                pass
        
        # Parse Intensity
        intensity_match = re.search(r'\*\*Intensity:\*\*\s*([^\n]+)', response, re.IGNORECASE)
        if intensity_match:
            intensity = intensity_match.group(1).strip().lower()
            result["intensity"] = intensity
        
        # Parse Key Indicators - extract quoted phrases from the response
        key_indicators = []
        # Look for quoted strings in the entire response that appear to be sentiment indicators
        quoted_phrases = re.findall(r'"([^"]+)"', response)
        seen_indicators = set()
        for phrase in quoted_phrases:
            # Filter to likely sentiment indicators (avoid long descriptions)
            if len(phrase.split()) <= 4 and phrase.strip():
                phrase_clean = phrase.strip().lower()
                if phrase_clean not in seen_indicators:
                    key_indicators.append(phrase.strip())
                    seen_indicators.add(phrase_clean)
        
        result["key_indicators"] = key_indicators
        
        # Parse Emotions - look for emotion patterns in the response
        emotions = []
        # Look for patterns like "* **Joy**: High (intensity level 8/10)"
        emotion_patterns = [
            r'\*\s*\*\*([A-Za-z]+)\*\*:\s*([^(\n]+)(?:\s*\(intensity level (\d+)/10\))?',  # * **Joy**: High (intensity level 8/10)
            r'\*\s*([A-Za-z]+):\s*([^(\n]+)(?:\s*\(intensity level (\d+)/10\))?',         # * Joy: High (intensity level 8/10)
            r'\*\s*\*\*([A-Za-z]+)\*\*\s*\(([^)]+)\)',                                      # * **Joy** (High)
        ]
        
        for pattern in emotion_patterns:
            emotion_matches = re.findall(pattern, response, re.IGNORECASE)
            for match in emotion_matches:
                if len(match) >= 2:
                    emotion = match[0].strip() if match[0] else ''
                    intensity_desc = match[1].strip() if match[1] else ''
                    intensity_level = match[2] if len(match) > 2 and match[2] else None
                    
                    # Parse intensity
                    intensity = 50  # default
                    
                    # First try to use the numeric intensity level if available
                    if intensity_level:
                        try:
                            intensity = int(intensity_level) * 10
                        except ValueError:
                            pass
                    else:
                        # Fall back to text-based intensity
                        if 'high' in intensity_desc.lower():
                            intensity = 80
                        elif 'medium' in intensity_desc.lower():
                            intensity = 60
                        elif 'low' in intensity_desc.lower():
                            intensity = 30
                    
                    # Filter out non-emotion words
                    non_emotions = {'confidence', 'intensity', 'explanation', 'overall', 'sentiment', 'analysis', 'detected', 'level'}
                    if emotion and emotion.lower() not in non_emotions and not any(e['emotion'].lower() == emotion.lower() for e in emotions):
                        emotions.append({
                            "emotion": emotion,
                            "intensity": intensity
                        })
        
        result["emotions_detected"] = emotions
        
        return result
