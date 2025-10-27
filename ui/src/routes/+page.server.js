/**
 * Home page server load
 * Ensures user is authenticated
 */

import { redirect } from '@sveltejs/kit';

/** @type {import('./$types').PageServerLoad} */
export function load({ locals }) {
	// Auth is already handled in root layout, just pass through user
	return {
		user: locals.user
	};
}
