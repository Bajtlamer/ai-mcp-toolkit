<script>
  import { Settings, Server, Palette, Globe, Shield, Download, RefreshCw, CheckCircle } from 'lucide-svelte';
  import { onMount } from 'svelte';
  import { browser } from '$app/environment';
  import ModelSwitcher from '$lib/components/ModelSwitcher.svelte';

  let serverConfig = {
    host: 'localhost',
    port: 8000,
    ollamaHost: 'localhost',
    ollamaPort: 11434,
    ollamaModel: 'llama3.2:3b'
  };

  let uiConfig = {
    theme: 'system', // light, dark, system
    language: 'en',
    autoSave: true,
    showTimestamps: true
  };

  let processingConfig = {
    maxTextLength: 100000,
    chunkSize: 1000,
    enableCache: true,
    cacheTTL: 3600
  };

  let serverStatus = 'unknown'; // connected, disconnected, unknown
  let saveStatus = ''; // 'saving', 'saved', ''
  
  // Load settings from localStorage on mount
  onMount(() => {
    loadSettings();
  });
  
  function loadSettings() {
    if (browser) {
      const savedServerConfig = localStorage.getItem('ai-mcp-server-config');
      if (savedServerConfig) {
        serverConfig = { ...serverConfig, ...JSON.parse(savedServerConfig) };
      }
      
      const savedUiConfig = localStorage.getItem('ai-mcp-ui-config');
      if (savedUiConfig) {
        uiConfig = { ...uiConfig, ...JSON.parse(savedUiConfig) };
      }
      
      const savedProcessingConfig = localStorage.getItem('ai-mcp-processing-config');
      if (savedProcessingConfig) {
        processingConfig = { ...processingConfig, ...JSON.parse(savedProcessingConfig) };
      }
      
      // Set initial theme
      applyTheme();
    }
  }
  
  function saveSettings() {
    if (browser) {
      saveStatus = 'saving';
      localStorage.setItem('ai-mcp-server-config', JSON.stringify(serverConfig));
      localStorage.setItem('ai-mcp-ui-config', JSON.stringify(uiConfig));
      localStorage.setItem('ai-mcp-processing-config', JSON.stringify(processingConfig));
      
      // Show saved confirmation briefly
      setTimeout(() => {
        saveStatus = 'saved';
        setTimeout(() => {
          saveStatus = '';
        }, 2000);
      }, 100);
    }
  }
  
  function applyTheme() {
    if (browser) {
      const isDark = uiConfig.theme === 'dark' || 
                     (uiConfig.theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);
      
      if (isDark) {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }
      
      // Update localStorage for header component
      localStorage.setItem('darkMode', isDark.toString());
    }
  }
  
  // Reactive statement to apply theme when changed
  $: if (browser && uiConfig.theme) {
    applyTheme();
    saveSettings();
  }
  
  // Save settings when they change
  $: if (browser && serverConfig) {
    saveSettings();
  }
  
  $: if (browser && processingConfig) {
    saveSettings();
  }
  
  async function checkServerConnection() {
    try {
      const response = await fetch(`http://${serverConfig.host}:${serverConfig.port}/health`);
      serverStatus = response.ok ? 'connected' : 'disconnected';
    } catch (error) {
      serverStatus = 'disconnected';
    }
  }

  async function testConnection() {
    await checkServerConnection();
  }

  function exportSettings() {
    const settings = {
      server: serverConfig,
      ui: uiConfig,
      processing: processingConfig,
      exportDate: new Date().toISOString()
    };
    
    const blob = new Blob([JSON.stringify(settings, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'ai-mcp-toolkit-settings.json';
    a.click();
    URL.revokeObjectURL(url);
  }

  function resetToDefaults() {
    if (confirm('Are you sure you want to reset all settings to their default values?')) {
      serverConfig = {
        host: 'localhost',
        port: 8000,
        ollamaHost: 'localhost',
        ollamaPort: 11434,
        ollamaModel: 'llama3.2:3b'
      };
      
      uiConfig = {
        theme: 'system',
        language: 'en',
        autoSave: true,
        showTimestamps: true
      };
      
      processingConfig = {
        maxTextLength: 100000,
        chunkSize: 1000,
        enableCache: true,
        cacheTTL: 3600
      };
    }
  }

  function getStatusColor(status) {
    switch (status) {
      case 'connected': return 'text-green-600 dark:text-green-400';
      case 'disconnected': return 'text-red-600 dark:text-red-400';
      default: return 'text-gray-500 dark:text-gray-400';
    }
  }

  function getStatusText(status) {
    switch (status) {
      case 'connected': return 'Connected';
      case 'disconnected': return 'Disconnected';
      default: return 'Unknown';
    }
  }

  // Check connection on mount
  checkServerConnection();
</script>

<svelte:head>
  <title>Settings - AI MCP Toolkit</title>
</svelte:head>

<div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
  <!-- Header -->
  <div class="mb-8">
    <div class="flex items-center justify-between">
      <div class="flex items-center space-x-3">
        <div class="w-12 h-12 bg-gradient-to-br from-gray-500 to-gray-600 rounded-xl flex items-center justify-center">
          <Settings size={24} class="text-white" />
        </div>
        <div>
          <h1 class="text-3xl font-bold text-gray-900 dark:text-white">Settings</h1>
          <div class="flex items-center space-x-2">
            <p class="text-gray-600 dark:text-gray-400">Configure your AI MCP Toolkit experience</p>
            {#if saveStatus === 'saving'}
              <span class="text-sm text-blue-600 dark:text-blue-400 animate-pulse">Saving...</span>
            {:else if saveStatus === 'saved'}
              <span class="flex items-center text-sm text-green-600 dark:text-green-400">
                <CheckCircle size={14} class="mr-1" /> Saved
              </span>
            {/if}
          </div>
        </div>
      </div>
      
      <div class="flex space-x-2">
        <button
          on:click={exportSettings}
          class="flex items-center px-3 py-2 text-sm bg-blue-100 dark:bg-blue-900 hover:bg-blue-200 dark:hover:bg-blue-800 text-blue-700 dark:text-blue-300 rounded-lg transition-colors"
        >
          <Download size={16} class="mr-1" />
          Export Settings
        </button>
        <button
          on:click={resetToDefaults}
          class="flex items-center px-3 py-2 text-sm bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-lg transition-colors"
        >
          <RefreshCw size={16} class="mr-1" />
          Reset to Defaults
        </button>
      </div>
    </div>
  </div>

  <div class="space-y-8">
    <!-- Server Configuration -->
    <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-6">
      <div class="flex items-center space-x-3 mb-6">
        <div class="w-8 h-8 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center">
          <Server size={18} class="text-blue-600 dark:text-blue-400" />
        </div>
        <div>
          <h2 class="text-xl font-semibold text-gray-900 dark:text-white">Server Configuration</h2>
          <p class="text-sm text-gray-500 dark:text-gray-400">Configure connection to the MCP server</p>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            MCP Server Host
          </label>
          <input
            bind:value={serverConfig.host}
            type="text"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            MCP Server Port
          </label>
          <input
            bind:value={serverConfig.port}
            type="number"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Ollama Host
          </label>
          <input
            bind:value={serverConfig.ollamaHost}
            type="text"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Ollama Port
          </label>
          <input
            bind:value={serverConfig.ollamaPort}
            type="number"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
          />
        </div>

        <div class="md:col-span-2">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Ollama Model
          </label>
          <select
            bind:value={serverConfig.ollamaModel}
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
          >
            <option value="llama3.2:3b">Llama 3.2 3B</option>
            <option value="llama3.2:7b">Llama 3.2 7B</option>
            <option value="llama3.1:8b">Llama 3.1 8B</option>
            <option value="llama3.1:13b">Llama 3.1 13B</option>
            <option value="mistral:7b">Mistral 7B</option>
          </select>
        </div>
      </div>

      <!-- Connection Status -->
      <div class="mt-6 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-3">
            <span class="text-sm font-medium text-gray-700 dark:text-gray-300">Connection Status:</span>
            <span class="text-sm font-medium {getStatusColor(serverStatus)}">
              {getStatusText(serverStatus)}
            </span>
          </div>
          <button
            on:click={testConnection}
            class="flex items-center px-3 py-1 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors"
          >
            <RefreshCw size={14} class="mr-1" />
            Test Connection
          </button>
        </div>
      </div>
    </div>

    <!-- Model Management -->
    <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-6">
      <div class="flex items-center space-x-3 mb-6">
        <div class="w-8 h-8 bg-green-100 dark:bg-green-900 rounded-lg flex items-center justify-center">
          <Server size={18} class="text-green-600 dark:text-green-400" />
        </div>
        <div>
          <h2 class="text-xl font-semibold text-gray-900 dark:text-white">AI Model Management</h2>
          <p class="text-sm text-gray-500 dark:text-gray-400">Switch between available AI models</p>
        </div>
      </div>

      <ModelSwitcher />
    </div>

    <!-- UI Preferences -->
    <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-6">
      <div class="flex items-center space-x-3 mb-6">
        <div class="w-8 h-8 bg-purple-100 dark:bg-purple-900 rounded-lg flex items-center justify-center">
          <Palette size={18} class="text-purple-600 dark:text-purple-400" />
        </div>
        <div>
          <h2 class="text-xl font-semibold text-gray-900 dark:text-white">UI Preferences</h2>
          <p class="text-sm text-gray-500 dark:text-gray-400">Customize the user interface</p>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Theme
          </label>
          <select
            bind:value={uiConfig.theme}
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
          >
            <option value="light">Light</option>
            <option value="dark">Dark</option>
            <option value="system">System</option>
          </select>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Language
          </label>
          <select
            bind:value={uiConfig.language}
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
          >
            <option value="en">English</option>
            <option value="es">Español</option>
            <option value="fr">Français</option>
            <option value="de">Deutsch</option>
            <option value="zh">中文</option>
          </select>
        </div>

        <div class="flex items-center justify-between p-3 border border-gray-200 dark:border-gray-600 rounded-lg">
          <div>
            <div class="text-sm font-medium text-gray-900 dark:text-white">Auto-save</div>
            <div class="text-xs text-gray-500 dark:text-gray-400">Automatically save your work</div>
          </div>
          <label class="relative inline-flex items-center cursor-pointer">
            <input
              bind:checked={uiConfig.autoSave}
              type="checkbox"
              class="sr-only peer"
            />
            <div class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300 dark:peer-focus:ring-purple-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-purple-600"></div>
          </label>
        </div>

        <div class="flex items-center justify-between p-3 border border-gray-200 dark:border-gray-600 rounded-lg">
          <div>
            <div class="text-sm font-medium text-gray-900 dark:text-white">Show timestamps</div>
            <div class="text-xs text-gray-500 dark:text-gray-400">Display timestamps in chat</div>
          </div>
          <label class="relative inline-flex items-center cursor-pointer">
            <input
              bind:checked={uiConfig.showTimestamps}
              type="checkbox"
              class="sr-only peer"
            />
            <div class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300 dark:peer-focus:ring-purple-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-purple-600"></div>
          </label>
        </div>
      </div>
    </div>

    <!-- Processing Settings -->
    <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-6">
      <div class="flex items-center space-x-3 mb-6">
        <div class="w-8 h-8 bg-green-100 dark:bg-green-900 rounded-lg flex items-center justify-center">
          <Shield size={18} class="text-green-600 dark:text-green-400" />
        </div>
        <div>
          <h2 class="text-xl font-semibold text-gray-900 dark:text-white">Processing Settings</h2>
          <p class="text-sm text-gray-500 dark:text-gray-400">Configure text processing behavior</p>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Max Text Length
          </label>
          <input
            bind:value={processingConfig.maxTextLength}
            type="number"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Chunk Size
          </label>
          <input
            bind:value={processingConfig.chunkSize}
            type="number"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
          />
        </div>

        <div class="flex items-center justify-between p-3 border border-gray-200 dark:border-gray-600 rounded-lg">
          <div>
            <div class="text-sm font-medium text-gray-900 dark:text-white">Enable Cache</div>
            <div class="text-xs text-gray-500 dark:text-gray-400">Cache results for faster processing</div>
          </div>
          <label class="relative inline-flex items-center cursor-pointer">
            <input
              bind:checked={processingConfig.enableCache}
              type="checkbox"
              class="sr-only peer"
            />
            <div class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-green-300 dark:peer-focus:ring-green-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-green-600"></div>
          </label>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Cache TTL (seconds)
          </label>
          <input
            bind:value={processingConfig.cacheTTL}
            type="number"
            disabled={!processingConfig.enableCache}
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-white disabled:bg-gray-100 dark:disabled:bg-gray-700 disabled:text-gray-500"
          />
        </div>
      </div>
    </div>
  </div>
</div>
