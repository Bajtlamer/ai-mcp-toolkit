/**
 * GPU page server load
 * Ensures user is authenticated
 */

/** @type {import('./$types').PageServerLoad} */
export function load({ locals }) {
	// Auth is already handled in root layout, just pass through user
	return {
		user: locals.user
	};
}
