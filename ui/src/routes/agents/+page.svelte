<script>
  import { 
    Shield, 
    Type,
    Sparkles,
    Languages,
    BarChart3,
    CheckCircle,
    FileText,
    Zap,
    Clock,
    Star,
    ArrowRight,
    Bot,
    Wand2,
    Filter,
    Search,
    Image,
    ScanText
  } from 'lucide-svelte';
  import { goto } from '$app/navigation';

  const agentCategories = [
    {
      title: "Text Analysis",
      description: "Analyze and understand your text content",
      icon: BarChart3,
      color: "blue",
      agents: [
        {
          name: "Text Analyzer",
          description: "Comprehensive text analysis including readability, word count, and structure metrics",
          path: "/agents/text-analyzer",
          icon: BarChart3,
          features: ["Readability Score", "Word Count", "Sentence Analysis", "Language Stats"],
          difficulty: "Easy",
          speed: "Fast"
        },
        {
          name: "Sentiment Analyzer", 
          description: "Detect emotions and sentiment in text with detailed confidence scoring",
          path: "/agents/sentiment-analyzer",
          icon: Bot,
          features: ["Emotion Detection", "Sentiment Score", "Confidence Rating", "Mood Analysis"],
          difficulty: "Easy",
          speed: "Fast"
        },
        {
          name: "Language Detector",
          description: "Identify the language of any text with high accuracy",
          path: "/agents/language-detector", 
          icon: Languages,
          features: ["Multi-language Support", "Confidence Score", "Language Families", "Dialect Detection"],
          difficulty: "Easy",
          speed: "Very Fast"
        }
      ]
    },
    {
      title: "Text Cleaning & Enhancement",
      description: "Clean, fix, and improve your text quality",
      icon: Sparkles,
      color: "green", 
      agents: [
        {
          name: "Text Cleaner",
          description: "Remove unwanted characters, normalize spacing, and clean up messy text",
          path: "/agents/text-cleaner",
          icon: Sparkles,
          features: ["Remove HTML", "Normalize Spaces", "Fix Encoding", "Clean Formatting"],
          difficulty: "Easy",
          speed: "Very Fast"
        },
        {
          name: "Grammar Checker",
          description: "Check and fix grammar, spelling, and punctuation errors",
          path: "/agents/grammar-checker",
          icon: CheckCircle,
          features: ["Grammar Check", "Spell Check", "Punctuation Fix", "Style Suggestions"],
          difficulty: "Medium",
          speed: "Medium"
        },
        {
          name: "Diacritic Remover",
          description: "Remove accents and diacritical marks from text for standardization",
          path: "/agents/diacritic-remover",
          icon: Type,
          features: ["Remove Accents", "Unicode Cleanup", "Text Standardization", "Multiple Languages"],
          difficulty: "Easy", 
          speed: "Very Fast"
        }
      ]
    },
    {
      title: "Text Transformation",
      description: "Transform and process text for specific purposes",
      icon: Wand2,
      color: "purple",
      agents: [
        {
          name: "Text Summarizer",
          description: "Generate concise summaries of long text using AI",
          path: "/agents/text-summarizer",
          icon: FileText,
          features: ["AI Summarization", "Length Control", "Key Points", "Bullet Points"],
          difficulty: "Medium",
          speed: "Medium"
        },
        {
          name: "Text Anonymizer",
          description: "Remove or replace sensitive information to protect privacy",
          path: "/agents/text-anonymizer",
          icon: Shield,
          features: ["PII Removal", "Hash Replacement", "Multiple Strategies", "AI Detection"],
          difficulty: "Advanced",
          speed: "Medium"
        }
      ]
    },
    {
      title: "Image Processing",
      description: "Extract and analyze content from images",
      icon: Image,
      color: "orange",
      agents: [
        {
          name: "OCR Text Extractor",
          description: "Extract text from images using advanced Optical Character Recognition (Tesseract OCR)",
          path: "/agents/ocr-extractor",
          icon: ScanText,
          features: ["Multi-language OCR", "High Accuracy", "Layout Preservation", "Copy to Clipboard"],
          difficulty: "Easy",
          speed: "Fast"
        }
      ]
    }
  ];

  function getDifficultyColor(difficulty) {
    switch (difficulty) {
      case 'Easy': return 'text-green-600 dark:text-green-400 bg-green-100 dark:bg-green-900/30';
      case 'Medium': return 'text-yellow-600 dark:text-yellow-400 bg-yellow-100 dark:bg-yellow-900/30';
      case 'Advanced': return 'text-red-600 dark:text-red-400 bg-red-100 dark:bg-red-900/30';
      default: return 'text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-700';
    }
  }

  function getSpeedColor(speed) {
    switch (speed) {
      case 'Very Fast': return 'text-green-600 dark:text-green-400';
      case 'Fast': return 'text-blue-600 dark:text-blue-400';
      case 'Medium': return 'text-yellow-600 dark:text-yellow-400';
      case 'Slow': return 'text-red-600 dark:text-red-400';
      default: return 'text-gray-600 dark:text-gray-400';
    }
  }

  function getCategoryColor(color) {
    switch (color) {
      case 'blue': return 'from-blue-500 to-blue-600';
      case 'green': return 'from-green-500 to-green-600';
      case 'purple': return 'from-purple-500 to-purple-600';
      case 'red': return 'from-red-500 to-red-600';
      case 'orange': return 'from-orange-500 to-orange-600';
      default: return 'from-gray-500 to-gray-600';
    }
  }

  function navigateToAgent(path) {
    goto(path);
  }

  let searchQuery = '';
  let selectedCategory = 'all';

  $: filteredCategories = agentCategories.filter(category => {
    if (selectedCategory !== 'all' && category.title.toLowerCase().replace(/\s+/g, '-') !== selectedCategory) {
      return false;
    }
    if (searchQuery) {
      return category.agents.some(agent => 
        agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        agent.description.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }
    return true;
  }).map(category => ({
    ...category,
    agents: category.agents.filter(agent =>
      !searchQuery || 
      agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      agent.description.toLowerCase().includes(searchQuery.toLowerCase())
    )
  }));

  const totalAgents = agentCategories.reduce((sum, category) => sum + category.agents.length, 0);
</script>

<svelte:head>
  <title>AI Agents - AI MCP Toolkit</title>
  <meta name="description" content="Explore our collection of AI-powered text processing agents for analysis, cleaning, and transformation." />
</svelte:head>

<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
  <!-- Header Section -->
  <div class="text-center mb-12">
    <div class="flex items-center justify-center mb-6">
      <div class="w-16 h-16 bg-gradient-to-br from-purple-500 to-purple-600 rounded-2xl flex items-center justify-center shadow-lg">
        <Bot size={32} class="text-white" />
      </div>
    </div>
    
    <h1 class="text-4xl font-bold text-gray-900 dark:text-white mb-4">
      AI Text Processing Agents
    </h1>
    <p class="text-xl text-gray-600 dark:text-gray-400 mb-6 max-w-3xl mx-auto">
      Discover our powerful collection of {totalAgents} AI-powered tools designed to analyze, clean, enhance, and transform your text content with precision and speed.
    </p>
    
    <!-- Stats -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-2xl mx-auto mb-8">
      <div class="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
        <div class="text-2xl font-bold text-blue-600 dark:text-blue-400 mb-1">{totalAgents}</div>
        <div class="text-sm text-gray-500 dark:text-gray-400">AI Agents</div>
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
        <div class="text-2xl font-bold text-green-600 dark:text-green-400 mb-1">{agentCategories.length}</div>
        <div class="text-sm text-gray-500 dark:text-gray-400">Categories</div>
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
        <div class="text-2xl font-bold text-purple-600 dark:text-purple-400 mb-1">∞</div>
        <div class="text-sm text-gray-500 dark:text-gray-400">Possibilities</div>
      </div>
    </div>
    
    <!-- Search and Filter -->
    <div class="flex flex-col sm:flex-row gap-4 max-w-2xl mx-auto">
      <div class="relative flex-1">
        <Search size={20} class="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
        <input
          type="text"
          bind:value={searchQuery}
          placeholder="Search agents..."
          class="w-full pl-10 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
        />
      </div>
      <div class="relative">
        <Filter size={20} class="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
        <select
          bind:value={selectedCategory}
          class="appearance-none pl-10 pr-8 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-white min-w-[200px]"
        >
          <option value="all">All Categories</option>
          {#each agentCategories as category}
            <option value={category.title.toLowerCase().replace(/\s+/g, '-')}>{category.title}</option>
          {/each}
        </select>
      </div>
    </div>
  </div>

  <!-- Agent Categories -->
  <div class="space-y-12">
    {#each filteredCategories as category}
      <div class="category-section">
        <!-- Category Header -->
        <div class="flex items-center mb-6">
          <div class="w-12 h-12 bg-gradient-to-r {getCategoryColor(category.color)} rounded-xl flex items-center justify-center mr-4">
            <svelte:component this={category.icon} size={24} class="text-white" />
          </div>
          <div>
            <h2 class="text-2xl font-bold text-gray-900 dark:text-white">{category.title}</h2>
            <p class="text-gray-600 dark:text-gray-400">{category.description}</p>
          </div>
        </div>

        <!-- Agent Cards -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {#each category.agents as agent}
            <div class="group bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600 transition-all duration-200 hover:shadow-lg cursor-pointer"
                 on:click={() => navigateToAgent(agent.path)}
                 role="button"
                 tabindex="0"
                 on:keydown={(e) => e.key === 'Enter' && navigateToAgent(agent.path)}>
              
              <!-- Card Header -->
              <div class="p-6 pb-4">
                <div class="flex items-start justify-between mb-4">
                  <div class="w-10 h-10 bg-gradient-to-r {getCategoryColor(category.color)} rounded-lg flex items-center justify-center">
                    <svelte:component this={agent.icon} size={20} class="text-white" />
                  </div>
                  <ArrowRight size={16} class="text-gray-400 group-hover:text-gray-600 dark:group-hover:text-gray-300 transition-colors" />
                </div>
                
                <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">{agent.name}</h3>
                <p class="text-sm text-gray-600 dark:text-gray-400 mb-4">{agent.description}</p>
                
                <!-- Agent Meta -->
                <div class="flex items-center space-x-4 mb-4">
                  <div class="flex items-center space-x-1">
                    <span class="px-2 py-1 text-xs font-medium rounded-full {getDifficultyColor(agent.difficulty)}">
                      {agent.difficulty}
                    </span>
                  </div>
                  <div class="flex items-center space-x-1">
                    <Clock size={12} class="{getSpeedColor(agent.speed)}" />
                    <span class="text-xs {getSpeedColor(agent.speed)} font-medium">{agent.speed}</span>
                  </div>
                </div>
              </div>
              
              <!-- Features -->
              <div class="px-6 pb-6">
                <div class="flex flex-wrap gap-1">
                  {#each agent.features.slice(0, 3) as feature}
                    <span class="px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 text-xs rounded">
                      {feature}
                    </span>
                  {/each}
                  {#if agent.features.length > 3}
                    <span class="px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400 text-xs rounded">
                      +{agent.features.length - 3} more
                    </span>
                  {/if}
                </div>
              </div>
            </div>
          {/each}
        </div>
      </div>
    {/each}
  </div>
  
  <!-- No Results -->
  {#if filteredCategories.every(cat => cat.agents.length === 0)}
    <div class="text-center py-12">
      <Search size={48} class="mx-auto text-gray-400 mb-4" />
      <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">No agents found</h3>
      <p class="text-gray-500 dark:text-gray-400 mb-4">
        Try adjusting your search terms or category filter
      </p>
      <button
        on:click={() => { searchQuery = ''; selectedCategory = 'all'; }}
        class="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
      >
        Clear Filters
      </button>
    </div>
  {/if}

  <!-- Call to Action -->
  <div class="mt-16 text-center bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-900/20 dark:to-blue-900/20 rounded-2xl p-8 border border-purple-100 dark:border-purple-800">
    <h3 class="text-2xl font-bold text-gray-900 dark:text-white mb-4">
      Ready to enhance your text processing workflow?
    </h3>
    <p class="text-gray-600 dark:text-gray-400 mb-6 max-w-2xl mx-auto">
      Each agent is designed to solve specific text processing challenges. Start with any tool above, or explore our interactive AI Chat for conversational text processing.
    </p>
    <button
      on:click={() => goto('/chat')}
      class="inline-flex items-center px-6 py-3 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-medium rounded-lg transition-all duration-200 transform hover:scale-105 shadow-lg"
    >
      <Bot size={20} class="mr-2" />
      Try AI Chat
    </button>
  </div>
</div>

<style>
  .category-section {
    scroll-margin-top: 100px;
  }
</style>
