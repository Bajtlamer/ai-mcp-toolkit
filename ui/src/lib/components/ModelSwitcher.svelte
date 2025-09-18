<script>
  import { onMount, createEventDispatcher } from 'svelte';
  import { RefreshCw, Cpu, Zap } from 'lucide-svelte';
  
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
      const response = await fetch('/api/models/switch');
      const data = await response.json();
      
      if (data.success) {
        availableModels = data.available;
        currentModel = data.current;
      } else {
        error = data.error;
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
      const response = await fetch('/api/models/switch', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ model: modelName })
      });
      
      const data = await response.json();
      
      if (data.success) {
        currentModel = data.model;
        success = data.message;
        dispatch('modelChanged', { model: data.model });
        
        // Clear success message after 3 seconds
        setTimeout(() => success = null, 3000);
      } else {
        error = data.error;
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

    <!-- Available Models -->
    {#if availableModels.length > 0}
      <div class="space-y-2">
        <div class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Available Models:</div>
        {#each availableModels as model}
          <button
            on:click={() => switchModel(model.name)}
            disabled={switching || model.name === currentModel}
            class="w-full flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 hover:bg-gray-100 dark:hover:bg-gray-600 border border-gray-200 dark:border-gray-600 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed {model.name === currentModel ? 'ring-2 ring-blue-500' : ''}"
          >
            <div class="text-left">
              <div class="text-sm font-medium text-gray-900 dark:text-white">{model.name}</div>
              <div class="text-xs text-gray-500 dark:text-gray-400">
                {getModelType(model.name)} • {getModelSize(model)} • {model.size}
              </div>
            </div>
            
            {#if switching && model.name === currentModel}
              <div class="text-xs text-blue-600 dark:text-blue-400 animate-pulse">Switching...</div>
            {:else if model.name === currentModel}
              <div class="text-xs text-green-600 dark:text-green-400 font-medium">Active</div>
            {:else}
              <div class="text-xs text-gray-400 dark:text-gray-500">Switch</div>
            {/if}
          </button>
        {/each}
      </div>
    {:else}
      <div class="text-center py-4 text-sm text-gray-500 dark:text-gray-400">
        No models available
      </div>
    {/if}
  {/if}
</div>