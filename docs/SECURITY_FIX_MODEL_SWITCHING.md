# Security Fix: Admin-Only Model Switching

## Issue Summary

Two security issues were identified related to AI model switching:

1. **Frontend UI visibility**: Model switching interface was visible to all authenticated users, not just admins
2. **Unauthenticated API endpoint**: The SvelteKit `/api/models/switch` endpoint had no authentication

## Fixes Applied

### 1. Frontend UI - Admin-Only Access

**File**: `ui/src/routes/settings/+page.svelte`

The Model Management section is now wrapped with an admin-only check:

```svelte
{#if $auth.user && $auth.user.role === 'admin'}
  <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-6">
    <!-- Model Management UI -->
    <ModelSwitcher />
  </div>
{/if}
```

**Result**: Non-admin users no longer see the model switching interface in Settings.

### 2. ModelSwitcher Component - Role-Based Display

**File**: `ui/src/lib/components/ModelSwitcher.svelte`

The component now shows different content based on user role:

- **Admin users**: See the full model switching interface
- **Non-admin users**: See a clear notice that model switching is admin-only

```svelte
{#if $auth.user && $auth.user.role !== 'admin'}
  <!-- Admin-only notice -->
  <div class="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-xl p-4">
    <div class="flex items-start space-x-3">
      <ShieldAlert size={20} class="text-yellow-600 dark:text-yellow-400 mt-0.5" />
      <div>
        <h3 class="text-sm font-semibold text-yellow-900 dark:text-yellow-100 mb-1">Admin Only Feature</h3>
        <p class="text-sm text-yellow-700 dark:text-yellow-300">
          Model switching is restricted to administrators only. Contact an admin to change the AI model.
        </p>
      </div>
    </div>
  </div>
{:else}
  <!-- Model switching interface for admins -->
{/if}
```

### 3. Deprecated SvelteKit Endpoint

**File**: `ui/src/routes/api/models/switch/+server.js`

The old unauthenticated endpoint has been disabled:

```javascript
export async function POST({ request }) {
  return json({ 
    success: false, 
    error: 'Model switching is now handled by the backend API and requires admin privileges'
  }, { status: 403 });
}

export async function GET() {
  return json({ 
    success: false, 
    error: 'Model information is now handled by the backend API'
  }, { status: 403 });
}
```

**Result**: Any attempts to use the old endpoint will fail with a 403 Forbidden error.

## Backend Security (Already in Place)

The backend API (`/chat/completions`) already has proper security:

**File**: `src/ai_mcp_toolkit/server/http_server.py`

```python
# Chat completions endpoint (requires auth, model selection admin-only)
@app.post("/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(
    request: ChatCompletionRequest,
    user: User = Depends(require_auth),
    req: Request = None
):
    """Handle chat completion requests via Ollama."""
    # Only admins can override the model
    if request.model and request.model != self.config.ollama_model:
        if user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=403,
                detail="Only administrators can change the model"
            )
```

**Security features**:
- ✅ Requires valid session authentication (`require_auth`)
- ✅ Checks user role before allowing model override
- ✅ Returns 403 Forbidden for non-admin users attempting model change
- ✅ Audit logs all actions with user_id

## Model Switching Implementation

The `/ollama/models/switch` endpoint now **physically unloads and reloads models** (no server restart needed):

**How it works**:
1. **Step 1**: Unload old model using `keep_alive: 0` (like `ollama stop`)
2. **Step 2**: Pre-load new model with warmup prompt (like `ollama run`)
3. **Step 3**: Update config only after successful load

**Why this fixes the restart issue**:
- Previously: Only updated Python config variable, old model stayed in Ollama memory
- Now: Physically manages Ollama model lifecycle, just like the bash script did

## How Model Selection Works Now

### For Admin Users

1. **Settings Page**: Admin sees "AI Model Management" section
2. **Model List**: Can view all available models via Ollama
3. **Switch Model**: Can switch to any installed model (future enhancement)
4. **Chat Requests**: Can override model in chat completion requests

### For Regular Users

1. **Settings Page**: Model Management section is hidden
2. **ModelSwitcher**: Shows admin-only notice if accessed elsewhere
3. **Chat Requests**: Can only use the default configured model
4. **Override Attempt**: Returns 403 Forbidden with clear error message

## Testing the Fix

### Test as Regular User

1. Log in as `testuser` (password: `test123`)
2. Go to Settings page
3. **Expected**: No "AI Model Management" section visible
4. Try to send chat request with different model via API:
   ```bash
   curl -X POST http://localhost:8000/chat/completions \
     -H "Content-Type: application/json" \
     -H "Cookie: session_id=YOUR_SESSION_ID" \
     -d '{
       "messages": [{"role": "user", "content": "Hello"}],
       "model": "qwen2.5:14b"
     }'
   ```
5. **Expected**: 403 Forbidden with message "Only administrators can change the model"

### Test as Admin User

1. Log in as `admin` (password: `admin123`)
2. Go to Settings page
3. **Expected**: "AI Model Management" section visible with model list
4. Can view current model and available models
5. Chat requests with different models are allowed

## Security Best Practices Applied

1. ✅ **Defense in Depth**: Multiple layers of security (UI, component, backend API)
2. ✅ **Principle of Least Privilege**: Regular users have minimal permissions
3. ✅ **Authentication Required**: All endpoints require valid session
4. ✅ **Authorization Checks**: Role-based access control enforced
5. ✅ **Audit Logging**: All operations logged with user context
6. ✅ **Clear Error Messages**: Users understand why access is denied
7. ✅ **Fail Secure**: Default behavior is to deny access

## Future Enhancements

Potential improvements for model management:

1. **Model Preloading**: Allow admins to pre-load specific models
2. **Per-User Model Assignment**: Admins can assign specific models to users
3. **Model Usage Quotas**: Track and limit model usage per user
4. **Model Performance Metrics**: Show model performance in admin dashboard
5. **Automatic Model Selection**: AI chooses best model based on query

## Related Documentation

- [PER_USER_STORAGE_MIGRATION.md](./PER_USER_STORAGE_MIGRATION.md) - Per-user conversation storage
- [AUTHENTICATION.md](./AUTHENTICATION.md) - Authentication system overview (if exists)
- Backend API docs: http://localhost:8000/docs

## Questions?

If you have questions about these security fixes or need to modify model access permissions, please refer to the backend `http_server.py` file or contact the development team.
