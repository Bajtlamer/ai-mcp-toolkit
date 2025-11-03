// File download API proxy to backend MCP server
const BACKEND_HOST = process.env.MCP_HOST || 'localhost';
const BACKEND_PORT = process.env.MCP_PORT || '8000';
const BACKEND_URL = `http://${BACKEND_HOST}:${BACKEND_PORT}`;

/** @type {import('./$types').RequestHandler} */
export async function GET({ params, cookies }) {
  try {
    const { file_id } = params;
    const sessionId = cookies.get('session_id');
    
    if (!sessionId) {
      return new Response(JSON.stringify({ 
        error: 'Authentication required. Please log in.' 
      }), { 
        status: 401,
        headers: { 'Content-Type': 'application/json' }
      });
    }
    
    // Forward the request to backend with auth cookie
    const response = await fetch(`${BACKEND_URL}/resources/download/${file_id}`, {
      method: 'GET',
      headers: {
        'Cookie': `session_id=${sessionId}`
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Download failed' }));
      console.error('Backend download error:', response.status, errorData);
      return new Response(JSON.stringify({ 
        error: errorData.detail || `Download failed: ${response.status}` 
      }), { 
        status: response.status,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    // Get the file content as blob
    const fileBlob = await response.blob();
    
    // Forward all relevant headers from backend
    const headers = new Headers();
    headers.set('Content-Type', response.headers.get('Content-Type') || 'application/octet-stream');
    headers.set('Content-Length', response.headers.get('Content-Length') || '0');
    
    const contentDisposition = response.headers.get('Content-Disposition');
    if (contentDisposition) {
      headers.set('Content-Disposition', contentDisposition);
    }
    
    const cacheControl = response.headers.get('Cache-Control');
    if (cacheControl) {
      headers.set('Cache-Control', cacheControl);
    }

    return new Response(fileBlob, {
      status: 200,
      headers
    });

  } catch (error) {
    console.error('Download API proxy error:', error);
    return new Response(JSON.stringify({ 
      error: `Failed to download file: ${error.message}` 
    }), { 
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}
