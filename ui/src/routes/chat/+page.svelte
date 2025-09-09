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
    const lowerInput = input.toLowerCase();
    
    try {
      // Parse the user input and determine what action to take
      const toolRequest = parseUserInput(input, lowerInput);
      
      if (toolRequest) {
        const response = await fetch('http://localhost:8000/tools/execute', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            name: toolRequest.tool,
            arguments: toolRequest.arguments
          })
        });
        
        const result = await response.json();
        
        if (result.success) {
          return formatToolResponse(toolRequest.tool, toolRequest.text, result.result);
        } else {
          return `I encountered an error while processing your request: ${result.error || 'Unknown error'}`;
        }
      }
      
      // Handle greetings
      if (lowerInput.includes('hello') || lowerInput.includes('hi') || lowerInput.includes('hey')) {
        return 'Hello! I\'m your AI assistant with access to powerful text processing tools. I can:\n\n• **Clean text** - Remove extra spaces, fix formatting\n• **Analyze sentiment** - Detect emotions and tone\n• **Detect language** - Identify what language text is in\n• **Remove diacritics** - Strip accents and marks (like café → cafe)\n• **Check grammar** - Fix spelling and grammar errors\n• **Summarize text** - Create concise summaries\n• **Analyze text** - Get detailed statistics\n• **Anonymize text** - Remove sensitive information\n\nJust tell me what you\'d like me to do with your text!';
      }
      
      // Default response - try to be helpful
      return `I\'m not sure exactly what you want me to do with "${input}".\n\nI can help you with text processing tasks like:\n\n• **"Clean this text: [your text]"**\n• **"Analyze sentiment: [your text]"**\n• **"Remove diacritics from: [your text]"**\n• **"Detect language: [your text]"**\n• **"Summarize: [your text]"**\n• **"Check grammar: [your text]"**\n• **"Anonymize: [your text]"**\n\nTry one of these formats with your text!`;
      
    } catch (error) {
      console.error('Error processing request:', error);
      return 'I\'m sorry, I encountered an error processing your request. Please make sure the MCP server is running and try again.';
    }
  }
  
  function parseUserInput(input, lowerInput) {
    // Extract text after common command patterns
    let text = null;
    let tool = null;
    
    // Remove diacritics patterns
    if (lowerInput.includes('remove diacritic') || lowerInput.includes('remove accent') || lowerInput.includes('diacritic')) {
      text = extractTextAfterPattern(input, /remove diacritics? from:?\s*/i) ||
             extractTextAfterPattern(input, /remove accents? from:?\s*/i) ||
             extractTextAfterPattern(input, /diacritics?:?\s*/i) ||
             extractQuotedText(input);
      tool = 'remove_diacritics';
    }
    
    // Sentiment analysis patterns
    else if (lowerInput.includes('sentiment') || lowerInput.includes('emotion') || lowerInput.includes('analyze')) {
      text = extractTextAfterPattern(input, /analyze sentiment:?\s*/i) ||
             extractTextAfterPattern(input, /sentiment:?\s*/i) ||
             extractQuotedText(input);
      tool = 'analyze_sentiment';
    }
    
    // Language detection patterns
    else if (lowerInput.includes('detect language') || lowerInput.includes('language') || lowerInput.includes('detect')) {
      text = extractTextAfterPattern(input, /detect language:?\s*/i) ||
             extractTextAfterPattern(input, /language:?\s*/i) ||
             extractQuotedText(input);
      tool = 'detect_language';
    }
    
    // Text cleaning patterns
    else if (lowerInput.includes('clean') || lowerInput.includes('messy')) {
      text = extractTextAfterPattern(input, /clean:?\s*/i) ||
             extractTextAfterPattern(input, /clean this:?\s*/i) ||
             extractQuotedText(input);
      tool = 'clean_text';
    }
    
    // Grammar checking patterns
    else if (lowerInput.includes('grammar') || lowerInput.includes('check grammar') || lowerInput.includes('correct')) {
      text = extractTextAfterPattern(input, /check grammar:?\s*/i) ||
             extractTextAfterPattern(input, /grammar:?\s*/i) ||
             extractTextAfterPattern(input, /correct:?\s*/i) ||
             extractQuotedText(input);
      tool = 'check_grammar';
    }
    
    // Summarization patterns
    else if (lowerInput.includes('summarize') || lowerInput.includes('summary')) {
      text = extractTextAfterPattern(input, /summarize:?\s*/i) ||
             extractTextAfterPattern(input, /summary:?\s*/i) ||
             extractQuotedText(input);
      tool = 'summarize_text';
    }
    
    if (text && tool) {
      return {
        tool: tool,
        text: text,
        arguments: { text: text }
      };
    }
    
    return null;
  }
  
  function extractTextAfterPattern(input, pattern) {
    const match = input.match(pattern);
    if (match) {
      let text = input.substring(match.index + match[0].length).trim();
      // Remove quotes if present
      text = text.replace(/^['"]|['"]$/g, '');
      return text || null;
    }
    return null;
  }
  
  function extractQuotedText(input) {
    // Extract text between single or double quotes
    const singleQuoteMatch = input.match(/'([^']+)'/);  
    const doubleQuoteMatch = input.match(/"([^"]+)"/);  
    
    if (singleQuoteMatch) return singleQuoteMatch[1];
    if (doubleQuoteMatch) return doubleQuoteMatch[1];
    
    return null;
  }
  
  function formatToolResponse(tool, originalText, result) {
    switch (tool) {
      case 'remove_diacritics':
        return `I removed the diacritics from your text:\n\n**Original:** ${originalText}\n**Result:** ${result}`;
      
      case 'analyze_sentiment':
        try {
          const parsed = JSON.parse(result);
          const sentiment = parsed.overall_sentiment || 'unknown';
          const confidence = parsed.confidence ? (parsed.confidence * 100).toFixed(1) : 'unknown';
          return `I analyzed the sentiment of your text:\n\n**Text:** ${originalText}\n**Sentiment:** ${sentiment.charAt(0).toUpperCase() + sentiment.slice(1)}\n**Confidence:** ${confidence}%${parsed.key_indicators ? '\n**Key indicators:** ' + parsed.key_indicators.join(', ') : ''}`;
        } catch {
          return `I analyzed your text sentiment:\n\n**Text:** ${originalText}\n**Analysis:** ${result}`;
        }
      
      case 'detect_language':
        try {
          const parsed = JSON.parse(result);
          const language = parsed.detected_language || 'unknown';
          const confidence = parsed.confidence_score ? (parsed.confidence_score * 100).toFixed(1) : 'unknown';
          return `I detected the language of your text:\n\n**Text:** ${originalText}\n**Language:** ${language}\n**Confidence:** ${confidence}%`;
        } catch {
          return `I detected your text language:\n\n**Text:** ${originalText}\n**Result:** ${result}`;
        }
      
      case 'clean_text':
        return `I cleaned your text:\n\n**Original:** ${originalText}\n**Cleaned:** ${result}`;
      
      case 'check_grammar':
        return `I checked the grammar of your text:\n\n**Original:** ${originalText}\n**Corrected:** ${result}`;
      
      case 'summarize_text':
        return `I created a summary of your text:\n\n**Original text:** ${originalText.substring(0, 100)}${originalText.length > 100 ? '...' : ''}\n\n**Summary:** ${result}`;
      
      default:
        return `Here's the result:\n\n**Original:** ${originalText}\n**Result:** ${result}`;
    }
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

<div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
  <!-- Header -->
  <div class="mb-8">
    <div class="flex items-center space-x-3 mb-4">
      <div class="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
        <MessageSquare size={24} class="text-white" />
      </div>
      <div>
        <h1 class="text-3xl font-bold text-gray-900 dark:text-white">AI Chat</h1>
        <p class="text-gray-600 dark:text-gray-400">Intelligent conversation with access to powerful text processing tools</p>
      </div>
    </div>
  </div>

  <!-- Conversation Starters (shown when no messages) -->
  {#if messages.length <= 1}
    <div class="mb-6">
      <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-3">Quick Start Examples</h2>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
        {#each conversationStarters as starter}
          <button
            on:click={() => useStarter(starter)}
            class="p-4 text-left text-sm bg-gray-50 dark:bg-gray-800 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/30 hover:border-blue-200 dark:hover:border-blue-700 border border-gray-200 dark:border-gray-700 transition-all duration-200 group"
          >
            <div class="flex items-start space-x-3">
              <div class="w-6 h-6 bg-blue-100 dark:bg-blue-900/50 rounded-lg flex items-center justify-center group-hover:bg-blue-200 dark:group-hover:bg-blue-800/70 transition-colors">
                <MessageSquare size={14} class="text-blue-600 dark:text-blue-400" />
              </div>
              <span class="text-gray-700 dark:text-gray-300 group-hover:text-blue-700 dark:group-hover:text-blue-300 transition-colors">{starter}</span>
            </div>
          </button>
        {/each}
      </div>
    </div>
  {/if}

  <!-- Chat Container -->
  <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-sm mb-6">
    <!-- Chat Header -->
    <div class="border-b border-gray-200 dark:border-gray-700 p-4">
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-2">
          <div class="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
          <span class="text-sm font-medium text-gray-700 dark:text-gray-300">AI Assistant Active</span>
        </div>
        <div class="flex space-x-2">
          <button
            on:click={downloadChat}
            class="flex items-center px-3 py-1.5 text-xs bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-md transition-colors"
            title="Download conversation"
          >
            <Download size={14} class="mr-1" />
            Export
          </button>
          <button
            on:click={clearChat}
            class="flex items-center px-3 py-1.5 text-xs bg-red-100 dark:bg-red-900/50 hover:bg-red-200 dark:hover:bg-red-800/70 text-red-700 dark:text-red-300 rounded-md transition-colors"
            title="Clear conversation"
          >
            <Trash2 size={14} class="mr-1" />
            Clear
          </button>
        </div>
      </div>
    </div>
    
    <!-- Messages -->
    <div 
      bind:this={chatContainer}
      class="h-96 overflow-y-auto p-4 space-y-4 bg-gray-50 dark:bg-gray-900/50 chat-scroll"
    >
      {#each messages as message (message.id)}
        <div class="flex {message.type === 'user' ? 'justify-end' : 'justify-start'} animate-fadeIn">
          <div class="flex items-start space-x-3 max-w-4xl w-full">
            {#if message.type === 'assistant'}
              <div class="flex-shrink-0 w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
                <Bot size={18} class="text-white" />
              </div>
            {/if}
            
            <div class="flex-1 {message.type === 'user' ? 'flex justify-end' : ''}">
              <div class="{message.type === 'user' ? 'max-w-lg' : 'w-full'}">
                <div class="flex items-center space-x-2 mb-2 {message.type === 'user' ? 'justify-end' : ''}">
                  <span class="text-xs font-medium {message.type === 'user' ? 'text-blue-600 dark:text-blue-400' : 'text-purple-600 dark:text-purple-400'}">
                    {message.type === 'user' ? 'You' : 'AI Assistant'}
                  </span>
                  <span class="text-xs text-gray-500 dark:text-gray-400">
                    {formatTimestamp(message.timestamp)}
                  </span>
                </div>
                
                <div class="relative group">
                  <div class="{message.type === 'user' 
                    ? 'bg-gradient-to-r from-blue-600 to-blue-500 text-white shadow-lg' 
                    : 'bg-white dark:bg-gray-800 text-gray-900 dark:text-white border border-gray-200 dark:border-gray-600 shadow-sm'
                  } p-4 rounded-lg {message.type === 'user' ? 'rounded-br-sm' : 'rounded-tl-sm'}">
                    <div class="prose prose-sm max-w-none {message.type === 'user' ? 'prose-invert' : 'dark:prose-invert'}">
                      <pre class="whitespace-pre-wrap text-sm font-sans leading-relaxed">{message.content}</pre>
                    </div>
                  </div>
                  
                  <!-- Copy button -->
                  <button
                    on:click={() => copyMessage(message.content)}
                    class="absolute top-2 right-2 opacity-0 group-hover:opacity-100 p-1.5 {message.type === 'user' ? 'bg-blue-700/50 hover:bg-blue-700/70' : 'bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600'} rounded-md transition-all duration-200"
                    title="Copy message"
                  >
                    <Copy size={12} class="{message.type === 'user' ? 'text-white' : 'text-gray-600 dark:text-gray-300'}" />
                  </button>
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
                <span class="text-xs font-medium text-purple-600 dark:text-purple-400">AI Assistant</span>
              </div>
              <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 p-4 rounded-lg rounded-tl-sm shadow-sm">
                <div class="flex items-center space-x-3">
                  <div class="flex space-x-1">
                    <div class="w-2.5 h-2.5 bg-blue-400 rounded-full animate-bounce"></div>
                    <div class="w-2.5 h-2.5 bg-purple-400 rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
                    <div class="w-2.5 h-2.5 bg-blue-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
                  </div>
                  <span class="text-sm text-gray-500 dark:text-gray-400">AI is processing your request...</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      {/if}
      
      <!-- Error message -->
      {#if error}
        <div class="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg shadow-sm animate-fadeIn">
          <div class="flex items-center space-x-2">
            <div class="w-5 h-5 bg-red-500 rounded-full flex items-center justify-center">
              <span class="text-white text-xs font-bold">!</span>
            </div>
            <div class="text-red-600 dark:text-red-400 text-sm">
              <strong>Connection Error:</strong> {error}
            </div>
          </div>
        </div>
      {/if}
    </div>
    
    <!-- Input Section -->
    <div class="border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-4">
      <div class="flex items-start space-x-3">
        <div class="flex-1 relative">
          <textarea
            bind:value={inputText}
            on:keydown={handleKeyDown}
            placeholder="Ask me to analyze sentiment, clean text, detect language, or use any other tool..."
            class="w-full px-4 py-3 pr-12 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-all"
            rows="1"
            style="min-height: 48px; max-height: 120px;"
          ></textarea>
          
          <!-- Character counter -->
          <div class="absolute bottom-2 right-2 text-xs text-gray-400 dark:text-gray-500">
            {inputText.length}
          </div>
        </div>
        
        <button
          on:click={sendMessage}
          disabled={!inputText.trim() || isLoading}
          class="flex items-center justify-center w-12 h-12 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 disabled:from-gray-400 disabled:to-gray-400 text-white rounded-lg transition-all duration-200 transform hover:scale-105 disabled:hover:scale-100 shadow-lg flex-shrink-0"
          title="Send message (Enter)"
          style="height: 48px;"
        >
          {#if isLoading}
            <div class="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
          {:else}
            <Send size={18} />
          {/if}
        </button>
      </div>
      
      <!-- Keyboard shortcut hint -->
      <div class="mt-2 text-xs text-gray-500 dark:text-gray-400 text-center">
        Press <kbd class="px-1.5 py-0.5 bg-gray-200 dark:bg-gray-700 rounded text-xs font-mono">Enter</kbd> to send • <kbd class="px-1.5 py-0.5 bg-gray-200 dark:bg-gray-700 rounded text-xs font-mono">Shift + Enter</kbd> for new line
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
</style>
