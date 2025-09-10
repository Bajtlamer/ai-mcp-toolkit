"""Text analyzer agent for comprehensive text statistics and analysis."""

import time
import re
from typing import Any, Dict, List
from mcp.types import Tool
import textstat

from .base_agent import BaseAgent
from ..utils.url_fetcher import fetch_url_content


class TextAnalyzerAgent(BaseAgent):
    """Agent for analyzing text statistics and linguistic properties."""

    def get_tools(self) -> List[Tool]:
        """Return list of tools provided by this agent."""
        return [
            Tool(
                name="analyze_text_basic",
                description="Analyze basic text statistics from text input or URL content",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "The text to analyze (either this or 'url' must be provided)"
                        },
                        "url": {
                            "type": "string",
                            "description": "URL to fetch content from and analyze (either this or 'text' must be provided)"
                        },
                        "include_whitespace": {
                            "type": "boolean",
                            "description": "Whether to include whitespace in character count",
                            "default": True
                        }
                    }
                }
            ),
            Tool(
                name="analyze_readability",
                description="Analyze text readability from text input or URL content",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "The text to analyze for readability (either this or 'url' must be provided)"
                        },
                        "url": {
                            "type": "string",
                            "description": "URL to fetch content from and analyze readability (either this or 'text' must be provided)"
                        },
                        "metrics": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Specific readability metrics to calculate",
                            "default": ["flesch_kincaid", "flesch_reading_ease", "coleman_liau", "automated_readability"]
                        }
                    }
                }
            ),
            Tool(
                name="word_frequency_analysis",
                description="Analyze word frequency and distribution from text input or URL content",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "The text to analyze for word frequency (either this or 'url' must be provided)"
                        },
                        "url": {
                            "type": "string",
                            "description": "URL to fetch content from and analyze word frequency (either this or 'text' must be provided)"
                        },
                        "top_n": {
                            "type": "integer",
                            "description": "Number of most frequent words to return",
                            "default": 10
                        },
                        "min_length": {
                            "type": "integer",
                            "description": "Minimum word length to include",
                            "default": 3
                        },
                        "exclude_common": {
                            "type": "boolean",
                            "description": "Whether to exclude common stop words",
                            "default": True
                        }
                    }
                }
            ),
            Tool(
                name="text_complexity_analysis",
                description="Analyze text complexity from text input or URL content",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "The text to analyze for complexity (either this or 'url' must be provided)"
                        },
                        "url": {
                            "type": "string",
                            "description": "URL to fetch content from and analyze complexity (either this or 'text' must be provided)"
                        }
                    }
                }
            )
        ]

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute a tool with given arguments and return result."""
        start_time = time.time()
        
        try:
            if tool_name == "analyze_text_basic":
                result = await self._analyze_text_basic(arguments)
            elif tool_name == "analyze_readability":
                result = await self._analyze_readability(arguments)
            elif tool_name == "word_frequency_analysis":
                result = await self._word_frequency_analysis(arguments)
            elif tool_name == "text_complexity_analysis":
                result = await self._text_complexity_analysis(arguments)
            else:
                raise ValueError(f"Unknown tool: {tool_name}")
            
            duration = time.time() - start_time
            self.log_execution(tool_name, arguments, duration)
            return self.format_result(result, "json")
            
        except Exception as e:
            self.logger.error(f"Error executing {tool_name}: {e}")
            raise

    async def _get_text_content(self, arguments: Dict[str, Any]) -> str:
        """Get text content from either direct input or URL."""
        text = arguments.get("text")
        url = arguments.get("url")
        
        if not text and not url:
            raise ValueError("Either 'text' or 'url' must be provided")
        
        if text and url:
            raise ValueError("Only one of 'text' or 'url' should be provided, not both")
        
        if url:
            try:
                self.logger.info(f"Fetching content from URL: {url}")
                content_data = await fetch_url_content(url)
                text = content_data['text']
                self.logger.info(f"Successfully fetched {len(text)} characters from {url}")
                
                # Add URL info to the text for context
                if content_data.get('title'):
                    text = f"Title: {content_data['title']}\n\n{text}"
                
            except Exception as e:
                self.logger.error(f"Failed to fetch content from URL {url}: {e}")
                raise ValueError(f"Failed to fetch content from URL: {str(e)}")
        
        return self.validate_text_input(text)

    async def _analyze_text_basic(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze basic text statistics."""
        text = await self._get_text_content(arguments)
        include_whitespace = arguments.get("include_whitespace", True)
        
        # Character counts
        char_count = len(text) if include_whitespace else len(text.replace(' ', '').replace('\t', '').replace('\n', ''))
        char_count_no_spaces = len(re.sub(r'\s', '', text))
        
        # Word analysis
        words = text.split()
        word_count = len(words)
        unique_words = len(set(word.lower().strip('.,!?;:"()[]') for word in words))
        avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
        
        # Sentence analysis
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        sentence_count = len(sentences)
        avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0
        
        # Paragraph analysis
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        paragraph_count = len(paragraphs)
        avg_paragraph_length = sentence_count / paragraph_count if paragraph_count > 0 else 0
        
        return {
            "character_statistics": {
                "total_characters": char_count,
                "characters_without_spaces": char_count_no_spaces,
                "whitespace_characters": char_count - char_count_no_spaces
            },
            "word_statistics": {
                "total_words": word_count,
                "unique_words": unique_words,
                "vocabulary_richness": unique_words / word_count if word_count > 0 else 0,
                "average_word_length": round(avg_word_length, 2)
            },
            "sentence_statistics": {
                "total_sentences": sentence_count,
                "average_sentence_length": round(avg_sentence_length, 2)
            },
            "paragraph_statistics": {
                "total_paragraphs": paragraph_count,
                "average_paragraph_length": round(avg_paragraph_length, 2)
            },
            "text_density": {
                "words_per_paragraph": round(word_count / paragraph_count, 2) if paragraph_count > 0 else 0,
                "characters_per_word": round(char_count_no_spaces / word_count, 2) if word_count > 0 else 0
            }
        }

    async def _analyze_readability(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze text readability using various metrics."""
        text = await self._get_text_content(arguments)
        metrics = arguments.get("metrics", ["flesch_kincaid", "flesch_reading_ease", "coleman_liau", "automated_readability"])
        
        results = {}
        
        try:
            if "flesch_kincaid" in metrics:
                results["flesch_kincaid_grade"] = {
                    "score": textstat.flesch_kincaid().grade(text),
                    "description": "Grade level needed to understand the text"
                }
        except:
            results["flesch_kincaid_grade"] = {"error": "Could not calculate"}
        
        try:
            if "flesch_reading_ease" in metrics:
                score = textstat.flesch_reading_ease(text)
                results["flesch_reading_ease"] = {
                    "score": score,
                    "level": self._get_flesch_level(score),
                    "description": "Reading ease score (higher = easier)"
                }
        except:
            results["flesch_reading_ease"] = {"error": "Could not calculate"}
        
        try:
            if "coleman_liau" in metrics:
                results["coleman_liau_index"] = {
                    "score": textstat.coleman_liau_index(text),
                    "description": "Grade level based on characters per word and sentences per word"
                }
        except:
            results["coleman_liau_index"] = {"error": "Could not calculate"}
        
        try:
            if "automated_readability" in metrics:
                results["automated_readability_index"] = {
                    "score": textstat.automated_readability_index(text),
                    "description": "Grade level based on character and sentence length"
                }
        except:
            results["automated_readability_index"] = {"error": "Could not calculate"}
        
        return {
            "readability_metrics": results,
            "overall_assessment": self._get_readability_assessment(results)
        }

    async def _word_frequency_analysis(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze word frequency and distribution."""
        text = await self._get_text_content(arguments)
        top_n = arguments.get("top_n", 10)
        min_length = arguments.get("min_length", 3)
        exclude_common = arguments.get("exclude_common", True)
        
        # Common stop words (basic set)
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
            'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must',
            'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
            'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their'
        } if exclude_common else set()
        
        # Extract and clean words
        words = re.findall(r'\b\w+\b', text.lower())
        filtered_words = [
            word for word in words 
            if len(word) >= min_length and (not exclude_common or word not in stop_words)
        ]
        
        # Count frequencies
        word_freq = {}
        for word in filtered_words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Get top words
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:top_n]
        
        return {
            "word_frequency": {
                "total_words_analyzed": len(filtered_words),
                "unique_words": len(word_freq),
                "most_frequent": [{"word": word, "count": count, "frequency": count/len(filtered_words)} for word, count in top_words]
            },
            "analysis_parameters": {
                "minimum_word_length": min_length,
                "excluded_common_words": exclude_common,
                "total_unique_words_found": len(word_freq)
            }
        }

    async def _text_complexity_analysis(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze text complexity including vocabulary richness and sentence structure."""
        text = await self._get_text_content(arguments)
        
        words = text.split()
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Vocabulary richness (Type-Token Ratio)
        unique_words = set(word.lower().strip('.,!?;:"()[]') for word in words)
        ttr = len(unique_words) / len(words) if words else 0
        
        # Sentence complexity
        avg_sentence_length = len(words) / len(sentences) if sentences else 0
        
        # Lexical diversity
        word_lengths = [len(word.strip('.,!?;:"()[]')) for word in words]
        avg_word_length = sum(word_lengths) / len(word_lengths) if word_lengths else 0
        
        # Syllable complexity (rough estimation)
        syllable_count = sum(self._estimate_syllables(word.strip('.,!?;:"()[]')) for word in words)
        avg_syllables_per_word = syllable_count / len(words) if words else 0
        
        complexity_score = (
            (avg_sentence_length / 20) * 0.3 +  # Sentence length factor
            (avg_word_length / 8) * 0.2 +       # Word length factor
            (avg_syllables_per_word / 3) * 0.3 + # Syllable factor
            ((1 - ttr) * 2) * 0.2               # Vocabulary repetition factor
        )
        
        return {
            "complexity_metrics": {
                "type_token_ratio": round(ttr, 3),
                "average_sentence_length": round(avg_sentence_length, 2),
                "average_word_length": round(avg_word_length, 2),
                "average_syllables_per_word": round(avg_syllables_per_word, 2),
                "complexity_score": round(complexity_score, 3)
            },
            "complexity_assessment": self._get_complexity_assessment(complexity_score),
            "vocabulary_analysis": {
                "total_words": len(words),
                "unique_words": len(unique_words),
                "vocabulary_richness": round(ttr, 3)
            }
        }

    def _get_flesch_level(self, score: float) -> str:
        """Get Flesch reading ease level description."""
        if score >= 90:
            return "Very Easy"
        elif score >= 80:
            return "Easy"
        elif score >= 70:
            return "Fairly Easy"
        elif score >= 60:
            return "Standard"
        elif score >= 50:
            return "Fairly Difficult"
        elif score >= 30:
            return "Difficult"
        else:
            return "Very Difficult"

    def _get_readability_assessment(self, results: Dict) -> str:
        """Get overall readability assessment."""
        scores = []
        for metric, data in results.items():
            if isinstance(data, dict) and "score" in data:
                if "flesch_reading_ease" in metric:
                    scores.append(data["score"] / 10)  # Normalize to roughly 0-10 scale
                else:
                    scores.append(min(data["score"], 20) / 2)  # Cap at grade 20, normalize to 0-10
        
        if not scores:
            return "Unable to assess"
        
        avg_score = sum(scores) / len(scores)
        if avg_score <= 3:
            return "Elementary level"
        elif avg_score <= 6:
            return "Middle school level"
        elif avg_score <= 9:
            return "High school level"
        elif avg_score <= 12:
            return "College level"
        else:
            return "Graduate level"

    def _get_complexity_assessment(self, score: float) -> str:
        """Get complexity assessment based on score."""
        if score <= 0.3:
            return "Simple"
        elif score <= 0.6:
            return "Moderate"
        elif score <= 0.8:
            return "Complex"
        else:
            return "Very Complex"

    def _estimate_syllables(self, word: str) -> int:
        """Estimate syllable count for a word."""
        word = word.lower()
        if not word:
            return 0
        
        # Count vowel groups
        vowels = 'aeiouy'
        syllables = 0
        prev_was_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_was_vowel:
                syllables += 1
            prev_was_vowel = is_vowel
        
        # Handle silent e
        if word.endswith('e') and syllables > 1:
            syllables -= 1
        
        return max(1, syllables)  # Every word has at least one syllable
