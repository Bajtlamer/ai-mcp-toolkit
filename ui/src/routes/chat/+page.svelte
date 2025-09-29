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
    Download,
    Square
  } from 'lucide-svelte';
  
  import ConversationSidebar from '$lib/components/ConversationSidebar.svelte';
  import SafeMarkdownRenderer from '$lib/components/SafeMarkdownRenderer.svelte';
  import { conversations, currentConversation, currentConversationId } from '$lib/stores/conversations.js';
  import { chatAPI } from '$lib/services/chat-api.js';

  let inputText = '';
  let chatContainer;
  let error = null;
  let serverStatus = { mcp: false, ollama: false, canChat: false };
  let showSidebar = false; // Start with sidebar closed on mobile, open on desktop
  let editingMessageId = null;
  let editingText = '';
  let regeneratingMessageId = null;
  let notification = null;
  let currentAbortController = null; // For canceling requests

  // Reactive current conversation and messages
  $: currentMessages = $currentConversation?.messages || [];
  $: isLoading = $currentConversation?.isLoading || false;

  // Auto-scroll to bottom when new messages arrive
  let shouldAutoScroll = true;
  let lastMessageCount = 0;
  
  // Function to scroll to bottom
  function scrollToBottom(force = false) {
    if (!chatContainer) return;
    
    // Check if user has scrolled up manually (unless forced)
    if (!force && !shouldAutoScroll) return;
    
    // Use requestAnimationFrame to ensure DOM is updated
    requestAnimationFrame(() => {
      if (chatContainer) {
        chatContainer.scrollTo({
          top: chatContainer.scrollHeight,
          behavior: 'smooth'
        });
      }
    });
  }
  
  // Check if user has scrolled away from bottom
  function handleScroll() {
    if (!chatContainer) return;
    
    const { scrollTop, scrollHeight, clientHeight } = chatContainer;
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 50; // 50px threshold
    shouldAutoScroll = isAtBottom;
  }
  
  // Auto-scroll when messages change
  $: if (currentMessages.length !== lastMessageCount) {
    lastMessageCount = currentMessages.length;
    tick().then(() => scrollToBottom(true)); // Force scroll on new messages
  }
  
  // Auto-scroll when loading state changes (for typing indicators)
  $: if (isLoading !== undefined) {
    tick().then(() => scrollToBottom());
  }

  onMount(async () => {
    // Handle responsive sidebar visibility
    const handleResize = () => {
      if (window.innerWidth >= 1024) { // lg breakpoint
        showSidebar = true;
      }
    };
    
    handleResize();
    window.addEventListener('resize', handleResize);
    
    // Check server status
    await checkServerStatus();
    // Set up periodic status checks
    const statusInterval = setInterval(checkServerStatus, 30000); // Check every 30 seconds
    
    return () => {
      clearInterval(statusInterval);
      window.removeEventListener('resize', handleResize);
    };
  });

  async function checkServerStatus() {
    try {
      serverStatus = await chatAPI.getServerStatus();
    } catch (err) {
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

    // Create abort controller for cancellation
    currentAbortController = new AbortController();

    // Add user message
    const userMessage = {
      type: 'user',
      content: messageContent,
      timestamp: new Date()
    };
    
    conversations.addMessage($currentConversation.id, userMessage);
    conversations.setConversationLoading($currentConversation.id, true);
    
    // Ensure scroll to bottom after user message is added
    tick().then(() => scrollToBottom(true));

    try {
      // Track thinking time
      const startTime = Date.now();
      
      // Get AI response with conversation history
      const response = await chatAPI.sendMessage(
        messageContent, 
        $currentConversation.id, 
        $currentConversation.messages,
        currentAbortController.signal
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
        assistantContent = 'Error: Invalid response format';
      }
      
      const assistantMessage = {
        type: 'assistant',
        content: assistantContent,
        timestamp: new Date(),
        metrics: response?.metrics // Add timing metrics
      };
      
      conversations.addMessage($currentConversation.id, assistantMessage);
      conversations.addThinkingTime($currentConversation.id, thinkingTime);
      
      // Ensure scroll to bottom after assistant response
      tick().then(() => scrollToBottom(true));
    } catch (err) {
      if (err.name === 'AbortError') {
        // Mark the last user message as cancelled
        conversations.update(convs => 
          convs.map(conv => {
            if (conv.id === $currentConversation.id && conv.messages.length > 0) {
              const messages = [...conv.messages];
              const lastMessage = messages[messages.length - 1];
              if (lastMessage.type === 'user') {
                messages[messages.length - 1] = { ...lastMessage, cancelled: true };
              }
              return { ...conv, messages };
            }
            return conv;
          })
        );
        showNotification('success', 'Request cancelled successfully');
      } else {
        error = err.message || 'Failed to get AI response';
      }
    } finally {
      conversations.setConversationLoading($currentConversation.id, false);
      currentAbortController = null; // Clear the abort controller
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
    
    // Create abort controller for cancellation
    currentAbortController = new AbortController();
    
    try {
      // Track thinking time for regeneration
      const startTime = Date.now();
      
      const response = await chatAPI.sendMessage(
        lastUserMessage.content,
        $currentConversation.id,
        messagesWithoutLast,
        currentAbortController.signal
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
        regeneratedContent = 'Error: Invalid response format';
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
      
      // Ensure scroll to bottom after regenerated response
      tick().then(() => scrollToBottom(true));
    } catch (err) {
      if (err.name === 'AbortError') {
        // Mark the regenerating message as cancelled
        conversations.update(convs => 
          convs.map(conv => {
            if (conv.id === $currentConversation.id) {
              const messages = conv.messages.map(msg => 
                msg.id === regeneratingMessageId 
                  ? { ...msg, cancelled: true }
                  : msg
              );
              return { ...conv, messages };
            }
            return conv;
          })
        );
        showNotification('success', 'Request cancelled successfully');
      } else {
        error = err.message || 'Failed to regenerate response';
      }
    } finally {
      regeneratingMessageId = null;
      conversations.setConversationLoading($currentConversation.id, false);
      currentAbortController = null; // Clear the abort controller
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
  
  function cancelCurrentRequest() {
    if (currentAbortController) {
      currentAbortController.abort();
      currentAbortController = null;
    }
  }

  function copyMessage(content) {
    // Modern clipboard API with fallback for remote computers
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(content)
        .then(() => {
          showNotification('success', 'Message copied to clipboard!');
        })
        .catch(() => {
          // Fallback to execCommand for remote computers
          fallbackCopyToClipboard(content);
        });
    } else {
      // Fallback for browsers without clipboard API or insecure contexts
      fallbackCopyToClipboard(content);
    }
  }
  
  // Fallback copy function for older browsers or insecure contexts
  function fallbackCopyToClipboard(text) {
    try {
      const textArea = document.createElement('textarea');
      textArea.value = text;
      textArea.style.position = 'fixed';
      textArea.style.left = '-999999px';
      textArea.style.top = '-999999px';
      document.body.appendChild(textArea);
      textArea.focus();
      textArea.select();
      
      const successful = document.execCommand('copy');
      document.body.removeChild(textArea);
      
      if (successful) {
        showNotification('success', 'Message copied to clipboard!');
      } else {
        showNotification('error', 'Copy failed - please select and copy manually');
      }
    } catch (err) {
      showNotification('error', 'Copy failed - please select and copy manually');
    }
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
    
    // Reset auto-scroll behavior and scroll to bottom
    shouldAutoScroll = true;
    tick().then(() => scrollToBottom(true));
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

<!-- True 2-Column ChatGPT Layout -->
<div class="h-full flex bg-white dark:bg-gray-900" style="margin: -1.5rem; height: calc(100vh - 4rem);">
  <!-- Left Column: Conversation History (30% width) -->
  <div class="{showSidebar ? 'w-[30%]' : 'w-0'} flex-shrink-0 transition-all duration-300 overflow-hidden bg-gray-50 dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700">
    <ConversationSidebar 
      on:conversationChanged={onConversationChanged}
      on:showNotification={(e) => showNotification(e.detail.type, e.detail.message)}
    />
  </div>

  <!-- Right Column: Chat Area -->
  <div class="flex-1 flex flex-col bg-white dark:bg-gray-900">
    <!-- Minimal Header -->
    <div class="border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-6 py-3">
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-3">
          <!-- Sidebar toggle -->
          <button
            on:click={toggleSidebar}
            class="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            title="Toggle conversation history"
          >
            <Sidebar size={18} />
          </button>
          
          <!-- Conversation Title -->
          <div>
            <h1 class="text-lg font-semibold text-gray-900 dark:text-white truncate">
              {$currentConversation?.title || 'New Chat'}
            </h1>
            <div class="flex items-center space-x-2 text-xs">
              <div class="w-2 h-2 {serverStatus.canChat ? 'bg-green-500' : 'bg-red-500'} rounded-full {serverStatus.canChat ? 'animate-pulse' : ''}"></div>
              <span class="text-gray-500 dark:text-gray-400">
                {serverStatus.model?.name || 'AI Assistant'}
              </span>
            </div>
          </div>
        </div>
        
        <!-- Action Buttons -->
        <div class="flex items-center space-x-2">
          {#if currentMessages.length > 1}
            <button
              on:click={regenerateLastResponse}
              disabled={isLoading || !serverStatus.canChat}
              class="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              title="Regenerate last response"
            >
              <RotateCcw size={16} />
            </button>
          {/if}
        </div>
      </div>
    </div>

    <!-- Chat Content Area (Scrollable) -->
    <div 
      bind:this={chatContainer}
      class="flex-1 overflow-y-auto"
      on:scroll={handleScroll}
    >
      <div class="w-full">
        <!-- Messages and Input Container -->
        <div class="min-h-full flex flex-col">
          <!-- Messages Area -->
          <div class="flex-1 px-6 py-6 space-y-4">
            {#if currentMessages.length === 0}
              <!-- Welcome Screen -->
              <div class="text-center py-12">
                <div class="w-20 h-20 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center mb-6 mx-auto">
                  <MessageSquare size={36} class="text-white" />
                </div>
                <h2 class="text-3xl font-bold text-gray-900 dark:text-white mb-4">How can I help you today?</h2>
                <p class="text-lg text-gray-600 dark:text-gray-400 mb-8">
                  I'm {serverStatus.model?.name || 'your AI assistant'}, ready to help with writing, analysis, coding, and more.
                </p>
                
                <!-- Quick Start Examples -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-2xl mx-auto">
                  <button
                    on:click={() => inputText = 'Hello! What can you help me with today?'}
                    class="group p-4 text-left bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl hover:border-blue-300 dark:hover:border-blue-600 hover:shadow-sm transition-all"
                  >
                    <div class="text-2xl mb-2">👋</div>
                    <div class="font-medium text-gray-900 dark:text-white mb-1">Get Started</div>
                    <div class="text-sm text-gray-600 dark:text-gray-400">Say hello and see what I can do</div>
                  </button>
                  
                  <button
                    on:click={() => inputText = 'Help me write a professional email'}
                    class="group p-4 text-left bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl hover:border-blue-300 dark:hover:border-blue-600 hover:shadow-sm transition-all"
                  >
                    <div class="text-2xl mb-2">✍️</div>
                    <div class="font-medium text-gray-900 dark:text-white mb-1">Writing Help</div>
                    <div class="text-sm text-gray-600 dark:text-gray-400">Emails, documents, and more</div>
                  </button>
                  
                  <button
                    on:click={() => inputText = 'Explain machine learning concepts'}
                    class="group p-4 text-left bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl hover:border-blue-300 dark:hover:border-blue-600 hover:shadow-sm transition-all"
                  >
                    <div class="text-2xl mb-2">🧠</div>
                    <div class="font-medium text-gray-900 dark:text-white mb-1">Learning</div>
                    <div class="text-sm text-gray-600 dark:text-gray-400">Explain complex topics simply</div>
                  </button>
                  
                  <button
                    on:click={() => inputText = 'Help me debug this code'}
                    class="group p-4 text-left bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl hover:border-blue-300 dark:hover:border-blue-600 hover:shadow-sm transition-all"
                  >
                    <div class="text-2xl mb-2">💻</div>
                    <div class="font-medium text-gray-900 dark:text-white mb-1">Code Help</div>
                    <div class="text-sm text-gray-600 dark:text-gray-400">Debug and improve your code</div>
                  </button>
                </div>
              </div>
            {:else}
              {#each currentMessages as message (message.id)}
                <div class="message-container animate-fadeIn">
                  {#if message.type === 'assistant'}
                    <!-- AI Message -->
                    <div class="w-full py-2">
                      <div class="flex items-start space-x-4">
                        <div class="flex-shrink-0 w-8 h-8 bg-gradient-to-br from-green-500 to-emerald-600 rounded-full flex items-center justify-center">
                          <Bot size={16} class="text-white" />
                        </div>
                        <div class="flex-1 min-w-0 pr-4">
                          <div class="flex items-center space-x-2 mb-3">
                            <span class="text-sm font-medium text-gray-900 dark:text-white">
                              {serverStatus.model?.name || 'AI Assistant'}
                            </span>
                            <span class="text-xs text-gray-500 dark:text-gray-400">
                              {formatTimestamp(message.timestamp)}
                            </span>
                            {#if message.metrics}
                              <span class="text-xs text-gray-500 dark:text-gray-400">
                                • {message.metrics.totalTime?.toFixed(1)}s
                              </span>
                              {#if message.metrics.tokensPerSecond > 0}
                                <span class="text-xs text-gray-500 dark:text-gray-400">
                                  • {message.metrics.tokensPerSecond}t/s
                                </span>
                              {/if}
                            {/if}
                          </div>
                          
                          <div class="relative group w-full">
                            <div class="prose prose-gray dark:prose-invert w-full" style="max-width: none;">
                              <SafeMarkdownRenderer content={message.content} className="text-gray-800 dark:text-gray-200 leading-relaxed" />
                            </div>
                            
                            <!-- Message Actions -->
                            <div class="absolute top-0 right-0 opacity-0 group-hover:opacity-100 transition-opacity">
                              <button
                                on:click={() => copyMessage(message.content)}
                                class="p-1.5 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-md transition-colors border border-gray-200 dark:border-gray-600 shadow-sm"
                                title="Copy message"
                              >
                                <Copy size={14} class="text-gray-600 dark:text-gray-300" />
                              </button>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  {:else}
                    <!-- User Message -->
                    <div class="w-full py-2">
                      <div class="flex items-start space-x-4 justify-end">
                        <div class="flex-1 flex flex-col items-end">
                          <div class="flex items-center space-x-2 mb-3">
                            <span class="text-xs text-gray-500 dark:text-gray-400">
                              {formatTimestamp(message.timestamp)}
                              {#if message.edited}
                                <span class="ml-1">(edited)</span>
                              {/if}
                              {#if message.cancelled}
                                <span class="ml-1 text-orange-600 dark:text-orange-400 font-medium">(cancelled)</span>
                              {/if}
                            </span>
                            <span class="text-sm font-medium text-gray-900 dark:text-white">You</span>
                          </div>
                          
                          <div class="relative group max-w-[80%]">
                            {#if editingMessageId === message.id}
                              <div class="bg-gray-100 dark:bg-gray-700 rounded-2xl p-4 w-full">
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
                              <div class="{message.cancelled ? 'bg-gray-400 dark:bg-gray-600' : 'bg-blue-600'} text-white rounded-3xl px-5 py-3 {message.cancelled ? 'opacity-70' : ''}">
                                <div class="prose prose-sm max-w-none prose-invert">
                                  <pre class="whitespace-pre-wrap font-sans leading-relaxed bg-transparent border-none p-0 m-0">{message.content}</pre>
                                </div>
                              </div>
                              
                              <!-- Message Actions - positioned below the message -->
                              <div class="flex justify-end mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                <div class="flex items-center space-x-1">
                                  <button
                                    on:click={() => copyMessage(message.content)}
                                    class="p-1.5 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-md transition-colors border border-gray-200 dark:border-gray-600 shadow-sm"
                                    title="Copy message"
                                  >
                                    <Copy size={12} class="text-gray-600 dark:text-gray-300" />
                                  </button>
                                  
                                  <button
                                    on:click={() => startEditingMessage(message)}
                                    class="p-1.5 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-md transition-colors border border-gray-200 dark:border-gray-600 shadow-sm"
                                    title="Edit message"
                                  >
                                    <Edit3 size={12} class="text-gray-600 dark:text-gray-300" />
                                  </button>
                                </div>
                              </div>
                            {/if}
                          </div>
                        </div>
                        <div class="flex-shrink-0 w-8 h-8 bg-gradient-to-br from-blue-500 to-blue-600 rounded-full flex items-center justify-center">
                          <User size={16} class="text-white" />
                        </div>
                      </div>
                    </div>
                  {/if}
                </div>
              {/each}
          
              <!-- Loading indicator -->
              {#if isLoading}
                <div class="flex items-start space-x-4 py-6 animate-fadeIn">
                  <div class="flex-shrink-0 w-8 h-8 bg-gradient-to-br from-green-500 to-emerald-600 rounded-full flex items-center justify-center">
                    <Bot size={16} class="text-white" />
                  </div>
                  <div class="flex-1">
                    <div class="flex items-center space-x-2 mb-3">
                      <span class="text-sm font-medium text-gray-900 dark:text-white">
                        {serverStatus.model?.name || 'AI Assistant'}
                      </span>
                    </div>
                    <div class="bg-gray-100 dark:bg-gray-800 rounded-2xl px-4 py-3">
                      <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-2">
                          <div class="flex space-x-1">
                            <div class="w-2 h-2 bg-blue-500 rounded-full animate-bounce"></div>
                            <div class="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
                            <div class="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
                          </div>
                          <span class="text-sm text-gray-600 dark:text-gray-400">Thinking...</span>
                        </div>
                        <!-- Cancel button -->
                        {#if currentAbortController}
                          <button
                            on:click={cancelCurrentRequest}
                            class="p-1 text-gray-500 hover:text-red-600 dark:text-gray-400 dark:hover:text-red-400 transition-colors rounded"
                            title="Cancel request"
                          >
                            <Square size={14} class="fill-current" />
                          </button>
                        {/if}
                      </div>
                    </div>
                  </div>
                </div>
              {/if}
          
              <!-- Error message -->
              {#if error}
                <div class="flex items-start space-x-4 py-6 animate-fadeIn">
                  <div class="flex-shrink-0 w-8 h-8 bg-red-500 rounded-full flex items-center justify-center">
                    <AlertTriangle size={16} class="text-white" />
                  </div>
                  <div class="flex-1">
                    <div class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-2xl p-4">
                      <div class="text-red-600 dark:text-red-400 text-sm">
                        <strong>Error:</strong> {error}
                      </div>
                    </div>
                  </div>
                </div>
              {/if}
            {/if}
          </div>
          
          <!-- Input Area (Following the conversation) -->
          <div class="px-6 py-6 border-t border-gray-200 dark:border-gray-700">
            <div class="relative">
              <textarea
                bind:value={inputText}
                on:keydown={handleKeyDown}
                placeholder="Message {serverStatus.model?.name || 'AI'}..."
                class="w-full px-4 py-3 pr-20 border border-gray-300 dark:border-gray-600 rounded-3xl focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-all max-h-40"
                rows="1"
                style="min-height: 52px;"
                disabled={!serverStatus.canChat}
              ></textarea>
              
              <div class="absolute right-3 bottom-3 flex items-center space-x-2">
                <!-- Character counter -->
                {#if inputText.length > 0}
                  <span class="text-xs text-gray-400 dark:text-gray-500">
                    {inputText.length}
                  </span>
                {/if}
                
                <!-- Send button -->
                <button
                  on:click={sendMessage}
                  disabled={!inputText.trim() || isLoading || !serverStatus.canChat}
                  class="flex items-center justify-center w-9 h-9 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-full transition-all disabled:cursor-not-allowed shadow-sm"
                  title="Send message (Enter)"
                >
                  {#if isLoading}
                    <div class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  {:else}
                    <Send size={16} />
                  {/if}
                </button>
              </div>
            </div>
            
            <!-- Status and shortcuts -->
            <div class="flex items-center justify-between mt-3 text-xs text-gray-500 dark:text-gray-400">
              <div>
                Press <kbd class="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-700 rounded text-xs font-mono">Enter</kbd> to send • 
                <kbd class="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-700 rounded text-xs font-mono">Shift+Enter</kbd> for new line
              </div>
              <div class="flex items-center space-x-1">
                <div class="w-2 h-2 {serverStatus.canChat ? 'bg-green-500' : 'bg-red-500'} rounded-full {serverStatus.canChat ? 'animate-pulse' : ''}"></div>
                <span class="{serverStatus.canChat ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}">
                  {serverStatus.canChat ? 'Connected' : 'Disconnected'}
                </span>
              </div>
            </div>
          </div>
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
