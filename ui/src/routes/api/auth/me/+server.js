import { json } from '@sveltejs/kit';

const BACKEND_HOST = process.env.MCP_HOST || 'localhost';
const BACKEND_PORT = process.env.MCP_PORT || '8000';
const BACKEND_URL = `http://${BACKEND_HOST}:${BACKEND_PORT}`;

/** @type {import('./$types').RequestHandler} */
export async function GET({ cookies }) {
  try {
    const sessionId = cookies.get('session_id');
    
    if (!sessionId) {
      return json({ detail: 'Not authenticated' }, { status: 401 });
    }
    
    const response = await fetch(`${BACKEND_URL}/auth/me`, {
      headers: {
        'Cookie': `session_id=${sessionId}`
      }
    });
    
    if (!response.ok) {
      return json({ detail: 'Not authenticated' }, { status: 401 });
    }
    
    const data = await response.json();
    return json(data);
    
  } catch (error) {
    console.error('Auth me proxy error:', error);
    return json({ detail: 'Not authenticated' }, { status: 401 });
  }
}
