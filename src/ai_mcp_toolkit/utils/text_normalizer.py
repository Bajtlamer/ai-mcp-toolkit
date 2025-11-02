"""
Text Normalizer Utility

Provides functions to normalize text by removing diacritics and applying
consistent Unicode normalization for improved search matching across
languages with accented characters (Czech, Slovak, German, French, etc.).

Used by:
- Search service to normalize queries
- Ingestion service to normalize stored text
- OCR agent to normalize extracted text
"""

import unicodedata
import re
from typing import Optional


def remove_diacritics(text: str) -> str:
    """
    Remove diacritics (accent marks) from text.
    
    Examples:
        "datová" -> "datova"
        "Škoda" -> "Skoda"
        "café" -> "cafe"
        "Zürich" -> "Zurich"
    
    Args:
        text: Input text with possible diacritics
        
    Returns:
        Text with diacritics removed
    """
    if not text:
        return text
    
    # Normalize to NFD (decomposed form) where diacritics are separate characters
    nfd = unicodedata.normalize('NFD', text)
    
    # Filter out combining characters (diacritics)
    without_diacritics = ''.join(
        char for char in nfd 
        if unicodedata.category(char) != 'Mn'  # Mn = Mark, nonspacing
    )
    
    # Normalize back to NFC (composed form)
    return unicodedata.normalize('NFC', without_diacritics)


def normalize_text(text: str, lowercase: bool = True) -> str:
    """
    Normalize text for search matching.
    
    - Removes diacritics
    - Optionally converts to lowercase
    - Normalizes whitespace
    - Removes extra punctuation
    
    Args:
        text: Input text to normalize
        lowercase: Whether to convert to lowercase (default: True)
        
    Returns:
        Normalized text
    """
    if not text:
        return text
    
    # Remove diacritics
    normalized = remove_diacritics(text)
    
    # Convert to lowercase if requested
    if lowercase:
        normalized = normalized.lower()
    
    # Normalize whitespace (collapse multiple spaces, tabs, newlines)
    normalized = re.sub(r'\s+', ' ', normalized)
    
    # Trim leading/trailing whitespace
    normalized = normalized.strip()
    
    return normalized


def normalize_query(query: str) -> str:
    """
    Normalize a search query for consistent matching.
    
    Same as normalize_text but ensures lowercase and minimal punctuation.
    
    Args:
        query: Search query string
        
    Returns:
        Normalized query
    """
    return normalize_text(query, lowercase=True)


def normalize_text_for_embedding(text: str) -> str:
    """
    Normalize text before generating embeddings.
    
    Preserves more structure than query normalization but still
    removes diacritics for consistent semantic matching.
    
    Args:
        text: Text to embed
        
    Returns:
        Normalized text ready for embedding
    """
    if not text:
        return text
    
    # Remove diacritics
    normalized = remove_diacritics(text)
    
    # Normalize whitespace but preserve sentence structure
    normalized = re.sub(r'\s+', ' ', normalized)
    normalized = normalized.strip()
    
    # Keep original case for embedding (better semantic representation)
    return normalized


def create_searchable_text(*text_parts: Optional[str], separator: str = " ") -> str:
    """
    Create a single searchable text field from multiple text sources.
    
    Combines and normalizes text, title, keywords, OCR text, etc.
    into a single field optimized for full-text search.
    
    Args:
        *text_parts: Variable number of text strings to combine
        separator: String to join parts with (default: space)
        
    Returns:
        Combined normalized searchable text
    """
    # Filter out None/empty values
    valid_parts = [part for part in text_parts if part]
    
    if not valid_parts:
        return ""
    
    # Combine all parts
    combined = separator.join(valid_parts)
    
    # Normalize
    return normalize_text(combined, lowercase=True)


def tokenize_for_search(text: str) -> list[str]:
    """
    Tokenize normalized text into search terms.
    
    Splits on whitespace and punctuation, removes very short tokens.
    
    Args:
        text: Normalized text
        
    Returns:
        List of search tokens
    """
    if not text:
        return []
    
    # Normalize first
    normalized = normalize_text(text)
    
    # Split on whitespace and common punctuation
    tokens = re.split(r'[\s\-_.,;:!?(){}[\]<>/"\']+', normalized)
    
    # Filter out very short tokens (< 2 chars) and empty strings
    tokens = [t for t in tokens if len(t) >= 2]
    
    return tokens


# Export all functions
__all__ = [
    'remove_diacritics',
    'normalize_text',
    'normalize_query',
    'normalize_text_for_embedding',
    'create_searchable_text',
    'tokenize_for_search',
]
