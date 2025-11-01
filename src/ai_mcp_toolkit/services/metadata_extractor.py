"""Metadata extraction utility for document ingestion.

Extracts structured metadata from document chunks during ingestion:
- Keywords (IDs, emails, IBANs, long numbers)
- Money amounts and currency
- Vendor/company names
- Named entities
- File type classification

Used to populate ResourceChunk fields for compound search.
"""

import re
from typing import Dict, List, Optional
import logging

from .query_analyzer import QueryAnalyzer

logger = logging.getLogger(__name__)


class MetadataExtractor:
    """Extract structured metadata from document chunks during ingestion."""
    
    def __init__(self):
        self.analyzer = QueryAnalyzer()
    
    def extract(self, content: str, file_type: Optional[str] = None) -> Dict:
        """Extract all metadata from chunk content.
        
        Args:
            content: Text content of the chunk
            file_type: File type hint (pdf, csv, txt, image)
            
        Returns:
            Dict with extracted metadata:
            {
                'keywords': List[str],        # Exact match tokens
                'currency': str or None,      # ISO currency code
                'amounts_cents': List[int],   # Amounts in cents
                'vendor': str or None,        # Normalized vendor name
                'entities': List[str],        # Named entities
                'file_type': str             # Confirmed file type
            }
        """
        if not content or not content.strip():
            return self._empty_metadata(file_type)
        
        logger.debug(f"Extracting metadata from {len(content)} chars")
        
        # Use QueryAnalyzer to extract structured patterns
        analysis = self.analyzer.analyze(content)
        
        # Extract keywords (more thorough than query analysis)
        keywords = self._extract_keywords(content)
        
        # Extract vendor/company
        vendor = self._extract_vendor(content)
        
        # Build metadata dict
        metadata = {
            'keywords': keywords,
            'currency': analysis['money']['currency'] if analysis['money'] else None,
            'amounts_cents': [analysis['money']['cents']] if analysis['money'] else [],
            'vendor': vendor,
            'entities': analysis['entities'],
            'file_type': file_type
        }
        
        logger.debug(f"Extracted metadata: {len(keywords)} keywords, vendor={vendor}, currency={metadata['currency']}")
        return metadata
    
    def _extract_keywords(self, content: str) -> List[str]:
        """Extract exact match keywords (IDs, codes, long numbers, emails, IBANs).
        
        More comprehensive than QueryAnalyzer for ingestion purposes.
        """
        keywords = []
        
        # IDs like INV-2024-001, ORD-12345
        id_pattern = r'\b[A-Z]{2,}-\d{4,}\b'
        keywords.extend(re.findall(id_pattern, content))
        
        # Long numbers (8+ digits, likely account/order numbers)
        long_num_pattern = r'\b\d{8,}\b'
        keywords.extend(re.findall(long_num_pattern, content))
        
        # Emails
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        keywords.extend(re.findall(email_pattern, content))
        
        # IBANs
        iban_pattern = r'\b[A-Z]{2}\d{2}[A-Z0-9]{10,30}\b'
        keywords.extend(re.findall(iban_pattern, content))
        
        # Phone numbers
        phone_pattern = r'\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}'
        keywords.extend(re.findall(phone_pattern, content))
        
        # Tax IDs / VAT numbers (European format)
        vat_pattern = r'\b(?:VAT|TAX|IČO|DIČ)[:\s]*[A-Z0-9]{6,15}\b'
        keywords.extend(re.findall(vat_pattern, content, re.IGNORECASE))
        
        # Deduplicate and return
        return list(set(k.strip() for k in keywords if k.strip()))
    
    def _extract_vendor(self, content: str) -> Optional[str]:
        """Heuristic vendor/company detection.
        
        Looks for common patterns like:
        - "From: Company Name"
        - "Vendor: Company Name"
        - "Company Name Inc/LLC/Ltd/Corp"
        """
        # Pattern 1: "From:", "Vendor:", "Company:", "Supplier:" labels
        label_patterns = [
            r'(?:From|Vendor|Company|Supplier|Provider|Seller):\s*([A-Z][A-Za-z\s&\.\-]+)',
            r'(?:Sold by|Billed by|Issued by):\s*([A-Z][A-Za-z\s&\.\-]+)',
        ]
        
        for pattern in label_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                vendor = match.group(1).strip()
                # Clean up and normalize
                vendor = re.sub(r'\s+', ' ', vendor)  # normalize whitespace
                vendor = vendor.rstrip('.,;:')  # remove trailing punctuation
                if len(vendor) > 2:
                    return vendor.lower()  # normalize to lowercase for search
        
        # Pattern 2: Company name with legal suffix (Inc, LLC, Ltd, Corp, GmbH, etc.)
        legal_suffix_pattern = r'\b([A-Z][A-Za-z\s&\.\-]+?)\s+(?:Inc|LLC|Ltd|LTD|Corp|Corporation|GmbH|AG|SA|sro|s\.r\.o\.|a\.s\.)\.?\b'
        match = re.search(legal_suffix_pattern, content)
        if match:
            vendor = match.group(1).strip()
            if len(vendor) > 2:
                return vendor.lower()
        
        return None
    
    def _empty_metadata(self, file_type: Optional[str] = None) -> Dict:
        """Return empty metadata structure."""
        return {
            'keywords': [],
            'currency': None,
            'amounts_cents': [],
            'vendor': None,
            'entities': [],
            'file_type': file_type
        }
    
    def extract_csv_row_metadata(self, row: Dict[str, str], row_index: int) -> Dict:
        """Extract metadata from a CSV row (dict of column: value).
        
        Args:
            row: CSV row as dict (column name -> value)
            row_index: Row number in CSV
            
        Returns:
            Metadata dict with row-specific info
        """
        # Convert row to text representation
        row_text = ' | '.join(f"{k}: {v}" for k, v in row.items() if v)
        
        # Extract standard metadata
        metadata = self.extract(row_text, file_type='csv')
        
        # Add CSV-specific info
        metadata['row_index'] = row_index
        metadata['chunk_type'] = 'row'
        
        return metadata
    
    def extract_image_metadata(
        self,
        caption: Optional[str] = None,
        ocr_text: Optional[str] = None,
        labels: Optional[List[str]] = None
    ) -> Dict:
        """Extract metadata from image caption and OCR text.
        
        Args:
            caption: AI-generated image caption
            ocr_text: Text extracted via OCR
            labels: Image labels/tags
            
        Returns:
            Metadata dict for image chunk
        """
        # Combine all text sources
        combined_text = ' '.join(filter(None, [caption, ocr_text]))
        
        # Extract standard metadata
        metadata = self.extract(combined_text, file_type='image')
        
        # Add image-specific fields
        metadata['caption'] = caption
        metadata['ocr_text'] = ocr_text
        metadata['image_labels'] = labels or []
        metadata['chunk_type'] = 'image'
        
        return metadata


class VendorNormalizer:
    """Normalize vendor names for consistent search (future enhancement)."""
    
    # Common vendor name variations
    VENDOR_ALIASES = {
        'google': ['google llc', 'google inc', 'alphabet'],
        'microsoft': ['microsoft corporation', 'msft'],
        'amazon': ['amazon.com', 'amazon web services', 'aws'],
        't-mobile': ['t-mobile us', 'tmobile', 't mobile'],
        'verizon': ['verizon wireless', 'verizon communications'],
    }
    
    def normalize(self, vendor: str) -> str:
        """Normalize vendor name to canonical form.
        
        Args:
            vendor: Raw vendor name
            
        Returns:
            Normalized vendor name
        """
        if not vendor:
            return vendor
        
        vendor_lower = vendor.lower().strip()
        
        # Check aliases
        for canonical, aliases in self.VENDOR_ALIASES.items():
            if vendor_lower in aliases or vendor_lower == canonical:
                return canonical
        
        return vendor_lower
