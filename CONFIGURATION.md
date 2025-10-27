# Configuration Guide

## Single Configuration File

AI MCP Toolkit uses **ONE configuration file**: `.env`

```
/Users/roza/Sites/ai-mcp-toolkit/.env
```

## Setup

1. **Copy the example file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` with your settings:**
   ```bash
   nano .env  # or use your preferred editor
   ```

3. **Required settings to update:**
   - `MONGODB_URL` - Your MongoDB connection string
   - `MONGODB_DATABASE` - Your database name
   - `OLLAMA_MODEL` - Your preferred AI model

## Who Uses This File?

### Python Backend (Port 8000)
**Uses ALL settings:**
- Server configuration (MCP_HOST, MCP_PORT)
- MongoDB settings (MONGODB_URL, MONGODB_DATABASE)
- Redis settings (REDIS_URL)
- Ollama settings (OLLAMA_HOST, OLLAMA_MODEL)
- All other configuration

**File location:** `src/ai_mcp_toolkit/utils/config.py` loads `.env` via `load_dotenv()`

### SvelteKit Frontend (Port 5173)
**Uses ONLY these settings:**
- `MCP_HOST` - Where to find backend API
- `MCP_PORT` - Backend API port

**Frontend does NOT need:**
- ❌ MongoDB settings (backend handles this)
- ❌ Redis settings (backend handles this)
- ❌ Ollama settings (backend handles this)

The frontend reads `MCP_HOST` and `MCP_PORT` from the project root `.env` file via `process.env` in SvelteKit server routes.

## Configuration Structure

```
┌─────────────────────────────────────────────┐
│         .env (Project Root)                 │
│  - ALL backend configuration                │
│  - Frontend only reads MCP_HOST/PORT        │
└─────────────────────────────────────────────┘
                    │
        ┌───────────┴──────────┐
        │                      │
        ▼                      ▼
┌──────────────────┐  ┌──────────────────┐
│  Backend Server  │  │  SvelteKit UI    │
│  (Python)        │  │  (Frontend)      │
│  Port 8000       │  │  Port 5173       │
│                  │  │                  │
│  Reads:          │  │  Reads:          │
│  ✅ MongoDB      │  │  ✅ MCP_HOST     │
│  ✅ Redis        │  │  ✅ MCP_PORT     │
│  ✅ Ollama       │  │  (to forward     │
│  ✅ All config   │  │   to backend)    │
└──────────────────┘  └──────────────────┘
```

## Minimum Required Settings

### For Backend to Start

```bash
# Required
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=ai_mcp_toolkit

# Highly recommended
OLLAMA_HOST=localhost
OLLAMA_PORT=11434
OLLAMA_MODEL=llama3.2:3b

# Optional but recommended
REDIS_URL=redis://localhost:6379
REDIS_DB=0
```

### For Frontend to Work

```bash
# Required (to find backend)
MCP_HOST=localhost
MCP_PORT=8000
```

## Common Configurations

### Local Development (Default)
```bash
MCP_HOST=localhost
MCP_PORT=8000
MONGODB_URL=mongodb://localhost:27017
REDIS_URL=redis://localhost:6379
OLLAMA_HOST=localhost
```

### Network Access (Access from other machines)
```bash
MCP_HOST=0.0.0.0  # Allow external connections
MCP_PORT=8000
UI_HOST=0.0.0.0    # Allow external connections
MONGODB_URL=mongodb://localhost:27017  # Keep MongoDB local
OLLAMA_HOST=localhost  # Keep Ollama local
```

### Production (MongoDB Atlas)
```bash
MCP_HOST=0.0.0.0
MCP_PORT=8000
MONGODB_URL=mongodb+srv://<user>:<pass>@<cluster>.mongodb.net/?retryWrites=true&w=majority
MONGODB_DATABASE=ai_mcp_toolkit
REDIS_URL=redis://your-redis-cloud-url:6379
```

## Security Notes

1. **Never commit `.env` to git** - It contains secrets
2. **Use `.env.example` as template** - Commit this with placeholder values
3. **MongoDB credentials** - Keep in `.env`, never share
4. **Frontend security** - Session cookies are HTTP-only, never exposed to JavaScript

## Troubleshooting

### Backend can't find configuration
**Problem:** Backend starts but shows wrong settings
**Solution:** Make sure `.env` is in project root: `/Users/roza/Sites/ai-mcp-toolkit/.env`

### Frontend can't connect to backend
**Problem:** Frontend shows "Failed to connect to backend"
**Solution:** Check `MCP_HOST` and `MCP_PORT` in `.env` match where backend is running

### Database connection fails
**Problem:** "ServerSelectionTimeoutError"
**Solution:** 
1. Check `MONGODB_URL` is correct in `.env`
2. Verify MongoDB is running: `brew services list` or `mongosh`
3. For Atlas: Check network access allows your IP

## File Overview

| File | Purpose | Committed to Git? |
|------|---------|-------------------|
| `.env` | Your actual configuration with secrets | ❌ NO (gitignored) |
| `.env.example` | Template with placeholders | ✅ YES |

**That's it!** Only two files, simple and clear.

## Environment Variable Priority

If a variable is set multiple ways, this is the priority:

1. **Actual environment variables** (highest priority)
   ```bash
   export MONGODB_URL="..."
   python main.py
   ```

2. **`.env` file** (most common)
   ```bash
   # Reads from .env in current directory
   python main.py
   ```

3. **Default values in code** (lowest priority)
   ```python
   # config.py has fallback defaults
   port = int(os.getenv("MCP_PORT", "8000"))  # defaults to 8000
   ```

## Quick Reference

**Backend startup:**
```bash
# Backend reads .env automatically
python main.py
```

**Frontend startup:**
```bash
# Frontend reads MCP_HOST/PORT from root .env
cd ui && npm run dev
```

Both processes read from the same `.env` file at project root, but use different variables from it.
