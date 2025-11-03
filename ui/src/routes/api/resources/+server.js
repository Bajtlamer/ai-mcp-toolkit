// Resources API proxy to backend MCP server
import { json } from '@sveltejs/kit';

const BACKEND_HOST = process.env.MCP_HOST || 'localhost';
const BACKEND_PORT = process.env.MCP_PORT || '8000';
const BACKEND_URL = `http://${BACKEND_HOST}:${BACKEND_PORT}`;

/** @type {import('./$types').RequestHandler} */
export async function GET({ url, cookies }) {
  try {
    const sessionId = cookies.get('session_id');
    
    if (!sessionId) {
      return json({ 
        error: 'Authentication required. Please log in.' 
      }, { status: 401 });
    }
    
    // Forward query parameters to backend
    const params = url.searchParams.toString();
    const endpoint = params ? `${BACKEND_URL}/resources?${params}` : `${BACKEND_URL}/resources`;
    
    const response = await fetch(endpoint, {
      headers: {
        'Cookie': `session_id=${sessionId}`
      },
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Backend resources API error:', response.status, errorText);
      return json({ 
        error: `Failed to list resources: ${response.status}` 
      }, { status: response.status });
    }

    const data = await response.json();
    return json(data);

  } catch (error) {
    console.error('Resources API proxy error:', error);
    return json({ 
      error: `Failed to connect to backend server: ${error.message}` 
    }, { status: 500 });
  }
}

/** @type {import('./$types').RequestHandler} */
export async function POST({ request, cookies }) {
  try {
    const sessionId = cookies.get('session_id');
    
    if (!sessionId) {
      return json({ 
        error: 'Authentication required. Please log in.' 
      }, { status: 401 });
    }
    
    const body = await request.json();
    
    // Forward create resource request to backend
    const response = await fetch(`${BACKEND_URL}/resources`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Cookie': `session_id=${sessionId}`
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Backend create resource error:', response.status, errorText);
      return json({ 
        error: `Failed to create resource: ${response.status}` 
      }, { status: response.status });
    }

    const data = await response.json();
    return json(data);

  } catch (error) {
    console.error('Create resource API proxy error:', error);
    return json({ 
      error: `Failed to connect to backend server: ${error.message}` 
    }, { status: 500 });
  }
}
