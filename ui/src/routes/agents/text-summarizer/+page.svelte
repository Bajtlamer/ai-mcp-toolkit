<script>
  import { Zap, Play, Copy, Download } from 'lucide-svelte';

  let inputText = '';
  let outputText = '';
  let isProcessing = false;
  let error = null;

  // Example texts for demonstration
  const examples = [
    "Artificial intelligence (AI) refers to the simulation of human intelligence in machines that are programmed to think like humans and mimic their actions. The term may also be applied to any machine that exhibits traits associated with a human mind such as learning and problem-solving. The ideal characteristic of artificial intelligence is its ability to rationalize and take actions that have the best chance of achieving a specific goal. A subset of artificial intelligence is machine learning, which refers to the concept that computer programs can automatically learn from and adapt to new data without being assisted by humans. Deep learning techniques enable this automatic learning through the absorption of huge amounts of unstructured data such as text, images, or video.",
    "Climate change refers to long-term shifts in global or regional climate patterns. Since the mid-20th century, scientists have observed that the pace of climate change has increased significantly, largely due to human activities, particularly fossil fuel burning, which produces heat-trapping greenhouse gases. The consequences of climate change are diverse and complex, affecting ecosystems, weather patterns, ice caps, and sea levels. Rising global temperatures have led to more frequent extreme weather events, including hurricanes, droughts, heatwaves, and flooding. These changes pose significant challenges to agriculture, water resources, human health, and biodiversity. International efforts to address climate change include the Paris Agreement, which aims to limit global warming to well below 2 degrees Celsius above pre-industrial levels.",
    "The Renaissance was a period of European cultural, artistic, political and economic rebirth following the Middle Ages. Generally described as taking place from the 14th century to the 17th century, the Renaissance promoted the rediscovery of classical philosophy, literature and art. Some of the greatest thinkers, authors, statesmen, scientists and artists in human history thrived during this era, while global exploration opened up new lands and cultures to European commerce. The Renaissance is credited with bridging the gap between the Middle Ages and modern-day civilization. Renaissance art was characterized by realism and human emotion, a departure from the Byzantine and gothic styles that dominated the Middle Ages.",
    "Renewable energy comes from sources that are naturally replenishing and virtually inexhaustible in duration but limited in the amount of energy that is available per unit of time. The major types of renewable energy sources are solar energy, wind energy, hydroelectric energy, geothermal energy, and biomass energy. Solar energy harnesses the power of the sun through photovoltaic cells or solar thermal collectors. Wind energy uses turbines to convert the kinetic energy of moving air into electricity. Hydroelectric power generates electricity by using the flow of water to spin turbine generators. Geothermal energy taps into the Earth's internal heat, while biomass energy comes from organic materials. These renewable sources are increasingly important as the world seeks to reduce greenhouse gas emissions and combat climate change while meeting growing energy demands."
  ];

  async function summarizeText() {
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
          name: 'summarize_text',
          arguments: {
            text: inputText
          }
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
      <div class="flex items-center justify-between">
        <h3 class="text-lg font-medium text-gray-900 dark:text-white">Input Text</h3>
        <span class="text-sm text-gray-500 dark:text-gray-400">
          {inputText.length} characters
        </span>
      </div>
      
      <textarea
        bind:value={inputText}
        placeholder="Enter long text to summarize..."
        class="w-full h-64 px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent resize-none bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
      ></textarea>
      
      <button
        on:click={summarizeText}
        disabled={!inputText.trim() || isProcessing}
        class="w-full flex items-center justify-center px-4 py-2 bg-orange-600 hover:bg-orange-700 disabled:bg-gray-400 text-white font-medium rounded-lg transition-colors"
      >
        {#if isProcessing}
          <div class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
          Summarizing...
        {:else}
          <Play size={16} class="mr-2" />
          Summarize Text
        {/if}
      </button>
    </div>

    <!-- Output -->
    <div class="space-y-4">
      <div class="flex items-center justify-between">
        <h3 class="text-lg font-medium text-gray-900 dark:text-white">Summary</h3>
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
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div class="p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
        <h3 class="font-medium text-gray-900 dark:text-white mb-2">Concise Summaries</h3>
        <p class="text-sm text-gray-600 dark:text-gray-400">
          Creates brief, coherent summaries that capture the main points.
        </p>
      </div>
      <div class="p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
        <h3 class="font-medium text-gray-900 dark:text-white mb-2">Key Point Extraction</h3>
        <p class="text-sm text-gray-600 dark:text-gray-400">
          Identifies and highlights the most important information.
        </p>
      </div>
      <div class="p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
        <h3 class="font-medium text-gray-900 dark:text-white mb-2">Context Preservation</h3>
        <p class="text-sm text-gray-600 dark:text-gray-400">
          Maintains the original meaning and context in the summary.
        </p>
      </div>
    </div>
  </div>
</div>
