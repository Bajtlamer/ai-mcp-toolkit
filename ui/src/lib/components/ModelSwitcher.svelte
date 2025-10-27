<script>
  import { onMount, createEventDispatcher } from 'svelte';
  import { RefreshCw, Cpu, Zap, ShieldAlert } from 'lucide-svelte';
  
  export let user = null;
  
  const dispatch = createEventDispatcher();
  
  let availableModels = [];
  let currentModel = null;
  let loading = false;
  let switching = false;
  let error = null;
  let success = null;

  onMount(() => {
    loadModels();
  });

  async function loadModels() {
    loading = true;
    error = null;
    
    try {
      // Fetch models from UI API proxy
      const response = await fetch('/api/models');
      
      if (!response.ok) {
        if (response.status === 403) {
          throw new Error('Admin access required to view models');
        }
        throw new Error('Failed to connect to backend');
      }
      
      const data = await response.json();
      
      if (data.success) {
        currentModel = data.current_model;
        availableModels = data.available_models.map(model => ({
          name: model.name || model,
          size: model.size || 'Unknown',
          id: model.name || model
        }));
      } else {
        error = data.error || 'Failed to load models';
      }
      
    } catch (err) {
      error = 'Failed to load models: ' + err.message;
    } finally {
      loading = false;
    }
  }

  async function switchModel(modelName) {
    if (switching || modelName === currentModel) return;
    
    switching = true;
    error = null;
    success = null;
    
    try {
      // Call UI API proxy to switch model (admin only)
      const response = await fetch('/api/models/switch', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ model: modelName })
      });
      
      const data = await response.json();
      
      if (response.ok && data.success) {
        currentModel = data.current_model;
        success = data.message;
        
        // Show note about persistence if present
        if (data.note) {
          setTimeout(() => {
            success = data.note;
          }, 3000);
        }
        
        // Reload models to refresh list
        setTimeout(() => loadModels(), 5000);
      } else {
        error = data.error || data.detail || 'Failed to switch model';
      }
    } catch (err) {
      error = 'Failed to switch model: ' + err.message;
    } finally {
      switching = false;
    }
  }

  function getModelSize(model) {
    // Extract model size from name for display
    if (model.name.includes(':3b')) return '3B';
    if (model.name.includes(':7b')) return '7B';
    if (model.name.includes(':8b')) return '8B';
    if (model.name.includes(':14b')) return '14B';
    if (model.name.includes(':13b')) return '13B';
    return model.size;
  }

  function getModelType(modelName) {
    if (modelName.includes('qwen')) return 'Qwen';
    if (modelName.includes('llama')) return 'Llama';
    if (modelName.includes('mistral')) return 'Mistral';
    return 'Other';
  }
</script>

{#if user && user.role !== 'admin'}
  <!-- Non-admin notice -->
  <div class="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-xl p-4">
    <div class="flex items-start space-x-3">
      <ShieldAlert size={20} class="text-yellow-600 dark:text-yellow-400 mt-0.5" />
      <div>
        <h3 class="text-sm font-semibold text-yellow-900 dark:text-yellow-100 mb-1">Admin Only Feature</h3>
        <p class="text-sm text-yellow-700 dark:text-yellow-300">
          Model switching is restricted to administrators only. Contact an admin to change the AI model.
        </p>
      </div>
    </div>
  </div>
{:else}
  <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-4">
  <div class="flex items-center justify-between mb-4">
    <div class="flex items-center space-x-2">
      <Cpu size={18} class="text-blue-600 dark:text-blue-400" />
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white">AI Model</h3>
    </div>
    <button
      on:click={loadModels}
      disabled={loading || switching}
      class="flex items-center px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded transition-colors disabled:opacity-50"
      title="Refresh models"
    >
      <RefreshCw size={12} class="mr-1 {loading ? 'animate-spin' : ''}" />
      Refresh
    </button>
  </div>

  {#if loading}
    <div class="text-center py-4">
      <div class="text-sm text-gray-500 dark:text-gray-400">Loading models...</div>
    </div>
  {:else if error}
    <div class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3">
      <div class="text-sm text-red-700 dark:text-red-300">{error}</div>
    </div>
  {:else}
    <!-- Current Model Display -->
    {#if currentModel}
      <div class="mb-3 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
        <div class="flex items-center justify-between">
          <div>
            <div class="text-sm font-medium text-blue-900 dark:text-blue-100">Currently Active</div>
            <div class="text-lg font-semibold text-blue-700 dark:text-blue-300">{currentModel}</div>
          </div>
          <Zap size={20} class="text-blue-600 dark:text-blue-400" />
        </div>
      </div>
    {/if}

    <!-- Success Message -->
    {#if success}
      <div class="mb-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-3">
        <div class="text-sm text-green-700 dark:text-green-300">{success}</div>
      </div>
    {/if}

    <!-- Model Selector Dropdown -->
    {#if availableModels.length > 0}
      <div>
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Select AI Model
        </label>
        <select
          value={currentModel}
          on:change={(e) => switchModel(e.target.value)}
          disabled={switching}
          class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-white disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {#each availableModels as model}
            <option value={model.name}>
              {model.name} • {getModelType(model.name)} • {getModelSize(model)}
              {#if model.name === currentModel} (Active){/if}
            </option>
          {/each}
        </select>
        
        {#if switching}
          <div class="mt-2 text-sm text-blue-600 dark:text-blue-400 flex items-center">
            <RefreshCw size={14} class="mr-2 animate-spin" />
            Switching model, please wait...
          </div>
        {/if}
      </div>
    {:else}
      <div class="text-center py-4 text-sm text-gray-500 dark:text-gray-400">
        No models available
      </div>
    {/if}
  {/if}
  </div>
{/if}
