# Architecture Rules

## Frontend-Backend Separation Principles

### Core Rule: Frontend Always Uses Backend API

**The SvelteKit frontend MUST ALWAYS use the backend Python API for ALL data operations.**

### What This Means

1. **No Direct Database Access**: The frontend (SvelteKit) NEVER directly connects to MongoDB, Redis, or any other database.

2. **Backend API is the Single Source of Truth**: All business logic, data validation, authentication, and database operations happen in the backend Python server.

3. **SvelteKit API Routes are Pure Proxies**: The SvelteKit API routes (`/api/*`) only exist to:
   - Forward browser requests to the backend
   - Pass session cookies from browser to backend
   - Return backend responses to browser
   - Handle CORS if needed

4. **No MCP Protocol in Frontend**: The frontend does NOT implement MCP protocol directly. It only calls HTTP/REST endpoints exposed by the backend.

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Browser (Client)                         │
│                     Svelte Components (.svelte)                  │
└────────────────────────────────┬────────────────────────────────┘
                                 │ HTTP/REST
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                  SvelteKit Frontend (port 5173)                  │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │         SvelteKit API Routes (/api/*)                    │   │
│  │         - Pure HTTP proxies                              │   │
│  │         - Forward requests to backend                    │   │
│  │         - Pass session cookies                           │   │
│  │         - NO business logic                              │   │
│  │         - NO database access                             │   │
│  └─────────────────────────────────────────────────────────┘   │
└────────────────────────────────┬────────────────────────────────┘
                                 │ HTTP/REST
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Backend Python API (port 8000)                   │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │         FastAPI HTTP Server                              │   │
│  │         - Authentication & Authorization                 │   │
│  │         - Business Logic                                 │   │
│  │         - MCP Protocol Implementation                    │   │
│  │         - Data Validation                                │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                 │                                │
│                                 ▼                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │         Database Layer                                   │   │
│  │         - MongoDB (persistent storage)                   │   │
│  │         - Redis (caching)                                │   │
│  │         - Beanie ODM                                     │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Frontend Configuration

The frontend ONLY needs to know where the backend is:

```bash
# ui/ only needs these environment variables:
MCP_HOST=localhost
MCP_PORT=8000
```

**The frontend does NOT need:**
- ❌ MONGODB_URL
- ❌ MONGODB_DATABASE
- ❌ REDIS_URL
- ❌ OLLAMA_HOST (backend handles this)
- ❌ Any other backend configuration

### Backend Configuration

The backend handles ALL service configuration:

```bash
# Backend needs:
✅ MCP_HOST=localhost
✅ MCP_PORT=8000
✅ MONGODB_URL=mongodb://localhost:27017
✅ MONGODB_DATABASE=ai_mcp_toolkit
✅ REDIS_URL=redis://localhost:6379
✅ OLLAMA_HOST=localhost
✅ OLLAMA_PORT=11434
✅ All other service configurations
```

### Example: How a Chat Request Flows

```javascript
// ❌ WRONG - Frontend calling services directly
// browser → SvelteKit → MongoDB/Ollama directly

// ✅ CORRECT - Frontend always uses backend API
// browser → SvelteKit proxy → Backend API → MongoDB/Ollama

// 1. Browser sends request to SvelteKit
fetch('/api/chat', {
  method: 'POST',
  body: JSON.stringify({ message: 'Hello' })
});

// 2. SvelteKit proxy forwards to backend
// File: ui/src/routes/api/chat/+server.js
export async function POST({ request, cookies }) {
  const sessionId = cookies.get('session_id');
  
  // Just forward to backend API
  const response = await fetch(`${BACKEND_URL}/chat/completions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Cookie': `session_id=${sessionId}`
    },
    body: JSON.stringify(await request.json())
  });
  
  return json(await response.json());
}

// 3. Backend handles everything
// File: src/ai_mcp_toolkit/server/http_server.py
@app.post("/chat/completions")
async def chat_completions(request, user = Depends(require_auth)):
  # Backend does:
  # - Authentication
  # - Call Ollama
  # - Save to MongoDB
  # - Return response
```

### Why This Architecture?

**Benefits:**

1. **Security**: Single point of authentication and authorization
2. **Maintainability**: Business logic in one place
3. **Scalability**: Backend can be scaled independently
4. **Database Schema Changes**: Only backend needs updates
5. **Testing**: Easier to test backend API independently
6. **Deployment**: Frontend and backend can be deployed separately

**Anti-patterns to Avoid:**

❌ **Frontend connecting to MongoDB directly**
```javascript
// NEVER DO THIS in SvelteKit
import { MongoClient } from 'mongodb';
const client = new MongoClient(MONGODB_URL);
```

❌ **Frontend implementing business logic**
```javascript
// NEVER DO THIS in SvelteKit
function validateConversation(conv) {
  // Business logic belongs in backend
}
```

❌ **Frontend calling Ollama directly**
```javascript
// NEVER DO THIS in SvelteKit
fetch('http://localhost:11434/api/generate', {...});
```

### Implementation Guidelines

#### SvelteKit API Route Template

All SvelteKit API routes should follow this pattern:

```javascript
// ui/src/routes/api/[endpoint]/+server.js
import { json } from '@sveltejs/kit';

const BACKEND_HOST = process.env.MCP_HOST || 'localhost';
const BACKEND_PORT = process.env.MCP_PORT || '8000';
const BACKEND_URL = `http://${BACKEND_HOST}:${BACKEND_PORT}`;

export async function POST({ request, cookies }) {
  try {
    // 1. Get session cookie
    const sessionId = cookies.get('session_id');
    
    // 2. Forward to backend with cookie
    const response = await fetch(`${BACKEND_URL}/backend/endpoint`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Cookie': `session_id=${sessionId}`
      },
      body: JSON.stringify(await request.json())
    });
    
    // 3. Return backend response
    if (!response.ok) {
      return json({ error: 'Backend error' }, { status: response.status });
    }
    
    return json(await response.json());
  } catch (error) {
    return json({ error: error.message }, { status: 500 });
  }
}
```

#### What Belongs Where

**Frontend (SvelteKit):**
- ✅ UI components
- ✅ Client-side state management
- ✅ Form validation (basic, for UX)
- ✅ API proxy routes
- ✅ Routing and navigation

**Backend (Python/FastAPI):**
- ✅ Authentication & authorization
- ✅ Business logic
- ✅ Data validation (authoritative)
- ✅ Database operations
- ✅ External service integration (Ollama, etc.)
- ✅ MCP protocol implementation
- ✅ File operations
- ✅ Background jobs

### Configuration Management

**Single .env file at project root:**
```
/Users/roza/Sites/ai-mcp-toolkit/.env
```

**SvelteKit reads from project root .env:**
- Only uses `MCP_HOST` and `MCP_PORT`
- These are read via `process.env` in SvelteKit server routes

**Backend reads from project root .env:**
- Uses all configuration variables
- Managed by `src/ai_mcp_toolkit/utils/config.py`

### Testing This Architecture

**Frontend tests should:**
- Test that API proxies forward requests correctly
- Test that session cookies are passed
- NOT test business logic (that's backend's job)

**Backend tests should:**
- Test all business logic
- Test database operations
- Test authentication
- Test API endpoints

### Migration Checklist

When adding new features:

- [ ] Is this a data operation? → Backend API endpoint
- [ ] Is this authentication-related? → Backend only
- [ ] Is this calling external services? → Backend only
- [ ] Is this UI-only state management? → Frontend only
- [ ] Does frontend need new data? → Create backend API endpoint first

### Exceptions

There are NO exceptions to this rule. Even for:
- ❌ "Just reading data" → Use backend API
- ❌ "It's just a simple query" → Use backend API
- ❌ "For better performance" → Backend can implement caching
- ❌ "Because it's faster to implement" → Maintain proper architecture

### Questions?

**Q: Can the frontend cache data?**
A: Yes, client-side caching (in memory, Svelte stores) is fine for UI performance. But fetching data must always go through backend API.

**Q: What about real-time updates?**
A: Use WebSockets or SSE through the backend. Backend pushes updates, frontend displays them.

**Q: Can we use SvelteKit's server-side rendering with databases?**
A: Only if SvelteKit acts as a pure proxy to backend API. Never direct database access.

**Q: What if the backend is slow?**
A: Optimize the backend, add caching (Redis), or implement streaming. Don't bypass the architecture.

---

**This is a foundational architecture rule. Any code review should verify this separation is maintained.**

**Last Updated:** 2025-10-27
**Status:** ACTIVE - Must be followed for all new code
