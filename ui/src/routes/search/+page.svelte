<script>
  import { onMount } from 'svelte';
  
  let query = '';
  let results = [];
  let chunks = [];
  let searchMode = 'semantic'; // 'semantic' or 'chunks'
  let loading = false;
  let searchTime = 0;
  let error = null;
  let minScore = 0.5;
  let limit = 10;
  
  // Debounce timer
  let debounceTimer;
  
  // Example searches
  const exampleSearches = [
    'artificial intelligence',
    'machine learning algorithms',
    'neural networks and deep learning',
    'data science and analytics',
    'software engineering best practices'
  ];
  
  // Perform semantic search
  async function performSearch() {
    if (!query || query.trim().length < 2) {
      results = [];
      chunks = [];
      return;
    }
    
    loading = true;
    error = null;
    const startTime = performance.now();
    
    try {
      const formData = new FormData();
      formData.append('query', query);
      formData.append('limit', limit.toString());
      
      if (searchMode === 'semantic') {
        formData.append('min_score', minScore.toString());
      }
      
      const endpoint = searchMode === 'semantic' 
        ? '/resources/search/semantic'
        : '/resources/search/chunks';
      
      const response = await fetch(`http://localhost:8000${endpoint}`, {
        method: 'POST',
        body: formData,
        credentials: 'include'
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Search failed');
      }
      
      const data = await response.json();
      
      if (searchMode === 'semantic') {
        results = data.results || [];
        chunks = [];
      } else {
        chunks = data.chunks || [];
        results = [];
      }
      
      searchTime = (performance.now() - startTime).toFixed(0);
    } catch (err) {
      error = err.message;
      results = [];
      chunks = [];
    } finally {
      loading = false;
    }
  }
  
  // Debounced search
  function onQueryChange() {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      if (query.trim().length >= 2) {
        performSearch();
      } else {
        results = [];
        chunks = [];
      }
    }, 500); // Wait 500ms after user stops typing
  }
  
  // Use example search
  function useExample(example) {
    query = example;
    performSearch();
  }
  
  // Find similar documents
  async function findSimilar(uri) {
    loading = true;
    error = null;
    
    try {
      const encodedUri = encodeURIComponent(uri);
      const response = await fetch(
        `http://localhost:8000/resources/${encodedUri}/similar?limit=5`,
        { credentials: 'include' }
      );
      
      if (!response.ok) {
        throw new Error('Failed to find similar documents');
      }
      
      const data = await response.json();
      results = data.similar_resources || [];
      query = `Similar to: ${data.source.name}`;
      searchMode = 'semantic';
    } catch (err) {
      error = err.message;
    } finally {
      loading = false;
    }
  }
  
  // Get score color class
  function getScoreClass(score) {
    if (score >= 0.8) return 'score-high';
    if (score >= 0.6) return 'score-medium';
    return 'score-low';
  }
  
  // Format score as percentage
  function formatScore(score) {
    return `${(score * 100).toFixed(1)}%`;
  }
</script>

