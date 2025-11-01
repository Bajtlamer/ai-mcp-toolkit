"""Contextual search service using MongoDB Atlas hybrid search."""

import logging
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from bson import ObjectId

from ..models.documents import Resource, ResourceChunk
from .embedding_service import get_embedding_service
from .query_analyzer import QueryAnalyzer

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
        self.logger.info("SearchService initialized with compound search support")
    
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
        
        # Search in file names, summaries, and content using text matching
        import re
        query_pattern = re.compile(re.escape(query), re.IGNORECASE)
        
        all_resources = await Resource.find(
            Resource.company_id == company_id
        ).to_list(limit * 3)
        
        for resource in all_resources:
            score = 0.0
            match_field = None
            
            # Check file_name
            if resource.file_name and query_pattern.search(resource.file_name):
                score = 1.0
                match_field = 'file_name'
            # Check summary
            elif resource.summary and query_pattern.search(resource.summary):
                score = 0.9
                match_field = 'summary'
            # Check content
            elif resource.content and query_pattern.search(resource.content):
                score = 0.85
                match_field = 'content'
            # Check keywords
            elif resource.keywords and any(query_pattern.search(kw) for kw in resource.keywords):
                score = 0.95
                match_field = 'keywords'
            # Check entities
            elif resource.entities and any(query_pattern.search(ent) for ent in resource.entities):
                score = 0.8
                match_field = 'entities'
            
            if score > 0:
                results.append({
                    'id': str(resource.id),
                    'file_name': resource.file_name,
                    'file_type': resource.file_type,
                    'summary': resource.summary,
                    'vendor': resource.vendor,
                    'score': score,
                    'match_type': 'keyword',
                    'matched_field': match_field,
                    'created_at': resource.created_at.isoformat(),
                })
        
        # Also search in chunks for more precise results
        chunks = await ResourceChunk.find(
            ResourceChunk.company_id == company_id
        ).to_list(limit * 5)
        
        chunk_matches = {}
        for chunk in chunks:
            if chunk.text and query_pattern.search(chunk.text):
                parent_id = chunk.parent_id
                if parent_id not in chunk_matches or chunk_matches[parent_id]['score'] < 0.95:
                    chunk_matches[parent_id] = {
                        'id': parent_id,
                        'score': 0.95,
                        'match_type': 'chunk',
                        'chunk_index': chunk.chunk_index,
                        'chunk_text': chunk.text[:200] + '...' if len(chunk.text) > 200 else chunk.text
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
    
    async def compound_search(
        self,
        query: str,
        owner_id: str,
        company_id: Optional[str] = None,
        limit: int = 30
    ) -> Dict[str, Any]:
        """
        Simplified Atlas text search (compound doesn't work with knnBeta).
        
        Args:
            query: Natural language search query
            owner_id: User ID for ACL filtering
            company_id: Optional company ID for multi-tenant
            limit: Maximum results (default: 30)
            
        Returns:
            Search results with analysis
        """
        try:
            self.logger.info(f"Using legacy hybrid search (compound not working)")
            
            # Analyze query
            analysis = self.query_analyzer.analyze(query)
            
            # Just use legacy hybrid search - it was working
            return await self.search(query, company_id or owner_id, limit, search_type="hybrid")
            
            self.logger.info(f"Search text: '{search_text}'")
            
            # Build OR query for multiple words (better for partial matching)
            pipeline = [
                {
                    "$search": {
                        "index": "resource_chunks_compound",
                        "compound": {
                            "should": [
                                # Exact phrase in OCR (highest priority)
                                {
                                    "phrase": {
                                        "query": search_text,
                                        "path": "ocr_text",
                                        "score": {"boost": {"value": 20}}
                                    }
                                },
                                # Individual words in OCR with fuzzy (for diacritics)
                                {
                                    "text": {
                                        "query": search_text,
                                        "path": "ocr_text",
                                        "fuzzy": {"maxEdits": 2},
                                        "score": {"boost": {"value": 10}}
                                    }
                                },
                                # Fallback to regular text fields
                                {
                                    "text": {
                                        "query": search_text,
                                        "path": ["text", "content"],
                                        "fuzzy": {"maxEdits": 1}
                                    }
                                }
                            ],
                            "minimumShouldMatch": 1
                        }
                    }
                },
                # Add score as field BEFORE grouping
                {
                    "$addFields": {
                        "search_score": {"$meta": "searchScore"}
                    }
                },
                # ACL filter AFTER search (post-filter)
                {"$match": {"owner_id": owner_id}},
                # Sort by score first
                {"$sort": {"search_score": -1}},
                # Group by parent_id to avoid duplicates (keep highest scoring chunk per resource)
                {
                    "$group": {
                        "_id": "$parent_id",
                        "file_name": {"$first": "$file_name"},
                        "file_type": {"$first": "$file_type"},
                        "text": {"$first": "$text"},
                        "ocr_text": {"$first": "$ocr_text"},
                        "caption": {"$first": "$caption"},
                        "vendor": {"$first": "$vendor"},
                        "currency": {"$first": "$currency"},
                        "amounts_cents": {"$first": "$amounts_cents"},
                        "page_number": {"$first": "$page_number"},
                        "row_index": {"$first": "$row_index"},
                        "score": {"$first": "$search_score"}
                    }
                },
                # Sort grouped results by score
                {"$sort": {"score": -1}},
                {"$limit": limit},
                {
                    "$project": {
                        "parent_id": 1,
                        "file_name": 1,
                        "file_type": 1,
                        "text": 1,
                        "ocr_text": 1,
                        "caption": 1,
                        "vendor": 1,
                        "currency": 1,
                        "amounts_cents": 1,
                        "page_number": 1,
                        "row_index": 1,
                        "score": {"$meta": "searchScore"},
                        "highlights": {"$meta": "searchHighlights"}
                    }
                }
            ]
            
            # Execute search
            chunks_collection = ResourceChunk.get_pymongo_collection()
            cursor = chunks_collection.aggregate(pipeline)
            results_raw = await cursor.to_list(length=limit)
            
            # Format results (grouped by parent_id now)
            results = []
            for r in results_raw:
                results.append({
                    'id': str(r.get('_id')),  # _id is now parent_id from grouping
                    'file_name': r.get('file_name'),
                    'file_type': r.get('file_type'),
                    'text': r.get('text', '')[:200] if r.get('text') else '',
                    'ocr_text': r.get('ocr_text'),
                    'caption': r.get('caption'),
                    'vendor': r.get('vendor'),
                    'currency': r.get('currency'),
                    'amounts_cents': r.get('amounts_cents'),
                    'page_number': r.get('page_number'),
                    'row_index': r.get('row_index'),
                    'score': r.get('score', 0) / 10,  # Normalize score
                    'highlights': [],
                    'match_type': 'text_search',
                    'open_url': self._build_deep_link({'id': str(r.get('_id')), 'page_number': r.get('page_number'), 'row_index': r.get('row_index')})
                })
            
            self.logger.info(f"Found {len(results)} results")
            
            return {
                'query': query,
                'analysis': analysis,
                'results': results,
                'total': len(results),
                'search_strategy': 'simple_text',
            }
            
        except Exception as e:
            self.logger.error(f"Search error: {e}", exc_info=True)
            # Fallback to legacy
            return await self.search(query, company_id or owner_id, limit, search_type="hybrid")
    
    async def _execute_atlas_compound_search(
        self,
        must_clauses: List[Dict],
        should_clauses: List[Dict],
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Execute MongoDB Atlas $search.compound aggregation.
        
        Args:
            must_clauses: Required filters
            should_clauses: Optional ranking factors
            limit: Max results
            
        Returns:
            List of search results
        """
        # Build aggregation pipeline
        pipeline = [
            {
                "$search": {
                    "index": "resource_chunks_compound",
                    "compound": {
                        "must": must_clauses,
                        "should": should_clauses,
                        "minimumShouldMatch": 1 if should_clauses else 0
                    }
                }
            },
            {"$limit": limit},
            {
                "$project": {
                    "parent_id": 1,
                    "resource_uri": 1,
                    "file_name": 1,
                    "file_type": 1,
                    "text": 1,
                    "content": 1,
                    "page_number": 1,
                    "row_index": 1,
                    "bbox": 1,
                    "vendor": 1,
                    "currency": 1,
                    "amounts_cents": 1,
                    "keywords": 1,
                    "entities": 1,
                    "caption": 1,
                    "image_labels": 1,
                    "ocr_text": 1,
                    "score": {"$meta": "searchScore"},
                    "highlights": {"$meta": "searchHighlights"}
                }
            }
        ]
        
        # Execute aggregation on ResourceChunk collection
        chunks_collection = ResourceChunk.get_pymongo_collection()
        cursor = chunks_collection.aggregate(pipeline)
        results = await cursor.to_list(length=limit)
        
        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append({
                'id': str(result.get('parent_id')),
                'file_name': result.get('file_name'),
                'file_type': result.get('file_type'),
                'chunk_text': result.get('text') or result.get('content', '')[:200],
                'page_number': result.get('page_number'),
                'row_index': result.get('row_index'),
                'vendor': result.get('vendor'),
                'currency': result.get('currency'),
                'amounts_cents': result.get('amounts_cents'),
                'score': result.get('score', 0),
                'highlights': result.get('highlights', []),
                'caption': result.get('caption'),
                'ocr_text': result.get('ocr_text'),
            })
        
        return formatted_results
    
    def _determine_match_type(self, result: Dict, analysis: Dict) -> str:
        """Determine why this result matched (for explainability)."""
        if analysis['money'] and result.get('currency'):
            return 'exact_amount'
        elif analysis['ids'] and any(id in result.get('keywords', []) for id in analysis['ids']):
            return 'exact_id'
        elif result['score'] > 0.8:
            return 'semantic_strong'
        else:
            return 'hybrid'
    
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
