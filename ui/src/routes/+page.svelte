<script>
  import { onMount } from 'svelte';
  import {
    Bot, 
    Zap, 
    Shield, 
    Activity, 
    Users, 
    ArrowRight,
    Sparkles,
    FileText,
    Languages,
    Heart,
    Type,
    BarChart3
  } from 'lucide-svelte';
  
  
  let serverStats = null;
  let recentActivity = [];
  let loading = true;
  
  const agents = [
    {
      name: 'Text Cleaner',
      href: '/agents/text-cleaner',
      description: 'Remove special characters and normalize text',
      icon: Sparkles,
      color: 'text-blue-500'
    },
    {
      name: 'Text Analyzer',
      href: '/agents/text-analyzer',
      description: 'Analyze text statistics and readability',
      icon: BarChart3,
      color: 'text-green-500'
    },
    {
      name: 'Grammar Checker',
      href: '/agents/grammar-checker',
      description: 'Check and correct grammar mistakes',
      icon: FileText,
      color: 'text-purple-500'
    },
    {
      name: 'Text Summarizer',
      href: '/agents/text-summarizer',
      description: 'Generate concise summaries',
      icon: Zap,
      color: 'text-yellow-500'
    },
    {
      name: 'Language Detector',
      href: '/agents/language-detector',
      description: 'Detect text language automatically',
      icon: Languages,
      color: 'text-indigo-500'
    },
    {
      name: 'Sentiment Analyzer',
      href: '/agents/sentiment-analyzer',
      description: 'Analyze emotional tone and sentiment',
      icon: Heart,
      color: 'text-pink-500'
    },
    {
      name: 'Text Anonymizer',
      href: '/agents/text-anonymizer',
      description: 'Remove sensitive personal information',
      icon: Shield,
      color: 'text-red-500'
    },
    {
      name: 'Diacritic Remover',
      href: '/agents/diacritic-remover',
      description: 'Remove accents and diacritical marks',
      icon: Type,
      color: 'text-teal-500'
    }
  ];
  
  onMount(async () => {
    await loadDashboardData();
  });
  
  async function loadDashboardData() {
    try {
      // Simulate API calls for now
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      serverStats = {
        totalAgents: 8,
        totalTools: 24,
        uptime: '2h 34m',
        requests: 156
      };
      
      recentActivity = [
        { action: 'Text analyzed', agent: 'Text Analyzer', timestamp: '2 minutes ago' },
        { action: 'Grammar checked', agent: 'Grammar Checker', timestamp: '5 minutes ago' },
        { action: 'Text anonymized', agent: 'Text Anonymizer', timestamp: '8 minutes ago' },
        { action: 'Language detected', agent: 'Language Detector', timestamp: '12 minutes ago' }
      ];
      
      loading = false;
    } catch (error) {
      console.error('Error loading dashboard data:', error);
      loading = false;
    }
  }
</script>

<svelte:head>
  <title>Dashboard - AI MCP Toolkit</title>
</svelte:head>

