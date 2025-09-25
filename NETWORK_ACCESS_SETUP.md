# Network Access Setup - AI MCP Toolkit

## 🎯 Problem Solved

This configuration allows your AI MCP Toolkit to work correctly when accessed by other machines on your local network via IP address (e.g., `http://192.168.1.100:5173`).

**Previous Issue**: The chat functionality was making direct calls from the browser to `localhost:11434` (Ollama), which failed when users accessed the application from other machines because `localhost` referred to their local machine, not the server.

**Solution**: All AI/Ollama API calls now go through the server backend, ensuring they work regardless of how users access the application.

## 🔧 Architecture Changes Made

### **Before (Client-side Ollama calls)**
```
User Browser → localhost:11434 (Ollama) ❌ FAILS on remote access
```

### **After (Server-side proxy)**
```
User Browser → Server IP:5173 (UI) → Server IP:8000 (Backend) → localhost:11434 (Ollama) ✅ WORKS
```

## 📁 Files Modified/Added

### **New API Endpoints Created**
- `ui/src/routes/api/chat/+server.js` - Simple chat proxy
- `ui/src/routes/api/chat/conversation/+server.js` - Conversation-aware chat proxy  
- `ui/src/routes/api/tools/execute/+server.js` - Tools execution proxy

### **Frontend Updated**
- `ui/src/lib/services/chat-api.js` - Removed all direct `localhost:11434` calls
- All API calls now use relative URLs that work with any server IP

### **Configuration Added**
- `.env.server` - Example configuration for network deployment

## 🚀 Setup Instructions

### Step 1: Use Network Configuration
```bash
# Copy the server configuration
cp .env.server .env

# Or manually edit your .env file with these key settings:
MCP_HOST=0.0.0.0     # Allow connections from other machines
UI_HOST=0.0.0.0      # Allow UI access from other machines
OLLAMA_HOST=localhost # Keep Ollama on server (not changed)
CORS_ORIGINS=*        # Allow cross-origin requests
```

### Step 2: Start the Services
```bash
# Start backend MCP server
ai-mcp-toolkit serve --host 0.0.0.0 --port 8000

# Start UI (in another terminal)
ai-mcp-toolkit ui --host 0.0.0.0 --port 5173

# Make sure Ollama is running on the server
ollama serve
```

### Step 3: Test Network Access

#### From the server machine:
- http://localhost:5173 (should work)
- http://YOUR_SERVER_IP:5173 (should work)

#### From other machines on the network:
- http://YOUR_SERVER_IP:5173 (should work)
- Chat functionality should work properly ✅

## 🔍 How It Works

### **1. API Proxy Pattern**
```javascript
// Frontend makes relative API calls
fetch('/api/chat/conversation', { ... })

// Svelte server proxies to backend
fetch('http://localhost:8000/chat/completions', { ... })

// Backend calls Ollama locally  
fetch('http://localhost:11434/api/generate', { ... })
```

### **2. Environment Variable Configuration**
```bash
# Backend server (serves API endpoints)
MCP_HOST=0.0.0.0       # Accept connections from any IP
MCP_PORT=8000

# UI server (serves frontend)
UI_HOST=0.0.0.0        # Accept connections from any IP  
UI_PORT=5173

# Ollama (AI model server)
OLLAMA_HOST=localhost   # Only server needs to access this
OLLAMA_PORT=11434
```

### **3. Request Flow**
1. **User on remote machine** opens `http://192.168.1.100:5173`
2. **Browser loads** the UI from the server
3. **User types message** in chat
4. **Frontend calls** `/api/chat/conversation` (relative URL)
5. **Svelte API proxy** receives request on server
6. **Proxy forwards** request to `http://localhost:8000/chat/completions`
7. **Backend MCP server** processes request
8. **Backend calls** `http://localhost:11434/api/generate` (Ollama)
9. **Response flows back** through the same path

## ✅ Benefits

1. **Works with any IP address** - no hardcoded localhost URLs
2. **Network accessible** - other machines can use the chat
3. **Secure** - Ollama remains internal to the server
4. **Maintains performance** - all the GPU optimization features still work
5. **Future-proof** - works in Docker, cloud deployments, etc.

## 🔧 Testing Commands

```bash
# Test from server machine
curl http://localhost:8000/health
curl http://localhost:5173/api/gpu/health

# Test from remote machine (replace with your server IP)
curl http://192.168.1.100:8000/health
curl http://192.168.1.100:5173/api/gpu/health

# Test chat functionality
curl -X POST http://192.168.1.100:5173/api/chat/conversation \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, can you hear me?", "model": "qwen2.5:14b"}'
```

## 🎯 Network Deployment Checklist

- [ ] Copy `.env.server` to `.env` (or configure manually)
- [ ] Set `MCP_HOST=0.0.0.0` and `UI_HOST=0.0.0.0` 
- [ ] Keep `OLLAMA_HOST=localhost`
- [ ] Start backend server with `--host 0.0.0.0`
- [ ] Start UI server with `--host 0.0.0.0`
- [ ] Ensure Ollama is running on the server
- [ ] Test access from remote machine
- [ ] Verify chat functionality works from remote machine

## 🚨 Security Notes

For production deployment:

1. **Replace `CORS_ORIGINS=*`** with specific allowed domains
2. **Use proper firewall rules** to restrict access
3. **Consider HTTPS** for encrypted communication
4. **Use authentication** if needed for user access

Your AI MCP Toolkit is now ready for network deployment! 🎉