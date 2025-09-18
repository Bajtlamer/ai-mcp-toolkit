<script>
  import { onMount } from 'svelte';
  import { Sparkles, Play, Copy, Download } from 'lucide-svelte';

  let inputText = '';
  let outputText = '';
  let isProcessing = false;
  let error = null;

  // Example texts for demonstration - showing the problematic symbols it will remove
  const examples = [
    "Hello@world! This text has $$$ and &*@#% symbols that need cleaning!!!",
    "Check email@test.com and https://website.com with []()^*&% characters.",
    "Text with @!%^&*()_+}{:?<> exactly these problematic symbols.",
    "Mixed text with HTML <b>tags</b> and &amp; entities plus @@@ symbols.",
    "Corporate email: john.doe@company.com with (555) 123-4567 and weird **** symbols."
  ];

  async function cleanText() {
    if (!inputText.trim()) return;
    
    isProcessing = true;
    error = null;
    
    try {
      const response = await fetch('http://localhost:8000/tools/execute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: 'clean_text',
          arguments: {
            text: inputText
          }
        })
      });

      const result = await response.json();
      
      if (result.success) {
        outputText = result.result;
      } else {
        error = result.error || 'Failed to clean text';
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
  }

  function copyToClipboard() {
    navigator.clipboard.writeText(outputText);
  }

  function downloadText() {
    const blob = new Blob([outputText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'cleaned_text.txt';
    a.click();
    URL.revokeObjectURL(url);
  }
</script>

<svelte:head>
  <title>Text Cleaner - AI MCP Toolkit</title>
</svelte:head>

<div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
  <!-- Header -->
  <div class="mb-8">
    <div class="flex items-center space-x-3 mb-4">
      <div class="w-12 h-12 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center">
        <Sparkles size={24} class="text-white" />
      </div>
      <div>
        <h1 class="text-3xl font-bold text-gray-900 dark:text-white">Text Cleaner</h1>
        <p class="text-gray-600 dark:text-gray-400">Remove unnecessary symbols like @!%^&*()_+&#123;&#125; and clean up messy text</p>
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
  <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
    <!-- Input -->
    <div class="space-y-4">
      <div class="flex items-center justify-between">
        <h3 class="text-lg font-medium text-gray-900 dark:text-white">Input Text</h3>
        <span class="text-sm text-gray-500 dark:text-gray-400">
          {inputText.length} characters
        </span>
      </div>
      
      <textarea
        bind:value={inputText}
        placeholder="Enter your text here to clean it..."
        class="w-full h-64 px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
      ></textarea>
      
      <button
        on:click={cleanText}
        disabled={!inputText.trim() || isProcessing}
        class="w-full flex items-center justify-center px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-medium rounded-lg transition-colors"
      >
        {#if isProcessing}
          <div class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
          Cleaning...
        {:else}
          <Play size={16} class="mr-2" />
          Clean Text
        {/if}
      </button>
    </div>

    <!-- Output -->
    <div class="space-y-4">
      <div class="flex items-center justify-between">
        <h3 class="text-lg font-medium text-gray-900 dark:text-white">Cleaned Text</h3>
        {#if outputText}
          <div class="flex space-x-2">
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
      
      <div class="w-full h-64 px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-800 overflow-y-auto">
        {#if error}
          <div class="text-red-600 dark:text-red-400">
            <strong>Error:</strong> {error}
          </div>
        {:else if outputText}
          <pre class="text-gray-900 dark:text-white whitespace-pre-wrap font-mono text-sm">{outputText}</pre>
        {:else}
          <p class="text-gray-500 dark:text-gray-400 italic">
            Cleaned text will appear here...
          </p>
        {/if}
      </div>
    </div>
  </div>

  <!-- Features -->
  <div class="mt-12">
    <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-6">Features</h2>
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div class="p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
        <h3 class="font-medium text-gray-900 dark:text-white mb-2">Special Symbol Removal</h3>
        <p class="text-sm text-gray-600 dark:text-gray-400">
          Automatically removes problematic symbols: @!%^&*()_+&#123;&#125; while preserving readability.
        </p>
      </div>
      <div class="p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
        <h3 class="font-medium text-gray-900 dark:text-white mb-2">URL & Email Cleaning</h3>
        <p class="text-sm text-gray-600 dark:text-gray-400">
          Removes URLs, email addresses, and HTML tags by default for cleaner text.
        </p>
      </div>
      <div class="p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
        <h3 class="font-medium text-gray-900 dark:text-white mb-2">Smart Text Normalization</h3>
        <p class="text-sm text-gray-600 dark:text-gray-400">
          Normalizes spacing, removes excessive punctuation, and preserves readability.
        </p>
      </div>
    </div>
  </div>
</div>
