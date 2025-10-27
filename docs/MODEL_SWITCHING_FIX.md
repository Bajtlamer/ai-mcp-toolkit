# Model Switching Fix - No Server Restart Needed

## Problem Summary

**Issue**: After switching models via the API endpoint, users had to restart the Python server for the new model to actually be used by Ollama.

**Root Cause**: The `/ollama/models/switch` endpoint only updated the Python config variable (`self.config.ollama_model`) but didn't physically unload the old model or load the new one in Ollama.

## Why the Bash Script Worked

The original `switch-model.sh` bash script worked without server restart because it **physically managed Ollama models**:

```bash
# Step 1: Stop the old model
ollama stop "$old_model"

# Step 2: Start the new model with a warmup prompt
echo "Hello" | ollama run "$target_model"
```

This directly instructed Ollama to:
1. Unload the old model from memory
2. Load and warm up the new model

## What Was Wrong with the API Endpoint

The previous implementation only updated the config:

```python
# OLD (INCOMPLETE) - Only updates Python config
old_model = self.config.ollama_model
self.config.ollama_model = model_name  # ❌ Just changes a variable

# The old model is STILL loaded in Ollama memory!
# The new model is NOT loaded yet!
```

**Result**: 
- Old model stayed in Ollama's memory
- New model wasn't loaded
- Config said one thing, Ollama did another
- Required server restart to force Ollama to load the new model on first request

## The Fix

The updated endpoint now **physically manages Ollama models** just like the bash script:

```python
# NEW (COMPLETE) - Physically manages Ollama models

# Step 1: Unload old model from Ollama (like 'ollama stop')
await session.post(
    f"{ollama_url}/api/generate",
    json={
        "model": old_model,
        "prompt": "",
        "keep_alive": 0  # ⚡ Immediately unload from memory
    }
)

# Step 2: Pre-load and warm up new model (like 'ollama run')
await session.post(
    f"{ollama_url}/api/generate",
    json={
        "model": model_name,
        "prompt": "Hello",  # Warmup prompt
        "keep_alive": "30m"  # ⚡ Keep loaded for 30 minutes
    },
    timeout=aiohttp.ClientTimeout(total=120)  # Allow time for loading
)

# Step 3: Update config only AFTER successful load
self.config.ollama_model = model_name  # ✅ Now config matches reality
```

## How It Works Now

### The `keep_alive` Parameter

Ollama uses the `keep_alive` parameter to manage model lifecycle:

- **`keep_alive: 0`** → Immediately unload model from memory
- **`keep_alive: "30m"`** → Keep model loaded for 30 minutes
- **`keep_alive: "-1"`** → Keep model loaded indefinitely

### The Warmup Request

The warmup request serves multiple purposes:

1. **Forces model loading**: Ollama loads the model into memory
2. **Verifies model works**: We get a 200 response if successful
3. **Warms up the GPU**: First inference initializes GPU context
4. **Tests the model**: Ensures the model can generate text

### Error Handling

If the new model fails to load:
- The config is **NOT updated**
- The old model remains active
- User gets a clear error message
- System stays in a consistent state

## Testing the Fix

### Before the Fix
```bash
# Switch model via API
curl -X POST http://localhost:8000/ollama/models/switch \
  -H "Cookie: session_id=..." \
  -d '{"model": "qwen2.5:14b"}'

# Send chat request
curl -X POST http://localhost:8000/chat/completions \
  -d '{"messages": [{"role": "user", "content": "Hello"}]}'

# ❌ Still uses OLD model! Need to restart server!
```

### After the Fix
```bash
# Switch model via API
curl -X POST http://localhost:8000/ollama/models/switch \
  -H "Cookie: session_id=..." \
  -d '{"model": "qwen2.5:14b"}'

# Response includes:
# "note": "Model physically unloaded and reloaded in Ollama. No server restart needed."

# Send chat request
curl -X POST http://localhost:8000/chat/completions \
  -d '{"messages": [{"role": "user", "content": "Hello"}]}'

# ✅ Uses NEW model immediately! No restart needed!
```

## Benefits

1. **No Server Restart**: Model switching is instant and seamless
2. **Memory Efficient**: Old model is unloaded, freeing GPU memory
3. **Immediate Effect**: New model is ready to use right away
4. **Error Safety**: If loading fails, old model stays active
5. **User Experience**: Matches the behavior users expected from bash script

## Technical Details

### Why This Wasn't Obvious

- The config variable update made it **look** like it was working
- The error only appeared when actually using the chat
- Restarting the server **did** work (Ollama loaded new model on first request)
- The bash script worked fine, so it seemed like an API-specific issue

### The Real Issue

Ollama is a **separate service** from the Python server:
- Python server updates its config → ✅ Works
- But Ollama still has old model loaded → ❌ Problem
- Need to tell Ollama to unload/load → ✅ Fixed

### Why `keep_alive: 0` Works

From Ollama's API documentation:
> The `keep_alive` parameter controls how long the model stays in memory. Setting it to 0 will immediately unload the model.

This is exactly what `ollama stop` does internally!

## Related Files

- **Backend endpoint**: `src/ai_mcp_toolkit/server/http_server.py` (line 686-795)
- **Frontend proxy**: `ui/src/routes/api/models/switch/+server.js`
- **Original bash script**: `switch-model.sh`
- **Documentation**: `docs/SECURITY_FIX_MODEL_SWITCHING.md`

## Future Improvements

Potential enhancements:

1. **Progress feedback**: Show loading progress in UI during model switch
2. **Parallel unload**: Unload old model while loading new one
3. **Model preloading**: Allow admins to pre-load multiple models
4. **Smart warmup**: Use more comprehensive warmup prompts
5. **Health check**: Verify GPU acceleration after model switch

## Questions?

If the model switch still doesn't work:

1. Check Ollama is running: `ollama ps`
2. Check logs: Look for "Unloading old model" and "Successfully loaded" messages
3. Verify model exists: `ollama list`
4. Check GPU memory: Ensure enough VRAM for the new model
5. Test Ollama directly: `echo "Hello" | ollama run <model-name>`

---

**Created**: 2025-10-27  
**Issue**: Model switching required server restart  
**Fix**: Physical model unload/load via Ollama API  
**Result**: Seamless model switching without restart
