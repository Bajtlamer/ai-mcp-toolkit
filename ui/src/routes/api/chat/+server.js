// Chat API proxy to backend MCP server
import { json } from '@sveltejs/kit';

const BACKEND_HOST = process.env.MCP_HOST || 'localhost';
const BACKEND_PORT = process.env.MCP_PORT || '8000';
const BACKEND_URL = `http://${BACKEND_HOST}:${BACKEND_PORT}`;

/** @type {import('./$types').RequestHandler} */
export async function POST({ request }) {
  try {
    const { message, model, temperature, max_tokens } = await request.json();
    
    // Forward the request to the backend MCP server
    const response = await fetch(`${BACKEND_URL}/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        messages: [
          {
            role: 'user',
            content: message
          }
        ],
        model: model || 'qwen2.5:14b',
        temperature: temperature || 0.7,
        max_tokens: max_tokens || 2000,
        stream: false
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Backend chat API error:', response.status, errorText);
      return json({ 
        success: false, 
        error: `Backend server error: ${response.status}` 
      }, { status: 502 });
    }

    const data = await response.json();
    
    // Extract the response content and metrics from OpenAI-style format
    const content = data.choices?.[0]?.message?.content || 'No response received';
    const usage = data.usage || {};
    
    return json({
      success: true,
      content: content,
      metrics: {
        totalTime: usage.total_duration || 0,
        tokensPerSecond: usage.tokens_per_second || 0,
        promptTokens: usage.prompt_tokens || 0,
        completionTokens: usage.completion_tokens || 0,
        totalTokens: usage.total_tokens || 0,
        promptEvalDuration: usage.prompt_eval_duration || 0,
        evalDuration: usage.eval_duration || 0
      }
    });

  } catch (error) {
    console.error('Chat API proxy error:', error);
    return json({ 
      success: false, 
      error: `Failed to connect to backend server: ${error.message}` 
    }, { status: 500 });
  }
}