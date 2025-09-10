<script>
  import { Heart, Play, Download, Wand2, ArrowRight, RotateCcw } from 'lucide-svelte';

  let inputText = '';
  let sentimentResult = null;
  let isProcessing = false;
  let error = null;
  
  // Sentiment transformation variables
  let transformedText = '';
  let targetSentiment = 'positive';
  let isTransforming = false;
  let transformError = null;

  // Example texts for demonstration
  const examples = [
    { text: "I absolutely love this product! It's amazing and works perfectly.", sentiment: "Very Positive" },
    { text: "This is okay, nothing special but it works fine.", sentiment: "Neutral" },
    { text: "I'm really disappointed with this purchase. It doesn't work as expected.", sentiment: "Negative" },
    { text: "What a fantastic day! The weather is beautiful and I'm feeling great.", sentiment: "Positive" },
    { text: "I'm frustrated and angry about the poor customer service I received.", sentiment: "Very Negative" },
    { text: "The movie was decent. Some parts were good, others not so much.", sentiment: "Mixed" }
  ];
  
  // Target sentiment options for transformation
  const sentimentOptions = [
    { value: 'positive', label: 'Positive', icon: '😊', description: 'Upbeat and optimistic tone' },
    { value: 'negative', label: 'Negative', icon: '😞', description: 'Pessimistic or critical tone' },
    { value: 'neutral', label: 'Neutral', icon: '😐', description: 'Balanced and objective tone' },
    { value: 'professional', label: 'Professional', icon: '💼', description: 'Formal business tone' },
    { value: 'friendly', label: 'Friendly', icon: '😄', description: 'Warm and approachable tone' },
    { value: 'enthusiastic', label: 'Enthusiastic', icon: '🎉', description: 'Energetic and excited tone' }
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
  
  async function transformSentiment() {
    if (!inputText.trim()) return;
    
    isTransforming = true;
    transformError = null;
    transformedText = '';
    
    try {
      const response = await fetch('http://localhost:8000/tools/execute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: 'transform_sentiment',
          arguments: {
            text: inputText,
            target_sentiment: targetSentiment,
            preserve_meaning: true
          }
        })
      });

      const result = await response.json();
      
      if (result.success) {
        transformedText = result.result;
      } else {
        transformError = result.error || 'Failed to transform sentiment';
      }
    } catch (err) {
      transformError = 'Failed to connect to server. Make sure the MCP server is running on port 8000.';
      console.error('Transform error:', err);
    } finally {
      isTransforming = false;
    }
  }
  
  function copyTransformedText() {
    if (transformedText) {
      navigator.clipboard.writeText(transformedText);
      // You might want to add a toast notification here
    }
  }
  
  function useTransformedAsInput() {
    if (transformedText) {
      inputText = transformedText;
      transformedText = '';
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
        <h1 class="text-3xl font-bold text-gray-900 dark:text-white">Sentiment Analyzer & Transformer</h1>
        <p class="text-gray-600 dark:text-gray-400">Analyze emotional tone and transform text to match desired sentiment</p>
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
  
  <!-- Sentiment Transformation Section -->
  <div class="mb-6 bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 rounded-xl p-6 border border-purple-100 dark:border-purple-800">
    <div class="flex items-center space-x-3 mb-4">
      <div class="w-10 h-10 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg flex items-center justify-center">
        <Wand2 size={20} class="text-white" />
      </div>
      <div>
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Sentiment Transformation</h3>
        <p class="text-sm text-gray-600 dark:text-gray-400">Rewrite your text to match a desired sentiment tone</p>
      </div>
    </div>
    
    <!-- Target Sentiment Selection -->
    <div class="mb-4">
      <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
        Target Sentiment
      </label>
      <div class="grid grid-cols-2 md:grid-cols-3 gap-3">
        {#each sentimentOptions as option}
          <label class="relative cursor-pointer">
            <input
              type="radio"
              bind:group={targetSentiment}
              value={option.value}
              class="sr-only peer"
            />
            <div class="p-3 border-2 border-gray-200 dark:border-gray-700 rounded-lg peer-checked:border-purple-500 peer-checked:bg-purple-50 dark:peer-checked:bg-purple-900/30 hover:border-gray-300 dark:hover:border-gray-600 transition-all">
              <div class="flex items-center space-x-2 mb-1">
                <span class="text-lg">{option.icon}</span>
                <span class="font-medium text-gray-900 dark:text-white">{option.label}</span>
              </div>
              <p class="text-xs text-gray-500 dark:text-gray-400">{option.description}</p>
            </div>
          </label>
        {/each}
      </div>
    </div>
    
    <!-- Transform Actions -->
    <div class="flex flex-col sm:flex-row gap-3">
      <button
        on:click={transformSentiment}
        disabled={!inputText.trim() || isTransforming}
        class="flex items-center justify-center px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 disabled:from-gray-400 disabled:to-gray-400 text-white font-medium rounded-lg transition-all"
      >
        {#if isTransforming}
          <div class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
          Transforming...
        {:else}
          <Wand2 size={16} class="mr-2" />
          Transform to {sentimentOptions.find(opt => opt.value === targetSentiment)?.label}
        {/if}
      </button>
      
      {#if transformedText}
        <button
          on:click={copyTransformedText}
          class="flex items-center px-3 py-2 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600 rounded-lg transition-colors"
        >
          <Download size={14} class="mr-2" />
          Copy Result
        </button>
        
        <button
          on:click={useTransformedAsInput}
          class="flex items-center px-3 py-2 bg-green-100 dark:bg-green-900/30 hover:bg-green-200 dark:hover:bg-green-800/30 text-green-700 dark:text-green-300 border border-green-300 dark:border-green-700 rounded-lg transition-colors"
        >
          <RotateCcw size={14} class="mr-2" />
          Use as Input
        </button>
      {/if}
    </div>
    
    <!-- Transformed Text Result -->
    {#if transformError}
      <div class="mt-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
        <div class="text-red-600 dark:text-red-400 text-sm">
          <strong>Transform Error:</strong> {transformError}
        </div>
      </div>
    {:else if transformedText}
      <div class="mt-4">
        <div class="flex items-center justify-between mb-2">
          <label class="text-sm font-medium text-gray-700 dark:text-gray-300">
            Transformed Text ({sentimentOptions.find(opt => opt.value === targetSentiment)?.icon} {sentimentOptions.find(opt => opt.value === targetSentiment)?.label})
          </label>
          <span class="text-xs text-gray-500 dark:text-gray-400">
            {transformedText.length} characters
          </span>
        </div>
        <div class="relative">
          <div class="p-4 bg-white dark:bg-gray-800 border border-purple-200 dark:border-purple-700 rounded-lg font-medium text-gray-900 dark:text-white">
            {transformedText}
          </div>
          <div class="absolute top-2 right-2">
            <div class="flex items-center space-x-1 text-xs text-purple-600 dark:text-purple-400">
              <ArrowRight size={12} />
              <span>{sentimentOptions.find(opt => opt.value === targetSentiment)?.icon}</span>
            </div>
          </div>
        </div>
      </div>
    {/if}
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
          {#if sentimentResult.overall_sentiment}
            <div class="text-4xl">{getSentimentIcon(sentimentResult.overall_sentiment)}</div>
            <div>
              <div class="text-2xl font-bold {getSentimentColor(sentimentResult.overall_sentiment)}">
                {sentimentResult.overall_sentiment.charAt(0).toUpperCase() + sentimentResult.overall_sentiment.slice(1)}
              </div>
              {#if sentimentResult.confidence !== undefined}
                <div class="text-lg text-gray-600 dark:text-gray-400">
                  {sentimentResult.intensity ? sentimentResult.intensity.charAt(0).toUpperCase() + sentimentResult.intensity.slice(1) + ' intensity' : ''}
                </div>
              {/if}
            </div>
          {/if}
        </div>

        <!-- Key Indicators -->
        {#if sentimentResult.key_indicators && sentimentResult.key_indicators.length > 0}
          <div class="mb-4">
            <h5 class="text-sm font-medium text-gray-900 dark:text-white mb-2">Key Sentiment Indicators</h5>
            <div class="flex flex-wrap gap-2">
              {#each sentimentResult.key_indicators as indicator}
                <span class="px-2 py-1 bg-pink-100 dark:bg-pink-900/30 text-pink-800 dark:text-pink-200 text-xs rounded-full">
                  {indicator}
                </span>
              {/each}
            </div>
          </div>
        {/if}
      </div>

      <!-- Emotions Detected -->
      {#if sentimentResult.emotions_detected && sentimentResult.emotions_detected.length > 0}
        <div class="p-6 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
          <h4 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Emotions Detected</h4>
          <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
            {#each sentimentResult.emotions_detected as emotion}
              <div class="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div class="text-sm font-medium text-gray-900 dark:text-white capitalize">{emotion.emotion}</div>
                <div class="text-lg font-bold text-pink-600 dark:text-pink-400">{emotion.intensity}%</div>
                <div class="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2 mt-1">
                  <div 
                    class="h-2 rounded-full bg-pink-500"
                    style="width: {emotion.intensity}%"
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
              <h4 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Analysis Confidence</h4>
              <div class="text-3xl font-bold text-pink-600 dark:text-pink-400">
                {(sentimentResult.confidence * 100).toFixed(1)}%
              </div>
              <div class="text-sm text-gray-500 dark:text-gray-400 mt-1">
                {#if sentimentResult.overall_sentiment === 'negative'}
                  Certainty that sentiment is negative
                {:else if sentimentResult.overall_sentiment === 'positive'}
                  Certainty that sentiment is positive
                {:else}
                  Certainty of sentiment classification
                {/if}
              </div>
              {#if sentimentResult.overall_sentiment === 'negative' && sentimentResult.confidence > 0.8}
                <div class="text-xs text-red-600 dark:text-red-400 mt-2 font-medium">
                  High confidence in negative sentiment
                </div>
              {/if}
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
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
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
      <div class="p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
        <div class="flex items-center space-x-2 mb-2">
          <Wand2 size={16} class="text-purple-500" />
          <h3 class="font-medium text-gray-900 dark:text-white">Sentiment Transformation</h3>
        </div>
        <p class="text-sm text-gray-600 dark:text-gray-400">
          Rewrite text to match your desired emotional tone.
        </p>
      </div>
    </div>
  </div>
</div>
