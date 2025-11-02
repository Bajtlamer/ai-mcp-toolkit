"""Contextual search service using MongoDB Atlas hybrid search."""

import logging
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from bson import ObjectId

from ..models.documents import Resource, ResourceChunk
from ..models.search_config import SearchCategory, SearchConfigService
from .embedding_service import get_embedding_service
from .query_analyzer import QueryAnalyzer
from ..utils.text_normalizer import normalize_query, normalize_text, tokenize_for_search

logger = logging.getLogger(__name__)


class SearchService:
    """
    Service for contextual hybrid search across resources and chunks.
    
    Features:
    - Query classification and entity extraction
    - Hybrid search combining vector similarity + keyword/filters
    - Intelligent result ranking
    - Deep linking to exact locations (page, row, etc.)
    """
    
    def __init__(self):
        """Initialize search service."""
        self.logger = logging.getLogger(__name__)
        self.embedding_service = get_embedding_service()
        self.query_analyzer = QueryAnalyzer()
        self.logger.info("✅ SearchService initialized with diacritic-insensitive search support")
    
    async def search(
        self,
        query: str,
        company_id: str,
        limit: int = 20,
        search_type: str = "auto"  # auto, semantic, keyword, hybrid
    ) -> Dict[str, Any]:
        """
        Perform contextual search across resources.
        
        Args:
            query: User search query
            company_id: Company ID for ACL filtering
            limit: Maximum number of results
            search_type: Type of search to perform
            
        Returns:
            Search results with metadata
        """
        try:
            self.logger.info(f"Search query: '{query}' (company: {company_id}, type: {search_type})")
            
            # Classify query and extract entities
            query_analysis = self._analyze_query(query)
            
            # Determine search strategy
            if search_type == "auto":
                search_type = query_analysis['recommended_type']
            
            # Execute search based on type
            if search_type == "semantic":
                results = await self._semantic_search(query, company_id, limit, query_analysis)
            elif search_type == "keyword":
                results = await self._keyword_search(query, company_id, limit, query_analysis)
            else:  # hybrid
                results = await self._hybrid_search(query, company_id, limit, query_analysis)
            
            self.logger.info(f"Search returned {len(results)} results")
            
            return {
                'query': query,
                'query_analysis': query_analysis,
                'search_type': search_type,
                'results': results,
                'total': len(results),
            }
            
        except Exception as e:
            self.logger.error(f"Search error: {e}", exc_info=True)
            return {
                'query': query,
                'error': str(e),
                'results': [],
                'total': 0,
            }
    
    def _analyze_query(self, query: str) -> Dict[str, Any]:
        """
        Analyze query to extract entities and determine search strategy.
        
        Args:
            query: User query string
            
        Returns:
            Query analysis with extracted entities and recommended strategy
        """
        analysis = {
            'has_money': False,
            'has_exact_id': False,
            'has_date': False,
            'has_vendor': False,
            'money_amounts': [],
            'currencies': [],
            'exact_ids': [],
            'dates': [],
            'vendors': [],
            'recommended_type': 'semantic',  # default
        }
        
        # Extract money amounts
        money_pattern = r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(USD|EUR|CZK|GBP|dollars?|euros?|koruna)?'
        money_matches = re.findall(money_pattern, query, re.IGNORECASE)
        if money_matches:
            analysis['has_money'] = True
            for amount_str, currency in money_matches:
                # Convert to cents
                amount = float(amount_str.replace(',', ''))
                cents = int(amount * 100)
                analysis['money_amounts'].append(cents)
                if currency:
                    analysis['currencies'].append(currency.upper()[:3])
        
        # Extract exact IDs (numbers, invoice numbers, etc.)
        id_pattern = r'\b([A-Z0-9]{3,}[-_]?[A-Z0-9]+|INV-\d+|\d{6,})\b'
        id_matches = re.findall(id_pattern, query)
        if id_matches:
            analysis['has_exact_id'] = True
            analysis['exact_ids'] = id_matches
        
        # Extract dates (simple patterns)
        date_pattern = r'\b(\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{4})\b'
        date_matches = re.findall(date_pattern, query)
        if date_matches:
            analysis['has_date'] = True
            analysis['dates'] = date_matches
        
        # This will be replaced with dynamic category detection
        # Vendors will be detected using SearchCategory configuration
        analysis['categories'] = {}  # Will store detected categories
        
        # Determine recommended search type
        # Simple heuristic: use keyword for exact/simple queries, semantic for natural language
        query_words = query.strip().split()
        
        if analysis['has_exact_id']:
            analysis['recommended_type'] = 'keyword'
        elif len(query_words) <= 2 and not analysis['has_money'] and not analysis['has_date']:
            # Simple 1-2 word queries -> keyword search for exact matches
            analysis['recommended_type'] = 'keyword'
        elif analysis['has_money'] or analysis['has_date'] or analysis['has_vendor']:
            analysis['recommended_type'] = 'hybrid'
        else:
            # Complex natural language queries -> semantic search
            analysis['recommended_type'] = 'semantic'
        
        return analysis
    
    async def _semantic_search(
        self,
        query: str,
        company_id: str,
        limit: int,
        query_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Pure semantic/vector search.
        
        Args:
            query: Search query
            company_id: Company ID for filtering
            limit: Max results
            query_analysis: Query analysis metadata
            
        Returns:
            List of search results
        """
        # Generate query embedding
        query_embedding = await self.embedding_service.embed_text(query)
        
        # Search both resources and chunks using motor aggregation
        # Note: This is a simplified version - full Atlas Search syntax would be used in production
        
        # For now, do simple cosine similarity in Python (not optimal, but works without Atlas Search setup)
        resources = await Resource.find(
            Resource.company_id == company_id
        ).to_list(limit * 2)
        
        results_map = {}  # Use dict to track best score per resource
        
        # 1. Search document-level embeddings
        for resource in resources:
            if resource.text_embedding:
                # Calculate cosine similarity
                similarity = self._cosine_similarity(query_embedding, resource.text_embedding)
                
                if similarity > 0.15:  # Very low threshold for better recall on proper nouns
                    results_map[str(resource.id)] = {
                        'id': str(resource.id),
                        'file_name': resource.file_name,
                        'file_type': resource.file_type,
                        'summary': resource.summary,
                        'vendor': resource.vendor,
                        'score': similarity,
                        'match_type': 'semantic_document',
                        'created_at': resource.created_at.isoformat(),
                    }
        
        # 2. Also search chunk-level embeddings (more granular, better for specific terms)
        chunks = await ResourceChunk.find(
            ResourceChunk.company_id == company_id
        ).to_list(limit * 10)  # Get more chunks to search through
        
        chunk_matches = {}  # Track best chunk match per parent document
        for chunk in chunks:
            if chunk.text_embedding:
                similarity = self._cosine_similarity(query_embedding, chunk.text_embedding)
                
                if similarity > 0.05:  # Very low threshold to catch brand names in context
                    parent_id = str(chunk.parent_id)
                    
                    # Keep only the best matching chunk per document
                    if parent_id not in chunk_matches or similarity > chunk_matches[parent_id]['score']:
                        chunk_matches[parent_id] = {
                            'score': similarity,
                            'chunk_index': chunk.chunk_index,
                            'chunk_text': chunk.text[:200] + '...' if len(chunk.text) > 200 else chunk.text
                        }
        
        # 3. Merge chunk results with resource info
        for parent_id, chunk_match in chunk_matches.items():
            # Find the parent resource
            parent = await Resource.find_one(Resource.id == ObjectId(parent_id))
            if parent:
                # If we already have this document from document-level search, use the higher score
                if parent_id in results_map:
                    if chunk_match['score'] > results_map[parent_id]['score']:
                        results_map[parent_id]['score'] = chunk_match['score']
                        results_map[parent_id]['match_type'] = 'semantic_chunk'
                        results_map[parent_id]['matched_in_chunk'] = chunk_match['chunk_index']
                        results_map[parent_id]['chunk_preview'] = chunk_match['chunk_text']
                else:
                    # New result from chunk search
                    results_map[parent_id] = {
                        'id': parent_id,
                        'file_name': parent.file_name,
                        'file_type': parent.file_type,
                        'summary': parent.summary,
                        'vendor': parent.vendor,
                        'score': chunk_match['score'],
                        'match_type': 'semantic_chunk',
                        'matched_in_chunk': chunk_match['chunk_index'],
                        'chunk_preview': chunk_match['chunk_text'],
                        'created_at': parent.created_at.isoformat(),
                    }
        
        # Convert to list and sort by score
        results = list(results_map.values())
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:limit]
    
    async def _keyword_search(
        self,
        query: str,
        company_id: str,
        limit: int,
        query_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Keyword/exact match search.
        
        Args:
            query: Search query
            company_id: Company ID for filtering
            limit: Max results
            query_analysis: Query analysis metadata
            
        Returns:
            List of search results
        """
        results = []
        
        # ✨ Search in chunks using normalized searchable_text field
        # Chunks contain all content from resources, so we don't need resource-level search
        # Get ALL chunks (Beanie has a default limit of 150, so we need to specify explicitly)
        chunks = await ResourceChunk.find(
            ResourceChunk.company_id == company_id
        ).limit(1000).to_list()
        
        chunk_matches = {}
        
        # ✨ Normalize query for diacritic-insensitive matching
        query_normalized = normalize_query(query)
        query_tokens = set(tokenize_for_search(query_normalized))
        
        self.logger.info(f"🔍 KEYWORD SEARCH: query='{query}', normalized='{query_normalized}', company_id={company_id}")
        self.logger.info(f"🔍 Found {len(chunks)} chunks to search")
        self.logger.info(f"🔍 Query tokens: {query_tokens}")
        
        # Debug: Check first chunk to see what fields it has (safe for None)
        if chunks:
            sample = chunks[0]
            st = getattr(sample, 'searchable_text', None)
            st_preview = (st[:50] + '...') if isinstance(st, str) and st else ('NONE' if st is None else str(st))
            self.logger.info(
                f"🔍 Sample chunk fields: file_name={sample.file_name}, "
                f"has_attr={hasattr(sample, 'searchable_text')}, "
                f"is_str={isinstance(st, str)}, "
                f"searchable_text_preview={st_preview}"
            )
        
        for chunk in chunks:
            score = 0.0
            match_type = None
            matched_field = None
            
            # ✨ Priority 1: Exact phrase match in searchable_text (HIGHEST SCORE)
            if chunk.searchable_text and query_normalized in chunk.searchable_text:
                score = 1.0  # Perfect exact phrase match
                match_type = 'exact_phrase'
                matched_field = 'searchable_text'
                self.logger.info(f"✅ EXACT PHRASE! file={chunk.file_name}, score={score}")
            
            # ✨ Priority 2: Exact phrase match in OCR text
            elif chunk.ocr_text_normalized and query_normalized in chunk.ocr_text_normalized:
                score = 0.98  # Exact phrase in OCR text
                match_type = 'exact_phrase'
                matched_field = 'ocr_text_normalized'
                self.logger.info(f"✅ EXACT PHRASE in OCR! file={chunk.file_name}, score={score}")
            
            # ✨ Priority 3: Exact phrase match in regular text
            elif chunk.text_normalized and query_normalized in chunk.text_normalized:
                score = 0.95  # Exact phrase in regular text
                match_type = 'exact_phrase'
                matched_field = 'text_normalized'
                self.logger.info(f"✅ EXACT PHRASE in text! file={chunk.file_name}, score={score}")
            
            # ✨ Priority 4: Exact phrase in image description
            elif chunk.image_description:
                desc_normalized = normalize_text(chunk.image_description)
                if query_normalized in desc_normalized:
                    score = 0.93  # Exact phrase in image description
                    match_type = 'exact_phrase'
                    matched_field = 'image_description'
                    self.logger.info(f"✅ EXACT PHRASE in image desc! file={chunk.file_name}, score={score}")
            
            # ✨ Priority 5: Partial word matching (LOWER SCORES)
            if score == 0.0:
                # Check for individual word matches with much lower scores
                best_partial_score = 0.0
                best_partial_field = None
                
                # Check each field for partial matches
                # Lower base scores to reduce false positives
                fields_to_check = [
                    ('searchable_text', chunk.searchable_text, 0.5),
                    ('ocr_text_normalized', chunk.ocr_text_normalized, 0.45),
                    ('text_normalized', chunk.text_normalized, 0.4)
                ]
                
                for field_name, field_value, base_score in fields_to_check:
                    if field_value:
                        chunk_tokens = set(tokenize_for_search(field_value))
                        overlap = query_tokens & chunk_tokens
                        if overlap:
                            # Score based on percentage of query tokens found
                            overlap_ratio = len(overlap) / len(query_tokens) if query_tokens else 0
                            # Require at least 50% overlap for multi-word queries (stricter)
                            min_threshold = 0.5 if len(query_tokens) > 1 else 0.25
                            if overlap_ratio >= min_threshold:
                                partial_score = base_score * overlap_ratio
                                if partial_score > best_partial_score:
                                    best_partial_score = partial_score
                                    best_partial_field = field_name
                                    match_type = 'partial_words'
                                    matched_field = field_name
                                    self.logger.debug(
                                        f"🔍 Partial match in {field_name} for {chunk.file_name}: "
                                        f"{len(overlap)}/{len(query_tokens)} words, overlap={overlap_ratio:.0%}, score={partial_score:.2f}"
                                    )
                
                score = best_partial_score
            
            # Add to results if score is high enough
            # Filter out weak partial matches (below 50%) to reduce noise
            min_score_threshold = 0.5 if match_type == 'partial_words' else 0.0
            if score > min_score_threshold:
                parent_id = str(chunk.parent_id)
                
                # Keep only the best matching chunk per document
                if parent_id not in chunk_matches or score > chunk_matches[parent_id]['score']:
                    chunk_matches[parent_id] = {
                        'id': parent_id,
                        'score': score,
                        'match_type': match_type,
                        'matched_field': matched_field,
                        'chunk_index': chunk.chunk_index,
                        'chunk_text': (chunk.text or chunk.ocr_text or '')[:200] + '...' 
                                     if len(chunk.text or chunk.ocr_text or '') > 200 
                                     else (chunk.text or chunk.ocr_text or '')
                    }
        
        # Merge chunk results with resource info
        for parent_id, chunk_match in chunk_matches.items():
            # Find the parent resource
            parent = await Resource.find_one(Resource.id == ObjectId(parent_id))
            if parent:
                results.append({
                    'id': str(parent.id),
                    'file_name': parent.file_name,
                    'file_type': parent.file_type,
                    'summary': parent.summary,
                    'vendor': parent.vendor,
                    'score': chunk_match['score'],
                    'match_type': chunk_match['match_type'],
                    'matched_in_chunk': chunk_match['chunk_index'],
                    'chunk_preview': chunk_match['chunk_text'],
                    'created_at': parent.created_at.isoformat(),
                })
        
        # Search by exact IDs in keywords
        if query_analysis['exact_ids']:
            for exact_id in query_analysis['exact_ids']:
                resources = await Resource.find(
                    Resource.company_id == company_id,
                    Resource.keywords == exact_id
                ).to_list(limit)
                
                for resource in resources:
                    results.append({
                        'id': str(resource.id),
                        'file_name': resource.file_name,
                        'file_type': resource.file_type,
                        'summary': resource.summary,
                        'vendor': resource.vendor,
                        'score': 1.0,  # Exact match
                        'match_type': 'exact_keyword',
                        'matched_value': exact_id,
                        'created_at': resource.created_at.isoformat(),
                    })
        
        # Search by vendor
        # Only use vendor matching if vendor is the main search term (not just incidental)
        # e.g. "google" or "google invoices" YES, but "google tag manager" NO
        if query_analysis['vendors']:
            # Check if query is primarily about the vendor (not a specific product/service)
            query_words = set(query_normalized.split())
            vendor_words = set(v.lower() for v in query_analysis['vendors'])
            non_vendor_words = query_words - vendor_words - {'invoice', 'invoices', 'bill', 'bills', 'payment', 'payments'}
            
            # Only apply vendor filter if there is 1 or fewer non-vendor, non-invoice words
            # This allows "google", "google invoice", "google czech" but blocks "google tag manager"
            if len(non_vendor_words) <= 1:
                for vendor in query_analysis['vendors']:
                    resources = await Resource.find(
                        Resource.company_id == company_id,
                        Resource.vendor == vendor
                    ).to_list(limit)
                    
                    for resource in resources:
                        # Boost vendor matches with score 0.88
                        # This ensures vendor matches rank high but don't override exact/keyword matches
                        results.append({
                            'id': str(resource.id),
                            'file_name': resource.file_name,
                            'file_type': resource.file_type,
                            'summary': resource.summary,
                            'vendor': resource.vendor,
                            'score': 0.88,
                            'match_type': 'vendor_filter',  # Changed to differentiate from semantic matches
                            'matched_value': vendor,
                            'created_at': resource.created_at.isoformat(),
                        })
        
        # Deduplicate and limit
        # Keep the result with highest score for each document
        # Prefer content-based matches (exact_phrase, keyword) over vendor_filter matches
        results_map = {}
        for result in results:
            doc_id = result['id']
            if doc_id not in results_map:
                results_map[doc_id] = result
            else:
                existing = results_map[doc_id]
                # Prefer higher score, but if scores are close (within 0.05),
                # prefer content matches over vendor_filter matches
                score_diff = result['score'] - existing['score']
                if score_diff > 0.05:
                    # New result has significantly higher score, use it
                    results_map[doc_id] = result
                elif score_diff > -0.05:
                    # Scores are close, prefer content match over vendor_filter
                    if existing['match_type'] == 'vendor_filter' and result['match_type'] != 'vendor_filter':
                        results_map[doc_id] = result
                    elif result['match_type'] == 'vendor_filter' and existing['match_type'] != 'vendor_filter':
                        # Keep existing (content match)
                        pass
                    elif result['score'] > existing['score']:
                        # Both same type, take higher score
                        results_map[doc_id] = result
                # else: existing has higher score, keep it
        
        unique_results = list(results_map.values())
        
        # Sort by score descending (highest first)
        unique_results.sort(key=lambda x: x['score'], reverse=True)
        
        self.logger.info(f"✅ KEYWORD SEARCH COMPLETE: {len(unique_results)} unique results")
        if unique_results:
            for i, r in enumerate(unique_results[:3]):
                self.logger.info(f"  Result {i+1}: {r.get('file_name')} - score={r.get('score'):.2f} - type={r.get('match_type')}")
        
        return unique_results[:limit]
    
    async def _hybrid_search(
        self,
        query: str,
        company_id: str,
        limit: int,
        query_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search combining semantic + keyword/filters.
        
        Args:
            query: Search query
            company_id: Company ID for filtering
            limit: Max results
            query_analysis: Query analysis metadata
            
        Returns:
            List of search results
        """
        # Get results from both approaches
        semantic_results = await self._semantic_search(query, company_id, limit, query_analysis)
        keyword_results = await self._keyword_search(query, company_id, limit, query_analysis)
        
        # Merge and re-rank
        results_map = {}
        
        # Add semantic results
        for result in semantic_results:
            results_map[result['id']] = result
            result['semantic_score'] = result['score']
            result['keyword_score'] = 0
        
        # Boost with keyword results
        for result in keyword_results:
            if result['id'] in results_map:
                # Already exists, boost score
                results_map[result['id']]['keyword_score'] = result['score']
                results_map[result['id']]['score'] = (
                    results_map[result['id']]['semantic_score'] * 0.6 +
                    result['score'] * 0.4
                )
                results_map[result['id']]['match_type'] = 'hybrid'
            else:
                # New result from keyword search
                results_map[result['id']] = result
                result['semantic_score'] = 0
                result['keyword_score'] = result['score']
        
        # Apply filters based on extracted entities
        filtered_results = []
        for result in results_map.values():
            # Filter by money amounts if specified
            if query_analysis['money_amounts']:
                # Would check if resource has matching amounts
                pass  # Simplified
            
            filtered_results.append(result)
        
        # Sort by combined score
        filtered_results.sort(key=lambda x: x['score'], reverse=True)
        
        return filtered_results[:limit]
    
    async def compound_search(
        self,
        query: str,
        owner_id: str,
        company_id: Optional[str] = None,
        limit: int = 30
    ) -> Dict[str, Any]:
        """
        Compound search using normalized text matching.
        
        Uses keyword search with diacritic-insensitive matching for best accuracy.
        
        Args:
            query: Natural language search query
            owner_id: User ID for ACL filtering
            company_id: Optional company ID for multi-tenant
            limit: Maximum results (default: 30)
            
        Returns:
            Search results with analysis
        """
        try:
            self.logger.info(f"✨ Compound search using normalized text matching for: '{query}'")
            
            # Use keyword search which has the normalized text matching
            # This gives us the best accuracy for diacritic-insensitive queries
            return await self.search(query, company_id or owner_id, limit, search_type="keyword")
            
        except Exception as e:
            self.logger.error(f"Compound search error: {e}", exc_info=True)
            # Fallback to keyword search
            return await self.search(query, company_id or owner_id, limit, search_type="keyword")
    
    def _build_deep_link(self, result: Dict) -> str:
        """Generate open URL for PDF page, CSV row, or image region."""
        resource_id = result['id']
        
        if result.get('page_number'):
            return f"/resources/{resource_id}?page={result['page_number']}"
        elif result.get('row_index'):
            return f"/resources/{resource_id}?row={result['row_index']}"
        else:
            return f"/resources/{resource_id}"
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        try:
            import numpy as np
            v1 = np.array(vec1)
            v2 = np.array(vec2)
            return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))
        except Exception:
            return 0.0


# Global singleton
_search_service: Optional[SearchService] = None


def get_search_service() -> SearchService:
    """Get or create the global search service instance."""
    global _search_service
    if _search_service is None:
        _search_service = SearchService()
    return _search_service