<div class="space-y-6">
  <!-- Welcome Header -->
  <div class="bg-gradient-to-r from-primary-500 to-primary-600 rounded-xl p-6 text-white">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold mb-2">Welcome to AI MCP Toolkit</h1>
        <p class="text-primary-100">
          Powerful AI-driven text processing with local Ollama models
        </p>
      </div>
      <div class="hidden md:block">
        <Bot size={48} class="text-primary-200" />
      </div>
    </div>
  </div>
  
  <!-- Stats Cards -->
  {#if loading}
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {#each Array(4) as _}
        <div class="card p-6 animate-pulse">
          <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2 mb-4"></div>
          <div class="h-8 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
        </div>
      {/each}
    </div>
  {:else if serverStats}
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <div class="card p-6">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-gray-600 dark:text-gray-400">Total Agents</p>
            <p class="text-2xl font-bold text-gray-900 dark:text-white">{serverStats.totalAgents}</p>
          </div>
          <div class="w-12 h-12 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center">
            <Bot class="w-6 h-6 text-blue-600 dark:text-blue-400" />
          </div>
        </div>
      </div>
      
      <div class="card p-6">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-gray-600 dark:text-gray-400">Available Tools</p>
            <p class="text-2xl font-bold text-gray-900 dark:text-white">{serverStats.totalTools}</p>
          </div>
          <div class="w-12 h-12 bg-green-100 dark:bg-green-900 rounded-lg flex items-center justify-center">
            <Zap class="w-6 h-6 text-green-600 dark:text-green-400" />
          </div>
        </div>
      </div>
      
      <div class="card p-6">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-gray-600 dark:text-gray-400">Server Uptime</p>
            <p class="text-2xl font-bold text-gray-900 dark:text-white">{serverStats.uptime}</p>
          </div>
          <div class="w-12 h-12 bg-yellow-100 dark:bg-yellow-900 rounded-lg flex items-center justify-center">
            <Activity class="w-6 h-6 text-yellow-600 dark:text-yellow-400" />
          </div>
        </div>
      </div>
      
      <div class="card p-6">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-gray-600 dark:text-gray-400">Requests Today</p>
            <p class="text-2xl font-bold text-gray-900 dark:text-white">{serverStats.requests}</p>
          </div>
          <div class="w-12 h-12 bg-purple-100 dark:bg-purple-900 rounded-lg flex items-center justify-center">
            <Users class="w-6 h-6 text-purple-600 dark:text-purple-400" />
          </div>
        </div>
      </div>
    </div>
  {/if}
  
  <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
    <!-- AI Agents Grid -->
    <div class="lg:col-span-2">
      <div class="card">
        <div class="p-6 border-b border-gray-200 dark:border-gray-700">
          <div class="flex items-center justify-between">
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">AI Agents</h2>
            <a
              href="/agents"
              class="inline-flex items-center text-sm font-medium text-primary-600 hover:text-primary-500 dark:text-primary-400 dark:hover:text-primary-300"
            >
              View all
              <ArrowRight class="ml-1 w-4 h-4" />
            </a>
          </div>
        </div>
        
        <div class="p-6">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            {#each agents as agent}
              <a
                href={agent.href}
                class="group p-4 rounded-lg border border-gray-200 dark:border-gray-700 hover:border-primary-300 dark:hover:border-primary-600 hover:shadow-md transition-all duration-200"
              >
                <div class="flex items-start space-x-3">
                  <div class={`flex-shrink-0 ${agent.color}`}>
                    <svelte:component this={agent.icon} size={20} />
                  </div>
                  <div class="flex-1 min-w-0">
                    <h3 class="text-sm font-medium text-gray-900 dark:text-white group-hover:text-primary-600 dark:group-hover:text-primary-400">
                      {agent.name}
                    </h3>
                    <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
                      {agent.description}
                    </p>
                  </div>
                </div>
              </a>
            {/each}
          </div>
        </div>
      </div>
    </div>
    
    <!-- Recent Activity -->
    <div class="card">
      <div class="p-6 border-b border-gray-200 dark:border-gray-700">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Recent Activity</h2>
      </div>
      
      <div class="p-6">
        {#if loading}
          <div class="space-y-4">
            {#each Array(4) as _}
              <div class="animate-pulse">
                <div class="flex items-center space-x-3">
                  <div class="w-8 h-8 bg-gray-200 dark:bg-gray-700 rounded-full"></div>
                  <div class="flex-1">
                    <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-2"></div>
                    <div class="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
                  </div>
                </div>
              </div>
            {/each}
          </div>
        {:else if recentActivity.length > 0}
          <div class="space-y-4">
            {#each recentActivity as activity}
              <div class="flex items-center space-x-3">
                <div class="w-8 h-8 bg-primary-100 dark:bg-primary-900 rounded-full flex items-center justify-center">
                  <Activity class="w-4 h-4 text-primary-600 dark:text-primary-400" />
                </div>
                <div class="flex-1 min-w-0">
                  <p class="text-sm text-gray-900 dark:text-white font-medium">
                    {activity.action}
                  </p>
                  <div class="flex items-center space-x-2 text-xs text-gray-500 dark:text-gray-400">
                    <span>{activity.agent}</span>
                    <span>•</span>
                    <span>{activity.timestamp}</span>
                  </div>
                </div>
              </div>
            {/each}
          </div>
        {:else}
          <div class="text-center text-gray-500 dark:text-gray-400">
            <Activity class="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p class="text-sm">No recent activity</p>
          </div>
        {/if}
      </div>
    </div>
  </div>
  
  <!-- Quick Actions -->
  <div class="card">
    <div class="p-6 border-b border-gray-200 dark:border-gray-700">
      <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Quick Actions</h2>
    </div>
    
    <div class="p-6">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <a
          href="/agents/text-cleaner"
          class="group p-4 rounded-lg border-2 border-dashed border-gray-300 dark:border-gray-600 hover:border-primary-400 dark:hover:border-primary-500 transition-colors"
        >
          <div class="text-center">
            <Sparkles class="w-8 h-8 mx-auto text-blue-500 group-hover:text-primary-500 transition-colors" />
            <h3 class="mt-2 text-sm font-medium text-gray-900 dark:text-white">Clean Text</h3>
            <p class="text-xs text-gray-500 dark:text-gray-400">Remove unwanted characters</p>
          </div>
        </a>
        
        <a
          href="/agents/text-analyzer"
          class="group p-4 rounded-lg border-2 border-dashed border-gray-300 dark:border-gray-600 hover:border-primary-400 dark:hover:border-primary-500 transition-colors"
        >
          <div class="text-center">
            <BarChart3 class="w-8 h-8 mx-auto text-green-500 group-hover:text-primary-500 transition-colors" />
            <h3 class="mt-2 text-sm font-medium text-gray-900 dark:text-white">Analyze Text</h3>
            <p class="text-xs text-gray-500 dark:text-gray-400">Get detailed text statistics</p>
          </div>
        </a>
        
        <a
          href="/agents/text-anonymizer"
          class="group p-4 rounded-lg border-2 border-dashed border-gray-300 dark:border-gray-600 hover:border-primary-400 dark:hover:border-primary-500 transition-colors"
        >
          <div class="text-center">
            <Shield class="w-8 h-8 mx-auto text-red-500 group-hover:text-primary-500 transition-colors" />
            <h3 class="mt-2 text-sm font-medium text-gray-900 dark:text-white">Anonymize Text</h3>
            <p class="text-xs text-gray-500 dark:text-gray-400">Remove sensitive information</p>
          </div>
        </a>
      </div>
    </div>
  </div>
</div>
