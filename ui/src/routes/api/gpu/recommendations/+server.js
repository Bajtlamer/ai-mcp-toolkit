import { json } from '@sveltejs/kit';

/** @type {import('./$types').RequestHandler} */
export async function GET() {
	// Return empty recommendations since we now use charts instead
	return json({
		recommendations: [],
		timestamp: Date.now() / 1000,
		note: 'Recommendations replaced with performance charts'
	}, {
		headers: {
			'Cache-Control': 'no-cache, no-store, must-revalidate',
			'Pragma': 'no-cache',
			'Expires': '0'
		}
	});
}
