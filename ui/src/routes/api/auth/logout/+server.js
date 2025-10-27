import { json } from '@sveltejs/kit';

const BACKEND_HOST = process.env.MCP_HOST || 'localhost';
const BACKEND_PORT = process.env.MCP_PORT || '8000';
const BACKEND_URL = `http://${BACKEND_HOST}:${BACKEND_PORT}`;

/** @type {import('./$types').RequestHandler} */
export async function POST({ cookies }) {
  try {
    const sessionId = cookies.get('session_id');
    
    if (sessionId) {
      // Call backend logout
      await fetch(`${BACKEND_URL}/auth/logout`, {
        method: 'POST',
        headers: {
          'Cookie': `session_id=${sessionId}`
        }
      });
    }
    
    // Delete frontend cookie
    cookies.delete('session_id', { path: '/' });
    
    return json({ success: true });
    
  } catch (error) {
    console.error('Logout proxy error:', error);
    // Still delete cookie even if backend call fails
    cookies.delete('session_id', { path: '/' });
    return json({ success: true });
  }
}
