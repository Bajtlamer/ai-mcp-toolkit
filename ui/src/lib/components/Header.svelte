<script>
  import { createEventDispatcher } from 'svelte';
  import { Menu, Settings, Sun, Moon, Activity } from 'lucide-svelte';
  import { page } from '$app/stores';
  import { browser } from '$app/environment';
  import { goto } from '$app/navigation';
  
  const dispatch = createEventDispatcher();
  
  let darkMode = false;
  let serverStatus = 'unknown'; // unknown, connected, disconnected
  
  // Initialize dark mode from localStorage
  if (browser) {
    darkMode = localStorage.getItem('darkMode') === 'true' || 
               (!localStorage.getItem('darkMode') && window.matchMedia('(prefers-color-scheme: dark)').matches);
    updateDarkMode();
    
    // Listen for storage changes from settings page
    window.addEventListener('storage', (e) => {
      if (e.key === 'darkMode') {
        darkMode = e.newValue === 'true';
        updateDarkMode();
      }
    });
  }
  
  function toggleDarkMode() {
    darkMode = !darkMode;
    updateDarkMode();
    if (browser) {
      localStorage.setItem('darkMode', darkMode.toString());
      
      // Also update the theme setting to match
      const uiConfig = JSON.parse(localStorage.getItem('ai-mcp-ui-config') || '{}');
      uiConfig.theme = darkMode ? 'dark' : 'light';
      localStorage.setItem('ai-mcp-ui-config', JSON.stringify(uiConfig));
    }
  }
  
  function updateDarkMode() {
    if (browser) {
      if (darkMode) {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }
    }
  }
  
  function toggleSidebar() {
    dispatch('toggle-sidebar');
  }
  
  // Check server status periodically
  async function checkServerStatus() {
    try {
      // Use SvelteKit server route instead of direct API call
      const response = await fetch('/api/gpu/health');
      const data = await response.json();
      serverStatus = response.ok && data.gpu_available ? 'connected' : 'disconnected';
    } catch (error) {
      serverStatus = 'disconnected';
    }
  }
  
  // Check server status on mount and every 30 seconds
  if (browser) {
    checkServerStatus();
    setInterval(checkServerStatus, 30000);
  }
  
  $: pageTitle = getPageTitle($page.url.pathname);
  
  function getPageTitle(pathname) {
    const routes = {
      '/': 'Dashboard',
      '/agents': 'AI Agents',
      '/agents/text-cleaner': 'Text Cleaner',
      '/agents/text-analyzer': 'Text Analyzer',
      '/agents/grammar-checker': 'Grammar Checker',
      '/agents/text-summarizer': 'Text Summarizer',
      '/agents/language-detector': 'Language Detector',
      '/agents/sentiment-analyzer': 'Sentiment Analyzer',
      '/agents/text-anonymizer': 'Text Anonymizer',
      '/agents/diacritic-remover': 'Diacritic Remover',
      '/chat': 'AI Chat',
      '/settings': 'Settings',
      '/about': 'About'
    };
    return routes[pathname] || 'AI MCP Toolkit';
  }
</script>

<header class="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 min-h-2">
  <div class="flex items-center justify-between">
    <div class="flex items-center space-x-4">
      <!-- Mobile menu button -->
      <button
        on:click={toggleSidebar}
        class="sidebar-toggle lg:hidden p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500"
        aria-label="Toggle sidebar"
      >
        <Menu size={20} />
      </button>
      
      <!-- Page title -->
      <div class="flex items-center space-x-2 min-h-24">
        <h1 class="text-xl font-semibold text-gray-900 dark:text-white">
          {pageTitle}
        </h1>
        
        <!-- Server status indicator -->
        <div class="flex items-center space-x-1">
          <div class={`w-2 h-2 rounded-full ${
            serverStatus === 'connected' 
              ? 'bg-success-500 animate-pulse-subtle' 
              : serverStatus === 'disconnected'
              ? 'bg-error-500'
              : 'bg-warning-500'
          }`}></div>
          <span class="text-sm text-gray-500 dark:text-gray-400">
            {serverStatus === 'connected' ? 'Connected' : 
             serverStatus === 'disconnected' ? 'Disconnected' : 'Checking...'}
          </span>
        </div>
      </div>
    </div>
    
    <div class="flex items-center space-x-2">
      <!-- Server status details -->
      <button
        class="p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500"
        title="Server Status"
      >
        <Activity size={18} class={serverStatus === 'connected' ? 'text-success-500' : 'text-error-500'} />
      </button>
      
      <!-- Dark mode toggle -->
      <button
        on:click={toggleDarkMode}
        class="p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500"
        aria-label="Toggle dark mode"
      >
        {#if darkMode}
          <Sun size={18} />
        {:else}
          <Moon size={18} />
        {/if}
      </button>
      
      <!-- Settings button -->
      <button
        class="p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500"
        aria-label="Settings"
        on:click={() => goto('/settings')}
      >
        <Settings size={18} />
      </button>
    </div>
  </div>
</header>
