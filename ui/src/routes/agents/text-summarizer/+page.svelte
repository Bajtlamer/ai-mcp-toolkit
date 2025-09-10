<script>
  import { Zap, Play, Copy, Download } from 'lucide-svelte';

  let inputText = '';
  let inputUrl = '';
  let outputText = '';
  let isProcessing = false;
  let error = null;
  let compressionLevel = 'high';
  let summaryLength = 'short';
  let inputMode = 'text'; // 'text' or 'url'
  
  const compressionOptions = [
    { value: 'extreme', label: 'Extreme', description: 'Ultra-concise (< 5% of original)' },
    { value: 'high', label: 'High', description: 'Very concise (5-10% of original)' },
    { value: 'medium', label: 'Medium', description: 'Moderately concise (10-20% of original)' },
    { value: 'low', label: 'Low', description: 'Mildly concise (20-30% of original)' }
  ];
  
  const lengthOptions = [
    { value: 'short', label: 'Short', description: '1-2 sentences (20-50 words)' },
    { value: 'medium', label: 'Medium', description: '2-3 sentences (50-80 words)' },
    { value: 'long', label: 'Long', description: '1 paragraph (80-120 words)' }
  ];

  // Example texts for demonstration
  const examples = [
    "Artificial intelligence (AI) refers to the simulation of human intelligence in machines that are programmed to think like humans and mimic their actions. The term may also be applied to any machine that exhibits traits associated with a human mind such as learning and problem-solving. The ideal characteristic of artificial intelligence is its ability to rationalize and take actions that have the best chance of achieving a specific goal. A subset of artificial intelligence is machine learning, which refers to the concept that computer programs can automatically learn from and adapt to new data without being assisted by humans. Deep learning techniques enable this automatic learning through the absorption of huge amounts of unstructured data such as text, images, or video.",
    "Climate change refers to long-term shifts in global or regional climate patterns. Since the mid-20th century, scientists have observed that the pace of climate change has increased significantly, largely due to human activities, particularly fossil fuel burning, which produces heat-trapping greenhouse gases. The consequences of climate change are diverse and complex, affecting ecosystems, weather patterns, ice caps, and sea levels. Rising global temperatures have led to more frequent extreme weather events, including hurricanes, droughts, heatwaves, and flooding. These changes pose significant challenges to agriculture, water resources, human health, and biodiversity. International efforts to address climate change include the Paris Agreement, which aims to limit global warming to well below 2 degrees Celsius above pre-industrial levels.",
    "The Renaissance was a period of European cultural, artistic, political and economic rebirth following the Middle Ages. Generally described as taking place from the 14th century to the 17th century, the Renaissance promoted the rediscovery of classical philosophy, literature and art. Some of the greatest thinkers, authors, statesmen, scientists and artists in human history thrived during this era, while global exploration opened up new lands and cultures to European commerce. The Renaissance is credited with bridging the gap between the Middle Ages and modern-day civilization. Renaissance art was characterized by realism and human emotion, a departure from the Byzantine and gothic styles that dominated the Middle Ages.",
    "Renewable energy comes from sources that are naturally replenishing and virtually inexhaustible in duration but limited in the amount of energy that is available per unit of time. The major types of renewable energy sources are solar energy, wind energy, hydroelectric energy, geothermal energy, and biomass energy. Solar energy harnesses the power of the sun through photovoltaic cells or solar thermal collectors. Wind energy uses turbines to convert the kinetic energy of moving air into electricity. Hydroelectric power generates electricity by using the flow of water to spin turbine generators. Geothermal energy taps into the Earth's internal heat, while biomass energy comes from organic materials. These renewable sources are increasingly important as the world seeks to reduce greenhouse gas emissions and combat climate change while meeting growing energy demands."
  ];

  async function summarizeText() {
    // Validate input based on mode
    if (inputMode === 'text' && !inputText.trim()) return;
    if (inputMode === 'url' && !inputUrl.trim()) return;
    
    isProcessing = true;
    error = null;
    
    try {
      // Build arguments based on input mode
      const args = {
        length: summaryLength,
        compression_ratio: compressionLevel
      };
      
      if (inputMode === 'text') {
        args.text = inputText;
      } else {
        args.url = inputUrl;
      }
      
      const response = await fetch('http://localhost:8000/tools/execute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: 'summarize_text',
          arguments: args
        })
      });

      const result = await response.json();
      
      if (result.success) {
        outputText = result.result;
      } else {
        error = result.error || 'Failed to summarize text';
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
    a.download = 'text_summary.txt';
    a.click();
    URL.revokeObjectURL(url);
  }
</script>

<svelte:head>
  <title>Text Summarizer - AI MCP Toolkit</title>
</svelte:head>

