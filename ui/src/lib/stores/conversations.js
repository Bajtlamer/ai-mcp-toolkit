import { writable, derived } from 'svelte/store';
import { browser } from '$app/environment';

// Utility function to generate unique IDs
function generateId() {
  return Date.now().toString(36) + Math.random().toString(36).substr(2);
}

// Utility function to generate conversation titles from first message
function generateTitle(firstMessage) {
  if (!firstMessage) return 'New Conversation';
  
  const content = firstMessage.content || '';
  const words = content.trim().split(' ');
  
  if (words.length <= 6) {
    return content.slice(0, 50);
  }
  
  return words.slice(0, 6).join(' ') + '...';
}

// Default welcome message
const createWelcomeMessage = () => ({
  id: generateId(),
  type: 'assistant',
  content: "Hello! I'm your AI assistant. I can help you with a wide variety of tasks including:\n\n• **General conversation** - Ask me anything!\n• **Text processing** - Clean, analyze, or transform text\n• **Code assistance** - Help with programming questions\n• **Creative tasks** - Writing, brainstorming, and more\n• **Analysis** - Data interpretation, sentiment analysis\n\nWhat would you like to explore today?",
  timestamp: new Date(),
  isLoading: false
});

// Create initial conversation
const createNewConversation = () => ({
  id: generateId(),
  title: 'New Conversation',
  messages: [createWelcomeMessage()],
  createdAt: new Date(),
  updatedAt: new Date(),
  isLoading: false,
  // Thinking time metrics
  thinkingTimes: [], // Array of response times in seconds
  averageThinkingTime: 0, // Average response time
  totalThinkingTime: 0, // Total time spent thinking
  responseCount: 0 // Number of AI responses
});

