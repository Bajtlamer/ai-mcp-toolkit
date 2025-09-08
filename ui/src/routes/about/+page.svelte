<script>
  import { Info, Github, ExternalLink, Star, Heart, Zap } from 'lucide-svelte';

  const features = [
    {
      icon: Zap,
      title: 'Powerful AI Agents',
      description: '8 specialized AI agents for comprehensive text processing tasks.'
    },
    {
      icon: Star,
      title: 'MCP Protocol',
      description: 'Built on the Model Context Protocol standard for seamless integration.'
    },
    {
      icon: Heart,
      title: 'Privacy First',
      description: 'All processing happens locally - your data never leaves your machine.'
    }
  ];

  const agents = [
    { name: 'Text Cleaner', description: 'Clean and normalize messy text' },
    { name: 'Diacritic Remover', description: 'Remove accents and diacritical marks' },
    { name: 'Text Analyzer', description: 'Comprehensive text statistics and analysis' },
    { name: 'Grammar Checker', description: 'Fix grammar, spelling, and style issues' },
    { name: 'Text Summarizer', description: 'Generate concise summaries' },
    { name: 'Language Detector', description: 'Identify text language automatically' },
    { name: 'Sentiment Analyzer', description: 'Analyze emotional tone and sentiment' },
    { name: 'Text Anonymizer', description: 'Remove sensitive information for privacy' }
  ];

  const techStack = [
    { name: 'Backend', tech: 'Python, FastAPI, MCP Protocol' },
    { name: 'Frontend', tech: 'SvelteKit, TailwindCSS, Vite' },
    { name: 'AI Engine', tech: 'Ollama, Llama 3.2, Local Models' },
    { name: 'Architecture', tech: 'RESTful API, WebSocket Support' }
  ];

  function openGitHub() {
    // In a real implementation, this would open the actual GitHub repo
    window.open('https://github.com/yourusername/ai-mcp-toolkit', '_blank');
  }

  function openDocumentation() {
    // In a real implementation, this would open the documentation
    window.open('/docs', '_blank');
  }
</script>

<svelte:head>
  <title>About - AI MCP Toolkit</title>
</svelte:head>

