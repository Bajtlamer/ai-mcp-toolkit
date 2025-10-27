import { writable, derived, get } from 'svelte/store';
import {
	listConversations,
	getConversation,
	createConversation as apiCreateConversation,
	updateConversation as apiUpdateConversation,
	deleteConversation as apiDeleteConversation,
	addMessage as apiAddMessage,
	getConversationCount
} from '$lib/api/conversations';

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

// Convert backend conversation format to frontend format
function convertToFrontendFormat(backendConv) {
	return {
		id: backendConv.id,
		title: backendConv.title,
messages: backendConv.messages.map((msg, index) => ({
		...msg,
		id: msg.id || `${msg.role}-${msg.timestamp}-${index}`,
		timestamp: new Date(msg.timestamp),
		type: msg.role === 'assistant' ? 'assistant' : msg.role === 'system' ? 'system' : 'user',
		// Preserve metrics and model from backend
		metrics: msg.metrics || null,
		model: msg.model || null
	})),
		createdAt: new Date(backendConv.created_at),
		updatedAt: new Date(backendConv.updated_at),
		isLoading: false,
		// Thinking time metrics from metadata
		thinkingTimes: backendConv.metadata?.thinkingTimes || [],
		averageThinkingTime: backendConv.metadata?.averageThinkingTime || 0,
		totalThinkingTime: backendConv.metadata?.totalThinkingTime || 0,
		responseCount: backendConv.metadata?.responseCount || 0
	};
}

// Convert frontend message format to backend format
function convertMessageToBackend(message) {
	const backendMsg = {
		role: message.type === 'assistant' ? 'assistant' : message.type === 'system' ? 'system' : 'user',
		content: typeof message.content === 'string' ? message.content : JSON.stringify(message.content),
		timestamp: message.timestamp ? message.timestamp.toISOString() : new Date().toISOString()
	};
	
	// Preserve metrics and model for assistant messages
	if (message.metrics) {
		backendMsg.metrics = message.metrics;
	}
	if (message.model) {
		backendMsg.model = message.model;
	}
	
	return backendMsg;
}

