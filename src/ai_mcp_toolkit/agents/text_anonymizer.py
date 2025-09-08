"""Text anonymizer agent for removing or replacing sensitive personal information."""

import re
import time
import hashlib
from typing import Any, Dict, List, Optional, Tuple
from mcp.types import Tool

from .base_agent import BaseAgent
from ..models.ollama_client import OllamaClient, ChatMessage


class TextAnonymizerAgent(BaseAgent):
    """Agent for anonymizing sensitive information in text."""

    def __init__(self, config):
        """Initialize the text anonymizer agent."""
        super().__init__(config)
        self.ollama_client = OllamaClient(config)
        
        # Common patterns for sensitive data
        self.patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            'ssn': r'\b\d{3}-?\d{2}-?\d{4}\b',
            'credit_card': r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
            'ip_address': r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
            'url': r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:\w)*)?)?',
            'date': r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',
            'address_number': r'\b\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Court|Ct)\b',
        }

    def get_tools(self) -> List[Tool]:
        """Return list of tools provided by this agent."""
        return [
            Tool(
                name="anonymize_text",
                description="Remove or replace sensitive information in text with placeholders",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "The text to anonymize"
                        },
                        "anonymization_level": {
                            "type": "string",
                            "description": "Level of anonymization to apply",
                            "enum": ["basic", "standard", "aggressive"],
                            "default": "standard"
                        },
                        "replacement_strategy": {
                            "type": "string",
                            "description": "How to replace sensitive information",
                            "enum": ["placeholder", "fake_data", "hash", "remove"],
                            "default": "placeholder"
                        },
                        "preserve_structure": {
                            "type": "boolean",
                            "description": "Whether to maintain text structure and readability",
                            "default": True
                        },
                        "custom_patterns": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Custom regex patterns to anonymize",
                            "default": []
                        }
                    },
                    "required": ["text"]
                }
            ),
            Tool(
                name="detect_sensitive_info",
                description="Detect and identify sensitive information in text without anonymizing",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "The text to scan for sensitive information"
                        },
                        "detection_types": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Types of sensitive info to detect",
                            "default": ["names", "emails", "phones", "addresses", "ids", "financial"]
                        },
                        "confidence_threshold": {
                            "type": "number",
                            "description": "Minimum confidence threshold for AI detection",
                            "default": 0.7
                        }
                    },
                    "required": ["text"]
                }
            ),
            Tool(
                name="smart_anonymize",
                description="Use AI to intelligently identify and anonymize personal information",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "The text to anonymize using AI"
                        },
                        "context": {
                            "type": "string",
                            "description": "Context about the text type (email, report, document, etc.)",
                            "default": "general"
                        },
                        "preserve_meaning": {
                            "type": "boolean",
                            "description": "Whether to preserve the overall meaning while anonymizing",
                            "default": True
                        }
                    },
                    "required": ["text"]
                }
            ),
            Tool(
                name="create_anonymization_report",
                description="Generate a report of what sensitive information was found and anonymized",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "original_text": {
                            "type": "string",
                            "description": "The original text before anonymization"
                        },
                        "anonymized_text": {
                            "type": "string",
                            "description": "The text after anonymization"
                        }
                    },
                    "required": ["original_text", "anonymized_text"]
                }
            )
        ]

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute a tool with given arguments and return result."""
        start_time = time.time()
        
        try:
            if tool_name == "anonymize_text":
                result = await self._anonymize_text(arguments)
            elif tool_name == "detect_sensitive_info":
                result = await self._detect_sensitive_info(arguments)
            elif tool_name == "smart_anonymize":
                result = await self._smart_anonymize(arguments)
            elif tool_name == "create_anonymization_report":
                result = await self._create_anonymization_report(arguments)
            else:
                raise ValueError(f"Unknown tool: {tool_name}")
            
            duration = time.time() - start_time
            self.log_execution(tool_name, arguments, duration)
            
            if isinstance(result, dict):
                return self.format_result(result, "json")
            return result
            
        except Exception as e:
            self.logger.error(f"Error executing {tool_name}: {e}")
            raise

    async def _anonymize_text(self, arguments: Dict[str, Any]) -> str:
        """Anonymize sensitive information in text using rule-based approach."""
        text = self.validate_text_input(arguments["text"])
        anonymization_level = arguments.get("anonymization_level", "standard")
        replacement_strategy = arguments.get("replacement_strategy", "placeholder")
        preserve_structure = arguments.get("preserve_structure", True)
        custom_patterns = arguments.get("custom_patterns", [])
        
        anonymized_text = text
        replacements = {}
        
        # Apply pattern-based anonymization
        patterns_to_use = self._get_patterns_for_level(anonymization_level)
        
        # Add custom patterns
        for i, pattern in enumerate(custom_patterns):
            patterns_to_use[f'custom_{i}'] = pattern
        
        for pattern_name, pattern in patterns_to_use.items():
            matches = re.finditer(pattern, anonymized_text, re.IGNORECASE)
            for match in matches:
                original = match.group()
                replacement = self._generate_replacement(
                    original, pattern_name, replacement_strategy, preserve_structure
                )
                replacements[original] = replacement
                anonymized_text = anonymized_text.replace(original, replacement)
        
        return anonymized_text

    async def _detect_sensitive_info(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Detect sensitive information in text."""
        text = self.validate_text_input(arguments["text"])
        detection_types = arguments.get("detection_types", ["names", "emails", "phones", "addresses", "ids", "financial"])
        confidence_threshold = arguments.get("confidence_threshold", 0.7)
        
        detections = {}
        
        # Rule-based detection
        for pattern_name, pattern in self.patterns.items():
            if any(dtype in pattern_name for dtype in detection_types):
                matches = re.finditer(pattern, text, re.IGNORECASE)
                detected = []
                for match in matches:
                    detected.append({
                        "text": match.group(),
                        "start": match.start(),
                        "end": match.end(),
                        "confidence": 0.9,  # High confidence for regex matches
                        "type": pattern_name
                    })
                if detected:
                    detections[pattern_name] = detected
        
        # AI-based detection for names and other complex entities
        if "names" in detection_types or "addresses" in detection_types:
            ai_detections = await self._ai_detect_entities(text, detection_types, confidence_threshold)
            detections.update(ai_detections)
        
        return {
            "detections": detections,
            "total_sensitive_items": sum(len(items) for items in detections.values()),
            "text_length": len(text),
            "detection_types_used": detection_types
        }

    async def _smart_anonymize(self, arguments: Dict[str, Any]) -> str:
        """Use AI to intelligently anonymize text."""
        text = self.validate_text_input(arguments["text"])
        context = arguments.get("context", "general")
        preserve_meaning = arguments.get("preserve_meaning", True)
        
        meaning_instruction = "while preserving the overall meaning and context" if preserve_meaning else "thoroughly"
        
        system_prompt = f"""You are a data privacy expert specializing in text anonymization. Your task is to identify and anonymize all sensitive personal information in the provided {context} text {meaning_instruction}.

Anonymize the following types of sensitive information:
- Personal names (first, last, middle names)
- Email addresses  
- Phone numbers
- Physical addresses
- Social Security Numbers, ID numbers
- Financial information (credit card, bank account numbers)
- Medical information
- Dates of birth
- License plate numbers
- Any other personally identifiable information (PII)

Replace sensitive information with appropriate placeholders:
- Names: [NAME], [FIRST_NAME], [LAST_NAME]
- Emails: [EMAIL]
- Phones: [PHONE]
- Addresses: [ADDRESS]
- IDs: [ID_NUMBER]
- Financial: [CREDIT_CARD], [BANK_ACCOUNT]
- Dates: [DATE]

Maintain the text structure and readability. Return only the anonymized text."""
        
        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=f"Anonymize this {context} text:\n\n{text}")
        ]
        
        async with self.ollama_client as client:
            await client.ensure_model_available()
            response = await client.chat_completion(messages=messages)
            return response.response.strip()

    async def _create_anonymization_report(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Create a report of anonymization changes."""
        original_text = self.validate_text_input(arguments["original_text"])
        anonymized_text = self.validate_text_input(arguments["anonymized_text"])
        
        # Find differences
        original_words = set(original_text.split())
        anonymized_words = set(anonymized_text.split())
        
        removed_items = original_words - anonymized_words
        added_placeholders = anonymized_words - original_words
        
        # Count different types of placeholders
        placeholder_counts = {}
        placeholder_patterns = {
            'names': r'\[(?:NAME|FIRST_NAME|LAST_NAME)\]',
            'emails': r'\[EMAIL\]',
            'phones': r'\[PHONE\]',
            'addresses': r'\[ADDRESS\]',
            'ids': r'\[ID_NUMBER\]',
            'financial': r'\[(?:CREDIT_CARD|BANK_ACCOUNT)\]',
            'dates': r'\[DATE\]'
        }
        
        for category, pattern in placeholder_patterns.items():
            count = len(re.findall(pattern, anonymized_text))
            if count > 0:
                placeholder_counts[category] = count
        
        return {
            "original_length": len(original_text),
            "anonymized_length": len(anonymized_text),
            "items_anonymized": len(removed_items),
            "placeholders_added": len(added_placeholders),
            "anonymization_by_type": placeholder_counts,
            "anonymization_ratio": len(removed_items) / len(original_words) if original_words else 0,
            "readability_preserved": abs(len(original_text) - len(anonymized_text)) / len(original_text) < 0.3 if original_text else True
        }

    async def _ai_detect_entities(self, text: str, detection_types: List[str], threshold: float) -> Dict[str, List[Dict]]:
        """Use AI to detect named entities and sensitive information."""
        system_prompt = f"""You are a privacy expert. Identify sensitive personal information in the provided text. Look for:
- Personal names (people, not companies or places)
- Home/business addresses
- Any other personally identifiable information

For each item found, specify:
1. The exact text
2. The type (name, address, etc.)
3. Confidence level (0.0-1.0)
4. Character position in text

Only include items with confidence >= {threshold}. Format as: TYPE:TEXT:CONFIDENCE:START_POS"""
        
        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=f"Analyze this text:\n\n{text}")
        ]
        
        try:
            async with self.ollama_client as client:
                await client.ensure_model_available()
                response = await client.chat_completion(messages=messages)
                
                # Parse AI response (simplified parser)
                ai_detections = {}
                lines = response.response.strip().split('\n')
                
                for line in lines:
                    if ':' in line and len(line.split(':')) >= 4:
                        parts = line.split(':')
                        detection_type = parts[0].lower()
                        detected_text = parts[1]
                        confidence = float(parts[2]) if parts[2].replace('.', '').isdigit() else 0.5
                        
                        if confidence >= threshold:
                            if detection_type not in ai_detections:
                                ai_detections[detection_type] = []
                            
                            # Find position in original text
                            start_pos = text.find(detected_text)
                            if start_pos != -1:
                                ai_detections[detection_type].append({
                                    "text": detected_text,
                                    "start": start_pos,
                                    "end": start_pos + len(detected_text),
                                    "confidence": confidence,
                                    "type": detection_type
                                })
                
                return ai_detections
        except Exception as e:
            self.logger.warning(f"AI entity detection failed: {e}")
            return {}

    def _get_patterns_for_level(self, level: str) -> Dict[str, str]:
        """Get regex patterns based on anonymization level."""
        if level == "basic":
            return {
                'email': self.patterns['email'],
                'phone': self.patterns['phone'],
            }
        elif level == "standard":
            return {
                'email': self.patterns['email'],
                'phone': self.patterns['phone'],
                'ssn': self.patterns['ssn'],
                'credit_card': self.patterns['credit_card'],
                'ip_address': self.patterns['ip_address'],
            }
        else:  # aggressive
            return self.patterns

    def _generate_replacement(self, original: str, pattern_type: str, strategy: str, preserve_structure: bool) -> str:
        """Generate replacement text for sensitive information."""
        if strategy == "remove":
            return "[REDACTED]"
        
        elif strategy == "hash":
            hash_obj = hashlib.md5(original.encode())
            return f"[HASH_{hash_obj.hexdigest()[:8]}]"
        
        elif strategy == "fake_data":
            return self._generate_fake_data(pattern_type, preserve_structure)
        
        else:  # placeholder
            placeholder_map = {
                'email': '[EMAIL]',
                'phone': '[PHONE]',
                'ssn': '[SSN]',
                'credit_card': '[CREDIT_CARD]',
                'ip_address': '[IP_ADDRESS]',
                'url': '[URL]',
                'date': '[DATE]',
                'address_number': '[ADDRESS]'
            }
            return placeholder_map.get(pattern_type, '[SENSITIVE_DATA]')

    def _generate_fake_data(self, pattern_type: str, preserve_structure: bool) -> str:
        """Generate fake data that maintains format structure."""
        fake_data_map = {
            'email': 'user@example.com',
            'phone': '(555) 123-4567',
            'ssn': '123-45-6789',
            'credit_card': '1234 5678 9012 3456',
            'ip_address': '192.168.1.1',
            'url': 'https://example.com',
            'date': '01/01/2000',
            'address_number': '123 Main Street'
        }
        return fake_data_map.get(pattern_type, 'FAKE_DATA')
