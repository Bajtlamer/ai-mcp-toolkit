import { json } from '@sveltejs/kit';

const BACKEND_HOST = process.env.MCP_HOST || 'localhost';
const BACKEND_PORT = process.env.MCP_PORT || '8000';
const BACKEND_URL = `http://${BACKEND_HOST}:${BACKEND_PORT}`;

/** @type {import('./$types').RequestHandler} */
export async function POST({ request, cookies }) {
  try {
    const body = await request.json();
    
    const response = await fetch(`${BACKEND_URL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(body)
    });
    
    if (!response.ok) {
      const error = await response.json();
      return json(error, { status: response.status });
    }
    
    // Extract session cookie from backend response
    const setCookieHeader = response.headers.get('set-cookie');
    if (setCookieHeader) {
      const sessionMatch = setCookieHeader.match(/session_id=([^;]+)/);
      if (sessionMatch) {
        const sessionId = sessionMatch[1];
        // Set cookie on frontend domain
        cookies.set('session_id', sessionId, {
          path: '/',
          httpOnly: true,
          sameSite: 'lax',
          maxAge: 60 * 60 * 24 * 7 // 7 days
        });
      }
    }
    
    const data = await response.json();
    return json(data);
    
  } catch (error) {
    console.error('Login proxy error:', error);
    return json({ 
      detail: `Failed to connect to backend: ${error.message}` 
    }, { status: 500 });
  }
}
