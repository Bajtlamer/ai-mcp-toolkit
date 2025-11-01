/**
 * Search API service for compound search
 */

const API_BASE = 'http://localhost:8000';

/**
 * Perform compound search with automatic query analysis
 * @param {string} query - Search query
 * @param {number} limit - Maximum results to return (default: 30)
 * @returns {Promise<Object>} Search results with analysis and match types
 */
export async function compoundSearch(query, limit = 30) {
  const response = await fetch(`${API_BASE}/resources/compound-search`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify({ query, limit }),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `Search failed: ${response.statusText}`);
  }
  
  return await response.json();
}

/**
 * Legacy search endpoint (kept for backward compatibility)
 * @deprecated Use compoundSearch instead
 */
export async function legacySearch(query, searchType = 'auto', limit = 20) {
  const params = new URLSearchParams({
    q: query,
    limit: limit.toString(),
    search_type: searchType,
  });
  
  const response = await fetch(`${API_BASE}/resources/search?${params}`, {
    credentials: 'include',
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `Search failed: ${response.statusText}`);
  }
  
  return await response.json();
}
