// Resource search API proxy to backend MCP server
import { json } from '@sveltejs/kit';

const BACKEND_HOST = process.env.MCP_HOST || 'localhost';
const BACKEND_PORT = process.env.MCP_PORT || '8000';
const BACKEND_URL = `http://${BACKEND_HOST}:${BACKEND_PORT}`;

/** @type {import('./$types').RequestHandler} */
export async function GET({ params, url, cookies }) {
  try {
    const sessionId = cookies.get('session_id');
    
    if (!sessionId) {
      return json({ 
        error: 'Authentication required. Please log in.' 
      }, { status: 401 });
    }
    
    // Get query parameters (e.g., limit)
    const queryParams = url.searchParams.toString();
    const endpoint = queryParams 
      ? `${BACKEND_URL}/resources/search/${encodeURIComponent(params.query)}?${queryParams}`
      : `${BACKEND_URL}/resources/search/${encodeURIComponent(params.query)}`;
    
    const response = await fetch(endpoint, {
      headers: {
        'Cookie': `session_id=${sessionId}`
      },
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Backend resource search error:', response.status, errorText);
      return json({ 
        error: `Failed to search resources: ${response.status}` 
      }, { status: response.status });
    }

    const data = await response.json();
    return json(data);

  } catch (error) {
    console.error('Resource search API proxy error:', error);
    return json({ 
      error: `Failed to connect to backend server: ${error.message}` 
    }, { status: 500 });
  }
}
