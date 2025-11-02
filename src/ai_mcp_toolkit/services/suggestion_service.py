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
    
    async def index_resource(self, resource):
        """
        Index a single resource for suggestions.
        
        Adds:
        - File name
        - Vendor (if exists)
        - Entities (names, places, etc.)
        - Keywords
        - Common content terms
        
        Args:
            resource: Resource document to index
        """
        redis = await get_redis_client()
        if not redis:
            return
        
        try:
            from ..models.documents import Resource
            
            company_id = getattr(resource, 'company_id', None) or getattr(resource, 'owner_id', None)
            if not company_id:
                self.logger.warning(f"Resource {resource.id} has no company_id, skipping suggestion indexing")
                return
            
            prefix = f"{company_id}:"
            
            # Index file name
            if resource.file_name:
                file_name_norm = normalize_text(resource.file_name)
                await redis.zadd(
                    f"{prefix}{self.KEY_FILENAMES}",
                    {file_name_norm: 0}
                )
            
            # Index vendor
            if getattr(resource, 'vendor', None):
                vendor_norm = normalize_text(resource.vendor)
                await redis.zadd(
                    f"{prefix}{self.KEY_VENDORS}",
                    {vendor_norm: 0}
                )
            
            # Index entities
            if getattr(resource, 'entities', None):
                for entity in resource.entities[:20]:  # Limit to first 20
                    entity_norm = normalize_text(entity)
                    await redis.zadd(
                        f"{prefix}{self.KEY_ENTITIES}",
                        {entity_norm: 0}
                    )
            
            # Index keywords
            if getattr(resource, 'keywords', None):
                for keyword in resource.keywords[:30]:  # Limit to first 30
                    keyword_norm = normalize_text(keyword)
                    await redis.zadd(
                        f"{prefix}{self.KEY_KEYWORDS}",
                        {keyword_norm: 0}
                    )
            
            # Extract and index common terms from summary/content
            text = getattr(resource, 'summary', '') or ''
            if text:
                terms = self._extract_common_terms(text, max_terms=50)
                for term in terms:
                    term_norm = normalize_text(term)
                    await redis.zadd(
                        f"{prefix}{self.KEY_ALL_TERMS}",
                        {term_norm: 0}
                    )
            
            # Also index 2-3 word phrases from summary
            if text:
                phrases = self._extract_phrases(text, max_phrases=20)
                for phrase in phrases:
                    phrase_norm = normalize_text(phrase)
                    await redis.zadd(
                        f"{prefix}{self.KEY_ALL_TERMS}",
                        {phrase_norm: 0}
                    )
            
            self.logger.debug(f"Indexed suggestions for resource: {resource.file_name}")
            
        except Exception as e:
            self.logger.error(f"Error indexing resource: {e}", exc_info=True)
    
    async def remove_resource_suggestions(
        self,
        resource_id: str,
        company_id: str
    ):
        """
        Remove suggestions for a specific resource.
        
        Note: Currently, we don't track which suggestions came from which resource,
        so this is a no-op. In the future, could track resource_id with suggestions.
        
        Args:
            resource_id: Resource ID
            company_id: Company ID
        """
        # TODO: Implement resource-specific suggestion tracking
        # For now, suggestions accumulate and get naturally updated when resource is reindexed
        self.logger.debug(f"Remove resource suggestions called for {resource_id} (not implemented yet)")
        pass
