# User Data Migration Plan - Move to Per-User MongoDB Storage

## 🎯 Objective
**ALL user data must be stored in MongoDB per user, NOT in localStorage or any client-side storage.**

---

## 📋 Current Issues

### ❌ What's Currently Wrong:

1. **Chat Conversations** - Stored in localStorage (`ai-chat-conversations`)
   - File: `ui/src/lib/stores/conversations.js`
   - Problem: All users share the same browser storage

2. **UI Configuration** - Stored in localStorage (`ai-mcp-ui-config`)
   - File: `ui/src/lib/components/Header.svelte` and others
   - Problem: Settings not per-user, lost on logout

3. **Agent History** - Likely stored locally or not at all
   - Various agent pages
   - Problem: No persistence across devices

---

## ✅ Required Changes

### 1. **Backend: Add Conversation Endpoints**
Create REST API endpoints for user conversations:
- `GET /conversations` - List user's conversations
- `POST /conversations` - Create new conversation
- `GET /conversations/{id}` - Get specific conversation
- `PUT /conversations/{id}` - Update conversation (add messages, update title)
- `DELETE /conversations/{id}` - Delete conversation

**Key Points:**
- Filter by `user_id` automatically (from session)
- Store in MongoDB `conversations` collection
- Each conversation document includes:
  - `user_id` (owner)
  - `title`
  - `messages` array
  - `created_at`, `updated_at`
  - `metadata` (thinking times, etc.)

### 2. **Backend: Add User Preferences Endpoint**
- `GET /users/me/preferences` - Get user preferences
- `PUT /users/me/preferences` - Update user preferences

Stores:
- UI theme (dark/light)
- Agent settings
- Display preferences
- Any other user-specific config

### 3. **Frontend: Update Conversations Store**
Replace localStorage with API calls:
- Load conversations from API on init
- Save to API instead of localStorage
- Keep local state for performance
- Sync with API on changes

### 4. **Frontend: Update All Agent Pages**
Ensure all agent operations are:
- Authenticated (already done ✅)
- Stored per user in MongoDB
- No localStorage usage

---

## 🔧 Implementation Steps

### Step 1: Backend - Conversation Endpoints (HIGH PRIORITY)
```python
# Add to http_server.py
@app.get("/conversations")
async def list_conversations(user: User = Depends(require_auth)):
    # Return user's conversations from MongoDB
    
@app.post("/conversations")
async def create_conversation(data, user: User = Depends(require_auth)):
    # Create conversation with user_id
    
@app.put("/conversations/{id}")
async def update_conversation(id, data, user: User = Depends(require_auth)):
    # Update if owner matches
```

### Step 2: Backend - User Preferences
```python
@app.get("/users/me/preferences")
async def get_preferences(user: User = Depends(require_auth)):
    # Return user.metadata['preferences']
    
@app.put("/users/me/preferences")
async def update_preferences(data, user: User = Depends(require_auth)):
    # Update user.metadata['preferences']
```

### Step 3: Frontend - Conversation Service
```javascript
// New file: ui/src/lib/services/conversations.js
export async function listConversations() {
  const response = await fetch(`${API_BASE}/conversations`, {
    credentials: 'include'
  });
  return await response.json();
}

export async function createConversation(conversation) {
  // POST to API
}

export async function updateConversation(id, updates) {
  // PUT to API
}
```

### Step 4: Frontend - Update Conversations Store
Remove all localStorage code, use API instead:
- Load from API on init
- Save to API on changes
- Optimistic updates for UX

### Step 5: Frontend - User Preferences Service
```javascript
export async function getUserPreferences() {
  // GET from API
}

export async function updateUserPreferences(prefs) {
  // PUT to API
}
```

### Step 6: Testing
- [ ] Login as user1, create conversations
- [ ] Logout, login as user2, verify separate conversations
- [ ] Login as user1 again, verify conversations persisted
- [ ] Test on different browsers/devices

---

## 📊 Database Schema Updates

### Conversation Document (Already exists in models/documents.py ✅)
```python
class Conversation(Document):
    user_id: str  # ADD THIS FIELD!
    title: str
    messages: List[Message]
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]  # For thinking times, etc.
```

### User Document - Add Preferences Field
```python
class User(Document):
    # ... existing fields ...
    preferences: Dict[str, Any] = Field(default_factory=dict)
    # Stores: theme, agent_settings, display_prefs, etc.
```

---

## ⚠️ Migration Strategy

### For Existing Users:
1. **Conversations**: Lost (localStorage → MongoDB migration not needed for dev)
2. **Preferences**: Reset to defaults
3. **Agent History**: Fresh start

### For Production:
Would need migration script to:
1. Export localStorage data
2. Import to MongoDB per user
3. Clear localStorage

---

## 🎯 Benefits After Implementation

✅ **Per-User Data** - Each user has their own conversations and settings
✅ **Cross-Device** - Access data from any device
✅ **Persistent** - Data survives logout/clear cache
✅ **Secure** - Server-side storage with authentication
✅ **Scalable** - MongoDB handles large datasets
✅ **Auditable** - All data changes logged

---

## 📝 Summary

**CURRENT STATE:**
- ❌ Conversations in localStorage (shared across users)
- ❌ Settings in localStorage (lost on logout)
- ❌ No cross-device sync

**TARGET STATE:**
- ✅ Conversations in MongoDB per user
- ✅ Settings in MongoDB per user
- ✅ Cross-device sync
- ✅ Persistent across logout

**PRIORITY: HIGH** - This is critical for multi-user functionality!