// Conversations store - array of conversation objects
function createConversationsStore() {
  let initialConversations = [createNewConversation()];
  
  // Load from localStorage if available
  if (browser) {
    try {
      const stored = localStorage.getItem('ai-chat-conversations');
      if (stored) {
        const parsed = JSON.parse(stored);
        // Convert date strings back to Date objects and ensure thinking time metrics
        initialConversations = parsed.map(conv => ({
          ...conv,
          createdAt: new Date(conv.createdAt),
          updatedAt: new Date(conv.updatedAt),
          // Ensure thinking time metrics exist for backward compatibility
          thinkingTimes: conv.thinkingTimes || [],
          averageThinkingTime: conv.averageThinkingTime || 0,
          totalThinkingTime: conv.totalThinkingTime || 0,
          responseCount: conv.responseCount || 0,
          messages: conv.messages.map(msg => ({
            ...msg,
            timestamp: new Date(msg.timestamp),
            // Ensure content is always a string
            content: typeof msg.content === 'string' ? msg.content : JSON.stringify(msg.content)
          }))
        }));
        
        // Ensure at least one conversation exists
        if (initialConversations.length === 0) {
          initialConversations = [createNewConversation()];
        }
      }
    } catch (error) {
      console.error('Failed to load conversations from localStorage:', error);
      initialConversations = [createNewConversation()];
    }
  }

  const { subscribe, set, update } = writable(initialConversations);

  // Save to localStorage whenever conversations change
  const saveToStorage = (conversations) => {
    if (browser) {
      try {
        localStorage.setItem('ai-chat-conversations', JSON.stringify(conversations));
      } catch (error) {
        console.error('Failed to save conversations to localStorage:', error);
      }
    }
  };

  return {
    subscribe,
    set: (value) => {
      set(value);
      saveToStorage(value);
    },
    update: (fn) => {
      update((conversations) => {
        const newConversations = fn(conversations);
        saveToStorage(newConversations);
        return newConversations;
      });
    },

    // Add a new conversation
    createConversation: () => {
      const newConversation = createNewConversation();
      update(conversations => {
        const updated = [newConversation, ...conversations];
        saveToStorage(updated);
        return updated;
      });
      return newConversation.id;
    },

    // Delete a conversation
    deleteConversation: (conversationId) => {
      update(conversations => {
        const filtered = conversations.filter(conv => conv.id !== conversationId);
        // Ensure at least one conversation exists
        const updated = filtered.length > 0 ? filtered : [createNewConversation()];
        saveToStorage(updated);
        return updated;
      });
    },

    // Update conversation title
    updateTitle: (conversationId, newTitle) => {
      update(conversations => {
        const updated = conversations.map(conv =>
          conv.id === conversationId
            ? { ...conv, title: newTitle, updatedAt: new Date() }
            : conv
        );
        saveToStorage(updated);
        return updated;
      });
    },

    // Add message to conversation
    addMessage: (conversationId, message) => {
      update(conversations => {
        const updated = conversations.map(conv => {
          if (conv.id === conversationId) {
            // Ensure content is always a string
            const validatedMessage = {
              ...message,
              id: generateId(),
              content: typeof message.content === 'string' ? message.content : JSON.stringify(message.content)
            };
            const newMessages = [...conv.messages, validatedMessage];
            let title = conv.title;
            
            // Auto-generate title from first user message
            if (conv.title === 'New Conversation' && message.type === 'user') {
              title = generateTitle(message);
            }
            
            return {
              ...conv,
              messages: newMessages,
              title,
              updatedAt: new Date(),
              isLoading: false
            };
          }
          return conv;
        });
        saveToStorage(updated);
        return updated;
      });
    },

    // Update last message in conversation
    updateLastMessage: (conversationId, updates) => {
      update(conversations => {
        const updated = conversations.map(conv => {
          if (conv.id === conversationId && conv.messages.length > 0) {
            const messages = [...conv.messages];
            messages[messages.length - 1] = {
              ...messages[messages.length - 1],
              ...updates
            };
            
            return {
              ...conv,
              messages,
              updatedAt: new Date()
            };
          }
          return conv;
        });
        saveToStorage(updated);
        return updated;
      });
    },

    // Set conversation loading state
    setConversationLoading: (conversationId, isLoading) => {
      update(conversations => {
        const updated = conversations.map(conv =>
          conv.id === conversationId
            ? { ...conv, isLoading, updatedAt: new Date() }
            : conv
        );
        saveToStorage(updated);
        return updated;
      });
    },

    // Clear all conversations
    clearAll: () => {
      const freshConversations = [createNewConversation()];
      set(freshConversations);
      saveToStorage(freshConversations);
    },

    // Export conversations
    exportConversations: () => {
      let conversations;
      subscribe(value => conversations = value)();
      return JSON.stringify(conversations, null, 2);
    },

    // Import conversations
    importConversations: (jsonData) => {
      try {
        const imported = JSON.parse(jsonData);
        const validConversations = imported.map(conv => ({
          ...conv,
          createdAt: new Date(conv.createdAt),
          updatedAt: new Date(conv.updatedAt),
          // Ensure thinking time metrics exist
          thinkingTimes: conv.thinkingTimes || [],
          averageThinkingTime: conv.averageThinkingTime || 0,
          totalThinkingTime: conv.totalThinkingTime || 0,
          responseCount: conv.responseCount || 0,
          messages: conv.messages.map(msg => ({
            ...msg,
            timestamp: new Date(msg.timestamp),
            // Ensure content is always a string
            content: typeof msg.content === 'string' ? msg.content : JSON.stringify(msg.content)
          }))
        }));
        
        set(validConversations);
        return true;
      } catch (error) {
        console.error('Failed to import conversations:', error);
        return false;
      }
    },

    // Add thinking time to conversation
    addThinkingTime: (conversationId, thinkingTimeSeconds) => {
      update(conversations => {
        const updated = conversations.map(conv => {
          if (conv.id === conversationId) {
            const thinkingTimes = [...(conv.thinkingTimes || []), thinkingTimeSeconds];
            const totalThinkingTime = (conv.totalThinkingTime || 0) + thinkingTimeSeconds;
            const responseCount = (conv.responseCount || 0) + 1;
            const averageThinkingTime = totalThinkingTime / responseCount;
            
            return {
              ...conv,
              thinkingTimes,
              totalThinkingTime,
              responseCount,
              averageThinkingTime: Math.round(averageThinkingTime * 100) / 100, // Round to 2 decimals
              updatedAt: new Date()
            };
          }
          return conv;
        });
        saveToStorage(updated);
        return updated;
      });
    }
  };
}

// Current conversation ID store
function createCurrentConversationStore() {
  const { subscribe, set, update } = writable(null);

  return {
    subscribe,
    set,
    update,
    
    // Initialize with first conversation
    init: (conversations) => {
      if (conversations && conversations.length > 0) {
        set(conversations[0].id);
      }
    }
  };
}

// Create store instances
export const conversations = createConversationsStore();
export const currentConversationId = createCurrentConversationStore();

// Derived store for current conversation
export const currentConversation = derived(
  [conversations, currentConversationId],
  ([$conversations, $currentConversationId]) => {
    if (!$currentConversationId) {
      return $conversations[0] || null;
    }
    return $conversations.find(conv => conv.id === $currentConversationId) || $conversations[0] || null;
  }
);

// Initialize current conversation ID when conversations load
conversations.subscribe((convs) => {
  currentConversationId.update(currentId => {
    if (!currentId && convs.length > 0) {
      return convs[0].id;
    }
    // Check if current conversation still exists
    const exists = convs.find(conv => conv.id === currentId);
    return exists ? currentId : (convs[0]?.id || null);
  });
});