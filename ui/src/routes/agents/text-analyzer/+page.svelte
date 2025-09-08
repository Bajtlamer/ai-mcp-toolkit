<script>
  import { BarChart3, Play, Download } from 'lucide-svelte';

  let inputText = '';
  let analysisResult = null;
  let isProcessing = false;
  let error = null;

  // Example texts for demonstration
  const examples = [
    "The quick brown fox jumps over the lazy dog. This sentence contains every letter of the English alphabet.",
    "Machine learning is a subset of artificial intelligence that focuses on algorithms which can learn from and make predictions on data.",
    "To be or not to be, that is the question: Whether 'tis nobler in the mind to suffer the slings and arrows of outrageous fortune.",
    "Climate change represents one of the most pressing challenges of our time, affecting ecosystems, weather patterns, and human societies worldwide."
  ];

  async function analyzeText() {
    if (!inputText.trim()) return;
    
    isProcessing = true;
    error = null;
    analysisResult = null;
    
    try {
      const response = await fetch('http://localhost:8000/tools/execute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: 'analyze_text_basic',
          arguments: {
            text: inputText
          }
        })
      });

      const result = await response.json();
      
      if (result.success) {
        analysisResult = JSON.parse(result.result);
      } else {
        error = result.error || 'Failed to analyze text';
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

  function downloadAnalysis() {
    const data = JSON.stringify(analysisResult, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'text_analysis.json';
    a.click();
    URL.revokeObjectURL(url);
  }

  function formatNumber(num) {
    return new Intl.NumberFormat().format(num);
  }
</script>

<svelte:head>
  <title>Text Analyzer - AI MCP Toolkit</title>
</svelte:head>

<div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
  <!-- Header -->
  <div class="mb-8">
    <div class="flex items-center space-x-3 mb-4">
      <div class="w-12 h-12 bg-gradient-to-br from-green-500 to-green-600 rounded-xl flex items-center justify-center">
        <BarChart3 size={24} class="text-white" />
      </div>
      <div>
        <h1 class="text-3xl font-bold text-gray-900 dark:text-white">Text Analyzer</h1>
        <p class="text-gray-600 dark:text-gray-400">Analyze text for statistics, readability, and linguistic properties</p>
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
          <span class="text-gray-600 dark:text-gray-400 line-clamp-2">{example}</span>
        </button>
      {/each}
    </div>
  </div>

  <!-- Input Interface -->
  <div class="mb-6">
    <div class="space-y-4">
      <div class="flex items-center justify-between">
        <h3 class="text-lg font-medium text-gray-900 dark:text-white">Input Text</h3>
        <span class="text-sm text-gray-500 dark:text-gray-400">
          {inputText.length} characters
        </span>
      </div>
      
      <textarea
        bind:value={inputText}
        placeholder="Enter text to analyze..."
        class="w-full h-32 px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent resize-none bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
      ></textarea>
      
      <div class="flex space-x-3">
        <button
          on:click={analyzeText}
          disabled={!inputText.trim() || isProcessing}
          class="flex items-center justify-center px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white font-medium rounded-lg transition-colors"
        >
          {#if isProcessing}
            <div class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
            Analyzing...
          {:else}
            <Play size={16} class="mr-2" />
            Analyze Text
          {/if}
        </button>
        
        {#if analysisResult}
          <button
            on:click={downloadAnalysis}
            class="flex items-center px-3 py-2 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-lg transition-colors"
          >
            <Download size={14} class="mr-2" />
            Download Results
          </button>
        {/if}
      </div>
    </div>
  </div>

  <!-- Results -->
  {#if error}
    <div class="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
      <div class="text-red-600 dark:text-red-400">
        <strong>Error:</strong> {error}
      </div>
    </div>
  {:else if analysisResult}
    <div class="space-y-6">
      <!-- Basic Statistics -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        {#if analysisResult.basic_stats}
          <div class="p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
            <h4 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Characters</h4>
            <p class="text-2xl font-bold text-gray-900 dark:text-white">{formatNumber(analysisResult.basic_stats.character_count)}</p>
          </div>
          <div class="p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
            <h4 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Words</h4>
            <p class="text-2xl font-bold text-gray-900 dark:text-white">{formatNumber(analysisResult.basic_stats.word_count)}</p>
          </div>
          <div class="p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
            <h4 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Sentences</h4>
            <p class="text-2xl font-bold text-gray-900 dark:text-white">{formatNumber(analysisResult.basic_stats.sentence_count)}</p>
          </div>
          <div class="p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
            <h4 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Paragraphs</h4>
            <p class="text-2xl font-bold text-gray-900 dark:text-white">{formatNumber(analysisResult.basic_stats.paragraph_count)}</p>
          </div>
        {/if}
      </div>

      <!-- Detailed Analysis -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <!-- Readability -->
        {#if analysisResult.readability}
          <div class="p-6 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
            <h4 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Readability Scores</h4>
            <div class="space-y-3">
              {#each Object.entries(analysisResult.readability) as [key, value]}
                <div class="flex justify-between items-center">
                  <span class="text-sm text-gray-600 dark:text-gray-400 capitalize">{key.replace('_', ' ')}</span>
                  <span class="font-mono text-sm font-medium text-gray-900 dark:text-white">{typeof value === 'number' ? value.toFixed(1) : value}</span>
                </div>
              {/each}
            </div>
          </div>
        {/if}

        <!-- Language Stats -->
        {#if analysisResult.language_stats}
          <div class="p-6 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
            <h4 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Language Statistics</h4>
            <div class="space-y-3">
              {#each Object.entries(analysisResult.language_stats) as [key, value]}
                <div class="flex justify-between items-center">
                  <span class="text-sm text-gray-600 dark:text-gray-400 capitalize">{key.replace('_', ' ')}</span>
                  <span class="font-mono text-sm font-medium text-gray-900 dark:text-white">{typeof value === 'number' ? value.toFixed(2) : value}</span>
                </div>
              {/each}
            </div>
          </div>
        {/if}
      </div>

      <!-- Word Frequency -->
      {#if analysisResult.word_frequency}
        <div class="p-6 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
          <h4 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Most Common Words</h4>
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
            {#each Object.entries(analysisResult.word_frequency).slice(0, 8) as [word, count]}
              <div class="flex justify-between items-center p-2 bg-gray-50 dark:bg-gray-700 rounded">
                <span class="text-sm font-medium text-gray-900 dark:text-white">{word}</span>
                <span class="text-sm text-gray-500 dark:text-gray-400">{count}</span>
              </div>
            {/each}
          </div>
        </div>
      {/if}
    </div>
  {:else}
    <div class="p-8 text-center text-gray-500 dark:text-gray-400 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg">
      <BarChart3 size={48} class="mx-auto mb-4 text-gray-300 dark:text-gray-600" />
      <p>Enter text above and click "Analyze Text" to see detailed statistics and analysis</p>
    </div>
  {/if}
</div>
