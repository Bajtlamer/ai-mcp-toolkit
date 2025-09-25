// Chat API service for communicating with the MCP server
export class ChatAPI {
  constructor() {
    // Use relative URLs to work with any server IP address
    this.baseUrl = '';
    this.conversationContexts = new Map(); // Track conversation context
  }

  /**
   * Send a chat message to the AI model with conversation context
   */
  async sendMessage(message, conversationId, conversationHistory = []) {
    try {
      // Add markdown instruction to the message
      const markdownInstruction = "Please format your response using proper markdown syntax. Use \`\`\`language for code blocks, \`code\` for inline code, **bold** for emphasis, and proper headings with #.";
      const messageWithInstruction = `${message}\n\n${markdownInstruction}`;
      
      // Use the new conversation API endpoint that handles context properly
      const response = await fetch('/api/chat/conversation', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: messageWithInstruction,
          conversationHistory: conversationHistory,
          model: await this.getActiveModel(),
          temperature: 0.7,
          max_tokens: 2000
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.success) {
        // Auto-format code blocks if not already formatted
        const formattedContent = this.autoFormatCodeBlocks(data.content);
        
        return {
          content: formattedContent,
          metrics: data.metrics || {}
        };
      } else {
        throw new Error(data.error || 'Failed to get AI response');
      }

    } catch (error) {
      // Remove the fallback to direct Ollama - always go through server
      throw new Error(`Failed to get AI response: ${error.message}`);
    }
  }


  /**
   * Build context prompt from conversation history
   */
  buildContextPrompt(conversationHistory) {
    if (!conversationHistory || conversationHistory.length === 0) {
      return '';
    }

    // Filter out system messages and build conversation context
    const contextMessages = conversationHistory
      .filter(msg => msg.type === 'user' || msg.type === 'assistant')
      .slice(-10) // Keep last 10 exchanges
      .map(msg => {
        const role = msg.type === 'user' ? 'Human' : 'Assistant';
        // Ensure content is a string
        const content = typeof msg.content === 'string' ? msg.content : JSON.stringify(msg.content);
        return `${role}: ${content}`;
      });

    if (contextMessages.length === 0) {
      return '';
    }

    return `Previous conversation context:\n${contextMessages.join('\n\n')}\n\n---\n`;
  }

