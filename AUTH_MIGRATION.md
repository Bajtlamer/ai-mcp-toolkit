# Authentication System Migration

**Version:** 0.1.54-beta  
**Date:** 2025-10-27  
**Status:** ✅ Complete

## Overview

The AI MCP Toolkit now uses proper **SvelteKit server-side authentication** following best practices. This migration moved from client-side auth state management to server-side session validation.

## Architecture

### Backend (Python FastAPI)

#### Session Management
- **HTTP-only cookies** for session storage
- **24-hour session expiration**
- Session IDs stored in MongoDB via `SessionManager`
- Secure cookie settings: `httpOnly=True`, `sameSite=lax`

#### Endpoints
- `POST /auth/register` - Create new user account
- `POST /auth/login` - Authenticate and create session
- `POST /auth/logout` - Revoke session and clear cookie
- `GET /auth/me` - Get current user info (requires auth)

#### Models
```python
User:
  - username (unique)
  - email (unique)
  - password (bcrypt hashed)
  - role (USER/ADMIN)
  - full_name (optional)

Session:
  - session_id (unique, indexed)
  - user_id (reference to User)
  - expires_at (24h from creation)
  - ip_address
  - user_agent
```

### Frontend (SvelteKit)

#### 1. Server Hooks (`ui/src/hooks.server.js`)

**Purpose:** Validate session on every request

```javascript
export async function handle({ event, resolve }) {
  // Get session cookie
  const sessionId = event.cookies.get('session_id');
  
  if (sessionId) {
    // Validate session with backend
    const response = await fetch('http://localhost:8000/auth/me', {
      headers: { 'Cookie': `session_id=${sessionId}` }
    });
    
    if (response.ok) {
      event.locals.user = await response.json();
    }
  }
  
  return resolve(event);
}
```

**Key Features:**
- Runs on **every request** (server-side)
- Validates session before page renders
- Stores user in `event.locals.user`
- Handles expired sessions gracefully
- Includes request ID for logging

#### 2. Root Layout Server Load (`ui/src/routes/+layout.server.js`)

**Purpose:** Pass user data to pages and handle redirects

```javascript
export function load({ locals, url }) {
  const publicRoutes = ['/login', '/register'];
  const isPublicRoute = publicRoutes.includes(url.pathname);
  
  // Redirect to login if not authenticated
  if (!locals.user && !isPublicRoute) {
    throw redirect(302, `/login?redirect=${url.pathname}`);
  }
  
  // Redirect to home if already logged in
  if (locals.user && isPublicRoute) {
    throw redirect(302, '/');
  }
  
  return {
    user: locals.user,
    isPublicRoute
  };
}
```

**Key Features:**
- **Server-side redirects** (no client flash)
- Deep linking support (redirect query param)
- Public route handling
- User data injection

#### 3. Root Layout Component (`ui/src/routes/+layout.svelte`)

**Purpose:** Load conversations reactively and render layout

```svelte
<script>
  export let data;
  
  $: user = data.user;
  $: isAuthPage = data.isPublicRoute;
  
  // Reactively load conversations when user changes (client-side only)
  $: if (browser && user && !conversationsLoaded) {
    conversations.loadConversations().then(/* ... */);
  }
</script>

{#if isAuthPage}
  <slot />
{:else}
  <Header {user} />
  <Sidebar />
  <slot />
{/if}
```

**Key Features:**
- Uses server-provided user data
- Reactive conversation loading
- Client-side only (`browser` check)
- No auth store needed

#### 4. Page-Level Protection

Protected routes have `+page.server.js` files:

```javascript
// ui/src/routes/+page.server.js
export function load({ locals }) {
  return {
    user: locals.user
  };
}
```

**Protected Routes:**
- `/` - Dashboard
- `/chat` - AI Chat
- `/settings` - Settings
- `/gpu` - GPU monitoring
- All `/agents/*` routes

#### 5. API Proxy Routes

Frontend proxies auth endpoints to backend:

```
/api/auth/login    -> http://localhost:8000/auth/login
/api/auth/logout   -> http://localhost:8000/auth/logout
/api/auth/register -> http://localhost:8000/auth/register
```

**Why proxy?**
- Handles cookie forwarding between frontend/backend
- Sets cookies on the frontend domain
- Simplifies CORS handling

## Authentication Flow

### Login Flow

