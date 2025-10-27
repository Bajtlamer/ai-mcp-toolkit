# Per-User Conversation Storage Migration

## Overview

The AI MCP Toolkit has been upgraded from localStorage-based conversation storage to a **fully per-user MongoDB-backed storage system**. This provides true multi-user support with:

- ✅ **Secure per-user data isolation** - Each user only sees their own conversations
- ✅ **Database persistence** - All conversations stored in MongoDB
- ✅ **Authentication-based access** - All operations require valid session authentication
- ✅ **Audit logging** - All conversation operations are logged for security
- ✅ **Scalability** - No localStorage size limits, works across devices

## What Changed

### Backend Changes

1. **New ConversationManager** (`src/ai_mcp_toolkit/managers/conversation_manager.py`)
   - Full CRUD operations for conversations
   - User ownership verification on all operations
   - Pagination support for large conversation lists

2. **New REST API Endpoints** (added to `http_server.py`)
   - `GET /conversations` - List user's conversations
   - `POST /conversations` - Create a new conversation
   - `GET /conversations/{id}` - Get specific conversation
   - `PUT /conversations/{id}` - Update conversation
   - `DELETE /conversations/{id}` - Delete conversation
   - `POST /conversations/{id}/messages` - Add message to conversation
   - `GET /conversations/stats/count` - Get conversation count

3. **Updated Conversation Model** (`models/documents.py`)
   - Already had `user_id` field for ownership
   - Messages stored as array directly in conversation document
   - Metadata field for thinking times and other metrics

### Frontend Changes

1. **New Conversation API Service** (`ui/src/lib/api/conversations.js`)
   - HTTP client functions for all conversation operations
   - Credentials included in all requests for session cookies
   - Error handling for failed operations

2. **Refactored Conversations Store** (`ui/src/lib/stores/conversations.js`)
   - **OLD**: Used localStorage directly (`ai-chat-conversations` key)
   - **NEW**: Fetches from backend API on load, syncs all changes to MongoDB
   - Maintains same API interface for backward compatibility
   - Adds `loadConversations()` method called on auth init

3. **Updated Root Layout** (`ui/src/routes/+layout.svelte`)
   - Calls `conversations.loadConversations()` after successful authentication
   - Ensures conversations are loaded before rendering main UI

## Migration Guide

### For Existing Users with localStorage Data

If you have existing conversations in localStorage, you can migrate them to MongoDB:

#### Step 1: Export Your Conversations

1. Open the AI Chat interface in your browser
2. Go to Settings (gear icon)
3. Click **"Export Conversations"**
4. Save the JSON file (e.g., `my_conversations.json`)

#### Step 2: Run Migration Script

```bash
# Make sure the backend server is running and you have created a user

# Migrate for user 'admin'
python scripts/migrate_localStorage_to_mongodb.py \
  --file my_conversations.json \
  --username admin

# Or for another user
python scripts/migrate_localStorage_to_mongodb.py \
  --file my_conversations.json \
  --username testuser
```

The script will:
- Connect to MongoDB
- Find the specified user
- Import all conversations with full message history
- Preserve timestamps, titles, and metadata
- Associate conversations with the user account

#### Step 3: Clear localStorage (Optional)

After successful migration, you can clear the old localStorage data:

```javascript
// In browser console:
localStorage.removeItem('ai-chat-conversations');
```

### For New Users

No migration needed! Just:
1. Log in with your account
2. Start chatting - conversations automatically save to MongoDB
3. All data is persistent and accessible from any device

## API Usage Examples

### List Conversations

```javascript
import { listConversations } from '$lib/api/conversations';

const conversations = await listConversations(limit=100, offset=0);
console.log(conversations);
```

### Create Conversation

```javascript
import { createConversation } from '$lib/api/conversations';

const conversation = await createConversation(
  'My New Conversation',
  [],  // initial messages
  {}   // metadata
);
console.log('Created:', conversation.id);
```

### Add Message

```javascript
import { addMessage } from '$lib/api/conversations';

const updated = await addMessage(
  conversationId,
  'user',
  'Hello, AI!'
);
console.log('Message added:', updated.messages.length);
```

### Delete Conversation

```javascript
import { deleteConversation } from '$lib/api/conversations';

await deleteConversation(conversationId);
console.log('Conversation deleted');
```

## Data Format

### Backend (MongoDB) Format

```json
{
  "_id": "ObjectId(...)",
  "user_id": "user_object_id",
  "title": "My Conversation",
  "messages": [
    {
      "role": "user",
      "content": "Hello",
      "timestamp": "2024-01-15T10:30:00.000Z"
    },
    {
      "role": "assistant",
      "content": "Hi! How can I help?",
      "timestamp": "2024-01-15T10:30:02.000Z"
    }
  ],
  "status": "active",
  "metadata": {
    "thinkingTimes": [2.5, 3.1],
    "averageThinkingTime": 2.8,
    "totalThinkingTime": 5.6,
    "responseCount": 2
  },
  "created_at": "2024-01-15T10:30:00.000Z",
  "updated_at": "2024-01-15T10:30:02.000Z"
}
```

### Frontend Format

```javascript
{
  id: "conversation_id",
  title: "My Conversation",
  messages: [
    {
      type: "user",  // mapped from role
      content: "Hello",
      timestamp: Date object
    },
    {
      type: "assistant",
      content: "Hi! How can I help?",
      timestamp: Date object
    }
  ],
  createdAt: Date object,
  updatedAt: Date object,
  isLoading: false,
  thinkingTimes: [2.5, 3.1],
  averageThinkingTime: 2.8,
  totalThinkingTime: 5.6,
  responseCount: 2
}
```

## Security

- **Authentication Required**: All conversation endpoints require valid session authentication
- **User Ownership**: Users can only access their own conversations
- **Audit Logging**: All operations logged with user_id, action, timestamp
- **Server-Side Sessions**: Session data stored in MongoDB, only session_id in HTTP-only cookie

## Troubleshooting

### "Failed to load conversations"

- Ensure you're logged in (valid session)
- Check backend server is running on http://localhost:8000
- Check browser console for detailed error messages
- Verify MongoDB is running and accessible

### "Conversation not found" when accessing

- Conversation may belong to another user
- Conversation may have been deleted
- Check conversation ID is correct

### Migration script fails

- Ensure MongoDB is running
- Verify user exists: `python scripts/create_test_users.py`
- Check JSON file is valid (exported from Settings)
- Review error messages for specific issues

## Backup Old localStorage Version

The old localStorage-based conversations store has been backed up to:
- `ui/src/lib/stores/conversations_old_localStorage.js`

This file is kept for reference but is no longer used by the application.

## Future Enhancements

Potential future additions:
- Conversation sharing between users
- Conversation export to PDF/Markdown
- Full-text search across all conversations
- Conversation tags and categories
- Conversation archiving
- Real-time sync across multiple tabs/devices

## Questions or Issues?

If you encounter any problems with the migration or per-user storage system:
1. Check this documentation
2. Review the audit logs in MongoDB (`audit_logs` collection)
3. Check server logs for backend errors
4. Check browser console for frontend errors
