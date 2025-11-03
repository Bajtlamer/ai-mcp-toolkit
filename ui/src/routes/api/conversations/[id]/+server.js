// Single conversation API proxy to backend MCP server
import { json } from '@sveltejs/kit';

const BACKEND_HOST = process.env.MCP_HOST || 'localhost';
const BACKEND_PORT = process.env.MCP_PORT || '8000';
const BACKEND_URL = `http://${BACKEND_HOST}:${BACKEND_PORT}`;

/** @type {import('./$types').RequestHandler} */
export async function GET({ params, cookies }) {
  try {
    const sessionId = cookies.get('session_id');
    
    if (!sessionId) {
      return json({ 
        error: 'Authentication required. Please log in.' 
      }, { status: 401 });
    }
    
    const response = await fetch(`${BACKEND_URL}/conversations/${params.id}`, {
      headers: {
        'Cookie': `session_id=${sessionId}`
      },
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Backend get conversation error:', response.status, errorText);
      return json({ 
        error: `Failed to get conversation: ${response.status}` 
      }, { status: response.status });
    }

    const data = await response.json();
    return json(data);

  } catch (error) {
    console.error('Get conversation API proxy error:', error);
    return json({ 
      error: `Failed to connect to backend server: ${error.message}` 
    }, { status: 500 });
  }
}

/** @type {import('./$types').RequestHandler} */
export async function PUT({ params, request, cookies }) {
  try {
    const sessionId = cookies.get('session_id');
    
    if (!sessionId) {
      return json({ 
        error: 'Authentication required. Please log in.' 
      }, { status: 401 });
    }
    
    const body = await request.json();
    
    const response = await fetch(`${BACKEND_URL}/conversations/${params.id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Cookie': `session_id=${sessionId}`
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Backend update conversation error:', response.status, errorText);
      return json({ 
        error: `Failed to update conversation: ${response.status}` 
      }, { status: response.status });
    }

    const data = await response.json();
    return json(data);

  } catch (error) {
    console.error('Update conversation API proxy error:', error);
    return json({ 
      error: `Failed to connect to backend server: ${error.message}` 
    }, { status: 500 });
  }
}

/** @type {import('./$types').RequestHandler} */
export async function DELETE({ params, cookies }) {
  try {
    const sessionId = cookies.get('session_id');
    
    if (!sessionId) {
      return json({ 
        error: 'Authentication required. Please log in.' 
      }, { status: 401 });
    }
    
    const response = await fetch(`${BACKEND_URL}/conversations/${params.id}`, {
      method: 'DELETE',
      headers: {
        'Cookie': `session_id=${sessionId}`
      },
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Backend delete conversation error:', response.status, errorText);
      return json({ 
        error: `Failed to delete conversation: ${response.status}` 
      }, { status: response.status });
    }

    return json({ success: true });

  } catch (error) {
    console.error('Delete conversation API proxy error:', error);
    return json({ 
      error: `Failed to connect to backend server: ${error.message}` 
    }, { status: 500 });
  }
}
