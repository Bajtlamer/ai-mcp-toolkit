"""Contextual search service using MongoDB Atlas hybrid search."""

import logging
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..models.documents import Resource, ResourceChunk
from .embedding_service import get_embedding_service

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
        self.logger.info("SearchService initialized")
    
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
        
        # Extract common vendor names
        vendor_patterns = [
            'google', 't-mobile', 'tmobile', 'amazon', 'aws', 'microsoft',
            'apple', 'adobe', 'salesforce', 'zoom', 'slack'
        ]
        query_lower = query.lower()
        for vendor in vendor_patterns:
            if vendor in query_lower:
                analysis['has_vendor'] = True
                analysis['vendors'].append(vendor)
        
        # Determine recommended search type
        if analysis['has_exact_id']:
            analysis['recommended_type'] = 'keyword'
        elif analysis['has_money'] or analysis['has_date'] or analysis['has_vendor']:
            analysis['recommended_type'] = 'hybrid'
        else:
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
        
        results = []
        for resource in resources:
            if resource.text_embedding:
                # Calculate cosine similarity
                similarity = self._cosine_similarity(query_embedding, resource.text_embedding)
                
                if similarity > 0.5:  # Threshold
                    results.append({
                        'id': str(resource.id),
                        'file_name': resource.file_name,
                        'file_type': resource.file_type,
                        'summary': resource.summary,
                        'vendor': resource.vendor,
                        'score': similarity,
                        'match_type': 'semantic',
                        'created_at': resource.created_at.isoformat(),
                    })
        
        # Sort by score and limit
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
        
        # Search by exact IDs
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
        if query_analysis['vendors']:
            for vendor in query_analysis['vendors']:
                resources = await Resource.find(
                    Resource.company_id == company_id,
                    Resource.vendor == vendor
                ).to_list(limit)
                
                for resource in resources:
                    results.append({
                        'id': str(resource.id),
                        'file_name': resource.file_name,
                        'file_type': resource.file_type,
                        'summary': resource.summary,
                        'vendor': resource.vendor,
                        'score': 0.95,
                        'match_type': 'vendor',
                        'matched_value': vendor,
                        'created_at': resource.created_at.isoformat(),
                    })
        
        # Deduplicate and limit
        seen = set()
        unique_results = []
        for result in results:
            if result['id'] not in seen:
                seen.add(result['id'])
                unique_results.append(result)
        
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
