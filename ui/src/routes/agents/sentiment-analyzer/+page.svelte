<script>
  import { Heart, Play, Download } from 'lucide-svelte';

  let inputText = '';
  let sentimentResult = null;
  let isProcessing = false;
  let error = null;

  // Example texts for demonstration
  const examples = [
    { text: "I absolutely love this product! It's amazing and works perfectly.", sentiment: "Very Positive" },
    { text: "This is okay, nothing special but it works fine.", sentiment: "Neutral" },
    { text: "I'm really disappointed with this purchase. It doesn't work as expected.", sentiment: "Negative" },
    { text: "What a fantastic day! The weather is beautiful and I'm feeling great.", sentiment: "Positive" },
    { text: "I'm frustrated and angry about the poor customer service I received.", sentiment: "Very Negative" },
    { text: "The movie was decent. Some parts were good, others not so much.", sentiment: "Mixed" }
  ];

  async function analyzeSentiment() {
    if (!inputText.trim()) return;
    
    isProcessing = true;
    error = null;
    sentimentResult = null;
    
    try {
      const response = await fetch('http://localhost:8000/tools/execute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: 'analyze_sentiment',
          arguments: {
            text: inputText
          }
        })
      });

      const result = await response.json();
      
      if (result.success) {
        sentimentResult = JSON.parse(result.result);
      } else {
        error = result.error || 'Failed to analyze sentiment';
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

  function downloadResult() {
    const data = JSON.stringify(sentimentResult, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'sentiment_analysis.json';
    a.click();
    URL.revokeObjectURL(url);
  }

  function getSentimentColor(sentiment) {
    if (!sentiment) return 'text-gray-500';
    const s = sentiment.toLowerCase();
    if (s.includes('very positive') || s.includes('extremely positive')) return 'text-green-600 dark:text-green-400';
    if (s.includes('positive')) return 'text-green-500 dark:text-green-400';
    if (s.includes('very negative') || s.includes('extremely negative')) return 'text-red-600 dark:text-red-400';
    if (s.includes('negative')) return 'text-red-500 dark:text-red-400';
    if (s.includes('neutral')) return 'text-gray-500 dark:text-gray-400';
    return 'text-yellow-500 dark:text-yellow-400';
  }

  function getSentimentIcon(sentiment) {
    if (!sentiment) return '😐';
    const s = sentiment.toLowerCase();
    if (s.includes('very positive') || s.includes('extremely positive')) return '😍';
    if (s.includes('positive')) return '😊';
    if (s.includes('very negative') || s.includes('extremely negative')) return '😡';
    if (s.includes('negative')) return '😞';
    if (s.includes('neutral')) return '😐';
    return '🤔';
  }

  function getScoreColor(score) {
    if (score >= 0.6) return 'text-green-600 dark:text-green-400';
    if (score >= 0.2) return 'text-green-500 dark:text-green-400';
    if (score >= -0.2) return 'text-gray-500 dark:text-gray-400';
    if (score >= -0.6) return 'text-red-500 dark:text-red-400';
    return 'text-red-600 dark:text-red-400';
  }
</script>

<svelte:head>
  <title>Sentiment Analyzer - AI MCP Toolkit</title>
</svelte:head>

<div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
  <!-- Header -->
  <div class="mb-8">
    <div class="flex items-center space-x-3 mb-4">
      <div class="w-12 h-12 bg-gradient-to-br from-pink-500 to-pink-600 rounded-xl flex items-center justify-center">
        <Heart size={24} class="text-white" />
      </div>
      <div>
        <h1 class="text-3xl font-bold text-gray-900 dark:text-white">Sentiment Analyzer</h1>
        <p class="text-gray-600 dark:text-gray-400">Analyze emotional tone and sentiment of text</p>
      </div>
    </div>
  </div>

  <!-- Examples -->
  <div class="mb-6">
    <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-3">Quick Examples</h2>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
      {#each examples as example}
        <button
          on:click={() => useExample(example.text)}
          class="p-3 text-left text-sm bg-gray-50 dark:bg-gray-800 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
        >
          <div class="flex items-center space-x-2 mb-1">
            <span class="text-lg">{getSentimentIcon(example.sentiment)}</span>
            <span class="font-medium {getSentimentColor(example.sentiment)}">{example.sentiment}</span>
          </div>
          <span class="text-gray-600 dark:text-gray-400 line-clamp-2">{example.text}</span>
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
        placeholder="Enter text to analyze sentiment..."
        class="w-full h-32 px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-transparent resize-none bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
      ></textarea>
      
      <div class="flex space-x-3">
        <button
          on:click={analyzeSentiment}
          disabled={!inputText.trim() || isProcessing}
          class="flex items-center justify-center px-4 py-2 bg-pink-600 hover:bg-pink-700 disabled:bg-gray-400 text-white font-medium rounded-lg transition-colors"
        >
          {#if isProcessing}
            <div class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
            Analyzing...
          {:else}
            <Play size={16} class="mr-2" />
            Analyze Sentiment
          {/if}
        </button>
        
        {#if sentimentResult}
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
  {:else if sentimentResult}
    <div class="space-y-6">
      <!-- Primary Result -->
      <div class="p-6 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Sentiment Analysis</h3>
        
        <div class="flex items-center space-x-4 mb-4">
          {#if sentimentResult.sentiment}
            <div class="text-4xl">{getSentimentIcon(sentimentResult.sentiment)}</div>
            <div>
              <div class="text-2xl font-bold {getSentimentColor(sentimentResult.sentiment)}">
                {sentimentResult.sentiment}
              </div>
              {#if sentimentResult.score !== undefined}
                <div class="text-lg {getScoreColor(sentimentResult.score)}">
                  Score: {sentimentResult.score.toFixed(3)}
                </div>
              {/if}
            </div>
          {/if}
        </div>

        <!-- Score Bar -->
        {#if sentimentResult.score !== undefined}
          <div class="mb-4">
            <div class="flex justify-between text-sm text-gray-600 dark:text-gray-400 mb-1">
              <span>Very Negative</span>
              <span>Neutral</span>
              <span>Very Positive</span>
            </div>
            <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
              <div 
                class="h-3 rounded-full transition-all duration-300 {
                  sentimentResult.score >= 0 ? 'bg-green-500' : 'bg-red-500'
                }"
                style="width: {Math.abs(sentimentResult.score) * 50 + 50}%; margin-left: {sentimentResult.score < 0 ? (50 + sentimentResult.score * 50) + '%' : '50%'}"
              ></div>
            </div>
            <div class="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-1">
              <span>-1.0</span>
              <span>0.0</span>
              <span>+1.0</span>
            </div>
          </div>
        {/if}
      </div>

      <!-- Detailed Breakdown -->
      {#if sentimentResult.breakdown}
        <div class="p-6 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
          <h4 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Emotional Breakdown</h4>
          <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
            {#each Object.entries(sentimentResult.breakdown) as [emotion, score]}
              <div class="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div class="text-sm font-medium text-gray-900 dark:text-white capitalize">{emotion}</div>
                <div class="text-lg font-bold {getScoreColor(score)}">{(score * 100).toFixed(1)}%</div>
                <div class="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2 mt-1">
                  <div 
                    class="h-2 rounded-full bg-pink-500"
                    style="width: {Math.abs(score) * 100}%"
                  ></div>
                </div>
              </div>
            {/each}
          </div>
        </div>
      {/if}

      <!-- Confidence & Statistics -->
      {#if sentimentResult.confidence || sentimentResult.statistics}
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          {#if sentimentResult.confidence}
            <div class="p-6 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
              <h4 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Confidence</h4>
              <div class="text-3xl font-bold text-pink-600 dark:text-pink-400">
                {(sentimentResult.confidence * 100).toFixed(1)}%
              </div>
              <div class="text-sm text-gray-500 dark:text-gray-400 mt-1">
                Analysis confidence level
              </div>
            </div>
          {/if}

          {#if sentimentResult.statistics}
            <div class="p-6 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
              <h4 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Statistics</h4>
              <div class="space-y-2">
                {#each Object.entries(sentimentResult.statistics) as [key, value]}
                  <div class="flex justify-between">
                    <span class="text-sm text-gray-600 dark:text-gray-400 capitalize">{key.replace('_', ' ')}</span>
                    <span class="font-mono text-sm font-medium text-gray-900 dark:text-white">{value}</span>
                  </div>
                {/each}
              </div>
            </div>
          {/if}
        </div>
      {/if}
    </div>
  {:else}
    <div class="p-8 text-center text-gray-500 dark:text-gray-400 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg">
      <Heart size={48} class="mx-auto mb-4 text-gray-300 dark:text-gray-600" />
      <p>Enter text above and click "Analyze Sentiment" to understand the emotional tone</p>
    </div>
  {/if}

  <!-- Features -->
  <div class="mt-12">
    <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-6">Features</h2>
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div class="p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
        <h3 class="font-medium text-gray-900 dark:text-white mb-2">Emotion Detection</h3>
        <p class="text-sm text-gray-600 dark:text-gray-400">
          Identifies specific emotions beyond simple positive/negative.
        </p>
      </div>
      <div class="p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
        <h3 class="font-medium text-gray-900 dark:text-white mb-2">Confidence Scoring</h3>
        <p class="text-sm text-gray-600 dark:text-gray-400">
          Provides confidence levels for sentiment accuracy.
        </p>
      </div>
      <div class="p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
        <h3 class="font-medium text-gray-900 dark:text-white mb-2">Detailed Analysis</h3>
        <p class="text-sm text-gray-600 dark:text-gray-400">
          Breaks down sentiment into emotional components.
        </p>
      </div>
    </div>
  </div>
</div>
