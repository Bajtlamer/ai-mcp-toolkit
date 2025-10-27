/**
 * API service for conversation management
 */

const API_BASE_URL = 'http://localhost:8000';

/**
 * List all conversations for the authenticated user
 * @param {number} limit - Maximum number of conversations to return
 * @param {number} offset - Offset for pagination
 * @returns {Promise<Array>} Array of conversations
 */
export async function listConversations(limit = 100, offset = 0) {
	const response = await fetch(
		`${API_BASE_URL}/conversations?limit=${limit}&offset=${offset}`,
		{
			method: 'GET',
			credentials: 'include',
			headers: {
				'Content-Type': 'application/json'
			}
		}
	);

	if (!response.ok) {
		const error = await response.json();
		throw new Error(error.detail || 'Failed to list conversations');
	}

	return await response.json();
}

/**
 * Get a specific conversation by ID
 * @param {string} conversationId - Conversation ID
 * @returns {Promise<Object>} Conversation object
 */
export async function getConversation(conversationId) {
	const response = await fetch(
		`${API_BASE_URL}/conversations/${conversationId}`,
		{
			method: 'GET',
			credentials: 'include',
			headers: {
				'Content-Type': 'application/json'
			}
		}
	);

	if (!response.ok) {
		const error = await response.json();
		throw new Error(error.detail || 'Failed to get conversation');
	}

	return await response.json();
}

/**
 * Create a new conversation
 * @param {string} title - Conversation title
 * @param {Array} messages - Initial messages (optional)
 * @param {Object} metadata - Additional metadata (optional)
 * @returns {Promise<Object>} Created conversation
 */
export async function createConversation(title = 'New Conversation', messages = [], metadata = {}) {
	const response = await fetch(
		`${API_BASE_URL}/conversations`,
		{
			method: 'POST',
			credentials: 'include',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({
				title,
				messages,
				metadata
			})
		}
	);

	if (!response.ok) {
		const error = await response.json();
		throw new Error(error.detail || 'Failed to create conversation');
	}

	return await response.json();
}

/**
 * Update an existing conversation
 * @param {string} conversationId - Conversation ID
 * @param {Object} updates - Fields to update (title, messages, metadata, status)
 * @returns {Promise<Object>} Updated conversation
 */
export async function updateConversation(conversationId, updates) {
	const response = await fetch(
		`${API_BASE_URL}/conversations/${conversationId}`,
		{
			method: 'PUT',
			credentials: 'include',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify(updates)
		}
	);

	if (!response.ok) {
		const error = await response.json();
		throw new Error(error.detail || 'Failed to update conversation');
	}

	return await response.json();
}

/**
 * Delete a conversation
 * @param {string} conversationId - Conversation ID
 * @returns {Promise<void>}
 */
export async function deleteConversation(conversationId) {
	const response = await fetch(
		`${API_BASE_URL}/conversations/${conversationId}`,
		{
			method: 'DELETE',
			credentials: 'include',
			headers: {
				'Content-Type': 'application/json'
			}
		}
	);

	if (!response.ok) {
		const error = await response.json();
		throw new Error(error.detail || 'Failed to delete conversation');
	}
}

/**
 * Add a message to a conversation
 * @param {string} conversationId - Conversation ID
 * @param {Object} message - Message object with role, content, timestamp, and optionally metrics/model
 * @returns {Promise<Object>} Updated conversation
 */
export async function addMessage(conversationId, message) {
	const response = await fetch(
		`${API_BASE_URL}/conversations/${conversationId}/messages`,
		{
			method: 'POST',
			credentials: 'include',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify(message)
		}
	);

	if (!response.ok) {
		const error = await response.json();
		throw new Error(error.detail || 'Failed to add message');
	}

	return await response.json();
}

/**
 * Get conversation count for the authenticated user
 * @returns {Promise<number>} Count of conversations
 */
export async function getConversationCount() {
	const response = await fetch(
		`${API_BASE_URL}/conversations/stats/count`,
		{
			method: 'GET',
			credentials: 'include',
			headers: {
				'Content-Type': 'application/json'
			}
		}
	);

	if (!response.ok) {
		const error = await response.json();
		throw new Error(error.detail || 'Failed to get conversation count');
	}

	const data = await response.json();
	return data.count;
}
