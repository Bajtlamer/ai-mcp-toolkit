// Chat API service for communicating with the MCP server
export class ChatAPI {
  constructor() {
    this.baseUrl = 'http://localhost:8000';
    this.conversationContexts = new Map(); // Track conversation context
  }

  /**
   * Send a chat message to the AI model with conversation context
   */
  async sendMessage(message, conversationId, conversationHistory = []) {
    try {
      // Build context from conversation history (last 20 messages for efficiency)
      const recentHistory = conversationHistory.slice(-20);
      const context = this.buildContextPrompt(recentHistory);
      
      // Prepare the prompt with context and markdown instruction
      const markdownInstruction = "Please format your response using proper markdown syntax. Use \`\`\`language for code blocks, \`code\` for inline code, **bold** for emphasis, and proper headings with #.";
      const promptWithContext = context ? 
        `${context}\n\nHuman: ${message}\n\n${markdownInstruction}\n\nAssistant:` : 
        `Human: ${message}\n\n${markdownInstruction}\n\nAssistant:`;

      // Send request to MCP server's chat endpoint
      const response = await fetch(`${this.baseUrl}/chat/completions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          messages: [
            {
              role: 'user',
              content: promptWithContext
            }
          ],
          stream: false,
          model: await this.getActiveModel(), // Use the currently loaded model
          temperature: 0.7,
          max_tokens: 2000
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      // Extract the response content and timing metrics
      if (data.choices && data.choices.length > 0) {
        let content = data.choices[0].message.content.trim();
        const usage = data.usage || {};
        
        // Auto-format code blocks if not already formatted
        content = this.autoFormatCodeBlocks(content);
        
        // Return both content and metrics
        return {
          content,
          metrics: {
            totalTime: usage.total_duration || 0,
            tokensPerSecond: usage.tokens_per_second || 0,
            promptTokens: usage.prompt_tokens || 0,
            completionTokens: usage.completion_tokens || 0,
            totalTokens: usage.total_tokens || 0,
            promptEvalDuration: usage.prompt_eval_duration || 0,
            evalDuration: usage.eval_duration || 0
          }
        };
      } else {
        throw new Error('No response content received');
      }

    } catch (error) {
      console.error('Chat API error:', error);
      
      // Fallback to direct Ollama API if MCP server is not available
      try {
        return await this.fallbackToOllama(message, conversationHistory);
      } catch (fallbackError) {
        console.error('Fallback error:', fallbackError);
        throw new Error('Failed to get AI response. Please ensure the MCP server or Ollama is running.');
      }
    }
  }

  /**
   * Fallback to direct Ollama API
   */
  async fallbackToOllama(message, conversationHistory = []) {
    const recentHistory = conversationHistory.slice(-20);
    const context = this.buildContextPrompt(recentHistory);
    
    const promptWithContext = context ? 
      `${context}\n\nHuman: ${message}\n\nAssistant:` : 
      message;

    const response = await fetch('http://localhost:11434/api/generate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: await this.getActiveModel(),
        prompt: promptWithContext,
        stream: false,
        options: {
          temperature: 0.7,
          top_p: 0.9,
          max_tokens: 2000
        }
      }),
    });

    if (!response.ok) {
      throw new Error(`Ollama API error! status: ${response.status}`);
    }

    const data = await response.json();
    let content = data.response || 'No response received';
    
    // Auto-format code blocks if not already formatted
    content = this.autoFormatCodeBlocks(content);
    
    // Calculate basic metrics from Ollama response
    const promptEvalCount = data.prompt_eval_count || 0;
    const evalCount = data.eval_count || 0;
    const totalDuration = (data.total_duration || 0) / 1e9; // Convert to seconds
    const evalDuration = (data.eval_duration || 0) / 1e9;
    const tokensPerSecond = evalCount / evalDuration || 0;
    
    return {
      content,
      metrics: {
        totalTime: totalDuration,
        tokensPerSecond: Math.round(tokensPerSecond * 100) / 100,
        promptTokens: promptEvalCount,
        completionTokens: evalCount,
        totalTokens: promptEvalCount + evalCount,
        promptEvalDuration: (data.prompt_eval_duration || 0) / 1e9,
        evalDuration: evalDuration
      }
    };
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
   */
  async sendMessageStream(message, conversationId, onChunk, conversationHistory = []) {
    try {
      const recentHistory = conversationHistory.slice(-20);
      const context = this.buildContextPrompt(recentHistory);
      
      const promptWithContext = context ? 
        `${context}\n\nHuman: ${message}\n\nAssistant:` : 
        message;

      const response = await fetch('http://localhost:11434/api/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model: await this.getActiveModel(),
          prompt: promptWithContext,
          stream: true,
          options: {
            temperature: 0.7,
            top_p: 0.9,
            max_tokens: 2000
          }
        }),
      });

      if (!response.ok) {
        throw new Error(`Streaming API error! status: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let fullResponse = '';

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split('\n').filter(line => line.trim());

          for (const line of lines) {
            try {
              const data = JSON.parse(line);
              if (data.response) {
                fullResponse += data.response;
                onChunk(data.response);
              }
            } catch (parseError) {
              // Ignore parsing errors for incomplete JSON
            }
          }
        }
      } finally {
        reader.releaseLock();
      }

      return fullResponse;

    } catch (error) {
      console.error('Streaming error:', error);
      throw error;
    }
  }

  /**
   * Check if the MCP server is available
   */
  async isServerAvailable() {
    try {
      const response = await fetch(`${this.baseUrl}/health`, {
        method: 'GET',
        signal: AbortSignal.timeout(5000), // 5 second timeout
      });
      return response.ok;
    } catch (error) {
      return false;
    }
  }

  /**
   * Check if Ollama is available
   */
  async isOllamaAvailable() {
    try {
      const response = await fetch('http://localhost:11434/api/tags', {
        method: 'GET',
        signal: AbortSignal.timeout(5000),
      });
      return response.ok;
    } catch (error) {
      return false;
    }
  }

  /**
   * Get the currently active/loaded model from Ollama
   */
  async getActiveModel() {
    try {
      const response = await fetch('http://localhost:11434/api/ps', {
        method: 'GET',
        signal: AbortSignal.timeout(5000),
      });
      
      if (response.ok) {
        const data = await response.json();
        // Return the first loaded model, or fall back to a default
        if (data.models && data.models.length > 0) {
          return data.models[0].name;
        }
      }
    } catch (error) {
      console.warn('Could not get active model, using default:', error);
    }
    
    // Fallback to qwen2.5:7b if we can't detect the active model
    return 'qwen2.5:7b';
  }

  /**
   * Get information about the currently active model
   */
  async getActiveModelInfo() {
    try {
      const response = await fetch('http://localhost:11434/api/ps', {
        method: 'GET',
        signal: AbortSignal.timeout(5000),
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.models && data.models.length > 0) {
          const model = data.models[0];
          return {
            name: model.name,
            size: model.size,
            processor: model.processor || 'Unknown',
            context: model.context || 0,
            id: model.name // For display purposes
          };
        }
      }
    } catch (error) {
      console.warn('Could not get active model info:', error);
    }
    
    return {
      name: 'qwen2.5:7b',
      size: 'Unknown',
      processor: 'Unknown',
      context: 4096,
      id: 'qwen2.5:7b'
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
      const response = await fetch(`${this.baseUrl}/tools/execute`, {
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