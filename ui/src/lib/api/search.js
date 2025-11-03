/**
 * Search API service for compound search
 * All requests go through SvelteKit server endpoints for proper authentication
 */

/**
 * Perform compound search with automatic query analysis
 * @param {string} query - Search query
 * @param {number} limit - Maximum results to return (default: 30)
 * @returns {Promise<Object>} Search results with analysis and match types
 */
export async function compoundSearch(query, limit = 30) {
  const response = await fetch('/api/search', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ query, limit }),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `Search failed: ${response.statusText}`);
  }
  
  return await response.json();
}

/**
 * Get search suggestions
 * @param {string} query - Partial search query
 * @param {number} limit - Maximum suggestions to return (default: 10)
 * @returns {Promise<Array>} Array of suggestions
 */
export async function getSearchSuggestions(query, limit = 10) {
  const params = new URLSearchParams({
    q: query,
    limit: limit.toString(),
  });
  
  const response = await fetch(`/api/search?${params}`, {
    method: 'GET',
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `Search failed: ${response.statusText}`);
  }
  
  return await response.json();
}
