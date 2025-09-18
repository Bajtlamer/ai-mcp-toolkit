import { json } from '@sveltejs/kit';

const API_BASE = 'http://localhost:8000';

/** @type {import('./$types').RequestHandler} */
export async function GET() {
	try {
		// Forward request to the Python backend GPU metrics endpoint
		const response = await fetch(`${API_BASE}/gpu/metrics`, {
			method: 'GET',
			headers: {
				'Content-Type': 'application/json',
			},
		});

		if (!response.ok) {
			throw new Error(`Backend API error: ${response.status}`);
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
		
		// Return simulated data for development
		const currentTime = Date.now();
		return json({
			performance_summary: {
				current_timestamp: currentTime / 1000,
				metrics_count: Math.round(Math.random() * 1000 + 100),
				average_gpu_utilization: Math.round(Math.random() * 50 + 50),
				average_memory_usage: Math.round(Math.random() * 40 + 60),
				current_ollama_memory: 5416,
				total_requests: Math.round(Math.random() * 500 + 100),
				total_tokens_processed: Math.round(Math.random() * 50000 + 10000),
				average_response_time: Math.random() * 2 + 0.5
			},
			current_metrics: {
				timestamp: currentTime / 1000,
				gpu_utilization: Math.round(Math.random() * 100),
				gpu_memory_usage: Math.round(Math.random() * 40 + 60),
				ollama_memory_usage: 5416,
				inference_speed: Math.round(Math.random() * 100 + 50),
				total_requests: Math.round(Math.random() * 500 + 100),
				total_tokens_processed: Math.round(Math.random() * 50000 + 10000)
			},
			_note: 'Simulated data - backend not available'
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