<div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
  <!-- Header -->
  <div class="text-center mb-12">
    <div class="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center mx-auto mb-6">
      <Info size={32} class="text-white" />
    </div>
    <h1 class="text-4xl font-bold text-gray-900 dark:text-white mb-4">AI MCP Toolkit</h1>
    <p class="text-xl text-gray-600 dark:text-gray-400 max-w-3xl mx-auto">
      A comprehensive AI-powered text processing toolkit built on the Model Context Protocol (MCP) standard, 
      designed to work seamlessly with local AI models through Ollama.
    </p>
    <div class="mt-6">
      <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
        Version 0.1.0
      </span>
    </div>
  </div>

  <!-- Features -->
  <div class="mb-16">
    <h2 class="text-3xl font-bold text-center text-gray-900 dark:text-white mb-8">Key Features</h2>
    <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
      {#each features as feature}
        <div class="text-center p-6 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl">
          <div class="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center mx-auto mb-4">
            <svelte:component this={feature.icon} size={24} class="text-white" />
          </div>
          <h3 class="text-xl font-semibold text-gray-900 dark:text-white mb-2">{feature.title}</h3>
          <p class="text-gray-600 dark:text-gray-400">{feature.description}</p>
        </div>
      {/each}
    </div>
  </div>

  <!-- AI Agents -->
  <div class="mb-16">
    <h2 class="text-3xl font-bold text-center text-gray-900 dark:text-white mb-8">AI Agents</h2>
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {#each agents as agent}
        <div class="p-4 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
          <h3 class="font-semibold text-gray-900 dark:text-white mb-1">{agent.name}</h3>
          <p class="text-sm text-gray-600 dark:text-gray-400">{agent.description}</p>
        </div>
      {/each}
    </div>
  </div>

  <!-- Tech Stack -->
  <div class="mb-16">
    <h2 class="text-3xl font-bold text-center text-gray-900 dark:text-white mb-8">Technology Stack</h2>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      {#each techStack as item}
        <div class="flex items-start space-x-4 p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
          <div class="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
          <div>
            <h3 class="font-semibold text-gray-900 dark:text-white">{item.name}</h3>
            <p class="text-gray-600 dark:text-gray-400">{item.tech}</p>
          </div>
        </div>
      {/each}
    </div>
  </div>

  <!-- Statistics -->
  <div class="mb-16">
    <div class="bg-gradient-to-r from-blue-500 to-purple-600 rounded-2xl p-8 text-white">
      <h2 class="text-2xl font-bold text-center mb-8">Project Statistics</h2>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
        <div>
          <div class="text-3xl font-bold mb-2">8</div>
          <div class="text-sm opacity-90">AI Agents</div>
        </div>
        <div>
          <div class="text-3xl font-bold mb-2">24</div>
          <div class="text-sm opacity-90">Tools</div>
        </div>
        <div>
          <div class="text-3xl font-bold mb-2">100%</div>
          <div class="text-sm opacity-90">Local Processing</div>
        </div>
        <div>
          <div class="text-3xl font-bold mb-2">0</div>
          <div class="text-sm opacity-90">Data Sent to Cloud</div>
        </div>
      </div>
    </div>
  </div>

  <!-- Architecture -->
  <div class="mb-16">
    <h2 class="text-3xl font-bold text-center text-gray-900 dark:text-white mb-8">Architecture</h2>
    <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-8">
      <div class="text-center space-y-6">
        <div class="flex flex-col md:flex-row justify-center items-center space-y-4 md:space-y-0 md:space-x-8">
          <div class="px-4 py-2 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded-lg font-semibold">
            Svelte UI
          </div>
          <div class="text-gray-400">↔</div>
          <div class="px-4 py-2 bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 rounded-lg font-semibold">
            FastAPI Server
          </div>
          <div class="text-gray-400">↔</div>
          <div class="px-4 py-2 bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200 rounded-lg font-semibold">
            MCP Protocol
          </div>
        </div>
        <div class="text-center">
          <div class="text-gray-400 mb-2">↓</div>
          <div class="px-4 py-2 bg-orange-100 dark:bg-orange-900 text-orange-800 dark:text-orange-200 rounded-lg font-semibold inline-block">
            AI Agents
          </div>
        </div>
        <div class="text-center">
          <div class="text-gray-400 mb-2">↓</div>
          <div class="px-4 py-2 bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200 rounded-lg font-semibold inline-block">
            Ollama + Local Models
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Links and Resources -->
  <div class="mb-16">
    <h2 class="text-3xl font-bold text-center text-gray-900 dark:text-white mb-8">Resources</h2>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <button
        on:click={openGitHub}
        class="flex items-center justify-center space-x-3 p-6 bg-gray-900 dark:bg-gray-800 text-white rounded-xl hover:bg-gray-800 dark:hover:bg-gray-700 transition-colors"
      >
        <Github size={24} />
        <span class="font-semibold">View on GitHub</span>
        <ExternalLink size={16} />
      </button>
      
      <button
        on:click={openDocumentation}
        class="flex items-center justify-center space-x-3 p-6 bg-blue-600 hover:bg-blue-700 text-white rounded-xl transition-colors"
      >
        <Info size={24} />
        <span class="font-semibold">Documentation</span>
        <ExternalLink size={16} />
      </button>
    </div>
  </div>

  <!-- License and Credits -->
  <div class="text-center py-8 border-t border-gray-200 dark:border-gray-700">
    <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Open Source</h3>
    <p class="text-gray-600 dark:text-gray-400 mb-4">
      This project is licensed under the MIT License. Feel free to use, modify, and distribute.
    </p>
    <div class="space-y-2 text-sm text-gray-500 dark:text-gray-400">
      <p>Built with ❤️ for the AI community</p>
      <p>Powered by <a href="https://ollama.ai" class="text-blue-600 dark:text-blue-400 hover:underline" target="_blank">Ollama</a> and the <a href="https://modelcontextprotocol.io" class="text-blue-600 dark:text-blue-400 hover:underline" target="_blank">Model Context Protocol</a></p>
    </div>
  </div>
</div>
