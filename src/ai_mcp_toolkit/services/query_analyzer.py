"""Query analysis utility for compound search.

Extracts structured patterns from natural language queries:
- Money amounts and currency
- IDs, emails, IBANs, codes
- Dates and time periods
- File types
- Entity candidates (capitalized names)

Used to build intelligent Atlas $search.compound queries without mode selection.
"""

import re
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class QueryAnalyzer:
    """Extract structured patterns from natural language search queries."""
    
    # Regex patterns for structured data
    MONEY_PATTERN = re.compile(
        r'(?:USD|EUR|GBP|CHF|CZK|\$|€|£|Kč)\s*(\d{1,3}(?:[,\s]\d{3})*(?:\.\d{2})?)|'
        r'(\d{1,3}(?:[,\s]\d{3})*(?:\.\d{2})?)\s*(?:USD|EUR|GBP|CHF|CZK|dollars?|euros?|korun|crowns?)',
        re.IGNORECASE
    )
    
    ID_PATTERN = re.compile(r'\b[A-Z]{2,}-\d{4,}|\b[A-Z0-9]{8,}\b')
    EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    IBAN_PATTERN = re.compile(r'\b[A-Z]{2}\d{2}[A-Z0-9]{10,30}\b')
    PHONE_PATTERN = re.compile(r'\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}')
    
    DATE_PATTERNS = [
        r'\b\d{4}-\d{2}-\d{2}\b',                    # 2024-01-15
        r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',              # 01/15/2024
        r'\b\d{1,2}\.\d{1,2}\.\d{2,4}\b',            # 15.01.2024 (European)
        r'\bQ[1-4]\s+\d{4}\b',                       # Q4 2023
        r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\b',  # January 2024
        r'\b(?:last|this|next)\s+(?:week|month|quarter|year)\b',  # relative dates
    ]
    
    FILE_TYPES = {
        'pdf', 'csv', 'xlsx', 'xls', 'doc', 'docx', 'txt', 'json', 'xml',
        'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'svg',
        'invoice', 'receipt', 'contract', 'spreadsheet', 'document', 'image', 'photo'
    }
    
    # Currency symbols to ISO codes
    CURRENCY_MAP = {
        '$': 'USD',
        '€': 'EUR',
        '£': 'GBP',
        'Kč': 'CZK',
        'dollars': 'USD',
        'dollar': 'USD',
        'euros': 'EUR',
        'euro': 'EUR',
        'pounds': 'GBP',
        'pound': 'GBP',
        'crowns': 'CZK',
        'crown': 'CZK',
        'korun': 'CZK',
    }
    
    def analyze(self, query: str) -> Dict:
        """Extract all structured patterns from query.
        
        Args:
            query: Natural language search query
            
        Returns:
            Dict with extracted patterns:
            {
                'money': {'amount': float, 'cents': int, 'currency': str} or None,
                'ids': List[str],
                'dates': List[str],
                'file_types': List[str],
                'entities': List[str],
                'clean_text': str  # Query with structured patterns removed
            }
        """
        logger.debug(f"Analyzing query: {query}")
        
        result = {
            'money': self._extract_money(query),
            'ids': self._extract_ids(query),
            'dates': self._extract_dates(query),
            'file_types': self._extract_file_types(query),
            'entities': self._extract_entities(query),
            'clean_text': self._clean_query(query)
        }
        
        logger.debug(f"Analysis result: {result}")
        return result
    
    def _extract_money(self, query: str) -> Optional[Dict]:
        """Extract currency and amount from query.
        
        Examples:
            "$1234.56" -> {'amount': 1234.56, 'cents': 123456, 'currency': 'USD'}
            "9 USD" -> {'amount': 9.0, 'cents': 900, 'currency': 'USD'}
            "€500" -> {'amount': 500.0, 'cents': 50000, 'currency': 'EUR'}
        """
        match = self.MONEY_PATTERN.search(query)
        if not match:
            return None
        
        # Extract amount string
        amount_str = match.group(1) or match.group(2)
        if not amount_str:
            return None
            
        # Parse amount (remove thousands separators)
        amount = float(amount_str.replace(',', '').replace(' ', ''))
        
        # Detect currency from query
        query_lower = query.lower()
        currency = 'USD'  # default
        
        for symbol, code in self.CURRENCY_MAP.items():
            if symbol in query:
                currency = code
                break
        
        # Also check for explicit currency codes
        for code in ['USD', 'EUR', 'GBP', 'CHF', 'CZK']:
            if code in query.upper():
                currency = code
                break
        
        return {
            'amount': amount,
            'cents': int(amount * 100),
            'currency': currency,
            'raw': match.group(0)
        }
    
    def _extract_ids(self, query: str) -> List[str]:
        """Extract IDs, emails, IBANs, phone numbers.
        
        Examples:
            "INV-2024-001" -> ["INV-2024-001"]
            "user@example.com" -> ["user@example.com"]
            "CZ1234567890123456" -> ["CZ1234567890123456"]
        """
        ids = []
        
        # IDs like INV-2024-001
        ids.extend(self.ID_PATTERN.findall(query))
        
        # Emails
        ids.extend(self.EMAIL_PATTERN.findall(query))
        
        # IBANs
        ids.extend(self.IBAN_PATTERN.findall(query))
        
        # Phone numbers
        ids.extend(self.PHONE_PATTERN.findall(query))
        
        return list(set(ids))  # deduplicate
    
    def _extract_dates(self, query: str) -> List[str]:
        """Extract date patterns from query.
        
        Examples:
            "2024-01-15" -> ["2024-01-15"]
            "Q4 2023" -> ["Q4 2023"]
            "last month" -> ["last month"]
        """
        dates = []
        for pattern in self.DATE_PATTERNS:
            dates.extend(re.findall(pattern, query, re.IGNORECASE))
        return dates
    
    def _extract_file_types(self, query: str) -> List[str]:
        """Detect file type mentions in query.
        
        Examples:
            "pdf invoice" -> ["pdf", "invoice"]
            "spreadsheet with data" -> ["spreadsheet"]
        """
        query_lower = query.lower()
        return [ft for ft in self.FILE_TYPES if ft in query_lower]
    
    def _extract_entities(self, query: str) -> List[str]:
        """Extract capitalized entity candidates (simple heuristic).
        
        Looks for capitalized words that aren't at sentence start.
        
        Examples:
            "invoice from Google" -> ["Google"]
            "contract with Acme Corp" -> ["Acme", "Corp"]
        """
        words = query.split()
        entities = []
        
        for i, word in enumerate(words):
            # Skip first word (might be capitalized naturally)
            if i == 0:
                continue
            
            # Check if word is capitalized and not a common word
            if word and word[0].isupper() and len(word) > 2:
                # Remove trailing punctuation
                clean_word = word.rstrip('.,;:!?')
                if clean_word:
                    entities.append(clean_word)
        
        return entities
    
    def _clean_query(self, query: str) -> str:
        """Remove extracted structured patterns, return semantic text.
        
        Removes money amounts, IDs, dates to leave clean text for semantic search.
        
        Examples:
            "invoice for $1234.56 from Google" -> "invoice from Google"
            "INV-2024-001 payment" -> "payment"
        """
        clean = query
        
        # Remove money amounts
        clean = self.MONEY_PATTERN.sub('', clean)
        
        # Remove IDs (but preserve emails in text for context)
        clean = self.ID_PATTERN.sub('', clean)
        
        # Remove IBANs
        clean = self.IBAN_PATTERN.sub('', clean)
        
        # Clean up multiple spaces
        clean = ' '.join(clean.split()).strip()
        
        return clean if clean else query  # fallback to original if everything removed


class QueryRouter:
    """Route queries to appropriate search strategy (for future use)."""
    
    def __init__(self):
        self.analyzer = QueryAnalyzer()
    
    def should_use_exact_match(self, analysis: Dict) -> bool:
        """Determine if query should prioritize exact matching.
        
        Returns True if query contains IDs, specific amounts, or exact codes.
        """
        return bool(analysis['ids']) or bool(analysis['money'])
    
    def should_search_images(self, analysis: Dict) -> bool:
        """Determine if query is looking for images.
        
        Returns True if query mentions image types or photo-related terms.
        """
        file_types = analysis.get('file_types', [])
        image_types = {'jpg', 'jpeg', 'png', 'gif', 'image', 'photo'}
        return bool(image_types & set(file_types))
    
    def estimate_search_strategy(self, query: str) -> str:
        """Estimate best search strategy (for logging/debugging).
        
        Returns:
            'exact' - query has IDs or specific amounts
            'semantic' - natural language query
            'hybrid' - mixed query
        """
        analysis = self.analyzer.analyze(query)
        
        if self.should_use_exact_match(analysis):
            return 'exact' if not analysis['clean_text'] else 'hybrid'
        else:
            return 'semantic'
