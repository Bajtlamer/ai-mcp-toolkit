<script>
  import { onMount, afterUpdate, tick } from 'svelte';
  import { 
    MessageSquare, 
    Send, 
    Bot, 
    User, 
    Copy, 
    RotateCcw, 
    Edit3, 
    Check, 
    X,
    Sidebar,
    AlertTriangle,
    Wifi,
    WifiOff,
    Download
  } from 'lucide-svelte';
  
  import ConversationSidebar from '$lib/components/ConversationSidebar.svelte';
  import SafeMarkdownRenderer from '$lib/components/SafeMarkdownRenderer.svelte';
  import { conversations, currentConversation, currentConversationId } from '$lib/stores/conversations.js';
  import { chatAPI } from '$lib/services/chat-api.js';

  let inputText = '';
  let chatContainer;
  let error = null;
  let serverStatus = { mcp: false, ollama: false, canChat: false };
  let showSidebar = true;
  let editingMessageId = null;
  let editingText = '';
  let regeneratingMessageId = null;
  let notification = null;

  // Reactive current conversation and messages
  $: currentMessages = $currentConversation?.messages || [];
  $: isLoading = $currentConversation?.isLoading || false;

  // Auto-scroll to bottom when new messages arrive
  afterUpdate(() => {
    if (chatContainer) {
      chatContainer.scrollTop = chatContainer.scrollHeight;
    }
  });

  onMount(async () => {
    // Check server status
    await checkServerStatus();
    // Set up periodic status checks
    const statusInterval = setInterval(checkServerStatus, 30000); // Check every 30 seconds
    
    return () => clearInterval(statusInterval);
  });

  async function checkServerStatus() {
    try {
      serverStatus = await chatAPI.getServerStatus();
    } catch (err) {
      console.error('Failed to check server status:', err);
      serverStatus = { mcp: false, ollama: false, canChat: false };
    }
  }

  // Function to safely extract text from nested objects
  function extractTextFromObject(obj) {
    if (obj === null || obj === undefined) return '';
    if (typeof obj === 'string') return obj;
    if (typeof obj === 'number' || typeof obj === 'boolean') return String(obj);
    
    if (typeof obj === 'object') {
      // Try common text properties
      if (obj.content && typeof obj.content === 'string') return obj.content;
      if (obj.text && typeof obj.text === 'string') return obj.text;
      if (obj.message && typeof obj.message === 'string') return obj.message;
      if (obj.value && typeof obj.value === 'string') return obj.value;
      
      // If it's an array, join the extracted text from each element
      if (Array.isArray(obj)) {
        return obj.map(extractTextFromObject).join('');
      }
      
      // If it has nested content/text properties that are objects, recurse
      if (obj.content && typeof obj.content === 'object') {
        return extractTextFromObject(obj.content);
      }
      if (obj.text && typeof obj.text === 'object') {
        return extractTextFromObject(obj.text);
      }
      
      // Last resort: stringify it nicely
      return JSON.stringify(obj, null, 2);
    }
    
    return String(obj);
  }

  async function sendMessage() {
    if (!inputText.trim() || isLoading || !$currentConversation) return;
    if (!serverStatus.canChat) {
      showNotification('error', 'No AI service available. Please start MCP server or Ollama.');
      return;
    }

    const messageContent = inputText.trim();
    inputText = '';
    error = null;

    // Add user message
    const userMessage = {
      type: 'user',
      content: messageContent,
      timestamp: new Date()
    };
    
    conversations.addMessage($currentConversation.id, userMessage);
    conversations.setConversationLoading($currentConversation.id, true);

    try {
      // Track thinking time
      const startTime = Date.now();
      
      // Get AI response with conversation history
      const response = await chatAPI.sendMessage(
        messageContent, 
        $currentConversation.id, 
        $currentConversation.messages
      );
      
      // Calculate actual thinking time (response time)
      const thinkingTime = (Date.now() - startTime) / 1000;
      
      // Ensure we have valid content - always convert to string
      let assistantContent;
      if (response && typeof response === 'object' && response.content) {
        assistantContent = extractTextFromObject(response.content);
      } else if (typeof response === 'string') {
        assistantContent = response;
      } else {
        console.error('Invalid response format:', response);
        assistantContent = 'Error: Invalid response format - received: ' + JSON.stringify(response);
      }
      
      const assistantMessage = {
        type: 'assistant',
        content: assistantContent,
        timestamp: new Date(),
        metrics: response?.metrics // Add timing metrics
      };
      
      conversations.addMessage($currentConversation.id, assistantMessage);
      conversations.addThinkingTime($currentConversation.id, thinkingTime);
    } catch (err) {
      error = err.message || 'Failed to get AI response';
      console.error('Chat error:', err);
    } finally {
      conversations.setConversationLoading($currentConversation.id, false);
    }
  }

  async function regenerateLastResponse() {
    if (!$currentConversation || currentMessages.length < 2) return;
    
    const lastUserMessage = [...currentMessages].reverse().find(msg => msg.type === 'user');
    if (!lastUserMessage) return;
    
    // Remove the last assistant message
    const messagesWithoutLast = currentMessages.slice(0, -1);
    conversations.update(convs => 
      convs.map(conv => 
        conv.id === $currentConversation.id
          ? { ...conv, messages: messagesWithoutLast }
          : conv
      )
    );
    
    regeneratingMessageId = lastUserMessage.id;
    conversations.setConversationLoading($currentConversation.id, true);
    
    try {
      // Track thinking time for regeneration
      const startTime = Date.now();
      
      const response = await chatAPI.sendMessage(
        lastUserMessage.content,
        $currentConversation.id,
        messagesWithoutLast
      );
      
      // Calculate thinking time
      const thinkingTime = (Date.now() - startTime) / 1000;
      
      // Ensure we have valid content - always convert to string
      let regeneratedContent;
      if (response && typeof response === 'object' && response.content) {
        regeneratedContent = extractTextFromObject(response.content);
      } else if (typeof response === 'string') {
        regeneratedContent = response;
      } else {
        console.error('Invalid response format in regenerate:', response);
        regeneratedContent = 'Error: Invalid response format - received: ' + JSON.stringify(response);
      }
      
      const assistantMessage = {
        type: 'assistant',
        content: regeneratedContent,
        timestamp: new Date(),
        metrics: response?.metrics
      };
      
      conversations.addMessage($currentConversation.id, assistantMessage);
      
      // Track thinking time for this conversation
      conversations.addThinkingTime($currentConversation.id, thinkingTime);
    } catch (err) {
      error = err.message || 'Failed to regenerate response';
      console.error('Regenerate error:', err);
    } finally {
      regeneratingMessageId = null;
      conversations.setConversationLoading($currentConversation.id, false);
    }
  }

  function startEditingMessage(message) {
    editingMessageId = message.id;
    editingText = message.content;
  }

  function saveMessageEdit() {
    if (!editingText.trim()) {
      cancelMessageEdit();
      return;
    }
    
    conversations.update(convs =>
      convs.map(conv =>
        conv.id === $currentConversation.id
          ? {
              ...conv,
              messages: conv.messages.map(msg =>
                msg.id === editingMessageId
                  ? { ...msg, content: editingText.trim(), edited: true }
                  : msg
              )
            }
          : conv
      )
    );
    
    editingMessageId = null;
    editingText = '';
  }

  function cancelMessageEdit() {
    editingMessageId = null;
    editingText = '';
  }

  function copyMessage(content) {
    navigator.clipboard.writeText(content);
    showNotification('success', 'Message copied to clipboard!');
  }

  function exportCurrentConversation() {
    if (!$currentConversation) return;
    
    const chatContent = currentMessages.map(m => 
      `[${formatTimestamp(m.timestamp)}] ${m.type.toUpperCase()}: ${m.content}`
    ).join('\n\n');
    
    const blob = new Blob([chatContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${$currentConversation.title.replace(/[^a-z0-9]/gi, '_').toLowerCase()}_conversation.txt`;
    a.click();
    URL.revokeObjectURL(url);
  }

  function onConversationChanged() {
    // Clear any editing state when switching conversations
    editingMessageId = null;
    editingText = '';
    regeneratingMessageId = null;
    error = null;
  }

  function showNotification(type, message) {
    notification = { type, message };
    setTimeout(() => notification = null, 5000);
  }

  function toggleSidebar() {
    showSidebar = !showSidebar;
  }

  function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  }

  function formatTimestamp(timestamp) {
    return timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }
</script>

<svelte:head>
  <title>AI Chat - AI MCP Toolkit</title>
</svelte:head>

<!-- Notification -->
{#if notification}
  <div class="fixed top-4 right-4 z-50 max-w-sm">
    <div class="{notification.type === 'success' ? 'bg-green-50 border-green-200 text-green-800' : 'bg-red-50 border-red-200 text-red-800'} border rounded-lg p-4 shadow-lg animate-fadeIn">
      <div class="flex items-center space-x-2">
        <div class="w-5 h-5 {notification.type === 'success' ? 'bg-green-500' : 'bg-red-500'} rounded-full flex items-center justify-center">
          <span class="text-white text-xs font-bold">{notification.type === 'success' ? '✓' : '!'}</span>
        </div>
        <p class="text-sm font-medium">{notification.message}</p>
      </div>
    </div>
  </div>
{/if}

<div class="h-screen flex bg-gray-50 dark:bg-gray-900">
  <!-- Sidebar -->
  <div class="{showSidebar ? 'w-80' : 'w-0'} transition-all duration-300 overflow-hidden">
    <ConversationSidebar 
      on:conversationChanged={onConversationChanged}
      on:showNotification={(e) => showNotification(e.detail.type, e.detail.message)}
    />
  </div>

  <!-- Main Chat Area -->
  <div class="flex-1 flex flex-col">
    <!-- Chat Header -->
    <div class="border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-6 py-4">
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-4">
          <button
            on:click={toggleSidebar}
            class="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            title="Toggle sidebar"
          >
            <Sidebar size={20} />
          </button>
          
          <div class="flex items-center space-x-3">
            <div class="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
              <MessageSquare size={20} class="text-white" />
            </div>
            <div>
              <h1 class="text-xl font-semibold text-gray-900 dark:text-white">
                {$currentConversation?.title || 'AI Chat'}
              </h1>
              <div class="flex items-center space-x-2">
                <div class="w-2 h-2 {serverStatus.canChat ? 'bg-green-500' : 'bg-red-500'} rounded-full {serverStatus.canChat ? 'animate-pulse' : ''}"></div>
                <span class="text-sm text-gray-500 dark:text-gray-400">
                  {#if serverStatus.mcp}
                    MCP Server • Qwen2.5 14B
                  {:else if serverStatus.ollama}
                    Direct Ollama • Qwen2.5 14B
                  {:else}
                    Disconnected
                  {/if}
                </span>
              </div>
            </div>
          </div>
        </div>
        
        <div class="flex items-center space-x-2">
          <button
            on:click={exportCurrentConversation}
            class="flex items-center px-3 py-2 text-sm bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-lg transition-colors"
            title="Export conversation"
          >
            <Download size={16} class="mr-2" />
            Export
          </button>
          
          {#if currentMessages.length > 1}
            <button
              on:click={regenerateLastResponse}
              disabled={isLoading || !serverStatus.canChat}
              class="flex items-center px-3 py-2 text-sm bg-blue-100 dark:bg-blue-900/50 hover:bg-blue-200 dark:hover:bg-blue-800/70 text-blue-700 dark:text-blue-300 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              title="Regenerate last response"
            >
              <RotateCcw size={16} class="mr-2" />
              Regenerate
            </button>
          {/if}
        </div>
      </div>
    </div>

    <!-- Messages Area -->
    <div class="flex-1 overflow-hidden">
      <div 
        bind:this={chatContainer}
        class="h-full overflow-y-auto px-6 py-4 space-y-6 chat-scroll"
      >
        {#if currentMessages.length === 0}
          <div class="flex items-center justify-center h-full">
            <div class="text-center max-w-md">
              <div class="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center mb-4 mx-auto">
                <MessageSquare size={32} class="text-white" />
              </div>
              <h2 class="text-2xl font-semibold text-gray-900 dark:text-white mb-2">Start a conversation</h2>
              <p class="text-gray-600 dark:text-gray-400 mb-6">Ask me anything! I'm powered by Qwen2.5 14B and can help with a wide variety of tasks.</p>
              <div class="grid grid-cols-1 gap-2">
                <button
                  on:click={() => inputText = 'Hello! What can you help me with today?'}
                  class="p-3 text-left text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg hover:border-blue-300 dark:hover:border-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors"
                >
                  👋 Say hello
                </button>
                <button
                  on:click={() => inputText = 'Can you help me write a professional email?'}
                  class="p-3 text-left text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg hover:border-blue-300 dark:hover:border-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors"
                >
                  ✍️ Help with writing
                </button>
                <button
                  on:click={() => inputText = 'Explain machine learning in simple terms'}
                  class="p-3 text-left text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg hover:border-blue-300 dark:hover:border-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors"
                >
                  🧠 Learn something new
                </button>
              </div>
            </div>
          </div>
        {:else}
          {#each currentMessages as message (message.id)}
            <div class="flex {message.type === 'user' ? 'justify-end' : 'justify-start'} animate-fadeIn">
              <div class="flex items-start space-x-3 max-w-4xl w-full">
                {#if message.type === 'assistant'}
                  <div class="flex-shrink-0 w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
                    <Bot size={18} class="text-white" />
                  </div>
                {/if}
                
                <div class="flex-1 {message.type === 'user' ? 'flex justify-end' : ''}">
                  <div class="{message.type === 'user' ? 'max-w-2xl' : 'w-full'}">
                    <div class="flex items-center space-x-2 mb-2 {message.type === 'user' ? 'justify-end' : ''}">
                      <span class="text-xs font-medium {message.type === 'user' ? 'text-blue-600 dark:text-blue-400' : 'text-purple-600 dark:text-purple-400'}">
                        {message.type === 'user' ? 'You' : 'Qwen2.5 14B'}
                      </span>
                      <div class="flex items-center space-x-2 text-xs text-gray-500 dark:text-gray-400">
                        <span>
                          {formatTimestamp(message.timestamp)}
                          {#if message.edited}
                            <span class="ml-1 text-gray-400 dark:text-gray-500">(edited)</span>
                          {/if}
                        </span>
                        {#if message.metrics && message.type === 'assistant'}
                          <span class="hidden sm:inline-flex items-center space-x-1 px-2 py-1 bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300 rounded text-xs">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                              <circle cx="12" cy="12" r="10"/>
                              <polyline points="12,6 12,12 16,14"/>
                            </svg>
                            <span>{message.metrics.totalTime.toFixed(1)}s</span>
                            {#if message.metrics.tokensPerSecond > 0}
                              <span>•</span>
                              <span>{message.metrics.tokensPerSecond}t/s</span>
                            {/if}
                          </span>
                        {/if}
                      </div>
                    </div>
                    
                    <div class="relative group">
                      {#if editingMessageId === message.id}
                        <div class="bg-white dark:bg-gray-800 border border-blue-300 dark:border-blue-600 rounded-lg p-4">
                          <textarea
                            bind:value={editingText}
                            class="w-full resize-none bg-transparent text-gray-900 dark:text-white focus:outline-none"
                            rows="3"
                          ></textarea>
                          <div class="flex justify-end space-x-2 mt-3">
                            <button
                              on:click={cancelMessageEdit}
                              class="px-3 py-1 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 transition-colors"
                            >
                              Cancel
                            </button>
                            <button
                              on:click={saveMessageEdit}
                              class="px-3 py-1 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors"
                            >
                              Save
                            </button>
                          </div>
                        </div>
                      {:else}
                        <div class="{message.type === 'user' 
                          ? 'bg-gradient-to-r from-blue-600 to-blue-500 text-white shadow-lg' 
                          : 'bg-white dark:bg-gray-800 text-gray-900 dark:text-white border border-gray-200 dark:border-gray-600 shadow-sm'
                        } p-4 rounded-lg {message.type === 'user' ? 'rounded-br-sm' : 'rounded-tl-sm'}">
                          {#if message.type === 'user'}
                            <div class="prose prose-sm max-w-none prose-invert">
                              <pre class="whitespace-pre-wrap text-sm font-sans leading-relaxed bg-transparent border-none p-0 m-0">{message.content}</pre>
                            </div>
                          {:else}
                            <SafeMarkdownRenderer content={message.content} className="text-gray-900 dark:text-white" />
                          {/if}
                        </div>
                        
                        <!-- Message Actions -->
                        <div class="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                          <div class="flex items-center space-x-1">
                            <button
                              on:click={() => copyMessage(message.content)}
                              class="p-1.5 {message.type === 'user' ? 'bg-blue-700/50 hover:bg-blue-700/70' : 'bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600'} rounded-md transition-colors"
                              title="Copy message"
                            >
                              <Copy size={12} class="{message.type === 'user' ? 'text-white' : 'text-gray-600 dark:text-gray-300'}" />
                            </button>
                            
                            {#if message.type === 'user'}
                              <button
                                on:click={() => startEditingMessage(message)}
                                class="p-1.5 bg-blue-700/50 hover:bg-blue-700/70 rounded-md transition-colors"
                                title="Edit message"
                              >
                                <Edit3 size={12} class="text-white" />
                              </button>
                            {/if}
                          </div>
                        </div>
                      {/if}
                    </div>
                  </div>
                </div>
                
                {#if message.type === 'user'}
                  <div class="flex-shrink-0 w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center shadow-lg">
                    <User size={18} class="text-white" />
                  </div>
                {/if}
              </div>
            </div>
          {/each}
          
          <!-- Loading indicator -->
          {#if isLoading}
            <div class="flex justify-start animate-fadeIn">
              <div class="flex items-start space-x-3 max-w-4xl w-full">
                <div class="flex-shrink-0 w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
                  <Bot size={18} class="text-white" />
                </div>
                <div class="flex-1">
                  <div class="flex items-center space-x-2 mb-2">
                    <span class="text-xs font-medium text-purple-600 dark:text-purple-400">Qwen2.5 14B</span>
                  </div>
                  <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 p-4 rounded-lg rounded-tl-sm shadow-sm">
                    <div class="flex items-center space-x-3">
                      <div class="flex space-x-1">
                        <div class="w-2.5 h-2.5 bg-blue-400 rounded-full animate-bounce"></div>
                        <div class="w-2.5 h-2.5 bg-purple-400 rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
                        <div class="w-2.5 h-2.5 bg-blue-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
                      </div>
                      <div class="typing-indicator">
                        <span class="text-sm text-gray-500 dark:text-gray-400">AI is thinking</span>
                        <span class="typing-dots">
                          <span>.</span><span>.</span><span>.</span>
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          {/if}
          
          <!-- Error message -->
          {#if error}
            <div class="flex justify-start animate-fadeIn">
              <div class="flex items-start space-x-3 max-w-4xl w-full">
                <div class="flex-shrink-0 w-10 h-10 bg-red-500 rounded-xl flex items-center justify-center shadow-lg">
                  <AlertTriangle size={18} class="text-white" />
                </div>
                <div class="flex-1">
                  <div class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
                    <div class="text-red-600 dark:text-red-400 text-sm">
                      <strong>Error:</strong> {error}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          {/if}
        {/if}
      </div>
    </div>

    <!-- Input Section -->
    <div class="border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-6 py-4">
      <div class="flex items-end space-x-3">
        <div class="flex-1 relative">
          <textarea
            bind:value={inputText}
            on:keydown={handleKeyDown}
            placeholder="Message Qwen2.5 14B..."
            class="w-full px-4 py-3 pr-12 border border-gray-300 dark:border-gray-600 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-all"
            rows="1"
            style="min-height: 52px; max-height: 120px;"
            disabled={!serverStatus.canChat}
          ></textarea>
          
          <!-- Character counter -->
          <div class="absolute bottom-2 right-2 text-xs text-gray-400 dark:text-gray-500">
            {inputText.length}
          </div>
        </div>
        
        <button
          on:click={sendMessage}
          disabled={!inputText.trim() || isLoading || !serverStatus.canChat}
          class="flex items-center justify-center w-12 h-12 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 disabled:from-gray-400 disabled:to-gray-400 text-white rounded-xl transition-all duration-200 transform hover:scale-105 disabled:hover:scale-100 shadow-lg flex-shrink-0 disabled:opacity-50"
          title="Send message (Enter)"
        >
          {#if isLoading}
            <div class="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
          {:else}
            <Send size={18} />
          {/if}
        </button>
      </div>
      
      <!-- Status and shortcuts -->
      <div class="flex items-center justify-between mt-2 text-xs text-gray-500 dark:text-gray-400">
        <div class="flex items-center space-x-4">
          <span>
            Press <kbd class="px-1.5 py-0.5 bg-gray-200 dark:bg-gray-700 rounded text-xs font-mono">Enter</kbd> to send • 
            <kbd class="px-1.5 py-0.5 bg-gray-200 dark:bg-gray-700 rounded text-xs font-mono">Shift + Enter</kbd> for new line
          </span>
        </div>
        <div class="flex items-center space-x-1">
          {#if serverStatus.canChat}
            <Wifi size={14} class="text-green-500" />
            <span class="text-green-600 dark:text-green-400">Connected</span>
          {:else}
            <WifiOff size={14} class="text-red-500" />
            <span class="text-red-600 dark:text-red-400">Disconnected</span>
          {/if}
        </div>
      </div>
    </div>
  </div>
</div>

<style>
  /* Auto-resize textarea */
  textarea {
    field-sizing: content;
  }
  
  /* Custom animations */
  .animate-fadeIn {
    animation: fadeIn 0.3s ease-out forwards;
  }
  
  @keyframes fadeIn {
    from {
      opacity: 0;
      transform: translateY(10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
  
  /* Smooth scrollbar */
  .chat-scroll::-webkit-scrollbar {
    width: 6px;
  }
  
  .chat-scroll::-webkit-scrollbar-track {
    background: transparent;
  }
  
  .chat-scroll::-webkit-scrollbar-thumb {
    background: rgba(156, 163, 175, 0.3);
    border-radius: 3px;
  }
  
  .chat-scroll::-webkit-scrollbar-thumb:hover {
    background: rgba(156, 163, 175, 0.5);
  }
  
  /* Custom prose styling for messages */
  .prose pre {
    background: none !important;
    padding: 0 !important;
    margin: 0 !important;
    font-family: inherit !important;
  }
  
  /* Ensure user message pre styling */
  .prose pre.bg-transparent {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
    margin: 0 !important;
  }
  
  /* Typing indicator animation */
  .typing-indicator {
    display: flex;
    align-items: center;
    gap: 0.25rem;
  }
  
  .typing-dots {
    display: inline-flex;
  }
  
  .typing-dots span {
    animation: typingDots 1.4s infinite ease-in-out;
    opacity: 0.3;
  }
  
  .typing-dots span:nth-child(1) {
    animation-delay: 0s;
  }
  
  .typing-dots span:nth-child(2) {
    animation-delay: 0.2s;
  }
  
  .typing-dots span:nth-child(3) {
    animation-delay: 0.4s;
  }
  
  @keyframes typingDots {
    0%, 60%, 100% {
      opacity: 0.3;
      transform: translateY(0);
    }
    30% {
      opacity: 1;
      transform: translateY(-2px);
    }
  }
</style>