  /**
   * Auto-format code blocks in plain text responses
   */
  autoFormatCodeBlocks(content) {
    // If already has code blocks, return as is
    if (content.includes('```')) {
      return content;
    }

    // Pattern to detect command-line commands or code snippets
    const patterns = [
      // npm/yarn commands
      {
        regex: /^(npm|yarn|pnpm)\s+[\w\s\-@/.:]+$/gm,
        language: 'bash'
      },
      // Angular CLI commands
      {
        regex: /^ng\s+[\w\s\-@/.:]+$/gm,
        language: 'bash'
      },
      // Other shell commands
      {
        regex: /^(cd|mkdir|ls|cp|mv|rm|git)\s+[\w\s\-@/.:\"']+$/gm,
        language: 'bash'
      },
      // Code blocks with imports/exports (JavaScript/TypeScript)
      {
        regex: /(import\s+.+from\s+['"].+['"];?|export\s+(const|class|interface|type)\s+\w+)/gm,
        language: 'typescript'
      },
      // Function definitions
      {
        regex: /(function\s+\w+\s*\(|const\s+\w+\s*=\s*\(|def\s+\w+\s*\(|class\s+\w+)/gm,
        language: 'auto'
      }
    ];

    let formattedContent = content;

    patterns.forEach(({ regex, language }) => {
      const matches = [...content.matchAll(regex)];
      matches.forEach(match => {
        const codeSnippet = match[0];
        const wrappedCode = `\`\`\`${language}\n${codeSnippet}\n\`\`\``;
        formattedContent = formattedContent.replace(codeSnippet, wrappedCode);
      });
    });

    // Also wrap standalone lines that look like code (indented lines)
    const lines = formattedContent.split('\n');
    const processedLines = [];
    let inCodeBlock = false;
    let codeBlockLines = [];
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      const isCodeLine = /^\s{2,}[\w\s\[\]{}().,;:="'`\-+*/=<>!&|]+$/.test(line) && 
                        !line.trim().startsWith('//') && 
                        !line.trim().startsWith('*') &&
                        line.trim().length > 0;
      
      if (isCodeLine && !inCodeBlock && !line.includes('```')) {
        inCodeBlock = true;
        codeBlockLines = [line];
      } else if (isCodeLine && inCodeBlock) {
        codeBlockLines.push(line);
      } else if (!isCodeLine && inCodeBlock) {
        // End of code block
        if (codeBlockLines.length > 0) {
          processedLines.push('```');
          processedLines.push(...codeBlockLines);
          processedLines.push('```');
        }
        inCodeBlock = false;
        codeBlockLines = [];
        processedLines.push(line);
      } else {
        processedLines.push(line);
      }
    }

    // Handle case where code block is at the end
    if (inCodeBlock && codeBlockLines.length > 0) {
      processedLines.push('```');
      processedLines.push(...codeBlockLines);
      processedLines.push('```');
    }

    return processedLines.join('\n');
  }

  /**
   * Send a streaming message (for future implementation)
   * Note: Streaming is not yet implemented in the server API
   */
  async sendMessageStream(message, conversationId, onChunk, conversationHistory = []) {
    // For now, fall back to regular message sending
    // TODO: Implement streaming in server API
    const response = await this.sendMessage(message, conversationId, conversationHistory);
    
    // Simulate streaming by calling onChunk with the full response
    if (onChunk) {
      onChunk(response.content);
    }
    
    return response.content;
  }

  /**
   * Check if the MCP server is available
   */
  async isServerAvailable() {
    try {
      // Check if our backend server is available via the UI API proxy
      const response = await fetch('/api/gpu/health', {
        method: 'GET',
        signal: AbortSignal.timeout(5000), // 5 second timeout
      });
      return response.ok;
    } catch (error) {
      return false;
    }
  }

  /**
   * Check if Ollama is available (via server)
   */
  async isOllamaAvailable() {
    try {
      // Check Ollama availability through our server's GPU health endpoint
      const response = await fetch('/api/gpu/health', {
        method: 'GET',
        signal: AbortSignal.timeout(5000),
      });
      
      if (response.ok) {
        const data = await response.json();
        // If we get a response with model info, Ollama is working
        return data.ollama_model || false;
      }
      return false;
    } catch (error) {
      return false;
    }
  }

  /**
   * Get the currently active/loaded model from GPU health API
   */
  async getActiveModel() {
    try {
      // Get model from our server's GPU health API
      const response = await fetch('/api/gpu/health', {
        method: 'GET',
        signal: AbortSignal.timeout(5000),
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.ollama_model) {
          return data.ollama_model;
        }
      }
    } catch (error) {
      // Silently fallback to default
    }
    
    // Final fallback - use the default model from configuration
    return 'qwen2.5:14b';
  }

  /**
   * Get information about the currently active model
   */
  async getActiveModelInfo() {
    try {
      // Get model info from our server's GPU health API
      const response = await fetch('/api/gpu/health', {
        method: 'GET',
        signal: AbortSignal.timeout(5000),
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.ollama_model) {
          return {
            name: data.ollama_model,
            size: 'Unknown',
            processor: data.ollama_gpu_accelerated ? 'GPU' : 'CPU',
            context: 4096,
            id: data.ollama_model
          };
        }
      }
    } catch (error) {
      // Silently fallback to default
    }
    
    // Fallback to default model info
    return {
      name: 'qwen2.5:14b',
      size: 'Unknown',
      processor: 'Unknown',
      context: 4096,
      id: 'qwen2.5:14b'
    };
  }

  /**
   * Get server status information
   */
  async getServerStatus() {
    const mcpAvailable = await this.isServerAvailable();
    const ollamaAvailable = await this.isOllamaAvailable();
    
    // Get active model info if Ollama is available
    let modelInfo = null;
    if (ollamaAvailable) {
      modelInfo = await this.getActiveModelInfo();
    }
    
    return {
      mcp: mcpAvailable,
      ollama: ollamaAvailable,
      canChat: mcpAvailable || ollamaAvailable,
      model: modelInfo
    };
  }

  /**
   * Process text using MCP tools (legacy support)
   */
  async processWithTool(toolName, text) {
    try {
      // Use relative URL to work with any server IP address
      // This will be proxied to the backend server
      const response = await fetch('/api/tools/execute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: toolName,
          arguments: { text: text }
        }),
      });

      if (!response.ok) {
        throw new Error(`Tool execution error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Tool execution error:', error);
      throw error;
    }
  }
}

// Create a singleton instance
export const chatAPI = new ChatAPI();