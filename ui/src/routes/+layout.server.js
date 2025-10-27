/**
 * Root layout server load
 * Passes user data from event.locals to all pages
 */

import { redirect } from '@sveltejs/kit';

/** @type {import('./$types').LayoutServerLoad} */
export function load({ locals, url }) {
	// Public routes that don't require authentication
	const publicRoutes = ['/login', '/register'];
	const isPublicRoute = publicRoutes.includes(url.pathname);
	
	// Redirect to login if not authenticated and trying to access protected route
	if (!locals.user && !isPublicRoute) {
		throw redirect(302, `/login?redirect=${encodeURIComponent(url.pathname)}`);
	}
	
	// Redirect to home if authenticated user tries to access login/register
	if (locals.user && isPublicRoute) {
		throw redirect(302, '/');
	}
	
	return {
		user: locals.user || null,
		isPublicRoute
	};
}
