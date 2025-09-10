<script>
  import { BarChart3, Play, Download, Hash, Type, BookOpen, Target } from 'lucide-svelte';

  let inputText = '';
  let inputUrl = '';
  let inputMode = 'text'; // 'text' or 'url'
  let basicStats = null;
  let wordFrequency = null;
  let readabilityStats = null;
  let complexityStats = null;
  let isProcessing = false;
  let error = null;
  let selectedWord = null;
  let viewMode = 'dashboard'; // 'dashboard', 'wordcloud', 'density'

  // Example texts for demonstration
  const examples = [
    "The quick brown fox jumps over the lazy dog. This sentence contains every letter of the English alphabet.",
    "Machine learning is a subset of artificial intelligence that focuses on algorithms which can learn from and make predictions on data.",
    "To be or not to be, that is the question: Whether 'tis nobler in the mind to suffer the slings and arrows of outrageous fortune.",
    "Climate change represents one of the most pressing challenges of our time, affecting ecosystems, weather patterns, and human societies worldwide."
  ];

  async function analyzeText() {
    // Validate input based on mode
    if (inputMode === 'text' && !inputText.trim()) return;
    if (inputMode === 'url' && !inputUrl.trim()) return;
    
    isProcessing = true;
    error = null;
    basicStats = null;
    wordFrequency = null;
    readabilityStats = null;
    complexityStats = null;
    selectedWord = null;
    
    try {
      // Build arguments based on input mode
      const args = {};
      if (inputMode === 'text') {
        args.text = inputText;
      } else {
        args.url = inputUrl;
      }
      
      // Run all analyses in parallel
      const [basicResult, wordFreqResult, readabilityResult, complexityResult] = await Promise.all([
        executeAnalysis('analyze_text_basic', args),
        executeAnalysis('word_frequency_analysis', { ...args, top_n: 20 }),
        executeAnalysis('analyze_readability', args),
        executeAnalysis('text_complexity_analysis', args)
      ]);
      
      basicStats = basicResult;
      wordFrequency = wordFreqResult;
      readabilityStats = readabilityResult;
      complexityStats = complexityResult;
      
    } catch (err) {
      error = 'Failed to connect to server. Make sure the MCP server is running on port 8000.';
      console.error('Error:', err);
    } finally {
      isProcessing = false;
    }
  }
  
  async function executeAnalysis(toolName, arguments_) {
    const response = await fetch('http://localhost:8000/tools/execute', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        name: toolName,
        arguments: arguments_
      })
    });

    const result = await response.json();
    if (result.success) {
      return JSON.parse(result.result);
    } else {
      throw new Error(result.error || `Failed to execute ${toolName}`);
    }
  }

  function useExample(text) {
    inputText = text;
    inputMode = 'text';
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
  
  function formatPercent(num) {
    return (num * 100).toFixed(1) + '%';
  }
  
  function getWordSize(frequency, maxFreq, minFreq) {
    const minSize = 12;  // Size for least frequent word
    const maxSize = 40;  // Size for most frequent word
    
    // Calculate linear ratio based on frequency range
    const freqRange = maxFreq - minFreq;
    const ratio = freqRange === 0 ? 1 : (frequency - minFreq) / freqRange;
    
    return minSize + (maxSize - minSize) * ratio;
  }
  
  function getWordOpacity(frequency, maxFreq) {
    const minOpacity = 0.7;
    const maxOpacity = 1.0;
    const ratio = frequency / maxFreq;
    return minOpacity + (maxOpacity - minOpacity) * ratio;
  }
  
  function selectWord(word, frequency) {
    selectedWord = { word, frequency };
  }
  
  function downloadData() {
    const data = {
      analysis_timestamp: new Date().toISOString(),
      input_text: inputText,
      text_length: inputText.length,
      basic_statistics: basicStats,
      word_frequency: wordFrequency,
      readability: readabilityStats,
      complexity: complexityStats,
      summary: {
        total_words: basicStats?.word_statistics?.total_words || 0,
        total_characters: basicStats?.character_statistics?.total_characters || 0,
        unique_words: basicStats?.word_statistics?.unique_words || 0,
        vocabulary_richness: basicStats?.word_statistics?.vocabulary_richness || 0,
        most_frequent_word: wordFrequency?.word_frequency?.most_frequent?.[0] || null,
        complexity_score: complexityStats?.complexity_metrics?.complexity_score || 0,
        readability_level: readabilityStats?.overall_assessment || 'Unknown'
      }
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `text_analysis_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.json`;
    a.click();
    URL.revokeObjectURL(url);
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
      <!-- Input Mode Tabs -->
      <div class="border-b border-gray-200 dark:border-gray-700">
        <nav class="-mb-px flex space-x-8">
          <button
            on:click={() => inputMode = 'text'}
            class="{inputMode === 'text' ? 'border-green-500 text-green-600 dark:text-green-400' : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'} whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm transition-colors"
          >
            Text Input
          </button>
          <button
            on:click={() => inputMode = 'url'}
            class="{inputMode === 'url' ? 'border-green-500 text-green-600 dark:text-green-400' : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'} whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm transition-colors"
          >
            URL Input
          </button>
        </nav>
      </div>
      
      <div class="flex items-center justify-between">
        <h3 class="text-lg font-medium text-gray-900 dark:text-white">
          {inputMode === 'text' ? 'Input Text' : 'Website URL'}
        </h3>
        <div class="flex items-center space-x-4">
          {#if basicStats}
            <div class="flex items-center space-x-3 text-xs text-gray-500 dark:text-gray-400">
              <span class="bg-green-100 dark:bg-green-900/20 px-2 py-1 rounded">
                📝 {formatNumber(basicStats.word_statistics.total_words)} words
              </span>
              <span class="bg-blue-100 dark:bg-blue-900/20 px-2 py-1 rounded">
                🔤 {formatNumber(basicStats.character_statistics.characters_without_spaces)} letters
              </span>
              <span class="bg-purple-100 dark:bg-purple-900/20 px-2 py-1 rounded">
                🎯 {formatNumber(basicStats.word_statistics.unique_words)} unique
              </span>
              {#if wordFrequency?.word_frequency?.most_frequent?.[0]}
                <span class="bg-orange-100 dark:bg-orange-900/20 px-2 py-1 rounded font-medium">
                  👑 "{wordFrequency.word_frequency.most_frequent[0].word}" ({wordFrequency.word_frequency.most_frequent[0].count}x)
                </span>
              {/if}
            </div>
          {/if}
          <span class="text-sm text-gray-500 dark:text-gray-400">
            {inputMode === 'text' ? `${inputText.length} characters` : inputUrl ? '✓ URL entered' : 'Enter URL'}
          </span>
        </div>
      </div>
      
      <!-- Text Input Mode -->
      {#if inputMode === 'text'}
        <textarea
          bind:value={inputText}
          placeholder="Enter text to analyze statistics, word frequency, density, and more..."
          class="w-full h-32 px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent resize-none bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
        ></textarea>
      {:else}
        <!-- URL Input Mode -->
        <div class="space-y-4">
          <input
            type="url"
            bind:value={inputUrl}
            placeholder="https://example.com/article-to-analyze"
            class="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
          />
          
          <div class="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
            <div class="flex items-start space-x-3">
              <div class="flex-shrink-0">
                <svg class="w-5 h-5 text-blue-600 dark:text-blue-400 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"></path>
                </svg>
              </div>
              <div class="text-sm text-blue-700 dark:text-blue-300">
                <p class="font-medium">URL Analysis Features:</p>
                <ul class="mt-1 list-disc list-inside space-y-1">
                  <li>Extract and analyze content from any web article or blog post</li>
                  <li>Get statistics on readability, word frequency, and complexity</li>
                  <li>Works with news articles, documentation, and content-rich pages</li>
                  <li>Page title included in analysis context for better insights</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      {/if}
      
      <div class="flex flex-wrap gap-3">
        <button
          on:click={analyzeText}
          disabled={(inputMode === 'text' && !inputText.trim()) || (inputMode === 'url' && !inputUrl.trim()) || isProcessing}
          class="flex items-center justify-center px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white font-medium rounded-lg transition-colors"
        >
          {#if isProcessing}
            <div class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
            {inputMode === 'url' ? 'Fetching & Analyzing...' : 'Analyzing Text...'}
          {:else}
            <BarChart3 size={16} class="mr-2" />
            {inputMode === 'url' ? 'Analyze from URL' : 'Analyze Text'}
          {/if}
        </button>
        
        {#if basicStats}
          <div class="flex space-x-2">
            <button
              on:click={() => viewMode = 'dashboard'}
              class="flex items-center px-3 py-2 rounded-lg transition-colors {
                viewMode === 'dashboard' ? 'bg-blue-600 text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
              }"
            >
              <BarChart3 size={14} class="mr-2" />
              Dashboard
            </button>
            <button
              on:click={() => viewMode = 'wordcloud'}
              class="flex items-center px-3 py-2 rounded-lg transition-colors {
                viewMode === 'wordcloud' ? 'bg-purple-600 text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
              }"
            >
              <Type size={14} class="mr-2" />
              Word Cloud
            </button>
            <button
              on:click={() => viewMode = 'density'}
              class="flex items-center px-3 py-2 rounded-lg transition-colors {
                viewMode === 'density' ? 'bg-indigo-600 text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
              }"
            >
              <Target size={14} class="mr-2" />
              Density
            </button>
          </div>
          
          <button
            on:click={downloadData}
            class="flex items-center px-3 py-2 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-lg transition-colors"
          >
            <Download size={14} class="mr-2" />
            Download JSON
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
  {:else if basicStats}
    <!-- Dashboard View -->
    {#if viewMode === 'dashboard'}
      <div class="space-y-6">
        <!-- Key Statistics Overview -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div class="p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
            <div class="flex items-center justify-between">
              <div>
                <h4 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Total Words</h4>
                <p class="text-2xl font-bold text-green-600 dark:text-green-400">{formatNumber(basicStats.word_statistics.total_words)}</p>
              </div>
              <Hash class="text-green-500" size={24} />
            </div>
          </div>
          <div class="p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
            <div class="flex items-center justify-between">
              <div>
                <h4 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Letters</h4>
                <p class="text-2xl font-bold text-blue-600 dark:text-blue-400">{formatNumber(basicStats.character_statistics.characters_without_spaces)}</p>
              </div>
              <Type class="text-blue-500" size={24} />
            </div>
          </div>
          <div class="p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
            <div class="flex items-center justify-between">
              <div>
                <h4 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Unique Words</h4>
                <p class="text-2xl font-bold text-purple-600 dark:text-purple-400">{formatNumber(basicStats.word_statistics.unique_words)}</p>
              </div>
              <Target class="text-purple-500" size={24} />
            </div>
          </div>
          <div class="p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
            <div class="flex items-center justify-between">
              <div>
                <h4 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Vocabulary Richness</h4>
                <p class="text-2xl font-bold text-orange-600 dark:text-orange-400">{formatPercent(basicStats.word_statistics.vocabulary_richness)}</p>
              </div>
              <BookOpen class="text-orange-500" size={24} />
            </div>
          </div>
        </div>

        <!-- Detailed Statistics -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <!-- Character Statistics -->
          <div class="p-6 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
            <h4 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Character Statistics</h4>
            <div class="space-y-3">
              <div class="flex justify-between items-center">
                <span class="text-sm text-gray-600 dark:text-gray-400">Total Characters</span>
                <span class="font-mono text-sm font-medium text-gray-900 dark:text-white">{formatNumber(basicStats.character_statistics.total_characters)}</span>
              </div>
              <div class="flex justify-between items-center">
                <span class="text-sm text-gray-600 dark:text-gray-400">Without Spaces</span>
                <span class="font-mono text-sm font-medium text-gray-900 dark:text-white">{formatNumber(basicStats.character_statistics.characters_without_spaces)}</span>
              </div>
              <div class="flex justify-between items-center">
                <span class="text-sm text-gray-600 dark:text-gray-400">Whitespace</span>
                <span class="font-mono text-sm font-medium text-gray-900 dark:text-white">{formatNumber(basicStats.character_statistics.whitespace_characters)}</span>
              </div>
              <div class="flex justify-between items-center">
                <span class="text-sm text-gray-600 dark:text-gray-400">Chars per Word</span>
                <span class="font-mono text-sm font-medium text-gray-900 dark:text-white">{basicStats.text_density.characters_per_word}</span>
              </div>
            </div>
          </div>

          <!-- Word Statistics -->
          <div class="p-6 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
            <h4 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Word Statistics</h4>
            <div class="space-y-3">
              <div class="flex justify-between items-center">
                <span class="text-sm text-gray-600 dark:text-gray-400">Total Words</span>
                <span class="font-mono text-sm font-medium text-gray-900 dark:text-white">{formatNumber(basicStats.word_statistics.total_words)}</span>
              </div>
              <div class="flex justify-between items-center">
                <span class="text-sm text-gray-600 dark:text-gray-400">Unique Words</span>
                <span class="font-mono text-sm font-medium text-gray-900 dark:text-white">{formatNumber(basicStats.word_statistics.unique_words)}</span>
              </div>
              <div class="flex justify-between items-center">
                <span class="text-sm text-gray-600 dark:text-gray-400">Average Length</span>
                <span class="font-mono text-sm font-medium text-gray-900 dark:text-white">{basicStats.word_statistics.average_word_length}</span>
              </div>
              <div class="flex justify-between items-center">
                <span class="text-sm text-gray-600 dark:text-gray-400">Vocabulary Richness</span>
                <span class="font-mono text-sm font-medium text-gray-900 dark:text-white">{formatPercent(basicStats.word_statistics.vocabulary_richness)}</span>
              </div>
            </div>
          </div>

          <!-- Structure Statistics -->
          <div class="p-6 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
            <h4 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Text Structure</h4>
            <div class="space-y-3">
              <div class="flex justify-between items-center">
                <span class="text-sm text-gray-600 dark:text-gray-400">Sentences</span>
                <span class="font-mono text-sm font-medium text-gray-900 dark:text-white">{formatNumber(basicStats.sentence_statistics.total_sentences)}</span>
              </div>
              <div class="flex justify-between items-center">
                <span class="text-sm text-gray-600 dark:text-gray-400">Paragraphs</span>
                <span class="font-mono text-sm font-medium text-gray-900 dark:text-white">{formatNumber(basicStats.paragraph_statistics.total_paragraphs)}</span>
              </div>
              <div class="flex justify-between items-center">
                <span class="text-sm text-gray-600 dark:text-gray-400">Avg Sentence Length</span>
                <span class="font-mono text-sm font-medium text-gray-900 dark:text-white">{basicStats.sentence_statistics.average_sentence_length}</span>
              </div>
              <div class="flex justify-between items-center">
                <span class="text-sm text-gray-600 dark:text-gray-400">Words per Paragraph</span>
                <span class="font-mono text-sm font-medium text-gray-900 dark:text-white">{basicStats.text_density.words_per_paragraph}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Readability & Complexity -->
        {#if readabilityStats || complexityStats}
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            {#if readabilityStats}
              <div class="p-6 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
                <h4 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Readability Assessment</h4>
                <div class="mb-4">
                  <div class="text-2xl font-bold text-indigo-600 dark:text-indigo-400">{readabilityStats.overall_assessment}</div>
                  <div class="text-sm text-gray-500 dark:text-gray-400">Reading Level</div>
                </div>
                <div class="space-y-2">
                  {#each Object.entries(readabilityStats.readability_metrics) as [key, value]}
                    {#if value.score !== undefined}
                      <div class="flex justify-between items-center">
                        <span class="text-xs text-gray-600 dark:text-gray-400">{key.replace('_', ' ')}</span>
                        <span class="font-mono text-xs font-medium text-gray-900 dark:text-white">{value.score.toFixed(1)}</span>
                      </div>
                    {/if}
                  {/each}
                </div>
              </div>
            {/if}

            {#if complexityStats}
              <div class="p-6 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
                <h4 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Complexity Analysis</h4>
                <div class="mb-4">
                  <div class="text-2xl font-bold text-teal-600 dark:text-teal-400">{complexityStats.complexity_assessment}</div>
                  <div class="text-sm text-gray-500 dark:text-gray-400">Complexity Level</div>
                </div>
                <div class="space-y-2">
                  {#each Object.entries(complexityStats.complexity_metrics) as [key, value]}
                    <div class="flex justify-between items-center">
                      <span class="text-xs text-gray-600 dark:text-gray-400">{key.replace('_', ' ')}</span>
                      <span class="font-mono text-xs font-medium text-gray-900 dark:text-white">{typeof value === 'number' ? value.toFixed(3) : value}</span>
                    </div>
                  {/each}
                </div>
              </div>
            {/if}
          </div>
        {/if}
      </div>
    {/if}

    <!-- Word Cloud View -->
    {#if viewMode === 'wordcloud'}
      <div class="p-6 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-6">Interactive Word Cloud</h3>
        {#if wordFrequency?.word_frequency?.most_frequent}
          {@const maxFreq = Math.max(...wordFrequency.word_frequency.most_frequent.map(w => w.count))}
          {@const minFreq = Math.min(...wordFrequency.word_frequency.most_frequent.map(w => w.count))}
          <div class="flex flex-wrap gap-3 items-center justify-center p-8 min-h-64">
            {#each wordFrequency.word_frequency.most_frequent as wordData}
              <button
                on:click={() => selectWord(wordData.word, wordData.count)}
                class="px-3 py-1 rounded-lg transition-all duration-200 hover:scale-110 hover:shadow-lg {
                  selectedWord?.word === wordData.word ? 'bg-blue-600 text-white ring-2 ring-blue-300' : 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white hover:bg-blue-50 dark:hover:bg-blue-900/30'
                }"
                style="font-size: {getWordSize(wordData.count, maxFreq, minFreq)}px; opacity: {getWordOpacity(wordData.count, maxFreq)}"
              >
                {wordData.word}
              </button>
            {/each}
          </div>
          
          {#if selectedWord}
            <div class="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <h4 class="font-semibold text-blue-900 dark:text-blue-100 mb-2">Word Details: "{selectedWord.word}"</h4>
              <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                <div>
                  <span class="text-blue-700 dark:text-blue-300 font-medium">Frequency:</span>
                  <span class="text-gray-900 dark:text-white">{selectedWord.frequency} times</span>
                </div>
                <div>
                  <span class="text-blue-700 dark:text-blue-300 font-medium">Percentage:</span>
                  <span class="text-gray-900 dark:text-white">{formatPercent(selectedWord.frequency / basicStats.word_statistics.total_words)}</span>
                </div>
                <div>
                  <span class="text-blue-700 dark:text-blue-300 font-medium">Density:</span>
                  <span class="text-gray-900 dark:text-white">{(selectedWord.frequency / basicStats.word_statistics.total_words * 100).toFixed(2)} words per 100</span>
                </div>
              </div>
            </div>
          {/if}
        {:else}
          <div class="text-center text-gray-500 dark:text-gray-400 py-12">
            <Type size={48} class="mx-auto mb-4 opacity-50" />
            <p>No word frequency data available</p>
          </div>
        {/if}
      </div>
    {/if}

    <!-- Density View -->
    {#if viewMode === 'density'}
      <div class="space-y-6">
        <!-- Word Frequency Table -->
        <div class="p-6 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-6">Word Frequency & Density Analysis</h3>
          {#if wordFrequency?.word_frequency?.most_frequent}
            <div class="overflow-hidden">
              <table class="w-full">
                <thead>
                  <tr class="border-b border-gray-200 dark:border-gray-700">
                    <th class="text-left py-2 text-sm font-medium text-gray-500 dark:text-gray-400">Rank</th>
                    <th class="text-left py-2 text-sm font-medium text-gray-500 dark:text-gray-400">Word</th>
                    <th class="text-right py-2 text-sm font-medium text-gray-500 dark:text-gray-400">Count</th>
                    <th class="text-right py-2 text-sm font-medium text-gray-500 dark:text-gray-400">Frequency</th>
                    <th class="text-right py-2 text-sm font-medium text-gray-500 dark:text-gray-400">Density</th>
                    <th class="text-left py-2 text-sm font-medium text-gray-500 dark:text-gray-400">Visual</th>
                  </tr>
                </thead>
                <tbody>
                  {#each wordFrequency.word_frequency.most_frequent as wordData, index}
                    {@const percentage = wordData.frequency * 100}
                    <tr class="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                      <td class="py-2 text-sm text-gray-600 dark:text-gray-400">#{index + 1}</td>
                      <td class="py-2 text-sm font-medium text-gray-900 dark:text-white">{wordData.word}</td>
                      <td class="py-2 text-right text-sm font-mono text-gray-900 dark:text-white">{wordData.count}</td>
                      <td class="py-2 text-right text-sm font-mono text-gray-900 dark:text-white">{formatPercent(wordData.frequency)}</td>
                      <td class="py-2 text-right text-sm font-mono text-gray-900 dark:text-white">{(wordData.count / basicStats.word_statistics.total_words * 1000).toFixed(1)}/1K</td>
                      <td class="py-2">
                        <div class="w-20 h-2 bg-gray-200 dark:bg-gray-600 rounded-full overflow-hidden">
                          <div 
                            class="h-full bg-gradient-to-r from-blue-500 to-purple-500 transition-all duration-300"
                            style="width: {Math.min(percentage * 10, 100)}%"
                          ></div>
                        </div>
                      </td>
                    </tr>
                  {/each}
                </tbody>
              </table>
            </div>
          {:else}
            <div class="text-center text-gray-500 dark:text-gray-400 py-12">
              <Target size={48} class="mx-auto mb-4 opacity-50" />
              <p>No density data available</p>
            </div>
          {/if}
        </div>
      </div>
    {/if}
  {:else}
    <div class="p-8 text-center text-gray-500 dark:text-gray-400 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg">
      <BarChart3 size={48} class="mx-auto mb-4 text-gray-300 dark:text-gray-600" />
      <p>Enter text above and click "Analyze Text" to see comprehensive statistics, word frequency, and density analysis</p>
    </div>
  {/if}
</div>
