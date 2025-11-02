"""
Redis-based suggestion service for fast autocomplete.

Provides real-time search suggestions based on document content stored in Redis.
"""

import logging
from typing import List, Dict, Any, Optional
from ..models.database import get_redis_client
from ..utils.text_normalizer import normalize_text, tokenize_for_search


logger = logging.getLogger(__name__)


class SuggestionService:
    """Service for managing and querying search suggestions in Redis."""
    
    # Redis key prefixes
    KEY_FILENAMES = "suggestions:filenames"
    KEY_ENTITIES = "suggestions:entities"
    KEY_KEYWORDS = "suggestions:keywords"
    KEY_VENDORS = "suggestions:vendors"
    KEY_ALL_TERMS = "suggestions:all_terms"
    
    def __init__(self):
        self.logger = logger
    
    async def add_document_terms(
        self,
        file_name: str,
        entities: List[str] = None,
        keywords: List[str] = None,
        vendor: str = None,
        content: str = None,
        company_id: str = None
    ):
        """
        Add searchable terms from a document to Redis.
        
        Args:
            file_name: Document file name
            entities: List of extracted entities
            keywords: List of keywords
            vendor: Vendor name
            content: Document text content
            company_id: Company ID for multi-tenant isolation
        """
        redis = await get_redis_client()
        if not redis:
            self.logger.warning("Redis not available, skipping suggestion indexing")
            return
        
        try:
            # Prepare key prefix for multi-tenant isolation
            prefix = f"{company_id}:" if company_id else ""
            
            # Add file name (exact match)
            # NOTE: For ZRANGEBYLEX to work, all scores must be 0
            if file_name:
                await redis.zadd(
                    f"{prefix}{self.KEY_FILENAMES}",
                    {file_name: 0}
                )
            
            # Add entities
            if entities:
                for entity in entities:
                    normalized = normalize_text(entity)
                    if normalized and len(normalized) >= 2:
                        await redis.zadd(
                            f"{prefix}{self.KEY_ENTITIES}",
                            {normalized: 0}
                        )
            
            # Add keywords
            if keywords:
                for keyword in keywords:
                    normalized = normalize_text(keyword)
                    if normalized and len(normalized) >= 2:
                        await redis.zadd(
                            f"{prefix}{self.KEY_KEYWORDS}",
                            {normalized: 0}
                        )
            
            # Add vendor
            if vendor:
                normalized = normalize_text(vendor)
                if normalized and len(normalized) >= 2:
                    await redis.zadd(
                        f"{prefix}{self.KEY_VENDORS}",
                        {normalized: 0}
                    )
            
            # Extract and add content terms (words and phrases)
            if content:
                # Normalize but preserve spaces for phrase extraction
                normalized_content = normalize_text(content)
                
                # Extract individual words
                tokens = tokenize_for_search(normalized_content)
                # Filter out very short tokens and common stop words
                stop_words = {'the', 'and', 'for', 'are', 'but', 'not', 'this', 'that', 'with', 'from', 'have', 'has'}
                meaningful_tokens = [
                    t for t in tokens 
                    if len(t) >= 3 and t not in stop_words
                ]
                
                # Add individual words
                for token in set(meaningful_tokens):
                    await redis.zadd(
                        f"{prefix}{self.KEY_ALL_TERMS}",
                        {token: 0}
                    )
                
                # Extract 2-3 word phrases
                words = normalized_content.split()
                for i in range(len(words)):
                    # 2-word phrases
                    if i < len(words) - 1:
                        phrase = f"{words[i]} {words[i+1]}"
                        # Only add if both words are meaningful and don't contain punctuation
                        if (len(words[i]) >= 3 and len(words[i+1]) >= 3 and 
                            words[i] not in stop_words and words[i+1] not in stop_words and
                            not any(p in phrase for p in ['.', ',', '!', '?', ';', ':'])):
                            await redis.zadd(
                                f"{prefix}{self.KEY_ALL_TERMS}",
                                {phrase: 0}
                            )
                    
                    # 3-word phrases  
                    if i < len(words) - 2:
                        phrase = f"{words[i]} {words[i+1]} {words[i+2]}"
                        # Only add if all words are meaningful and don't contain punctuation
                        if (len(words[i]) >= 3 and len(words[i+1]) >= 3 and len(words[i+2]) >= 3 and
                            words[i] not in stop_words and words[i+1] not in stop_words and words[i+2] not in stop_words and
                            not any(p in phrase for p in ['.', ',', '!', '?', ';', ':'])):
                            await redis.zadd(
                                f"{prefix}{self.KEY_ALL_TERMS}",
                                {phrase: 0}
                            )
            
            self.logger.debug(f"Indexed suggestions for document: {file_name}")
            
        except Exception as e:
            self.logger.error(f"Error adding document terms to Redis: {e}", exc_info=True)
    
    async def get_suggestions(
        self,
        query: str,
        company_id: str = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get search suggestions based on query prefix.
        
        Args:
            query: Partial search query
            company_id: Company ID for filtering
            limit: Maximum number of suggestions
            
        Returns:
            List of suggestions with type and score
        """
        redis = await get_redis_client()
        if not redis:
            return []
        
        if not query or len(query) < 2:
            return []
        
        try:
            # Normalize query for matching
            query_normalized = normalize_text(query).strip()
            if not query_normalized:
                return []
            
            # Prepare key prefix for multi-tenant isolation
            prefix = f"{company_id}:" if company_id else ""
            
            suggestions = []
            
            # Search in different categories with priorities
            categories = [
                (f"{prefix}{self.KEY_FILENAMES}", "file", 1.0),
                (f"{prefix}{self.KEY_VENDORS}", "vendor", 0.9),
                (f"{prefix}{self.KEY_ENTITIES}", "entity", 0.8),
                (f"{prefix}{self.KEY_KEYWORDS}", "keyword", 0.7),
                (f"{prefix}{self.KEY_ALL_TERMS}", "term", 0.5),
            ]
            
            for key, suggestion_type, priority in categories:
                # Use ZRANGEBYLEX for prefix matching
                # Redis sorted set lexicographical range query
                # Create upper bound by incrementing last character
                if query_normalized:
                    # Increment last character for upper bound
                    upper_bound = query_normalized[:-1] + chr(ord(query_normalized[-1]) + 1)
                    matches = await redis.zrangebylex(
                        key,
                        f"[{query_normalized}",
                        f"[{upper_bound}",
                        start=0,
                        num=limit
                    )
                else:
                    matches = []
                
                # Add matched terms (score based on type priority only)
                for match in matches:
                    suggestions.append({
                        "text": match,
                        "type": suggestion_type,
                        "score": priority,
                        "query": query
                    })
            
            # Sort by score descending and limit
            suggestions.sort(key=lambda x: x["score"], reverse=True)
            
            # Deduplicate by text
            seen = set()
            unique_suggestions = []
            for s in suggestions:
                if s["text"] not in seen:
                    seen.add(s["text"])
                    unique_suggestions.append(s)
                    if len(unique_suggestions) >= limit:
                        break
            
            self.logger.debug(
                f"Found {len(unique_suggestions)} suggestions for query '{query}'"
            )
            
            return unique_suggestions
            
        except Exception as e:
            self.logger.error(f"Error getting suggestions: {e}", exc_info=True)
            return []
    
    async def remove_document_terms(
        self,
        file_name: str,
        company_id: str = None
    ):
        """
        Remove a document's terms from suggestions (e.g., when document is deleted).
        
        Args:
            file_name: Document file name
            company_id: Company ID
        """
        redis = await get_redis_client()
        if not redis:
            return
        
        try:
            prefix = f"{company_id}:" if company_id else ""
            
            # Remove filename
            await redis.zrem(f"{prefix}{self.KEY_FILENAMES}", file_name)
            
            self.logger.debug(f"Removed suggestions for document: {file_name}")
            
        except Exception as e:
            self.logger.error(f"Error removing document terms: {e}", exc_info=True)
    
    async def clear_company_suggestions(self, company_id: str):
        """
        Clear all suggestions for a company.
        
        Args:
            company_id: Company ID
        """
        redis = await get_redis_client()
        if not redis:
            return
        
        try:
            prefix = f"{company_id}:"
            keys = [
                f"{prefix}{self.KEY_FILENAMES}",
                f"{prefix}{self.KEY_ENTITIES}",
                f"{prefix}{self.KEY_KEYWORDS}",
                f"{prefix}{self.KEY_VENDORS}",
                f"{prefix}{self.KEY_ALL_TERMS}",
            ]
            
            for key in keys:
                await redis.delete(key)
            
            self.logger.info(f"Cleared all suggestions for company: {company_id}")
            
        except Exception as e:
            self.logger.error(f"Error clearing suggestions: {e}", exc_info=True)
