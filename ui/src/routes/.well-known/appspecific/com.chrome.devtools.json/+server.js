import { json } from '@sveltejs/kit';

// Chrome DevTools configuration endpoint
// This is requested automatically by Chrome DevTools and is completely optional
export async function GET() {
  return json({
    // Empty configuration - just prevents 404 in logs
    version: 1,
    sessions: []
  });
}