<div class="search-page">
  <div class="search-header">
    <h1>🔍 Semantic Search</h1>
    <p class="subtitle">Search your documents by meaning, not just keywords</p>
  </div>
  
  <!-- Search Box -->
  <div class="search-box-container">
    <div class="search-box">
      <input
        type="text"
        bind:value={query}
        on:input={onQueryChange}
        placeholder="Ask a question or describe what you're looking for..."
        class="search-input"
        autocomplete="off"
      />
      <button 
        class="search-button"
        on:click={performSearch}
        disabled={loading || !query}
      >
        {#if loading}
          <span class="spinner"></span>
        {:else}
          Search
        {/if}
      </button>
    </div>
    
    <!-- Search Mode Tabs -->
    <div class="search-mode-tabs">
      <button
        class="tab {searchMode === 'semantic' ? 'active' : ''}"
        on:click={() => { searchMode = 'semantic'; if (query) performSearch(); }}
      >
        📄 Documents
      </button>
      <button
        class="tab {searchMode === 'chunks' ? 'active' : ''}"
        on:click={() => { searchMode = 'chunks'; if (query) performSearch(); }}
      >
        📝 Precise Chunks
      </button>
    </div>
    
    <!-- Options -->
    {#if searchMode === 'semantic'}
      <div class="search-options">
        <label>
          Min Score:
          <input type="range" bind:value={minScore} min="0" max="1" step="0.1" />
          <span>{formatScore(minScore)}</span>
        </label>
        <label>
          Limit:
          <select bind:value={limit}>
            <option value={5}>5 results</option>
            <option value={10}>10 results</option>
            <option value={20}>20 results</option>
            <option value={50}>50 results</option>
          </select>
        </label>
      </div>
    {/if}
  </div>
  
  <!-- Example Searches -->
  {#if !query && !loading && results.length === 0 && chunks.length === 0}
    <div class="examples-section">
      <h3>Try these searches:</h3>
      <div class="examples">
        {#each exampleSearches as example}
          <button class="example-btn" on:click={() => useExample(example)}>
            {example}
          </button>
        {/each}
      </div>
    </div>
  {/if}
  
  <!-- Error Message -->
  {#if error}
    <div class="error-message">
      ⚠️ {error}
    </div>
  {/if}
  
  <!-- Results Header -->
  {#if query && !loading && (results.length > 0 || chunks.length > 0)}
    <div class="results-header">
      <span class="results-count">
        Found {searchMode === 'semantic' ? results.length : chunks.length} 
        {searchMode === 'semantic' ? 'documents' : 'chunks'}
      </span>
      <span class="search-time">in {searchTime}ms</span>
    </div>
  {/if}
  
  <!-- No Results -->
  {#if query && !loading && results.length === 0 && chunks.length === 0 && !error}
    <div class="no-results">
      <p>No results found for "{query}"</p>
      <p class="hint">Try adjusting your search or lowering the minimum score</p>
    </div>
  {/if}
  
  <!-- Document Results -->
  {#if searchMode === 'semantic' && results.length > 0}
    <div class="results-list">
      {#each results as result}
        <div class="result-card">
          <div class="result-header">
            <h3 class="result-title">{result.name}</h3>
            <div class="result-score {getScoreClass(result.score)}">
              <div class="score-bar">
                <div 
                  class="score-fill" 
                  style="width: {result.score * 100}%"
                ></div>
              </div>
              <span class="score-text">{formatScore(result.score)}</span>
            </div>
          </div>
          
          <p class="result-description">{result.description}</p>
          
          <div class="result-meta">
            <span class="result-type">{result.mimeType}</span>
            <span class="result-date">
              {new Date(result.createdAt).toLocaleDateString()}
            </span>
          </div>
          
          <div class="result-actions">
            <button class="action-btn view-btn">
              📄 View Document
            </button>
            <button 
              class="action-btn similar-btn"
              on:click={() => findSimilar(result.uri)}
            >
              🔗 Find Similar
            </button>
          </div>
        </div>
      {/each}
    </div>
  {/if}
  
  <!-- Chunk Results -->
  {#if searchMode === 'chunks' && chunks.length > 0}
    <div class="chunks-list">
      {#each chunks as chunk}
        <div class="chunk-card">
          <div class="chunk-header">
            <div>
              <h4 class="chunk-title">{chunk.name}</h4>
              <span class="chunk-index">Chunk #{chunk.chunkIndex + 1}</span>
            </div>
            <div class="result-score {getScoreClass(chunk.score)}">
              <span class="score-text">{formatScore(chunk.score)}</span>
            </div>
          </div>
          
          <div class="chunk-text">
            {chunk.chunkText}
          </div>
          
          <div class="chunk-meta">
            <span>Characters {chunk.charStart}-{chunk.charEnd}</span>
          </div>
        </div>
      {/each}
    </div>
  {/if}
  
  <!-- Loading Indicator -->
  {#if loading && query}
    <div class="loading-container">
      <div class="spinner-large"></div>
      <p>Searching...</p>
    </div>
  {/if}
</div>

<style>
  .search-page {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
  }
  
  .search-header {
    text-align: center;
    margin-bottom: 3rem;
  }
  
  .search-header h1 {
    font-size: 2.5rem;
    margin-bottom: 0.5rem;
    color: #1a1a1a;
  }
  
  .subtitle {
    color: #666;
    font-size: 1.1rem;
  }
  
  .search-box-container {
    background: white;
    border-radius: 12px;
    padding: 2rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    margin-bottom: 2rem;
  }
  
  .search-box {
    display: flex;
    gap: 1rem;
    margin-bottom: 1.5rem;
  }
  
  .search-input {
    flex: 1;
    padding: 1rem 1.5rem;
    font-size: 1.1rem;
    border: 2px solid #e0e0e0;
    border-radius: 8px;
    outline: none;
    transition: border-color 0.2s;
  }
  
  .search-input:focus {
    border-color: #2563eb;
  }
  
  .search-button {
    padding: 1rem 2rem;
    background: #2563eb;
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 1.1rem;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.2s;
    min-width: 120px;
  }
  
  .search-button:hover:not(:disabled) {
    background: #1d4ed8;
  }
  
  .search-button:disabled {
    background: #9ca3af;
    cursor: not-allowed;
  }
  
  .search-mode-tabs {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 1rem;
  }
  
  .tab {
    padding: 0.75rem 1.5rem;
    background: #f3f4f6;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s;
    font-weight: 500;
  }
  
  .tab.active {
    background: #2563eb;
    color: white;
  }
  
  .tab:hover:not(.active) {
    background: #e5e7eb;
  }
  
  .search-options {
    display: flex;
    gap: 2rem;
    padding-top: 1rem;
    border-top: 1px solid #e5e7eb;
  }
  
  .search-options label {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: #666;
  }
  
  .search-options input[type="range"] {
    width: 150px;
  }
  
  .examples-section {
    text-align: center;
    padding: 3rem 0;
  }
  
  .examples-section h3 {
    color: #666;
    margin-bottom: 1.5rem;
  }
  
  .examples {
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
    justify-content: center;
  }
  
  .example-btn {
    padding: 0.75rem 1.5rem;
    background: #f3f4f6;
    border: 2px solid #e5e7eb;
    border-radius: 20px;
    cursor: pointer;
    transition: all 0.2s;
    font-size: 0.95rem;
  }
  
  .example-btn:hover {
    background: #e5e7eb;
    border-color: #2563eb;
    transform: translateY(-2px);
  }
  
  .results-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 0;
    margin-bottom: 1rem;
    border-bottom: 2px solid #e5e7eb;
  }
  
  .results-count {
    font-weight: 600;
    font-size: 1.1rem;
  }
  
  .search-time {
    color: #666;
    font-size: 0.9rem;
  }
  
  .results-list, .chunks-list {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }
  
  .result-card, .chunk-card {
    background: white;
    border-radius: 8px;
    padding: 1.5rem;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    transition: transform 0.2s, box-shadow 0.2s;
  }
  
  .result-card:hover, .chunk-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.15);
  }
  
  .result-header, .chunk-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 1rem;
  }
  
  .result-title {
    font-size: 1.3rem;
    margin: 0;
    color: #1a1a1a;
  }
  
  .chunk-title {
    font-size: 1.1rem;
    margin: 0 0 0.25rem 0;
    color: #1a1a1a;
  }
  
  .chunk-index {
    font-size: 0.85rem;
    color: #666;
    background: #f3f4f6;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
  }
  
  .result-score {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  
  .score-bar {
    width: 80px;
    height: 8px;
    background: #e5e7eb;
    border-radius: 4px;
    overflow: hidden;
  }
  
  .score-fill {
    height: 100%;
    transition: width 0.3s;
  }
  
  .score-high .score-fill {
    background: #10b981;
  }
  
  .score-medium .score-fill {
    background: #f59e0b;
  }
  
  .score-low .score-fill {
    background: #ef4444;
  }
  
  .score-text {
    font-weight: 600;
    font-size: 0.9rem;
  }
  
  .score-high .score-text {
    color: #10b981;
  }
  
  .score-medium .score-text {
    color: #f59e0b;
  }
  
  .score-low .score-text {
    color: #ef4444;
  }
  
  .result-description {
    color: #4b5563;
    line-height: 1.6;
    margin-bottom: 1rem;
  }
  
  .result-meta, .chunk-meta {
    display: flex;
    gap: 1rem;
    font-size: 0.85rem;
    color: #9ca3af;
    margin-bottom: 1rem;
  }
  
  .result-type {
    background: #f3f4f6;
    padding: 0.25rem 0.75rem;
    border-radius: 12px;
  }
  
  .result-actions {
    display: flex;
    gap: 0.75rem;
  }
  
  .action-btn {
    padding: 0.5rem 1rem;
    border: 1px solid #e5e7eb;
    background: white;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s;
    font-size: 0.9rem;
  }
  
  .action-btn:hover {
    background: #f9fafb;
    border-color: #2563eb;
  }
  
  .chunk-text {
    background: #f9fafb;
    padding: 1rem;
    border-radius: 6px;
    line-height: 1.6;
    color: #374151;
    margin-bottom: 0.75rem;
    white-space: pre-wrap;
  }
  
  .no-results {
    text-align: center;
    padding: 3rem;
    color: #666;
  }
  
  .no-results .hint {
    margin-top: 0.5rem;
    font-size: 0.9rem;
    color: #9ca3af;
  }
  
  .error-message {
    background: #fee2e2;
    border: 1px solid #fecaca;
    color: #991b1b;
    padding: 1rem;
    border-radius: 8px;
    margin-bottom: 1rem;
  }
  
  .loading-container {
    text-align: center;
    padding: 3rem;
  }
  
  .spinner, .spinner-large {
    display: inline-block;
    width: 16px;
    height: 16px;
    border: 2px solid #ffffff40;
    border-top-color: white;
    border-radius: 50%;
    animation: spin 0.6s linear infinite;
  }
  
  .spinner-large {
    width: 40px;
    height: 40px;
    border-width: 4px;
    border-color: #e5e7eb;
    border-top-color: #2563eb;
  }
  
  @keyframes spin {
    to { transform: rotate(360deg); }
  }
</style>
