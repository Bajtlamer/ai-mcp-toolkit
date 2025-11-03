// Conversation count stats API proxy to backend MCP server
import { json } from '@sveltejs/kit';

const BACKEND_HOST = process.env.MCP_HOST || 'localhost';
const BACKEND_PORT = process.env.MCP_PORT || '8000';
const BACKEND_URL = `http://${BACKEND_HOST}:${BACKEND_PORT}`;

/** @type {import('./$types').RequestHandler} */
export async function GET({ cookies }) {
  try {
    const sessionId = cookies.get('session_id');
    
    if (!sessionId) {
      return json({ 
        error: 'Authentication required. Please log in.' 
      }, { status: 401 });
    }
    
    // Forward count request to backend
    const response = await fetch(`${BACKEND_URL}/conversations/stats/count`, {
      headers: {
        'Cookie': `session_id=${sessionId}`
      },
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Backend conversation count error:', response.status, errorText);
      return json({ 
        error: `Failed to get conversation count: ${response.status}` 
      }, { status: response.status });
    }

    const data = await response.json();
    return json(data);

  } catch (error) {
    console.error('Conversation count API proxy error:', error);
    return json({ 
      error: `Failed to connect to backend server: ${error.message}` 
    }, { status: 500 });
  }
}
