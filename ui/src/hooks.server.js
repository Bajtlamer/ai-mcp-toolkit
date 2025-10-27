/**
 * SvelteKit server hooks
 * Handles authentication via session cookies on every request
 */

import { randomBytes } from 'crypto';

const BACKEND_API = 'http://localhost:8000';

/** @type {import('@sveltejs/kit').Handle} */
export async function handle({ event, resolve }) {
	// Generate request ID for logging/debugging
	const requestId = randomBytes(5).toString('hex');
	event.locals.requestId = requestId;
	
	// Get session_id cookie
	const sessionId = event.cookies.get('session_id');
	
	// Try to get user from session
	if (sessionId) {
		try {
			const response = await fetch(`${BACKEND_API}/auth/me`, {
				headers: {
					'Cookie': `session_id=${sessionId}`,
					'X-Request-ID': requestId
				},
				signal: AbortSignal.timeout(5000) // 5s timeout
			});
			
			if (response.ok) {
				const user = await response.json();
				// Store user in event.locals for access in load functions
				event.locals.user = user;
			} else if (response.status === 401) {
				// Session expired or invalid - clear cookie silently
				event.cookies.delete('session_id', { path: '/' });
				event.locals.user = null;
			} else {
				// Server error - log but don't clear cookie (might be temporary)
				console.error(`[${requestId}] Auth check failed with status ${response.status}`);
				event.locals.user = null;
			}
		} catch (error) {
			// Network error or timeout - log and continue
			if (error.name === 'TimeoutError') {
				console.error(`[${requestId}] Auth check timeout`);
			} else {
				console.error(`[${requestId}] Auth check error:`, error.message);
			}
			event.locals.user = null;
		}
	} else {
		event.locals.user = null;
	}
	
	return resolve(event);
}
