"""Base processor class for file processing."""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


class BaseProcessor(ABC):
    """Abstract base class for file processors."""
    
    def __init__(self):
        """Initialize the processor."""
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    async def process(self, file_bytes: bytes, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a file and extract metadata and chunks.
        
        Args:
            file_bytes: Raw file content as bytes
            metadata: Initial metadata (filename, mime_type, size, etc.)
            
        Returns:
            Dictionary with:
            {
                "file_metadata": {
                    "file_type": "pdf",
                    "vendor": "google",
                    "currency": "USD",
                    "amounts_cents": [930],
                    "entities": ["google", "invoice"],
                    "keywords": ["INV-1234"],
                    "dates": [datetime(2025, 10, 31)],
                    ...
                },
                "chunks": [
                    {
                        "chunk_type": "page",
                        "chunk_index": 0,
                        "page_number": 1,
                        "text": "Page 1 content...",
                        "text_embedding": [0.1, 0.2, ...],
                        ...
                    },
                    ...
                ]
            }
        """
        pass
    
    def extract_amounts(self, text: str) -> List[int]:
        """
        Extract money amounts from text and convert to cents.
        
        Examples:
            "$9.30" -> [930]
            "9.30 USD" -> [930]
            "€10.00" -> [1000]
            "1,234.56 EUR" -> [123456]
        
        Args:
            text: Text to extract amounts from
            
        Returns:
            List of amounts in cents
        """
        import re
        
        amounts = []
        
        # Pattern 1: $X.XX or €X.XX
        pattern1 = r'[$€£¥]\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
        
        # Pattern 2: X.XX USD/EUR/CZK/GBP
        pattern2 = r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:USD|EUR|CZK|GBP|dollars?|euros?)'
        
        # Pattern 3: Simple decimal numbers near currency words
        pattern3 = r'(\d{1,3}(?:,\d{3})*\.\d{2})'
        
        for pattern in [pattern1, pattern2, pattern3]:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                amount_str = match.group(1).replace(',', '')
                try:
                    amount_float = float(amount_str)
                    amount_cents = int(amount_float * 100)
                    if amount_cents > 0 and amount_cents < 1000000000:  # Sanity check
                        amounts.append(amount_cents)
                except ValueError:
                    continue
        
        # Remove duplicates and sort
        return sorted(list(set(amounts)))
    
    def extract_currency(self, text: str) -> str:
        """
        Extract currency code from text.
        
        Args:
            text: Text to extract currency from
            
        Returns:
            Currency code (USD, EUR, CZK, GBP) or None
        """
        import re
        
        # Look for explicit currency codes
        currency_pattern = r'\b(USD|EUR|CZK|GBP|JPY|CNY)\b'
        match = re.search(currency_pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).upper()
        
        # Look for currency symbols
        if '$' in text:
            return 'USD'
        elif '€' in text:
            return 'EUR'
        elif '£' in text:
            return 'GBP'
        elif '¥' in text:
            return 'JPY'
        
        return None
    
    def extract_dates(self, text: str) -> List[datetime]:
        """
        Extract dates from text.
        
        Args:
            text: Text to extract dates from
            
        Returns:
            List of datetime objects
        """
        from dateutil import parser
        import re
        
        dates = []
        
        # Common date patterns
        date_patterns = [
            r'\b\d{4}-\d{2}-\d{2}\b',  # 2025-10-31
            r'\b\d{2}/\d{2}/\d{4}\b',  # 10/31/2025
            r'\b\d{2}\.\d{2}\.\d{4}\b',  # 31.10.2025
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b',  # October 31, 2025
        ]
        
        for pattern in date_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    date_str = match.group(0)
                    parsed_date = parser.parse(date_str, fuzzy=False)
                    dates.append(parsed_date)
                except (ValueError, parser.ParserError):
                    continue
        
        # Remove duplicates
        unique_dates = []
        seen = set()
        for date in dates:
            date_key = date.date()
            if date_key not in seen:
                seen.add(date_key)
                unique_dates.append(date)
        
        return sorted(unique_dates)
    
    def extract_entities(self, text: str) -> List[str]:
        """
        Extract named entities (companies, vendors) from text.
        
        Args:
            text: Text to extract entities from
            
        Returns:
            List of normalized entity names
        """
        entities = []
        
        # Common vendor patterns
        vendor_patterns = [
            r'\b(google|microsoft|amazon|apple|meta|facebook|netflix|tesla)\b',
            r'\b(t-mobile|verizon|at&t|sprint)\b',
            r'\b(paypal|stripe|square)\b',
        ]
        
        import re
        for pattern in vendor_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entity = match.group(1).lower()
                if entity not in entities:
                    entities.append(entity)
        
        return entities
    
    def extract_keywords(self, text: str) -> List[str]:
        """
        Extract exact searchable keywords (IDs, emails, phone numbers).
        
        Args:
            text: Text to extract keywords from
            
        Returns:
            List of exact keyword values
        """
        import re
        
        keywords = []
        
        # Pattern 1: Long numbers (8+ digits)
        long_numbers = re.findall(r'\b\d{8,}\b', text)
        keywords.extend(long_numbers)
        
        # Pattern 2: Invoice/Order numbers
        invoice_patterns = [
            r'\b(?:INV|ORDER|PO|REF)-?\d+\b',
            r'\b\d{4,}-\d{3,}\b',
        ]
        for pattern in invoice_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            keywords.extend(matches)
        
        # Pattern 3: Email addresses
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        keywords.extend(emails)
        
        # Pattern 4: Phone numbers
        phones = re.findall(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', text)
        keywords.extend(phones)
        
        # Remove duplicates and normalize
        return list(set(keywords))
    
    def normalize_vendor(self, vendor: str) -> str:
        """
        Normalize vendor name for consistent search.
        
        Args:
            vendor: Raw vendor name
            
        Returns:
            Normalized vendor name
        """
        if not vendor:
            return None
        
        # Convert to lowercase
        normalized = vendor.lower().strip()
        
        # Remove common suffixes
        normalized = normalized.replace(' inc.', '').replace(' llc', '').replace(' ltd', '')
        normalized = normalized.replace(',', '').replace('.', '')
        
        # Normalize spacing
        normalized = ' '.join(normalized.split())
        
        return normalized
