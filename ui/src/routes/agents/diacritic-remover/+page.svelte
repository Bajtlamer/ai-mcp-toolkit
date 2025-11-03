<script>
  import { Type, Play, Copy, Download, Database, X } from 'lucide-svelte';
  import ResourceSelector from '$lib/components/ResourceSelector.svelte';
  import * as resourceAPI from '$lib/services/resources';
  import { fetchResourceText } from '$lib/utils/resourceTextFetcher.js';

  let inputText = '';
  let outputText = '';
  let isProcessing = false;
  let error = null;
  let inputMode = 'text'; // 'text' or 'resource'
  let selectedResourceUri = '';

  // Example texts for demonstration
  const examples = [
    "Café français avec crème brûlée",
    "Zürich, München, and Köln",
    "Niño pequeño in español",
    "Björk from Reykjavík, Iceland"
  ];

  async function removeDiacritics() {
    if (inputMode === 'text' && !inputText.trim()) return;
    if (inputMode === 'resource' && !selectedResourceUri) return;
    
    isProcessing = true;
    error = null;
    
    try {
      let textToProcess = inputText;
      
      if (inputMode === 'resource') {
        textToProcess = await fetchResourceText(selectedResourceUri, resourceAPI.getResource);
      }
      
      const response = await fetch('/api/tools/execute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: 'remove_diacritics',
          arguments: {
            text: textToProcess
          }
        })
      });

      const result = await response.json();
      
      if (result.success) {
        outputText = result.result;
      } else {
        error = result.error || 'Failed to remove diacritics';
      }
    } catch (err) {
      error = 'Failed to connect to server. Make sure the MCP server is running on port 8000.';
      console.error('Error:', err);
    } finally {
      isProcessing = false;
    }
  }

  function useExample(text) {
    inputText = text;
    inputMode = 'text';
  }

  function copyToClipboard() {
    navigator.clipboard.writeText(outputText);
  }

  function downloadText() {
    const blob = new Blob([outputText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'text_without_diacritics.txt';
    a.click();
    URL.revokeObjectURL(url);
  }

  function clearText() {
    outputText = '';
    error = null;
  }
</script>

<svelte:head>
  <title>Diacritic Remover - AI MCP Toolkit</title>
</svelte:head>

<div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
  <!-- Header -->
  <div class="mb-8">
    <div class="flex items-center space-x-3 mb-4">
      <div class="w-12 h-12 bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl flex items-center justify-center">
        <Type size={24} class="text-white" />
      </div>
      <div>
        <h1 class="text-3xl font-bold text-gray-900 dark:text-white">Diacritic Remover</h1>
        <p class="text-gray-600 dark:text-gray-400">Remove diacritical marks and accents from text</p>
      </div>
    </div>
  </div>

  <!-- Examples -->
  <div class="mb-6">
    <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-3">Quick Examples</h2>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
      {#each examples as example}
        <button
          on:click={() => useExample(example)}
          class="p-3 text-left text-sm bg-gray-50 dark:bg-gray-800 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
        >
          <span class="text-gray-600 dark:text-gray-400 truncate block">{example}</span>
        </button>
      {/each}
    </div>
  </div>

  <!-- Input/Output Interface -->
  <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 h-[600px]">
    <!-- Input -->
    <div class="flex flex-col h-full">
      <!-- Input Mode Tabs -->
      <div class="border-b border-gray-200 dark:border-gray-700 mb-4">
        <nav class="-mb-px flex space-x-8">
          <button
            on:click={() => inputMode = 'text'}
            class="{inputMode === 'text' ? 'border-purple-500 text-purple-600 dark:text-purple-400' : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'} whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm transition-colors"
          >
            Text Input
          </button>
          <button
            on:click={() => inputMode = 'resource'}
            class="{inputMode === 'resource' ? 'border-purple-500 text-purple-600 dark:text-purple-400' : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'} whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm transition-colors"
          >
            <Database size={14} class="inline mr-1" />
            From Resource
          </button>
        </nav>
      </div>
      
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-medium text-gray-900 dark:text-white">
          {inputMode === 'text' ? 'Input Text' : 'Select Resource'}
        </h3>
        <span class="text-sm text-gray-500 dark:text-gray-400">
          {inputMode === 'text' ? `${inputText.length} characters` : (selectedResourceUri ? '✓ Resource selected' : 'Choose resource')}
        </span>
      </div>
      
      <div class="flex-1 mb-4">
        {#if inputMode === 'text'}
          <textarea
            bind:value={inputText}
            placeholder="Enter text with diacritical marks..."
            class="w-full h-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
          ></textarea>
        {:else}
          <ResourceSelector 
            bind:selectedResourceUri
            label="Select a resource to remove diacritics"
            infoText="Select any uploaded text file, PDF, or URL resource"
          />
        {/if}
      </div>
      
      <button
        on:click={removeDiacritics}
        disabled={(inputMode === 'text' && !inputText.trim()) || (inputMode === 'resource' && !selectedResourceUri) || isProcessing}
        class="w-full flex items-center justify-center px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400 text-white font-medium rounded-lg transition-colors"
      >
        {#if isProcessing}
          <div class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
          {inputMode === 'resource' ? 'Loading & Processing...' : 'Removing Diacritics...'}
        {:else}
          <Play size={16} class="mr-2" />
          {inputMode === 'resource' ? 'Process Resource' : 'Remove Diacritics'}
        {/if}
      </button>
    </div>

    <!-- Output -->
    <div class="flex flex-col h-full">
      <div class="flex items-center justify-between">
        <h3 class="text-lg font-medium text-gray-900 dark:text-white">Text Without Diacritics</h3>
        {#if outputText}
          <div class="flex space-x-2">
            <button
              on:click={clearText}
              class="flex items-center px-3 py-1 text-sm bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-md transition-colors"
            >
              <X size={14} class="mr-1" />
              Clear
            </button>
            <button
              on:click={copyToClipboard}
              class="flex items-center px-3 py-1 text-sm bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-md transition-colors"
            >
              <Copy size={14} class="mr-1" />
              Copy
            </button>
            <button
              on:click={downloadText}
              class="flex items-center px-3 py-1 text-sm bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-md transition-colors"
            >
              <Download size={14} class="mr-1" />
              Download
            </button>
          </div>
        {/if}
      </div>
      
      {#if error}
        <div class="flex-1 w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-800">
          <div class="text-red-600 dark:text-red-400">
            <strong>Error:</strong> {error}
          </div>
        </div>
      {:else if outputText}
        <textarea
          bind:value={outputText}
          class="flex-1 min-h-0 w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white text-sm font-mono resize-none focus:ring-2 focus:ring-purple-500 focus:border-transparent mt-4"
          readonly
        ></textarea>
      {:else}
        <div class="flex-1 w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-800">
          <p class="text-gray-500 dark:text-gray-400 italic">
            Text without diacritical marks will appear here...
          </p>
        </div>
      {/if}
    </div>
  </div>

  <!-- Features -->
  <div class="mt-12">
    <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-6">Features</h2>
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div class="p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
        <h3 class="font-medium text-gray-900 dark:text-white mb-2">Accent Removal</h3>
        <p class="text-sm text-gray-600 dark:text-gray-400">
          Removes accents from letters (é→e, ñ→n, ü→u, etc.)
        </p>
      </div>
      <div class="p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
        <h3 class="font-medium text-gray-900 dark:text-white mb-2">Text Transliteration</h3>
        <p class="text-sm text-gray-600 dark:text-gray-400">
          Converts accented characters to their ASCII equivalents.
        </p>
      </div>
      <div class="p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
        <h3 class="font-medium text-gray-900 dark:text-white mb-2">Multi-Language Support</h3>
        <p class="text-sm text-gray-600 dark:text-gray-400">
          Supports diacritics from various languages and scripts.
        </p>
      </div>
    </div>
  </div>
</div>
