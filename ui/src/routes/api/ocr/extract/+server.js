// OCR extraction API proxy to backend MCP server
import { json } from '@sveltejs/kit';

const BACKEND_HOST = process.env.MCP_HOST || 'localhost';
const BACKEND_PORT = process.env.MCP_PORT || '8000';
const BACKEND_URL = `http://${BACKEND_HOST}:${BACKEND_PORT}`;

/** @type {import('./$types').RequestHandler} */
export async function POST({ request, cookies }) {
  try {
    // Get the form data from the request
    const formData = await request.formData();
    
    // Get session cookie from request
    const sessionCookie = cookies.get('session_id');
    
    // Prepare headers with session cookie if available
    const headers = {};
    
    if (sessionCookie) {
      headers['Cookie'] = `session_id=${sessionCookie}`;
    }
    
    // Forward the request to the backend MCP server
    const response = await fetch(`${BACKEND_URL}/api/ocr/extract`, {
      method: 'POST',
      headers,
      body: formData, // Forward the FormData directly
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Backend OCR API error:', response.status, errorText);
      return json({ 
        success: false, 
        error: `Backend server error: ${response.status}` 
      }, { status: 502 });
    }

    const data = await response.json();
    return json(data);

  } catch (error) {
    console.error('OCR API proxy error:', error);
    return json({ 
      success: false, 
      error: `Failed to connect to backend server: ${error.message}` 
    }, { status: 500 });
  }
}