```
1. User submits credentials at /login
   ↓
2. POST /api/auth/login (SvelteKit proxy)
   ↓
3. POST /auth/login (Python backend)
   ↓
4. Backend validates credentials
   ↓
5. Backend creates session in MongoDB
   ↓
6. Backend returns user + sets session_id cookie
   ↓
7. SvelteKit proxy forwards cookie to browser
   ↓
8. Browser redirects to home page
   ↓
9. hooks.server.js validates session
   ↓
10. User data available in all pages
```

### Logout Flow

```
1. User clicks logout button
   ↓
2. POST /api/auth/logout
   ↓
3. Backend deletes session from MongoDB
   ↓
4. Backend clears session_id cookie
   ↓
5. Frontend clears conversations store
   ↓
6. Redirect to /login
```

### Registration Flow

```
1. User submits registration form
   ↓
2. POST /api/auth/register
   ↓
3. Backend creates user in MongoDB
   ↓
4. Auto-login: POST /api/auth/login
   ↓
5. Session created + cookie set
   ↓
6. Redirect to home page
```

## Key Benefits

### ✅ Security
- No auth state in browser localStorage
- HTTP-only cookies prevent XSS attacks
- Server-side session validation on every request
- Secure session storage in MongoDB

### ✅ User Experience
- No client-side auth flicker/loading states
- Deep linking works (redirect after login)
- Fast page loads (auth determined server-side)
- Seamless navigation

### ✅ Developer Experience
- Follows SvelteKit best practices
- Simple mental model (server validates, client displays)
- Easy to test and debug
- Clear separation of concerns

## Troubleshooting

### Issue: 401 Errors in Console

**Cause:** Old error from previous login attempt  
**Solution:** Clear browser console (Cmd+K / Ctrl+L)

### Issue: Session Not Persisting

**Check:**
1. Backend is setting cookie correctly: Look for `Set-Cookie` header in network tab
2. Cookie is being sent: Check request headers for `Cookie: session_id=...`
3. Session exists in MongoDB: Query `sessions` collection

### Issue: Redirects Not Working

**Check:**
1. `+layout.server.js` is handling redirects
2. Routes are correctly marked as public/protected
3. No client-side redirects overriding server redirects

### Issue: Conversations Not Loading

**Check:**
1. `browser` check in reactive statement
2. User is authenticated (`data.user` exists)
3. Backend `/conversations` endpoint accessible
4. No CORS issues (check console)

## Migration Checklist

- [x] Create `hooks.server.js` with session validation
- [x] Create `+layout.server.js` with server-side redirects
- [x] Update `+layout.svelte` to use server data
- [x] Update Header component to receive user as prop
- [x] Create registration page with auto-login
- [x] Remove client-side auth store
- [x] Update all components to use server-provided user
- [x] Add page-level protection with `+page.server.js`
- [x] Test login/logout/register flows
- [x] Fix SSR fetch warnings (add `browser` checks)

## Files Changed

### Created
- `ui/src/hooks.server.js` - Server-side session validation
- `ui/src/routes/+layout.server.js` - Root layout server load
- `ui/src/routes/+page.server.js` - Home page server load
- `ui/src/routes/settings/+page.server.js` - Settings page server load
- `ui/src/routes/gpu/+page.server.js` - GPU page server load
- `ui/src/routes/register/+page.svelte` - Registration page

### Modified
- `ui/src/routes/+layout.svelte` - Use server data, reactive conversations
- `ui/src/routes/login/+page.svelte` - Direct API calls, no auth store
- `ui/src/lib/components/Header.svelte` - Receive user prop, clear conversations
- `ui/src/lib/components/ModelSwitcher.svelte` - Receive user prop
- `ui/src/routes/settings/+page.svelte` - Use server data
- `ui/src/routes/gpu/+page.svelte` - Use server data

### Deleted
- `ui/src/lib/stores/auth.js` - No longer needed
- `ui/src/lib/services/auth.js` - No longer needed

## Next Steps

Potential enhancements:

1. **Session refresh** - Extend session before 24h expiration
2. **Remember me** - Longer session duration option
3. **Multi-factor auth** - Add 2FA support
4. **Password reset** - Email-based password recovery
5. **Social login** - OAuth integration (Google, GitHub, etc.)
6. **Admin panel** - User management interface

## References

- [SvelteKit Hooks Documentation](https://kit.svelte.dev/docs/hooks)
- [SvelteKit Server Load Functions](https://kit.svelte.dev/docs/load#server)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [HTTP-only Cookies](https://owasp.org/www-community/HttpOnly)

---

**Last Updated:** 2025-10-27  
**Maintained by:** AI MCP Toolkit Team
