// File upload API proxy to backend MCP server
import { json } from '@sveltejs/kit';

const BACKEND_HOST = process.env.MCP_HOST || 'localhost';
const BACKEND_PORT = process.env.MCP_PORT || '8000';
const BACKEND_URL = `http://${BACKEND_HOST}:${BACKEND_PORT}`;

/** @type {import('./$types').RequestHandler} */
export async function POST({ request, cookies }) {
  try {
    const sessionId = cookies.get('session_id');
    
    if (!sessionId) {
      return json({ 
        error: 'Authentication required. Please log in.' 
      }, { status: 401 });
    }
    
    // Get the FormData from the request
    const formData = await request.formData();
    
    // Forward the multipart form data to backend with auth cookie
    const response = await fetch(`${BACKEND_URL}/resources/upload`, {
      method: 'POST',
      headers: {
        'Cookie': `session_id=${sessionId}`
        // Don't set Content-Type - let fetch handle it with correct boundary
      },
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Upload failed' }));
      console.error('Backend upload error:', response.status, errorData);
      return json({ 
        error: errorData.detail || `Upload failed: ${response.status}` 
      }, { status: response.status });
    }

    const data = await response.json();
    return json(data);

  } catch (error) {
    console.error('Upload API proxy error:', error);
    return json({ 
      error: `Failed to upload file: ${error.message}` 
    }, { status: 500 });
  }
}
