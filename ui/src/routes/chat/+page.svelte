<script>
  import { onMount, afterUpdate } from 'svelte';
  import { MessageSquare, Send, Bot, User, Trash2, Download, Copy } from 'lucide-svelte';

  let messages = [];
  let inputText = '';
  let isLoading = false;
  let chatContainer;
  let error = null;

  // Sample conversation starters
  const conversationStarters = [
    "Analyze the sentiment of this text: 'I love sunny days!'",
    "Clean this messy text: 'Hello!!!   This    is   very   messy    text....'",
    "Summarize this: 'Artificial intelligence is transforming industries...'",
    "Detect the language: 'Bonjour, comment allez-vous?'",
    "Remove diacritics from: 'Café français avec crème brûlée'",
    "Check grammar: 'This are incorrect grammar that need fixing'"
  ];

  // Auto-scroll to bottom when new messages arrive
  afterUpdate(() => {
    if (chatContainer) {
      chatContainer.scrollTop = chatContainer.scrollHeight;
    }
  });

  onMount(() => {
    // Add welcome message
    messages = [{
      id: Date.now(),
      type: 'assistant',
      content: 'Hello! I\'m your AI assistant with access to powerful text processing tools. I can help you clean text, analyze sentiment, detect languages, check grammar, and much more. What would you like me to help you with?',
      timestamp: new Date()
    }];
  });

  async function sendMessage() {
    if (!inputText.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputText.trim(),
      timestamp: new Date()
    };

    messages = [...messages, userMessage];
    const userInput = inputText.trim();
    inputText = '';
    isLoading = true;
    error = null;

    try {
      // For this demo, we'll simulate AI responses based on keywords
      // In a real implementation, this would connect to your chat endpoint
      const response = await simulateAIResponse(userInput);
      
      const assistantMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: response,
        timestamp: new Date()
      };

      messages = [...messages, assistantMessage];
    } catch (err) {
      error = 'Failed to get AI response. Make sure the MCP server is running.';
      console.error('Chat error:', err);
    } finally {
      isLoading = false;
    }
  }

  async function simulateAIResponse(input) {
    // This is a simulation - in real implementation, you'd send to your chat API
    const lowerInput = input.toLowerCase();
    
    if (lowerInput.includes('clean') || lowerInput.includes('messy')) {
      // Simulate text cleaning
      try {
        const response = await fetch('http://localhost:8000/tools/execute', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            name: 'clean_text',
            arguments: { text: input }
          })
        });
        const result = await response.json();
        return result.success ? `Here's the cleaned text:\n\n${result.result}` : 'I had trouble cleaning that text. Please try again.';
      } catch (err) {
        return 'I can help you clean text! Try asking me to clean some messy text.';
      }
    }
    
    if (lowerInput.includes('sentiment') || lowerInput.includes('emotion')) {
      return 'I can analyze the sentiment of any text! Try sending me some text with "analyze sentiment:" followed by the text you want me to analyze.';
    }
    
    if (lowerInput.includes('language') || lowerInput.includes('detect')) {
      return 'I can detect the language of any text! Just send me some text and ask me to detect its language.';
    }
    
    if (lowerInput.includes('grammar') || lowerInput.includes('check')) {
      return 'I can check and correct grammar! Send me some text with grammar issues and I\'ll fix it for you.';
    }
    
    if (lowerInput.includes('summarize') || lowerInput.includes('summary')) {
      return 'I can create summaries of long texts! Send me a long piece of text and ask me to summarize it.';
    }
    
    if (lowerInput.includes('diacritic') || lowerInput.includes('accent')) {
      return 'I can remove diacritical marks and accents from text! Try sending me text with accents like "café" or "naïve".';
    }
    
    if (lowerInput.includes('hello') || lowerInput.includes('hi') || lowerInput.includes('hey')) {
      return 'Hello! I\'m here to help you with various text processing tasks. I can clean text, analyze sentiment, detect languages, check grammar, create summaries, and remove diacritics. What would you like to try?';
    }
    
    // Default response
    return `I understand you're asking about: "${input}"\n\nI have access to these text processing tools:\n\n• **Text Cleaner** - Clean and normalize messy text\n• **Sentiment Analyzer** - Analyze emotional tone\n• **Language Detector** - Identify text language\n• **Grammar Checker** - Fix grammar and spelling\n• **Text Summarizer** - Create concise summaries\n• **Diacritic Remover** - Remove accents and marks\n• **Text Analyzer** - Detailed text statistics\n• **Text Anonymizer** - Remove sensitive information\n\nTry asking me to use any of these tools with your text!`;
  }

  function useStarter(starter) {
    inputText = starter;
  }

  function clearChat() {
    messages = [{
      id: Date.now(),
      type: 'assistant',
      content: 'Chat cleared! How can I help you today?',
      timestamp: new Date()
    }];
  }

  function copyMessage(content) {
    navigator.clipboard.writeText(content);
  }

  function downloadChat() {
    const chatContent = messages.map(m => 
      `[${m.timestamp.toLocaleTimeString()}] ${m.type.toUpperCase()}: ${m.content}`
    ).join('\n\n');
    
    const blob = new Blob([chatContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'ai_chat_conversation.txt';
    a.click();
    URL.revokeObjectURL(url);
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

<div class="flex flex-col h-screen max-w-4xl mx-auto">
  <!-- Header -->
  <div class="flex-shrink-0 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-4">
    <div class="flex items-center justify-between">
      <div class="flex items-center space-x-3">
        <div class="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
          <MessageSquare size={20} class="text-white" />
        </div>
        <div>
          <h1 class="text-xl font-semibold text-gray-900 dark:text-white">AI Chat</h1>
          <p class="text-sm text-gray-500 dark:text-gray-400">Chat with AI using text processing tools</p>
        </div>
      </div>
      
      <div class="flex space-x-2">
        <button
          on:click={downloadChat}
          class="flex items-center px-3 py-2 text-sm bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-lg transition-colors"
          title="Download conversation"
        >
          <Download size={16} class="mr-1" />
          Export
        </button>
        <button
          on:click={clearChat}
          class="flex items-center px-3 py-2 text-sm bg-red-100 dark:bg-red-900 hover:bg-red-200 dark:hover:bg-red-800 text-red-700 dark:text-red-300 rounded-lg transition-colors"
          title="Clear conversation"
        >
          <Trash2 size={16} class="mr-1" />
          Clear
        </button>
      </div>
    </div>
  </div>

  <!-- Conversation Starters (shown when no messages) -->
  {#if messages.length <= 1}
    <div class="flex-shrink-0 p-4 bg-gray-50 dark:bg-gray-900">
      <h3 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">Try asking me to:</h3>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
        {#each conversationStarters as starter}
          <button
            on:click={() => useStarter(starter)}
            class="p-2 text-left text-sm bg-white dark:bg-gray-800 hover:bg-blue-50 dark:hover:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg transition-colors"
          >
            {starter}
          </button>
        {/each}
      </div>
    </div>
  {/if}

  <!-- Messages -->
  <div 
    bind:this={chatContainer}
    class="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50 dark:bg-gray-900"
  >
    {#each messages as message (message.id)}
      <div class="flex {message.type === 'user' ? 'justify-end' : 'justify-start'}">
        <div class="flex items-start space-x-3 max-w-3xl">
          {#if message.type === 'assistant'}
            <div class="flex-shrink-0 w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
              <Bot size={16} class="text-white" />
            </div>
          {/if}
          
          <div class="flex-1">
            <div class="flex items-center space-x-2 mb-1">
              <span class="text-sm font-medium {message.type === 'user' ? 'text-blue-600 dark:text-blue-400' : 'text-purple-600 dark:text-purple-400'}">
                {message.type === 'user' ? 'You' : 'AI Assistant'}
              </span>
              <span class="text-xs text-gray-500 dark:text-gray-400">
                {formatTimestamp(message.timestamp)}
              </span>
            </div>
            
            <div class="relative group">
              <div class="{message.type === 'user' 
                ? 'bg-blue-500 text-white' 
                : 'bg-white dark:bg-gray-800 text-gray-900 dark:text-white border border-gray-200 dark:border-gray-600'
              } p-3 rounded-lg shadow-sm">
                <pre class="whitespace-pre-wrap text-sm font-sans">{message.content}</pre>
              </div>
              
              <!-- Copy button -->
              <button
                on:click={() => copyMessage(message.content)}
                class="absolute top-2 right-2 opacity-0 group-hover:opacity-100 p-1 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded transition-all"
                title="Copy message"
              >
                <Copy size={14} />
              </button>
            </div>
          </div>
          
          {#if message.type === 'user'}
            <div class="flex-shrink-0 w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
              <User size={16} class="text-white" />
            </div>
          {/if}
        </div>
      </div>
    {/each}
    
    <!-- Loading indicator -->
    {#if isLoading}
      <div class="flex justify-start">
        <div class="flex items-start space-x-3 max-w-3xl">
          <div class="flex-shrink-0 w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
            <Bot size={16} class="text-white" />
          </div>
          <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 p-3 rounded-lg shadow-sm">
            <div class="flex items-center space-x-2">
              <div class="flex space-x-1">
                <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
                <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
              </div>
              <span class="text-sm text-gray-500 dark:text-gray-400">AI is thinking...</span>
            </div>
          </div>
        </div>
      </div>
    {/if}
    
    <!-- Error message -->
    {#if error}
      <div class="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
        <div class="text-red-600 dark:text-red-400 text-sm">
          <strong>Error:</strong> {error}
        </div>
      </div>
    {/if}
  </div>

  <!-- Input -->
  <div class="flex-shrink-0 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-4">
    <div class="flex space-x-3">
      <div class="flex-1">
        <textarea
          bind:value={inputText}
          on:keydown={handleKeyDown}
          placeholder="Type your message here... (Press Enter to send, Shift+Enter for new line)"
          class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
          rows="1"
          style="min-height: 38px; max-height: 120px;"
        ></textarea>
      </div>
      
      <button
        on:click={sendMessage}
        disabled={!inputText.trim() || isLoading}
        class="flex items-center justify-center px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-medium rounded-lg transition-colors"
      >
        {#if isLoading}
          <div class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
        {:else}
          <Send size={16} />
        {/if}
      </button>
    </div>
  </div>
</div>

<style>
  /* Auto-resize textarea */
  textarea {
    field-sizing: content;
  }
</style>
