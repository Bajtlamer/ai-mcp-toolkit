// Search API proxy to backend MCP server
import { json } from '@sveltejs/kit';

const BACKEND_HOST = process.env.MCP_HOST || 'localhost';
const BACKEND_PORT = process.env.MCP_PORT || '8000';
const BACKEND_URL = `http://${BACKEND_HOST}:${BACKEND_PORT}`;

/** @type {import('./$types').RequestHandler} */
export async function POST({ request, cookies }) {
  try {
    const body = await request.json();
    const sessionId = cookies.get('session_id');
    
    if (!sessionId) {
      return json({ 
        error: 'Authentication required. Please log in.' 
      }, { status: 401 });
    }
    
    // Forward compound search request to backend
    const response = await fetch(`${BACKEND_URL}/resources/compound-search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Cookie': `session_id=${sessionId}`
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Backend search API error:', response.status, errorText);
      return json({ 
        error: `Search failed: ${response.status}` 
      }, { status: response.status });
    }

    const data = await response.json();
    return json(data);

  } catch (error) {
    console.error('Search API proxy error:', error);
    return json({ 
      error: `Failed to connect to backend server: ${error.message}` 
    }, { status: 500 });
  }
}

/** @type {import('./$types').RequestHandler} */
export async function GET({ url, cookies }) {
  try {
    const query = url.searchParams.get('q');
    const limit = url.searchParams.get('limit') || '10';
    const sessionId = cookies.get('session_id');
    
    if (!sessionId) {
      return json({ 
        error: 'Authentication required. Please log in.' 
      }, { status: 401 });
    }
    
    // Forward suggestions request to backend
    const response = await fetch(
      `${BACKEND_URL}/search/suggestions?q=${encodeURIComponent(query)}&limit=${limit}`,
      {
        headers: {
          'Cookie': `session_id=${sessionId}`
        },
      }
    );

    if (!response.ok) {
      console.error('Backend suggestions API error:', response.status);
      return json([], { status: response.status });
    }

    const data = await response.json();
    return json(data);

  } catch (error) {
    console.error('Suggestions API proxy error:', error);
    return json([], { status: 500 });
  }
}
