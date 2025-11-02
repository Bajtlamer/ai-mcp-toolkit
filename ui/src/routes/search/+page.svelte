<script>
  import { onMount } from 'svelte';
  import {
    Search,
    Upload,
    FileText,
    Filter,
    X,
    Loader,
    Building,
    DollarSign,
    Calendar,
    Hash,
    File,
    Send,
    ExternalLink,
    Mail,
    CreditCard
  } from 'lucide-svelte';
  import toast from 'svelte-french-toast';
  import { compoundSearch } from '$lib/api/search';
  
  let query = '';
  let results = [];
  let queryAnalysis = null;
  let loading = false;
  let searchTime = 0;
  let error = null;
  let limit = 30;
  let searchPerformed = false;  // Track if user actually performed a search
  
  // Suggestions state
  let suggestions = [];
  let showSuggestions = false;
  let selectedSuggestionIndex = -1;
  let suggestionTimeout = null;
  let loadingSuggestions = false;
  
  let showUploadModal = false;
  let uploadFile = null;
  let uploadTags = '';
  let uploading = false;
  
  let showSnippetModal = false;
  let snippetTitle = '';
  let snippetText = '';
  let snippetTags = '';
  let snippetSource = 'user_input';
  let savingSnippet = false;
  
  async function performSearch() {
    if (!query || query.trim().length < 2) {
      results = [];
      queryAnalysis = null;
      searchPerformed = false;
      return;
    }
    
    searchPerformed = true;  // Mark that search was performed
    loading = true;
    error = null;
    const startTime = performance.now();
    
    try {
      const data = await compoundSearch(query, limit);
      
      results = data.results || [];
      queryAnalysis = data.analysis || null;
      searchTime = (performance.now() - startTime).toFixed(0);
      
    } catch (err) {
      error = err.message;
      results = [];
      toast.error(err.message);
    } finally {
      loading = false;
    }
  }
  
  async function getSuggestions(q) {
    if (q.length < 2) {
      suggestions = [];
      showSuggestions = false;
      return;
    }
    
    try {
      loadingSuggestions = true;
      const response = await fetch(
        `http://localhost:8000/search/suggestions?q=${encodeURIComponent(q)}&limit=10`,
        { credentials: 'include' }
      );
      
      if (response.ok) {
        suggestions = await response.json();
        showSuggestions = suggestions.length > 0;
        selectedSuggestionIndex = -1;
      }
    } catch (err) {
      console.error('Error fetching suggestions:', err);
      suggestions = [];
      showSuggestions = false;
    } finally {
      loadingSuggestions = false;
    }
  }
  
  function handleInput() {
    // Clear results if query is empty
    if (!query || query.trim().length === 0) {
      results = [];
      queryAnalysis = null;
      searchPerformed = false;
      showSuggestions = false;
      suggestions = [];
      return;
    }
    
    // Debounce suggestions
    if (suggestionTimeout) {
      clearTimeout(suggestionTimeout);
    }
    
    suggestionTimeout = setTimeout(() => {
      getSuggestions(query);
    }, 300);
  }
  
  function selectSuggestion(suggestion) {
    query = suggestion.text;
    showSuggestions = false;
    suggestions = [];
    selectedSuggestionIndex = -1;
    // Focus stays on input, user can press Enter to search
  }
  
  function handleKeyDown(event) {
    // Handle suggestion navigation
    if (showSuggestions && suggestions.length > 0) {
      if (event.key === 'ArrowDown') {
        event.preventDefault();
        selectedSuggestionIndex = Math.min(selectedSuggestionIndex + 1, suggestions.length - 1);
        return;
      } else if (event.key === 'ArrowUp') {
        event.preventDefault();
        selectedSuggestionIndex = Math.max(selectedSuggestionIndex - 1, -1);
        return;
      } else if (event.key === 'Enter' && selectedSuggestionIndex >= 0) {
        event.preventDefault();
        selectSuggestion(suggestions[selectedSuggestionIndex]);
        return;
      } else if (event.key === 'Escape') {
        showSuggestions = false;
        return;
      }
    }
    
    // Handle search
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      showSuggestions = false;
      performSearch();
    }
  }
  
  function getMatchTypeBadgeClass(matchType) {
    const classes = {
      'exact_phrase': 'badge-success',
      'exact_amount': 'badge-success',
      'exact_id': 'badge-primary',
      'exact_keyword': 'badge-primary',
      'keyword': 'badge-info',
      'partial_words': 'badge-secondary',
      'semantic_strong': 'badge-info',
      'semantic_chunk': 'badge-info',
      'vendor_match': 'badge-warning',
      'vendor_filter': 'badge-warning',
      'people_match': 'badge-error',
      'price_match': 'badge-success',
      'hybrid': 'badge-secondary'
    };
    return classes[matchType] || 'badge-secondary';
  }
  
  function getMatchTypeLabel(matchType) {
    const labels = {
      'exact_phrase': '✨ Exact Phrase',
      'exact_amount': 'Exact Amount',
      'exact_id': 'Exact ID',
      'exact_keyword': 'Exact Keyword',
      'keyword': 'Keyword',
      'partial_words': 'Partial Match',
      'semantic_strong': 'High Relevance',
      'semantic_chunk': 'Semantic',
      'vendor_match': '🏭 Vendor Match',
      'vendor_filter': 'Vendor Match',
      'people_match': '👤 People Match',
      'price_match': '💰 Price Match',
      'hybrid': 'Hybrid Match'
    };
    return labels[matchType] || matchType;
  }
  
  async function handleUpload() {
    if (!uploadFile) {
      toast.error('Please select a file');
      return;
    }
    
    uploading = true;
    
    try {
      const formData = new FormData();
      formData.append('file', uploadFile);
      formData.append('tags', uploadTags);
      
      const response = await fetch('http://localhost:8000/resources/upload', {
        method: 'POST',
        body: formData,
        credentials: 'include'
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Upload failed');
      }
      
      const data = await response.json();
      toast.success(`File uploaded: ${data.file_name}`);
      
      uploadFile = null;
      uploadTags = '';
      showUploadModal = false;
      
      if (query) performSearch();
      
    } catch (err) {
      toast.error(err.message);
    } finally {
      uploading = false;
    }
  }
  
  async function handleSnippetSave() {
    if (!snippetTitle || !snippetText) {
      toast.error('Title and text are required');
      return;
    }
    
    savingSnippet = true;
    
    try {
      const formData = new FormData();
      formData.append('title', snippetTitle);
      formData.append('text', snippetText);
      formData.append('tags', snippetTags);
      formData.append('snippet_source', snippetSource);
      
      const response = await fetch('http://localhost:8000/resources/snippet', {
        method: 'POST',
        body: formData,
        credentials: 'include'
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Save failed');
      }
      
      toast.success(`Snippet saved: ${snippetTitle}`);
      
      snippetTitle = '';
      snippetText = '';
      snippetTags = '';
      showSnippetModal = false;
      
      if (query) performSearch();
      
    } catch (err) {
      toast.error(err.message);
    } finally {
      savingSnippet = false;
    }
  }
</script>

<!-- Header -->
<div class="mb-6">
  <div class="flex items-center justify-between">
    <div>
      <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-2 flex items-center gap-3">
        <Search class="w-8 h-8 text-primary-600" />
        Intelligent Search
      </h1>
      <p class="text-gray-600 dark:text-gray-400">
        Unified search with automatic detection of IDs, amounts, vendors, and semantic meaning
      </p>
    </div>
    
    <div class="flex gap-3">
      <button class="btn btn-secondary" on:click={() => showUploadModal = true}>
        <Upload class="w-4 h-4 mr-2" />
        Upload
      </button>
      <button class="btn btn-secondary" on:click={() => showSnippetModal = true}>
        <FileText class="w-4 h-4 mr-2" />
        Snippet
      </button>
    </div>
  </div>
</div>

<!-- Search Box (Chat-style) -->
<div class="card p-6 mb-6">
  <!-- Input Area -->
  <div class="relative mb-4">
    <textarea
      bind:value={query}
      on:input={handleInput}
      on:keydown={handleKeyDown}
      on:focus={() => { if (query.length >= 2 && suggestions.length > 0) showSuggestions = true; }}
      on:blur={() => { setTimeout(() => showSuggestions = false, 200); }}
      placeholder="Search documents by meaning, IDs, amounts, vendors, or file types... (Press Enter)"
      class="w-full px-4 py-3 pr-20 border border-gray-300 dark:border-gray-600 rounded-3xl focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-all max-h-40"
      rows="1"
      style="min-height: 52px;"
    ></textarea>
    
    <!-- Suggestions Dropdown -->
    {#if showSuggestions && suggestions.length > 0}
      <div class="absolute top-full left-0 right-0 mt-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg max-h-80 overflow-y-auto z-50">
        {#each suggestions as suggestion, index}
          <button
            type="button"
            class="w-full px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors flex items-center justify-between gap-3 {index === selectedSuggestionIndex ? 'bg-primary-50 dark:bg-primary-900/20' : ''}"
            on:click={() => selectSuggestion(suggestion)}
          >
            <div class="flex items-center gap-3 flex-1 min-w-0">
              {#if suggestion.type === 'file'}
                <File class="w-4 h-4 text-primary-600 flex-shrink-0" />
              {:else if suggestion.type === 'vendor'}
                <Building class="w-4 h-4 text-blue-600 flex-shrink-0" />
              {:else if suggestion.type === 'entity'}
                <Hash class="w-4 h-4 text-green-600 flex-shrink-0" />
              {:else if suggestion.type === 'keyword'}
                <FileText class="w-4 h-4 text-purple-600 flex-shrink-0" />
              {:else}
                <Search class="w-4 h-4 text-gray-600 flex-shrink-0" />
              {/if}
              <span class="text-gray-900 dark:text-white truncate">{suggestion.text}</span>
            </div>
            <span class="text-xs text-gray-500 dark:text-gray-400 uppercase flex-shrink-0">{suggestion.type}</span>
          </button>
        {/each}
      </div>
    {/if}
    
    <div class="absolute right-3 bottom-3 flex items-center space-x-2">
      {#if query.length > 0}
        <span class="text-xs text-gray-400 dark:text-gray-500">
          {query.length}
        </span>
      {/if}
      
      <button
        on:click={performSearch}
        disabled={!query.trim() || loading}
        class="flex items-center justify-center w-9 h-9 bg-primary-600 hover:bg-primary-700 disabled:bg-gray-400 text-white rounded-full transition-all disabled:cursor-not-allowed shadow-sm"
        title="Search (Enter)"
      >
        {#if loading}
          <div class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
        {:else}
          <Send size={16} />
        {/if}
      </button>
    </div>
  </div>
  
  <!-- Query Analysis -->
  {#if queryAnalysis}
    <div class="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800 mb-4">
      <div class="flex items-center gap-2 text-sm font-medium text-blue-900 dark:text-blue-100 mb-2">
        <Filter class="w-4 h-4" />
        Detected Filters
      </div>
      <div class="flex flex-wrap gap-2">
        {#if queryAnalysis.ids && queryAnalysis.ids.length > 0}
          <span class="badge badge-success flex items-center gap-1">
            <Hash class="w-3 h-3" />
            IDs: {queryAnalysis.ids.join(', ')}
          </span>
        {/if}
        {#if queryAnalysis.emails && queryAnalysis.emails.length > 0}
          <span class="badge badge-info flex items-center gap-1">
            <Mail class="w-3 h-3" />
            {queryAnalysis.emails.join(', ')}
          </span>
        {/if}
        {#if queryAnalysis.ibans && queryAnalysis.ibans.length > 0}
          <span class="badge badge-primary flex items-center gap-1">
            <CreditCard class="w-3 h-3" />
            {queryAnalysis.ibans.join(', ')}
          </span>
        {/if}
        {#if queryAnalysis.money && queryAnalysis.money.length > 0}
          {#each queryAnalysis.money as m}
            <span class="badge badge-warning flex items-center gap-1">
              <DollarSign class="w-3 h-3" />
              {m.currency} {m.amount.toFixed(2)}
            </span>
          {/each}
        {/if}
        {#if queryAnalysis.entities && queryAnalysis.entities.length > 0}
          <span class="badge badge-secondary flex items-center gap-1">
            <Building class="w-3 h-3" />
            {queryAnalysis.entities.join(', ')}
          </span>
        {/if}
        {#if queryAnalysis.file_types && queryAnalysis.file_types.length > 0}
          <span class="badge badge-error flex items-center gap-1">
            <File class="w-3 h-3" />
            {queryAnalysis.file_types.join(', ').toUpperCase()}
          </span>
        {/if}
        {#if queryAnalysis.clean_text}
          <span class="text-xs text-blue-700 dark:text-blue-300">
            Semantic: "{queryAnalysis.clean_text}"
          </span>
        {/if}
      </div>
    </div>
  {/if}
  
  <!-- Hint -->
  <div class="flex items-center justify-between mt-3 text-xs text-gray-500 dark:text-gray-400">
    <div>
      Press <kbd class="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-700 rounded text-xs font-mono">Enter</kbd> to search • 
      <kbd class="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-700 rounded text-xs font-mono">↑↓</kbd> to navigate suggestions • 
      <kbd class="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-700 rounded text-xs font-mono">Esc</kbd> to close
    </div>
  </div>
</div>

<!-- Results Header -->
{#if query && !loading && results.length > 0}
  <div class="flex items-center justify-between mb-4">
    <span class="text-lg font-semibold text-gray-900 dark:text-white">
      {results.length} results
    </span>
    <span class="text-sm text-gray-500 dark:text-gray-400">
      {searchTime}ms
    </span>
  </div>
{/if}

<!-- Results -->
{#if results.length > 0}
  <div class="space-y-3">
    {#each results as result}
      <div class="card p-5 hover:shadow-md transition-shadow">
        <div class="flex items-start gap-4">
          <div class="flex-shrink-0 mt-1">
            <File class="w-8 h-8 text-gray-400" />
          </div>
          
          <div class="flex-1 min-w-0">
            <div class="flex items-start justify-between gap-3 mb-2">
              <h3 class="text-lg font-semibold text-gray-900 dark:text-white truncate">
                {result.file_name}
              </h3>
              {#if result.open_url}
                <a
                  href={result.open_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  class="btn btn-sm btn-secondary flex items-center gap-1 flex-shrink-0"
                  title="Open document"
                >
                  <ExternalLink class="w-3 h-3" />
                  Open
                </a>
              {/if}
            </div>
            
            {#if result.text}
              <p class="text-gray-600 dark:text-gray-400 text-sm mb-3 line-clamp-2">
                {result.text}
              </p>
            {:else if result.summary}
              <p class="text-gray-600 dark:text-gray-400 text-sm mb-3 line-clamp-2">
                {result.summary}
              </p>
            {/if}
            
            <!-- Highlights -->
            {#if result.highlights && result.highlights.length > 0}
              <div class="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded p-2 mb-3 text-xs">
                {#each result.highlights.slice(0, 2) as highlight}
                  <div class="text-gray-700 dark:text-gray-300 mb-1">
                    ...{highlight.texts.join(' ')}...
                  </div>
                {/each}
              </div>
            {/if}
            
            <div class="flex flex-wrap gap-2">
              {#if result.match_type}
                <span class="badge {getMatchTypeBadgeClass(result.match_type)} text-xs">
                  {getMatchTypeLabel(result.match_type)}
                </span>
              {/if}
              {#if result.file_type}
                <span class="badge badge-secondary text-xs uppercase">
                  {result.file_type}
                </span>
              {/if}
              {#if result.vendor}
                <span class="badge badge-primary text-xs flex items-center gap-1">
                  <Building class="w-3 h-3" />
                  {result.vendor}
                </span>
              {/if}
              {#if result.currency && result.amounts_cents && result.amounts_cents.length > 0}
                <span class="badge badge-warning text-xs flex items-center gap-1">
                  <DollarSign class="w-3 h-3" />
                  {result.currency} {(result.amounts_cents[0] / 100).toFixed(2)}
                </span>
              {/if}
              {#if result.page_number}
                <span class="badge badge-info text-xs">
                  Page {result.page_number}
                </span>
              {/if}
              {#if result.row_index !== null && result.row_index !== undefined}
                <span class="badge badge-info text-xs">
                  Row {result.row_index}
                </span>
              {/if}
            </div>
          </div>
          
          <div class="text-right flex-shrink-0">
            <div class="text-2xl font-bold mb-1
                        {result.score >= 0.7 ? 'text-green-600 dark:text-green-400' :
                         result.score >= 0.5 ? 'text-lime-600 dark:text-lime-400' :
                         result.score >= 0.3 ? 'text-yellow-600 dark:text-yellow-400' :
                         result.score >= 0.15 ? 'text-orange-600 dark:text-orange-400' :
                         'text-red-600 dark:text-red-400'}">
              {(result.score * 100).toFixed(0)}%
            </div>
            <div class="text-xs text-gray-500 dark:text-gray-400">relevance</div>
            {#if result.occurrences}
              <div class="text-xs text-gray-500 dark:text-gray-400 mt-1">
                {result.occurrences}× occurrence{result.occurrences !== 1 ? 's' : ''}
              </div>
            {/if}
            {#if result.matching_chunks && result.matching_chunks > 1}
              <div class="text-xs text-gray-500 dark:text-gray-400">
                in {result.matching_chunks} chunk{result.matching_chunks !== 1 ? 's' : ''}
              </div>
            {/if}
          </div>
        </div>
      </div>
    {/each}
  </div>
{/if}

<!-- No Results -->
{#if searchPerformed && !loading && results.length === 0 && !error}
  <div class="card p-12 text-center">
    <Search class="w-16 h-16 mx-auto text-gray-400 mb-4" />
    <h3 class="text-xl font-semibold text-gray-900 dark:text-white mb-2">
      No results found
    </h3>
    <p class="text-gray-600 dark:text-gray-400">
      No documents match "{query}"
    </p>
  </div>
{/if}

<!-- Loading -->
{#if loading}
  <div class="card p-12 text-center">
    <Loader class="w-12 h-12 mx-auto text-primary-600 animate-spin mb-4" />
    <p class="text-gray-600 dark:text-gray-400">Searching...</p>
  </div>
{/if}

<!-- Upload Modal -->
{#if showUploadModal}
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" on:click={() => showUploadModal = false}>
    <div class="card p-6 w-full max-w-lg" on:click|stopPropagation>
      <div class="flex items-center justify-between mb-6">
        <h2 class="text-xl font-semibold text-gray-900 dark:text-white flex items-center gap-2">
          <Upload class="w-5 h-5" />
          Upload File
        </h2>
        <button class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300" on:click={() => showUploadModal = false}>
          <X class="w-5 h-5" />
        </button>
      </div>
      
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Select File
          </label>
          <input
            type="file"
            on:change={(e) => uploadFile = e.target.files[0]}
            class="input-field"
            accept=".pdf,.csv,.txt,.md,.json,.ini,.png,.jpg,.jpeg,.gif"
          />
        </div>
        
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Tags (comma separated)
          </label>
          <input
            type="text"
            bind:value={uploadTags}
            placeholder="invoice, finance, 2025"
            class="input-field"
          />
        </div>
        
        <div class="flex gap-3 pt-4">
          <button
            class="btn btn-primary flex-1"
            on:click={handleUpload}
            disabled={uploading || !uploadFile}
          >
            {#if uploading}
              <Loader class="w-4 h-4 mr-2 animate-spin" />
            {/if}
            Upload
          </button>
          <button class="btn btn-secondary" on:click={() => showUploadModal = false}>
            Cancel
          </button>
        </div>
      </div>
    </div>
  </div>
{/if}

<!-- Snippet Modal -->
{#if showSnippetModal}
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" on:click={() => showSnippetModal = false}>
    <div class="card p-6 w-full max-w-lg" on:click|stopPropagation>
      <div class="flex items-center justify-between mb-6">
        <h2 class="text-xl font-semibold text-gray-900 dark:text-white flex items-center gap-2">
          <FileText class="w-5 h-5" />
          Save Snippet
        </h2>
        <button class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300" on:click={() => showSnippetModal = false}>
          <X class="w-5 h-5" />
        </button>
      </div>
      
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Title
          </label>
          <input
            type="text"
            bind:value={snippetTitle}
            placeholder="Important note"
            class="input-field"
          />
        </div>
        
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Text
          </label>
          <textarea
            bind:value={snippetText}
            placeholder="Paste or type your text..."
            rows="6"
            class="textarea-field"
          />
        </div>
        
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Tags
            </label>
            <input
              type="text"
              bind:value={snippetTags}
              placeholder="note, reminder"
              class="input-field"
            />
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Source
            </label>
            <select bind:value={snippetSource} class="input-field">
              <option value="user_input">User Input</option>
              <option value="ai_agent">AI Agent</option>
              <option value="paste">Paste</option>
              <option value="api">API</option>
            </select>
          </div>
        </div>
        
        <div class="flex gap-3 pt-4">
          <button
            class="btn btn-primary flex-1"
            on:click={handleSnippetSave}
            disabled={savingSnippet || !snippetTitle || !snippetText}
          >
            {#if savingSnippet}
              <Loader class="w-4 h-4 mr-2 animate-spin" />
            {/if}
            Save
          </button>
          <button class="btn btn-secondary" on:click={() => showSnippetModal = false}>
            Cancel
          </button>
        </div>
      </div>
    </div>
  </div>
{/if}

<style>
  /* Auto-resize textarea */
  textarea {
    field-sizing: content;
  }
</style>
