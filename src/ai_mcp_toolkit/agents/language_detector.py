"""Language detector agent for identifying text language."""

import time
from typing import Any, Dict, List
from mcp.types import Tool
from langdetect import detect, detect_langs

from .base_agent import BaseAgent


class LanguageDetectorAgent(BaseAgent):
    """Agent for detecting the language of input text."""

    def get_tools(self) -> List[Tool]:
        """Return list of tools provided by this agent."""
        return [
            Tool(
                name="detect_language",
                description="Detect the primary language of the given text",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "The text to analyze for language detection"
                        },
                        "include_confidence": {
                            "type": "boolean",
                            "description": "Whether to include confidence scores",
                            "default": True
                        }
                    },
                    "required": ["text"]
                }
            ),
            Tool(
                name="detect_multiple_languages",
                description="Detect multiple languages in text with confidence scores",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "The text to analyze for multiple languages"
                        },
                        "max_languages": {
                            "type": "integer",
                            "description": "Maximum number of languages to return",
                            "default": 3
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
            if tool_name == "detect_language":
                result = await self._detect_language(arguments)
            elif tool_name == "detect_multiple_languages":
                result = await self._detect_multiple_languages(arguments)
            else:
                raise ValueError(f"Unknown tool: {tool_name}")
            
            duration = time.time() - start_time
            self.log_execution(tool_name, arguments, duration)
            return self.format_result(result, "json")
            
        except Exception as e:
            self.logger.error(f"Error executing {tool_name}: {e}")
            raise

    async def _detect_language(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Detect the primary language of text."""
        text = self.validate_text_input(arguments["text"])
        include_confidence = arguments.get("include_confidence", True)
        
        try:
            if include_confidence:
                detected_langs = detect_langs(text)
                primary_lang = detected_langs[0] if detected_langs else None
                
                if primary_lang:
                    return {
                        "language": primary_lang.lang,
                        "language_name": self._get_language_name(primary_lang.lang),
                        "confidence": round(primary_lang.prob, 3),
                        "confidence_level": self._get_confidence_level(primary_lang.prob)
                    }
            else:
                lang_code = detect(text)
                return {
                    "language": lang_code,
                    "language_name": self._get_language_name(lang_code)
                }
        except Exception:
            return {
                "language": "unknown",
                "language_name": "Unknown",
                "error": "Could not detect language"
            }

    async def _detect_multiple_languages(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Detect multiple languages in text."""
        text = self.validate_text_input(arguments["text"])
        max_languages = arguments.get("max_languages", 3)
        
        try:
            detected_langs = detect_langs(text)
            languages = []
            
            for i, lang in enumerate(detected_langs[:max_languages]):
                languages.append({
                    "language": lang.lang,
                    "language_name": self._get_language_name(lang.lang),
                    "confidence": round(lang.prob, 3),
                    "confidence_level": self._get_confidence_level(lang.prob),
                    "rank": i + 1
                })
            
            return {
                "detected_languages": languages,
                "primary_language": languages[0] if languages else None,
                "total_candidates": len(detected_langs)
            }
        except Exception:
            return {
                "detected_languages": [],
                "error": "Could not detect languages"
            }

    def _get_language_name(self, lang_code: str) -> str:
        """Get full language name from language code."""
        language_names = {
            'en': 'English', 'es': 'Spanish', 'fr': 'French', 'de': 'German',
            'it': 'Italian', 'pt': 'Portuguese', 'ru': 'Russian', 'ja': 'Japanese',
            'ko': 'Korean', 'zh-cn': 'Chinese (Simplified)', 'zh-tw': 'Chinese (Traditional)',
            'ar': 'Arabic', 'hi': 'Hindi', 'th': 'Thai', 'vi': 'Vietnamese',
            'tr': 'Turkish', 'pl': 'Polish', 'nl': 'Dutch', 'sv': 'Swedish',
            'da': 'Danish', 'no': 'Norwegian', 'fi': 'Finnish', 'cs': 'Czech',
            'sk': 'Slovak', 'hu': 'Hungarian', 'ro': 'Romanian', 'bg': 'Bulgarian',
            'hr': 'Croatian', 'sr': 'Serbian', 'sl': 'Slovenian', 'et': 'Estonian',
            'lv': 'Latvian', 'lt': 'Lithuanian', 'uk': 'Ukrainian', 'be': 'Belarusian',
            'mk': 'Macedonian', 'sq': 'Albanian', 'ca': 'Catalan', 'eu': 'Basque',
            'gl': 'Galician', 'cy': 'Welsh', 'ga': 'Irish', 'mt': 'Maltese',
            'is': 'Icelandic', 'fo': 'Faroese', 'he': 'Hebrew', 'fa': 'Persian',
            'ur': 'Urdu', 'bn': 'Bengali', 'ta': 'Tamil', 'te': 'Telugu',
            'ml': 'Malayalam', 'kn': 'Kannada', 'gu': 'Gujarati', 'pa': 'Punjabi',
            'ne': 'Nepali', 'si': 'Sinhala', 'my': 'Burmese', 'km': 'Khmer',
            'lo': 'Lao', 'ka': 'Georgian', 'am': 'Amharic', 'sw': 'Swahili',
            'zu': 'Zulu', 'af': 'Afrikaans', 'id': 'Indonesian', 'ms': 'Malay',
            'tl': 'Filipino', 'haw': 'Hawaiian'
        }
        return language_names.get(lang_code, lang_code.title())

    def _get_confidence_level(self, confidence: float) -> str:
        """Get confidence level description."""
        if confidence >= 0.9:
            return "Very High"
        elif confidence >= 0.8:
            return "High"
        elif confidence >= 0.6:
            return "Medium"
        elif confidence >= 0.4:
            return "Low"
        else:
            return "Very Low"
