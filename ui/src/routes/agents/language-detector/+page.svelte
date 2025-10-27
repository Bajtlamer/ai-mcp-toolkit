<script>
  import { Languages, Play, Download, Database } from 'lucide-svelte';
  import ResourceSelector from '$lib/components/ResourceSelector.svelte';
  import * as resourceAPI from '$lib/services/resources';

  let inputText = '';
  let detectionResult = null;
  let isProcessing = false;
  let error = null;
  let inputMode = 'text'; // 'text' or 'resource'
  let selectedResourceUri = '';

  // Example texts for demonstration
  const examples = [
    { text: "Hello, how are you today?", language: "English" },
    { text: "Bonjour, comment allez-vous?", language: "French" },
    { text: "Hola, ¿cómo estás hoy?", language: "Spanish" },
    { text: "Guten Tag, wie geht es Ihnen?", language: "German" },
    { text: "Ciao, come stai oggi?", language: "Italian" },
    { text: "こんにちは、元気ですか？", language: "Japanese" },
    { text: "Привет, как дела?", language: "Russian" },
    { text: "你好，你今天怎么样？", language: "Chinese" }
  ];

  async function detectLanguage() {
    if (inputMode === 'text' && !inputText.trim()) return;
    if (inputMode === 'resource' && !selectedResourceUri) return;
    
    isProcessing = true;
    error = null;
    detectionResult = null;
    
    try {
      let textToDetect = inputText;
      
      if (inputMode === 'resource') {
        const resource = await resourceAPI.getResource(selectedResourceUri);
        if (resource && resource.text) {
          textToDetect = resource.text;
        } else {
          throw new Error('Could not fetch resource content');
        }
      }
      
      const response = await fetch('/api/tools/execute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: 'detect_language',
          arguments: {
            text: textToDetect
          }
        })
      });

      const result = await response.json();
      
      if (result.success) {
        detectionResult = JSON.parse(result.result);
      } else {
        error = result.error || 'Failed to detect language';
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

  function downloadResult() {
    const data = JSON.stringify(detectionResult, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'language_detection.json';
    a.click();
    URL.revokeObjectURL(url);
  }

  function getConfidenceColor(confidence) {
    if (confidence >= 0.9) return 'text-green-600 dark:text-green-400';
    if (confidence >= 0.7) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-red-600 dark:text-red-400';
  }

  function getConfidenceLabel(confidence) {
    if (confidence >= 0.9) return 'Very High';
    if (confidence >= 0.7) return 'High';
    if (confidence >= 0.5) return 'Medium';
    return 'Low';
  }
</script>

<svelte:head>
  <title>Language Detector - AI MCP Toolkit</title>
</svelte:head>

<div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
  <!-- Header -->
  <div class="mb-8">
    <div class="flex items-center space-x-3 mb-4">
      <div class="w-12 h-12 bg-gradient-to-br from-indigo-500 to-indigo-600 rounded-xl flex items-center justify-center">
        <Languages size={24} class="text-white" />
      </div>
      <div>
        <h1 class="text-3xl font-bold text-gray-900 dark:text-white">Language Detector</h1>
        <p class="text-gray-600 dark:text-gray-400">Detect the language of input text</p>
      </div>
    </div>
  </div>

  <!-- Examples -->
  <div class="mb-6">
    <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-3">Quick Examples</h2>
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
      {#each examples as example}
        <button
          on:click={() => useExample(example.text)}
          class="p-3 text-left text-sm bg-gray-50 dark:bg-gray-800 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
        >
          <div class="font-medium text-indigo-600 dark:text-indigo-400 mb-1">{example.language}</div>
          <span class="text-gray-600 dark:text-gray-400 text-xs">{example.text}</span>
        </button>
      {/each}
    </div>
  </div>

  <!-- Input Interface -->
  <div class="mb-6">
    <div class="space-y-4">
      <!-- Input Mode Tabs -->
      <div class="border-b border-gray-200 dark:border-gray-700">
        <nav class="-mb-px flex space-x-8">
          <button
            on:click={() => inputMode = 'text'}
            class="{inputMode === 'text' ? 'border-indigo-500 text-indigo-600 dark:text-indigo-400' : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'} whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm transition-colors"
          >
            Text Input
          </button>
          <button
            on:click={() => inputMode = 'resource'}
            class="{inputMode === 'resource' ? 'border-indigo-500 text-indigo-600 dark:text-indigo-400' : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'} whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm transition-colors"
          >
            <Database size={14} class="inline mr-1" />
            From Resource
          </button>
        </nav>
      </div>
      
      <div class="flex items-center justify-between">
        <h3 class="text-lg font-medium text-gray-900 dark:text-white">
          {inputMode === 'text' ? 'Input Text' : 'Select Resource'}
        </h3>
        <span class="text-sm text-gray-500 dark:text-gray-400">
          {inputMode === 'text' ? `${inputText.length} characters` : (selectedResourceUri ? '✓ Resource selected' : 'Choose resource')}
        </span>
      </div>
      
      {#if inputMode === 'text'}
        <textarea
          bind:value={inputText}
          placeholder="Enter text in any language to detect..."
          class="w-full h-32 px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
        ></textarea>
      {:else}
        <ResourceSelector 
          bind:selectedResourceUri
          label="Select a resource to detect language"
          infoText="Select any uploaded text file, PDF, or URL resource"
        />
      {/if}
      
      <div class="flex space-x-3">
        <button
          on:click={detectLanguage}
          disabled={(inputMode === 'text' && !inputText.trim()) || (inputMode === 'resource' && !selectedResourceUri) || isProcessing}
          class="flex items-center justify-center px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-400 text-white font-medium rounded-lg transition-colors"
        >
          {#if isProcessing}
            <div class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
            {inputMode === 'resource' ? 'Loading & Detecting...' : 'Detecting...'}
          {:else}
            <Play size={16} class="mr-2" />
            {inputMode === 'resource' ? 'Detect Language from Resource' : 'Detect Language'}
          {/if}
        </button>
        
        {#if detectionResult}
          <button
            on:click={downloadResult}
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
  {:else if detectionResult}
    <div class="space-y-6">
      <!-- Primary Result -->
      {#if detectionResult.language}
        <div class="p-6 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Detected Language</h3>
            {#if detectionResult.confidence}
              <span class="px-3 py-1 text-sm rounded-full bg-indigo-100 dark:bg-indigo-900 {getConfidenceColor(detectionResult.confidence)}">
                {getConfidenceLabel(detectionResult.confidence)} Confidence
              </span>
            {/if}
          </div>
          
          <div class="flex items-center space-x-4">
            <div class="text-3xl font-bold text-indigo-600 dark:text-indigo-400">
              {detectionResult.language}
            </div>
            {#if detectionResult.confidence}
              <div class="text-lg text-gray-600 dark:text-gray-400">
                {(detectionResult.confidence * 100).toFixed(1)}% confidence
              </div>
            {/if}
          </div>
          
          {#if detectionResult.iso_code}
            <div class="mt-2 text-sm text-gray-500 dark:text-gray-400">
              ISO Code: <span class="font-mono">{detectionResult.iso_code}</span>
            </div>
          {/if}
        </div>
      {/if}

      <!-- Alternative Languages -->
      {#if detectionResult.alternatives && detectionResult.alternatives.length > 0}
        <div class="p-6 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
          <h4 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Alternative Possibilities</h4>
          <div class="space-y-3">
            {#each detectionResult.alternatives.slice(0, 5) as alt}
              <div class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div class="flex items-center space-x-3">
                  <span class="font-medium text-gray-900 dark:text-white">{alt.language}</span>
                  {#if alt.iso_code}
                    <span class="text-sm text-gray-500 dark:text-gray-400 font-mono">{alt.iso_code}</span>
                  {/if}
                </div>
                {#if alt.confidence}
                  <div class="text-sm {getConfidenceColor(alt.confidence)}">
                    {(alt.confidence * 100).toFixed(1)}%
                  </div>
                {/if}
              </div>
            {/each}
          </div>
        </div>
      {/if}

      <!-- Statistics -->
      {#if detectionResult.statistics}
        <div class="p-6 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
          <h4 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Detection Statistics</h4>
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
            {#each Object.entries(detectionResult.statistics) as [key, value]}
              <div class="text-center">
                <div class="text-2xl font-bold text-indigo-600 dark:text-indigo-400">{value}</div>
                <div class="text-sm text-gray-500 dark:text-gray-400 capitalize">{key.replace('_', ' ')}</div>
              </div>
            {/each}
          </div>
        </div>
      {/if}
    </div>
  {:else}
    <div class="p-8 text-center text-gray-500 dark:text-gray-400 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg">
      <Languages size={48} class="mx-auto mb-4 text-gray-300 dark:text-gray-600" />
      <p>Enter text above and click "Detect Language" to identify the language</p>
    </div>
  {/if}

  <!-- Supported Languages -->
  <div class="mt-12">
    <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-6">Features</h2>
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div class="p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
        <h3 class="font-medium text-gray-900 dark:text-white mb-2">Multi-Language Support</h3>
        <p class="text-sm text-gray-600 dark:text-gray-400">
          Detects over 50 languages with high accuracy.
        </p>
      </div>
      <div class="p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
        <h3 class="font-medium text-gray-900 dark:text-white mb-2">Confidence Scoring</h3>
        <p class="text-sm text-gray-600 dark:text-gray-400">
          Provides confidence levels for detection accuracy.
        </p>
      </div>
      <div class="p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
        <h3 class="font-medium text-gray-900 dark:text-white mb-2">Alternative Suggestions</h3>
        <p class="text-sm text-gray-600 dark:text-gray-400">
          Shows possible alternative language matches.
        </p>
      </div>
    </div>
  </div>
</div>