<div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
  <!-- Header -->
  <div class="mb-8">
    <div class="flex items-center space-x-3 mb-4">
      <div class="w-12 h-12 bg-gradient-to-br from-orange-500 to-orange-600 rounded-xl flex items-center justify-center">
        <Zap size={24} class="text-white" />
      </div>
      <div>
        <h1 class="text-3xl font-bold text-gray-900 dark:text-white">Text Summarizer</h1>
        <p class="text-gray-600 dark:text-gray-400">Generate concise summaries of longer texts</p>
      </div>
    </div>
  </div>

  <!-- Examples -->
  <div class="mb-6">
    <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-3">Quick Examples</h2>
    <div class="grid grid-cols-1 gap-3">
      {#each examples as example, index}
        <button
          on:click={() => useExample(example)}
          class="p-3 text-left text-sm bg-gray-50 dark:bg-gray-800 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
        >
          <div class="font-medium text-gray-700 dark:text-gray-300 mb-1">
            Example {index + 1}: {example.split(' ').slice(0, 3).join(' ')}...
          </div>
          <span class="text-gray-600 dark:text-gray-400 line-clamp-2">{example}</span>
        </button>
      {/each}
    </div>
  </div>

  <!-- Input/Output Interface -->
  <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
    <!-- Input -->
    <div class="space-y-4">
      <!-- Input Mode Tabs -->
      <div class="border-b border-gray-200 dark:border-gray-700">
        <nav class="-mb-px flex space-x-8">
          <button
            on:click={() => inputMode = 'text'}
            class="{inputMode === 'text' ? 'border-orange-500 text-orange-600 dark:text-orange-400' : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'} whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm transition-colors"
          >
            Text Input
          </button>
          <button
            on:click={() => inputMode = 'url'}
            class="{inputMode === 'url' ? 'border-orange-500 text-orange-600 dark:text-orange-400' : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'} whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm transition-colors"
          >
            URL Input
          </button>
        </nav>
      </div>

      <!-- Input Header -->
      <div class="flex items-center justify-between">
        <h3 class="text-lg font-medium text-gray-900 dark:text-white">
          {inputMode === 'text' ? 'Input Text' : 'Website URL'}
        </h3>
        <span class="text-sm text-gray-500 dark:text-gray-400">
          {inputMode === 'text' ? `${inputText.length} characters` : inputUrl ? '✓ URL entered' : 'Enter URL'}
        </span>
      </div>
      
      <!-- Text Input Mode -->
      {#if inputMode === 'text'}
        <textarea
          bind:value={inputText}
          placeholder="Enter long text to summarize..."
          class="w-full h-64 px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent resize-none bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
        ></textarea>
      {:else}
        <!-- URL Input Mode -->
        <div class="space-y-4">
          <input
            type="url"
            bind:value={inputUrl}
            placeholder="https://example.com/article-to-summarize"
            class="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
          />
          
          <div class="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
            <div class="flex items-start space-x-3">
              <div class="flex-shrink-0">
                <svg class="w-5 h-5 text-blue-600 dark:text-blue-400 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"></path>
                </svg>
              </div>
              <div class="text-sm text-blue-700 dark:text-blue-300">
                <p class="font-medium">URL Input Tips:</p>
                <ul class="mt-1 list-disc list-inside space-y-1">
                  <li>Enter any web article, blog post, or news article URL</li>
                  <li>The system will extract the main content automatically</li>
                  <li>Works best with content-rich pages (articles, documentation, etc.)</li>
                  <li>Page title will be included in the analysis context</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      {/if}
      
      <!-- Summary Options -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <!-- Compression Level -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Compression Level
          </label>
          <select
            bind:value={compressionLevel}
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm"
          >
            {#each compressionOptions as option}
              <option value={option.value}>{option.label} - {option.description}</option>
            {/each}
          </select>
        </div>
        
        <!-- Summary Length -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Summary Length
          </label>
          <select
            bind:value={summaryLength}
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm"
          >
            {#each lengthOptions as option}
              <option value={option.value}>{option.label} - {option.description}</option>
            {/each}
          </select>
        </div>
      </div>
      
      <button
        on:click={summarizeText}
        disabled={(inputMode === 'text' && !inputText.trim()) || (inputMode === 'url' && !inputUrl.trim()) || isProcessing}
        class="w-full flex items-center justify-center px-4 py-2 bg-orange-600 hover:bg-orange-700 disabled:bg-gray-400 text-white font-medium rounded-lg transition-colors"
      >
        {#if isProcessing}
          <div class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
          {inputMode === 'url' ? 'Fetching & Summarizing...' : 'Summarizing...'}
        {:else}
          <Play size={16} class="mr-2" />
          {inputMode === 'url' ? 'Summarize from URL' : 'Summarize Text'}
        {/if}
      </button>
    </div>

    <!-- Output -->
    <div class="space-y-4">
      <div class="flex items-center justify-between">
        <div>
          <h3 class="text-lg font-medium text-gray-900 dark:text-white">Summary</h3>
          {#if outputText && inputText}
            <div class="text-sm text-gray-500 dark:text-gray-400 mt-1">
              Compressed from {inputText.length} to {outputText.length} characters 
              ({Math.round((outputText.length / inputText.length) * 100)}% of original)
            </div>
          {/if}
        </div>
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
          <pre class="text-gray-900 dark:text-white whitespace-pre-wrap text-sm">{outputText}</pre>
        {:else}
          <p class="text-gray-500 dark:text-gray-400 italic">
            Text summary will appear here...
          </p>
        {/if}
      </div>
    </div>
  </div>

  <!-- Features -->
  <div class="mt-12">
    <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-6">Features</h2>
    <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
      <div class="p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
        <h3 class="font-medium text-gray-900 dark:text-white mb-2">Aggressive Compression</h3>
        <p class="text-sm text-gray-600 dark:text-gray-400">
          Reduces text to 5-30% of original length while preserving key information.
        </p>
      </div>
      <div class="p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
        <h3 class="font-medium text-gray-900 dark:text-white mb-2">Customizable Compression</h3>
        <p class="text-sm text-gray-600 dark:text-gray-400">
          Choose from extreme, high, medium, or low compression levels.
        </p>
      </div>
      <div class="p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
        <h3 class="font-medium text-gray-900 dark:text-white mb-2">Smart Extraction</h3>
        <p class="text-sm text-gray-600 dark:text-gray-400">
          Identifies and retains only the most essential information.
        </p>
      </div>
      <div class="p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
        <h3 class="font-medium text-gray-900 dark:text-white mb-2">Length Control</h3>
        <p class="text-sm text-gray-600 dark:text-gray-400">
          Choose exact output length: short, medium, or long summaries.
        </p>
      </div>
    </div>
  </div>
</div>
