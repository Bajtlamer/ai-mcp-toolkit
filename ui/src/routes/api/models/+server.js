// Models API proxy to backend server
import { json } from '@sveltejs/kit';

const BACKEND_HOST = process.env.MCP_HOST || 'localhost';
const BACKEND_PORT = process.env.MCP_PORT || '8000';
const BACKEND_URL = `http://${BACKEND_HOST}:${BACKEND_PORT}`;

/** @type {import('./$types').RequestHandler} */
export async function GET({ cookies }) {
  try {
    // Get session cookie to forward to backend
    const sessionId = cookies.get('session_id');
    
    if (!sessionId) {
      return json({ 
        success: false, 
        error: 'Authentication required',
        available_models: [],
        count: 0
      }, { status: 401 });
    }
    
    // Forward the request to the backend server with auth cookie
    const response = await fetch(`${BACKEND_URL}/ollama/models`, {
      method: 'GET',
      headers: {
        'Cookie': `session_id=${sessionId}`
      }
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Backend models API error:', response.status, errorText);
      return json({ 
        success: false, 
        error: `Backend server error: ${response.status}`,
        available_models: [],
        count: 0
      }, { status: response.status });
    }

    const data = await response.json();
    return json(data);

  } catch (error) {
    console.error('Models API proxy error:', error);
    return json({ 
      success: false, 
      error: `Failed to connect to backend server: ${error.message}`,
      available_models: [],
      count: 0
    }, { status: 500 });
  }
}