// Conversations store - array of conversation objects from backend
function createConversationsStore() {
	const { subscribe, set, update } = writable([]);
	let isInitialized = false;

	return {
		subscribe,
		set,
		update,

		// Load conversations from backend
		loadConversations: async () => {
			try {
				const backendConversations = await listConversations();
				const frontendConversations = backendConversations.map(convertToFrontendFormat);
				set(frontendConversations);
				isInitialized = true;
				return frontendConversations;
			} catch (error) {
				console.error('Failed to load conversations from backend:', error);
				// Set empty array on error
				set([]);
				throw error;
			}
		},

		// Ensure conversations are loaded
		ensureLoaded: async () => {
			if (!isInitialized) {
				await conversations.loadConversations();
			}
		},

		// Add a new conversation
		createConversation: async (title = 'New Conversation') => {
			try {
				const backendConv = await apiCreateConversation(title, [], {});
				const frontendConv = convertToFrontendFormat(backendConv);
				update(conversations => [frontendConv, ...conversations]);
				return frontendConv;
			} catch (error) {
				console.error('Failed to create conversation:', error);
				throw error;
			}
		},

		// Delete a conversation
		deleteConversation: async (conversationId) => {
			try {
				await apiDeleteConversation(conversationId);
				update(conversations => conversations.filter(conv => conv.id !== conversationId));
			} catch (error) {
				console.error('Failed to delete conversation:', error);
				throw error;
			}
		},

		// Update conversation title
		updateTitle: async (conversationId, newTitle) => {
			try {
				const backendConv = await apiUpdateConversation(conversationId, { title: newTitle });
				const frontendConv = convertToFrontendFormat(backendConv);
				update(conversations => conversations.map(conv =>
					conv.id === conversationId ? frontendConv : conv
				));
			} catch (error) {
				console.error('Failed to update title:', error);
				throw error;
			}
		},

		// Add message to conversation
		addMessage: async (conversationId, message) => {
			try {
				const backendMessage = convertMessageToBackend(message);
				const backendConv = await apiAddMessage(
					conversationId,
					backendMessage
				);

				// Auto-generate title from first user message if needed
				if (backendConv.title === 'New Conversation' && message.type === 'user') {
					const newTitle = generateTitle(message);
					const updatedConv = await apiUpdateConversation(conversationId, { title: newTitle });
					const frontendConv = convertToFrontendFormat(updatedConv);
					update(conversations => conversations.map(conv =>
						conv.id === conversationId ? frontendConv : conv
					));
				} else {
					const frontendConv = convertToFrontendFormat(backendConv);
					update(conversations => conversations.map(conv =>
						conv.id === conversationId ? frontendConv : conv
					));
				}
			} catch (error) {
				console.error('Failed to add message:', error);
				throw error;
			}
		},

		// Update last message in conversation (local only, sync later)
		updateLastMessage: (conversationId, updates) => {
			update(conversations => {
				return conversations.map(conv => {
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
			});
		},

		// Sync conversation messages to backend
		syncMessages: async (conversationId) => {
			try {
				const currentConvs = get({ subscribe });
				const conv = currentConvs.find(c => c.id === conversationId);
				if (!conv) return;

				const backendMessages = conv.messages.map(convertMessageToBackend);
				const backendConv = await apiUpdateConversation(conversationId, {
					messages: backendMessages
				});
				const frontendConv = convertToFrontendFormat(backendConv);
				update(conversations => conversations.map(c =>
					c.id === conversationId ? frontendConv : c
				));
			} catch (error) {
				console.error('Failed to sync messages:', error);
				throw error;
			}
		},

		// Set conversation loading state (local only)
		setConversationLoading: (conversationId, isLoading) => {
			update(conversations => conversations.map(conv =>
				conv.id === conversationId
					? { ...conv, isLoading }
					: conv
			));
		},

		// Clear all conversations (delete all on backend)
		clearAll: async () => {
			try {
				const currentConvs = get({ subscribe });
				for (const conv of currentConvs) {
					await apiDeleteConversation(conv.id);
				}
				set([]);
			} catch (error) {
				console.error('Failed to clear all conversations:', error);
				throw error;
			}
		},

		// Export conversations (from backend)
		exportConversations: async () => {
			try {
				const currentConvs = get({ subscribe });
				return JSON.stringify(currentConvs, null, 2);
			} catch (error) {
				console.error('Failed to export conversations:', error);
				throw error;
			}
		},

		// Import conversations (to backend)
		importConversations: async (jsonData) => {
			try {
				const imported = JSON.parse(jsonData);
				// Create each conversation on backend
				for (const conv of imported) {
					const backendMessages = conv.messages.map(msg => ({
						role: msg.type === 'assistant' ? 'assistant' : msg.type === 'system' ? 'system' : 'user',
						content: msg.content,
						timestamp: msg.timestamp
					}));
					await apiCreateConversation(conv.title, backendMessages, {
						thinkingTimes: conv.thinkingTimes || [],
						averageThinkingTime: conv.averageThinkingTime || 0,
						totalThinkingTime: conv.totalThinkingTime || 0,
						responseCount: conv.responseCount || 0
					});
				}
				// Reload conversations
				await conversations.loadConversations();
				return true;
			} catch (error) {
				console.error('Failed to import conversations:', error);
				return false;
			}
		},

		// Add thinking time to conversation
		addThinkingTime: async (conversationId, thinkingTimeSeconds) => {
			try {
				const currentConvs = get({ subscribe });
				const conv = currentConvs.find(c => c.id === conversationId);
				if (!conv) return;

				const thinkingTimes = [...(conv.thinkingTimes || []), thinkingTimeSeconds];
				const totalThinkingTime = (conv.totalThinkingTime || 0) + thinkingTimeSeconds;
				const responseCount = (conv.responseCount || 0) + 1;
				const averageThinkingTime = totalThinkingTime / responseCount;

				// Update metadata on backend
				const backendConv = await apiUpdateConversation(conversationId, {
					metadata: {
						...conv.metadata,
						thinkingTimes,
						totalThinkingTime,
						responseCount,
						averageThinkingTime: Math.round(averageThinkingTime * 100) / 100
					}
				});

				const frontendConv = convertToFrontendFormat(backendConv);
				update(conversations => conversations.map(c =>
					c.id === conversationId ? frontendConv : c
				));
			} catch (error) {
				console.error('Failed to add thinking time:', error);
				throw error;
			}
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