import { json } from '@sveltejs/kit';

const API_BASE = 'http://localhost:8000';

/** @type {import('./$types').RequestHandler} */
export async function GET() {
	try {
		// Forward request to the Python backend GPU health endpoint
		const response = await fetch(`${API_BASE}/gpu/health`, {
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
		console.error('GPU health API error:', error);
		
		// Return simulated data for development
		return json({
			gpu_available: true,
			gpu_name: 'NVIDIA GeForce RTX 3070 Ti',
			gpu_utilization: Math.round(Math.random() * 100),
			gpu_memory_usage: '5400/8192 MB',
			gpu_temperature: Math.round(Math.random() * 30 + 40),
			ollama_gpu_accelerated: true,
			ollama_model: 'llama3.1:8b',
			ollama_memory_usage: '5416 MB',
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