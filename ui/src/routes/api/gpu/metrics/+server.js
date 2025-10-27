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
				error: 'Authentication required',
				performance_summary: {},
				current_metrics: {}
			}, { status: 401 });
		}
		
		// Forward request to backend
		const response = await fetch(`${BACKEND_URL}/gpu/metrics`, {
			method: 'GET',
			headers: {
				'Cookie': `session_id=${sessionId}`
			}
		});
		
		if (!response.ok) {
			throw new Error(`Backend returned ${response.status}`);
		}
		
		const data = await response.json();
		return json(data, {
			headers: {
				'Cache-Control': 'no-cache, no-store, must-revalidate',
				'Pragma': 'no-cache',
				'Expires': '0'
			}
		});
		
	} catch (error) {
		console.error('GPU metrics API error:', error);
		
		// Fallback: return empty metrics
		const currentTime = Date.now();
		return json({
			performance_summary: {
				current_timestamp: currentTime / 1000,
				metrics_count: 0,
				average_gpu_utilization: 0,
				average_memory_usage: 0,
				current_ollama_memory: 0,
				total_requests: 0,
				total_tokens_processed: 0,
				average_response_time: 0
			},
			current_metrics: {
				timestamp: currentTime / 1000,
				gpu_utilization: 0,
				gpu_memory_usage: 0,
				ollama_memory_usage: 0,
				inference_speed: 0,
				total_requests: 0,
				total_tokens_processed: 0
			},
			error: error.message
		}, {
			status: 200,
			headers: {
				'Cache-Control': 'no-cache, no-store, must-revalidate',
				'Pragma': 'no-cache',
				'Expires': '0'
			}
		});
	}
}
