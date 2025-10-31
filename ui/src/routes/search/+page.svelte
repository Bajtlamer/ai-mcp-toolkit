<script>
  import { onMount } from 'svelte';
  import {
    Search,
    Upload,
    FileText,
    Sparkles,
    Brain,
    Target,
    Zap,
    Filter,
    X,
    Loader,
    Building,
    DollarSign,
    Calendar,
    Hash,
    File,
    Send
  } from 'lucide-svelte';
  import toast from 'svelte-french-toast';
  
  let query = '';
  let results = [];
  let queryAnalysis = null;
  let searchType = 'auto';
  let loading = false;
  let searchTime = 0;
  let error = null;
  let limit = 20;
  
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
  
  let debounceTimer;
  
  const searchTypes = [
    { value: 'auto', label: 'Auto', icon: Sparkles },
    { value: 'semantic', label: 'Semantic', icon: Brain },
    { value: 'keyword', label: 'Keyword', icon: Target },
    { value: 'hybrid', label: 'Hybrid', icon: Zap }
  ];
  
  async function performSearch() {
    if (!query || query.trim().length < 2) {
      results = [];
      queryAnalysis = null;
      return;
    }
    
    loading = true;
    error = null;
    const startTime = performance.now();
    
    try {
      const params = new URLSearchParams({
        q: query,
        limit: limit.toString(),
        search_type: searchType
      });
      
      const response = await fetch(
        `http://localhost:8000/resources/search?${params}`,
        { credentials: 'include' }
      );
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Search failed');
      }
      
      const data = await response.json();
      results = data.results || [];
      queryAnalysis = data.query_analysis || null;
      // Don't override user's manual search type selection
      // searchType = data.search_type || 'auto';
      searchTime = (performance.now() - startTime).toFixed(0);
      
    } catch (err) {
      error = err.message;
      results = [];
      toast.error(err.message);
    } finally {
      loading = false;
    }
  }
  
  // Removed auto-search on typing - search only on Enter or button click
  
  function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      performSearch();
    }
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
        Contextual Search
      </h1>
      <p class="text-gray-600 dark:text-gray-400">
        Smart hybrid search with automatic query understanding
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
      on:keydown={handleKeyDown}
      placeholder="Search by meaning, exact IDs, amounts, vendors... (Press Enter to search)"
      class="w-full px-4 py-3 pr-20 border border-gray-300 dark:border-gray-600 rounded-3xl focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-all max-h-40"
      rows="1"
      style="min-height: 52px;"
    ></textarea>
    
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
  
  <!-- Search Type Tabs -->
  <div class="flex gap-2 flex-wrap mb-4">
    {#each searchTypes as type}
      {@const IconComponent = type.icon}
      <button
        class="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all
               {searchType === type.value 
                 ? 'bg-primary-600 text-white' 
                 : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'}"
        on:click={() => { searchType = type.value; if (query) performSearch(); }}
      >
        <IconComponent class="w-4 h-4" />
        {type.label}
      </button>
    {/each}
  </div>
  
  <!-- Query Analysis -->
  {#if queryAnalysis}
    <div class="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
      <div class="flex items-center gap-2 text-sm font-medium text-blue-900 dark:text-blue-100 mb-2">
        <Filter class="w-4 h-4" />
        Query Analysis
      </div>
      <div class="flex flex-wrap gap-2">
        {#if queryAnalysis.has_exact_id}
          <span class="badge badge-success flex items-center gap-1">
            <Hash class="w-3 h-3" />
            ID: {queryAnalysis.exact_ids?.join(', ')}
          </span>
        {/if}
        {#if queryAnalysis.has_money}
          <span class="badge badge-warning flex items-center gap-1">
            <DollarSign class="w-3 h-3" />
            Amounts
          </span>
        {/if}
        {#if queryAnalysis.has_vendor}
          <span class="badge badge-primary flex items-center gap-1">
            <Building class="w-3 h-3" />
            {queryAnalysis.vendors?.join(', ')}
          </span>
        {/if}
        {#if queryAnalysis.has_date}
          <span class="badge badge-error flex items-center gap-1">
            <Calendar class="w-3 h-3" />
            Dates
          </span>
        {/if}
      </div>
    </div>
  {/if}
  
  <!-- Hint -->
  <div class="flex items-center justify-between mt-3 text-xs text-gray-500 dark:text-gray-400">
    <div>
      Press <kbd class="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-700 rounded text-xs font-mono">Enter</kbd> to search • 
      <kbd class="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-700 rounded text-xs font-mono">Shift+Enter</kbd> for new line
    </div>
  </div>
</div>

<!-- Results Header -->
{#if query && !loading && results.length > 0}
  <div class="flex items-center justify-between mb-4">
    <div class="flex items-center gap-3">
      <span class="text-lg font-semibold text-gray-900 dark:text-white">
        {results.length} results
      </span>
      <span class="badge badge-primary">{searchType}</span>
    </div>
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
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-1 truncate">
              {result.file_name}
            </h3>
            
            <p class="text-gray-600 dark:text-gray-400 text-sm mb-3 line-clamp-2">
              {result.summary || 'No description'}
            </p>
            
            <div class="flex flex-wrap gap-2">
              {#if result.match_type}
                <span class="badge badge-secondary text-xs">{result.match_type}</span>
              {/if}
              {#if result.file_type}
                <span class="badge badge-secondary text-xs">{result.file_type}</span>
              {/if}
              {#if result.vendor}
                <span class="badge badge-primary text-xs flex items-center gap-1">
                  <Building class="w-3 h-3" />
                  {result.vendor}
                </span>
              {/if}
              {#if result.currency}
                <span class="badge badge-warning text-xs flex items-center gap-1">
                  <DollarSign class="w-3 h-3" />
                  {result.currency}
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
          </div>
        </div>
      </div>
    {/each}
  </div>
{/if}

<!-- No Results -->
{#if query && !loading && results.length === 0 && !error}
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
