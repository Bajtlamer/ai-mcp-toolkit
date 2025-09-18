import { json } from '@sveltejs/kit';

const API_BASE = 'http://localhost:8000';

/** @type {import('./$types').RequestHandler} */
export async function GET() {
	try {
		// Forward request to the Python backend GPU recommendations endpoint
		const response = await fetch(`${API_BASE}/gpu/recommendations`, {
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
		console.error('GPU recommendations API error:', error);
		
		// Return simulated recommendations for development
		const recommendations = [
			'✅ Ollama is successfully using GPU acceleration',
			'🔥 GPU utilization is excellent - maximum performance achieved',
			'📊 Moderate GPU memory available - suitable for 3B models',
			'❄️ GPU temperature is optimal for sustained workloads',
			'⚡ Consider batch processing for improved efficiency'
		];
		
		// Randomly select 3-5 recommendations
		const selectedRecs = recommendations
			.sort(() => 0.5 - Math.random())
			.slice(0, Math.floor(Math.random() * 3) + 3);
		
		return json({
			recommendations: selectedRecs,
			timestamp: Date.now() / 1000,
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