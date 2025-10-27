<script>
  import { onMount } from 'svelte';
  import {
    Database,
    Plus,
    Search,
    Edit,
    Trash2,
    FileText,
    File,
    Globe,
    Server,
    Code,
    X,
    Save,
    Loader,
    Upload
  } from 'lucide-svelte';
  import * as resourceAPI from '$lib/services/resources';

  let resources = [];
  let filteredResources = [];
  let loading = true;
  let searchQuery = '';
  let filterType = 'all';
  let totalCount = 0;
  
  // Modal state
  let showCreateModal = false;
  let showEditModal = false;
  let showDeleteModal = false;
  let selectedResource = null;
  
  // Form state
  let formData = {
    uri: '',
    name: '',
    description: '',
    mime_type: 'text/plain',
    resource_type: 'text',
    content: ''
  };
  
  let formErrors = {};
  let submitting = false;
  let selectedFile = null;
  let fileInputElement;
  
  const resourceTypes = [
    { value: 'file', label: 'File', icon: File },
    { value: 'url', label: 'URL', icon: Globe },
    { value: 'database', label: 'Database', icon: Server },
    { value: 'api', label: 'API', icon: Code },
    { value: 'text', label: 'Text', icon: FileText }
  ];
  
  const mimeTypes = [
    'text/plain',
    'text/html',
    'text/markdown',
    'application/json',
    'application/xml',
    'text/csv',
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'image/png',
    'image/jpeg',
    'image/gif',
    'application/octet-stream'
  ];
  
  onMount(async () => {
    await loadResources();
  });
  
  async function loadResources() {
    try {
      loading = true;
      resources = await resourceAPI.listResources();
      filteredResources = resources;
      totalCount = resources.length;
      
      loading = false;
    } catch (error) {
      console.error('Error loading resources:', error);
      loading = false;
    }
  }
  
  function filterResources() {
    let filtered = resources;
    
    // Apply type filter
    if (filterType !== 'all') {
      filtered = filtered.filter(r => r.mimeType && r.mimeType.startsWith(filterType));
    }
    
    // Apply search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(r =>
        r.name.toLowerCase().includes(query) ||
        r.description.toLowerCase().includes(query) ||
        r.uri.toLowerCase().includes(query)
      );
    }
    
    filteredResources = filtered;
  }
  
  $: {
    searchQuery;
    filterType;
    filterResources();
  }
  
  function openCreateModal() {
    formData = {
      uri: '',
      name: '',
      description: '',
      mime_type: 'text/plain',
      resource_type: 'text',
      content: ''
    };
    formErrors = {};
    selectedFile = null;
    showCreateModal = true;
  }
  
  // Auto-generate URI based on resource type
  function generateURI() {
    const timestamp = Date.now();
    const randomStr = Math.random().toString(36).substring(2, 8);
    
    switch(formData.resource_type) {
      case 'file':
        if (selectedFile) {
          return `file:///${selectedFile.name}`;
        }
        return `file:///document-${randomStr}.txt`;
      case 'url':
        return formData.uri || `https://example.com/resource-${randomStr}`;
      case 'text':
        const slug = formData.name ? formData.name.toLowerCase().replace(/\s+/g, '-') : `text-${randomStr}`;
        return `text:///${slug}`;
      case 'database':
        return `db:///${randomStr}`;
      case 'api':
        return `api:///${randomStr}`;
      default:
        return `resource:///${randomStr}`;
    }
  }
  
  // Detect MIME type from file extension
  function detectMimeType(filename) {
    const ext = filename.split('.').pop().toLowerCase();
    const mimeMap = {
      'txt': 'text/plain',
      'md': 'text/markdown',
      'html': 'text/html',
      'htm': 'text/html',
      'json': 'application/json',
      'xml': 'application/xml',
      'csv': 'text/csv',
      'pdf': 'application/pdf',
      'doc': 'application/msword',
      'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'xls': 'application/vnd.ms-excel',
      'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'png': 'image/png',
      'jpg': 'image/jpeg',
      'jpeg': 'image/jpeg',
      'gif': 'image/gif',
      'svg': 'image/svg+xml'
    };
    return mimeMap[ext] || 'application/octet-stream';
  }
  
  // Handle file selection
  async function handleFileSelect(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    
    selectedFile = file;
    
    // Auto-fill form fields
    if (!formData.name) {
      formData.name = file.name;
    }
    
    // Detect MIME type
    formData.mime_type = detectMimeType(file.name);
    
    // Generate URI
    formData.uri = generateURI();
    
    // Read file content for preview (only for text files under 1MB for display)
    if (formData.mime_type.startsWith('text/') || formData.mime_type === 'application/json') {
      if (file.size < 1024 * 1024) { // 1MB limit for preview
        try {
          const text = await readFileAsText(file);
          formData.content = text;
        } catch (error) {
          console.error('Error reading file:', error);
          formErrors.file = 'Error reading file content';
        }
      } else if (file.size > 10 * 1024 * 1024) {
        formErrors.file = 'File is too large (max 10MB)';
        selectedFile = null;
        fileInputElement.value = '';
        return;
      } else {
        formData.content = `[Large text file: ${file.name}, ${formatFileSize(file.size)}]`;
      }
    } else {
      // Binary files - will be uploaded directly
      if (file.size > 10 * 1024 * 1024) {
        formErrors.file = 'File is too large (max 10MB)';
        selectedFile = null;
        fileInputElement.value = '';
        return;
      }
      formData.content = `[Binary file: ${file.name}, ${formatFileSize(file.size)}]`;
    }
  }
  
  // Read file as text
  function readFileAsText(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => resolve(e.target.result);
      reader.onerror = (e) => reject(e);
      reader.readAsText(file);
    });
  }
  
  // Format file size
  function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  }
  
  // Handle resource type change
  function handleResourceTypeChange() {
    // Clear file selection when switching away from file type
    if (formData.resource_type !== 'file') {
      selectedFile = null;
      if (fileInputElement) {
        fileInputElement.value = '';
      }
    }
    
    // Auto-generate URI for new type
    if (!formData.uri || formData.uri.startsWith('file://') || formData.uri.startsWith('text://')) {
      formData.uri = generateURI();
    }
  }
  
  // Drag and drop handlers
  let isDragging = false;
  
  function handleDragEnter(event) {
    event.preventDefault();
    event.stopPropagation();
    isDragging = true;
  }
  
  function handleDragLeave(event) {
    event.preventDefault();
    event.stopPropagation();
    isDragging = false;
  }
  
  function handleDragOver(event) {
    event.preventDefault();
    event.stopPropagation();
  }
  
  async function handleDrop(event) {
    event.preventDefault();
    event.stopPropagation();
    isDragging = false;
    
    const files = event.dataTransfer?.files;
    if (files && files.length > 0) {
      // Simulate file input change
      const file = files[0];
      
      // Create a mock event with the file
      selectedFile = file;
      
      // Auto-fill form fields
      if (!formData.name) {
        formData.name = file.name;
      }
      
      // Detect MIME type
      formData.mime_type = detectMimeType(file.name);
      
      // Generate URI
      formData.uri = generateURI();
      
      // Read file content
      if (formData.mime_type.startsWith('text/') || formData.mime_type === 'application/json') {
        if (file.size < 1024 * 1024) {
          try {
            const text = await readFileAsText(file);
            formData.content = text;
          } catch (error) {
            console.error('Error reading file:', error);
            formErrors.file = 'Error reading file content';
          }
        } else if (file.size > 10 * 1024 * 1024) {
          formErrors.file = 'File is too large (max 10MB)';
          selectedFile = null;
          return;
        } else {
          formData.content = `[Large text file: ${file.name}, ${formatFileSize(file.size)}]`;
        }
      } else {
        if (file.size > 10 * 1024 * 1024) {
          formErrors.file = 'File is too large (max 10MB)';
          selectedFile = null;
          return;
        }
        formData.content = `[Binary file: ${file.name}, ${formatFileSize(file.size)}]`;
      }
    }
  }
  
  function openEditModal(resource) {
    selectedResource = resource;
    formData = {
      name: resource.name,
      description: resource.description,
      content: '' // We'll load content separately if needed
    };
    formErrors = {};
    showEditModal = true;
  }
  
  function openDeleteModal(resource) {
    selectedResource = resource;
    showDeleteModal = true;
  }
  
  function closeModals() {
    showCreateModal = false;
    showEditModal = false;
    showDeleteModal = false;
    selectedResource = null;
    formErrors = {};
  }
  
  function validateForm() {
    formErrors = {};
    
    if (showCreateModal) {
      // Validate based on resource type
      if (formData.resource_type === 'file') {
        if (!selectedFile && !formData.content) {
          formErrors.file = 'Please select a file';
        }
      } else if (formData.resource_type === 'url') {
        if (!formData.uri) {
          formErrors.uri = 'URL is required';
        } else if (!formData.uri.startsWith('http://') && !formData.uri.startsWith('https://')) {
          formErrors.uri = 'URL must start with http:// or https://';
        }
      }
      
      // Auto-generate URI if not set (except for URL type)
      if (!formData.uri && formData.resource_type !== 'url') {
        formData.uri = generateURI();
      }
      
      if (!formData.name) formErrors.name = 'Name is required';
      if (!formData.description) formErrors.description = 'Description is required';
    } else if (showEditModal) {
      if (!formData.name) formErrors.name = 'Name is required';
    }
    
    return Object.keys(formErrors).length === 0;
  }
  
  async function handleCreate() {
    if (!validateForm()) return;
    
    try {
      submitting = true;
      
      // If file type with selected file, use upload endpoint
      if (formData.resource_type === 'file' && selectedFile) {
        await resourceAPI.uploadResource(
          selectedFile,
          formData.name,
          formData.description
        );
      } else {
        // Otherwise use regular create endpoint
        await resourceAPI.createResource(formData);
      }
      
      await loadResources();
      closeModals();
    } catch (error) {
      formErrors.submit = error.message;
    } finally {
      submitting = false;
    }
  }
  
  async function handleUpdate() {
    if (!validateForm() || !selectedResource) return;
    
    try {
      submitting = true;
      await resourceAPI.updateResource(selectedResource.uri, formData);
      await loadResources();
      closeModals();
    } catch (error) {
      formErrors.submit = error.message;
    } finally {
      submitting = false;
    }
  }
  
  async function handleDelete() {
    if (!selectedResource) return;
    
    try {
      submitting = true;
      await resourceAPI.deleteResource(selectedResource.uri);
      await loadResources();
      closeModals();
    } catch (error) {
      formErrors.submit = error.message;
    } finally {
      submitting = false;
    }
  }
  
  function getResourceTypeIcon(mimeType) {
    if (!mimeType) return FileText;
    if (mimeType.startsWith('text/')) return FileText;
    if (mimeType.startsWith('application/json')) return Code;
    if (mimeType.startsWith('application/xml')) return Code;
    return File;
  }
</script>

<svelte:head>
  <title>Resources - AI MCP Toolkit</title>
</svelte:head>

<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
  <!-- Header -->
  <div class="mb-8">
    <div class="flex items-center justify-between">
      <div class="flex items-center space-x-3">
        <div class="w-12 h-12 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center">
          <Database size={24} class="text-white" />
        </div>
        <div>
          <h1 class="text-3xl font-bold text-gray-900 dark:text-white">Resources</h1>
          <p class="text-gray-600 dark:text-gray-400">
            Store and manage documents, files, and data for AI agents to use
          </p>
        </div>
      </div>
      <button
        on:click={openCreateModal}
        class="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors"
      >
        <Plus size={18} />
        Add Resource
      </button>
    </div>
    
    <!-- Explanation Card -->
    <div class="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
      <h3 class="text-sm font-medium text-blue-900 dark:text-blue-100 mb-2">What are Resources?</h3>
      <p class="text-sm text-blue-800 dark:text-blue-200">
        Resources are documents, text files, or data that AI agents can reference and use. For example: documentation to summarize, text to analyze, or content to process. Each resource has a unique URI identifier and can be accessed by any agent.
      </p>
    </div>
  </div>
  
  <!-- Stats Cards -->
  <div class="mb-6">
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-gray-600 dark:text-gray-400">Total Resources</p>
            <p class="text-2xl font-bold text-gray-900 dark:text-white">{totalCount}</p>
          </div>
          <div class="w-12 h-12 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center">
            <Database class="w-6 h-6 text-blue-600 dark:text-blue-400" />
          </div>
        </div>
      </div>
    
    {#each resourceTypes.slice(0, 3) as type}
      <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-gray-600 dark:text-gray-400">{type.label}</p>
            <p class="text-2xl font-bold text-gray-900 dark:text-white">
              {resources.filter(r => r.uri && r.uri.includes(type.value)).length}
            </p>
          </div>
          <div class="w-12 h-12 bg-gray-100 dark:bg-gray-700 rounded-lg flex items-center justify-center">
            <svelte:component this={type.icon} class="w-6 h-6 text-gray-600 dark:text-gray-400" />
          </div>
        </div>
      </div>
    {/each}
    </div>
  </div>
  
  <!-- Filters and Search -->
  <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 mb-6">
    <div class="flex flex-col md:flex-row gap-4">
      <div class="flex-1 relative">
        <Search class="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={18} />
        <input
          type="text"
          bind:value={searchQuery}
          placeholder="Search resources by name, description, or URI..."
          class="w-full pl-10 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
        />
      </div>
      
      <select bind:value={filterType} class="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white md:w-48">
        <option value="all">All Types</option>
        <option value="text">Text</option>
        <option value="application">Application</option>
      </select>
    </div>
  </div>
  
  <!-- Resources List -->
  <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
    <div class="p-6 border-b border-gray-200 dark:border-gray-700">
      <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
        Resources ({filteredResources.length})
      </h2>
    </div>
    
    <div class="p-6">
      {#if loading}
        <div class="flex items-center justify-center py-12">
          <Loader class="animate-spin text-primary-500" size={32} />
        </div>
      {:else if filteredResources.length === 0}
        <div class="text-center py-12">
          <Database class="mx-auto h-12 w-12 text-gray-400" />
          <h3 class="mt-2 text-sm font-medium text-gray-900 dark:text-white">No resources found</h3>
          <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
            {searchQuery || filterType !== 'all' ? 'Try adjusting your filters' : 'Get started by creating a new resource'}
          </p>
          {#if !searchQuery && filterType === 'all'}
            <button
              on:click={openCreateModal}
              class="mt-4 inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors"
            >
              <Plus size={18} />
              Add Your First Resource
            </button>
          {/if}
        </div>
      {:else}
        <div class="space-y-4">
          {#each filteredResources as resource}
            <div class="border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
              <div class="flex items-start justify-between">
                <div class="flex items-start gap-3 flex-1">
                  <div class="mt-1">
                    <svelte:component 
                      this={getResourceTypeIcon(resource.mimeType)} 
                      class="text-gray-400" 
                      size={20} 
                    />
                  </div>
                  <div class="flex-1 min-w-0">
                    <h3 class="text-sm font-medium text-gray-900 dark:text-white truncate">
                      {resource.name}
                    </h3>
                    <p class="text-sm text-gray-600 dark:text-gray-400 mt-1">
                      {resource.description}
                    </p>
                    <div class="flex items-center gap-4 mt-2">
                      <span class="text-xs text-gray-500 dark:text-gray-400 font-mono">
                        {resource.uri}
                      </span>
                      {#if resource.mimeType}
                        <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300">
                          {resource.mimeType}
                        </span>
                      {/if}
                      {#if resource.ownerUsername}
                        <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300">
                          👤 {resource.ownerUsername}
                        </span>
                      {/if}
                    </div>
                  </div>
                </div>
                
                <div class="flex items-center gap-2 ml-4">
                  <button
                    on:click={() => openEditModal(resource)}
                    class="p-2 text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                    title="Edit resource"
                  >
                    <Edit size={18} />
                  </button>
                  <button
                    on:click={() => openDeleteModal(resource)}
                    class="p-2 text-gray-400 hover:text-red-600 dark:hover:text-red-400 transition-colors"
                    title="Delete resource"
                  >
                    <Trash2 size={18} />
                  </button>
                </div>
              </div>
            </div>
          {/each}
        </div>
      {/if}
    </div>
  </div>
</div>

<!-- Create Resource Modal -->
{#if showCreateModal}
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
    <div class="bg-white dark:bg-gray-800 rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
      <div class="p-6 border-b border-gray-200 dark:border-gray-700">
        <div class="flex items-center justify-between">
          <h2 class="text-xl font-semibold text-gray-900 dark:text-white">Create New Resource</h2>
          <button on:click={closeModals} class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
            <X size={20} />
          </button>
        </div>
      </div>
      
      <div class="p-6 space-y-4">
        <!-- Resource Type Selection (First) -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Resource Type *
          </label>
          <select 
            bind:value={formData.resource_type} 
            on:change={handleResourceTypeChange}
            class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          >
            {#each resourceTypes as type}
              <option value={type.value}>{type.label}</option>
            {/each}
          </select>
          <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
            {#if formData.resource_type === 'file'}
              Upload a file from your computer
            {:else if formData.resource_type === 'url'}
              Reference a resource from a URL
            {:else if formData.resource_type === 'text'}
              Create a text note or document
            {:else if formData.resource_type === 'database'}
              Connect to a database
            {:else if formData.resource_type === 'api'}
              Reference an API endpoint
            {/if}
          </p>
        </div>
        
        <!-- File Upload (Only for 'file' type) -->
        {#if formData.resource_type === 'file'}
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Select File *
            </label>
            <div 
              class="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 {isDragging ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' : 'border-gray-300 dark:border-gray-600'} border-dashed rounded-lg hover:border-blue-500 dark:hover:border-blue-400 transition-colors"
              on:dragenter={handleDragEnter}
              on:dragleave={handleDragLeave}
              on:dragover={handleDragOver}
              on:drop={handleDrop}
            >
              <div class="space-y-1 text-center">
                <Upload class="mx-auto h-12 w-12 {isDragging ? 'text-blue-500' : 'text-gray-400'}" />
                <div class="flex text-sm text-gray-600 dark:text-gray-400">
                  <label class="relative cursor-pointer bg-white dark:bg-gray-800 rounded-md font-medium text-blue-600 hover:text-blue-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-blue-500">
                    <span class="px-2">Upload a file</span>
                    <input 
                      type="file" 
                      bind:this={fileInputElement}
                      on:change={handleFileSelect}
                      class="sr-only" 
                    />
                  </label>
                  <p class="pl-1">or drag and drop</p>
                </div>
                <p class="text-xs text-gray-500 dark:text-gray-400">
                  Any file type up to 10MB
                </p>
              </div>
            </div>
            {#if selectedFile}
              <div class="mt-2 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-2">
                    <File size={16} class="text-blue-600 dark:text-blue-400" />
                    <span class="text-sm text-blue-900 dark:text-blue-100 font-medium">{selectedFile.name}</span>
                    <span class="text-xs text-blue-600 dark:text-blue-400">({formatFileSize(selectedFile.size)})</span>
                  </div>
                  <button
                    on:click={() => {
                      selectedFile = null;
                      fileInputElement.value = '';
                      formData.content = '';
                    }}
                    class="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
                  >
                    <X size={16} />
                  </button>
                </div>
              </div>
            {/if}
            {#if formErrors.file}
              <p class="text-red-500 text-sm mt-1">{formErrors.file}</p>
            {/if}
          </div>
        {/if}
        
        <!-- URI Input (conditional based on type) -->
        {#if formData.resource_type === 'url'}
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              URL *
            </label>
            <input
              type="url"
              bind:value={formData.uri}
              placeholder="https://example.com/document.pdf"
              class="w-full px-4 py-2 border {formErrors.uri ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'} rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
            />
            {#if formErrors.uri}
              <p class="text-red-500 text-sm mt-1">{formErrors.uri}</p>
            {/if}
          </div>
        {:else if formData.resource_type !== 'file'}
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              URI <span class="text-gray-500 text-xs">(auto-generated)</span>
            </label>
            <input
              type="text"
              bind:value={formData.uri}
              placeholder="Will be auto-generated"
              class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 font-mono text-sm"
            />
          </div>
        {/if}
        
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Name *
          </label>
          <input
            type="text"
            bind:value={formData.name}
            placeholder="My Document"
            class="w-full px-4 py-2 border {formErrors.name ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'} rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
          />
          {#if formErrors.name}
            <p class="text-red-500 text-sm mt-1">{formErrors.name}</p>
          {/if}
        </div>
        
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Description *
          </label>
          <textarea
            bind:value={formData.description}
            placeholder="A brief description of this resource"
            rows="3"
            class="w-full px-4 py-2 border {formErrors.description ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'} rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
          />
          {#if formErrors.description}
            <p class="text-red-500 text-sm mt-1">{formErrors.description}</p>
          {/if}
        </div>
        
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            MIME Type <span class="text-gray-500 text-xs">(auto-detected for files)</span>
          </label>
          <select bind:value={formData.mime_type} class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
            {#each mimeTypes as mimeType}
              <option value={mimeType}>{mimeType}</option>
            {/each}
          </select>
        </div>
        
        <!-- Content field - only show for text and database types -->
        {#if formData.resource_type === 'text' || formData.resource_type === 'database' || (formData.resource_type === 'file' && selectedFile)}
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Content {formData.resource_type === 'file' && selectedFile ? '(from file)' : formData.resource_type === 'text' ? '*' : '(optional)'}
            </label>
            <textarea
              bind:value={formData.content}
              placeholder={formData.resource_type === 'file' ? 'File content will be loaded automatically...' : formData.resource_type === 'text' ? 'Enter your text content...' : 'Resource content...'}
              rows="6"
              class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 font-mono text-sm"
              readonly={formData.resource_type === 'file' && selectedFile}
            />
            {#if formData.resource_type === 'text' && !formData.content}
              <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Add your text content here
              </p>
            {/if}
          </div>
        {/if}
        
        <!-- Info message for URL type -->
        {#if formData.resource_type === 'url'}
          <div class="p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
            <p class="text-sm text-blue-800 dark:text-blue-200">
              ℹ️ The content from this URL will be automatically fetched when the resource is accessed by agents.
            </p>
          </div>
        {/if}
        
        {#if formErrors.submit}
          <div class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
            <p class="text-red-600 dark:text-red-400 text-sm">{formErrors.submit}</p>
          </div>
        {/if}
      </div>
      
      <div class="p-6 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-3">
        <button
          on:click={closeModals}
          class="px-4 py-2 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 font-medium rounded-lg transition-colors"
          disabled={submitting}
        >
          Cancel
        </button>
        <button
          on:click={handleCreate}
          class="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-colors"
          disabled={submitting}
        >
          {#if submitting}
            <Loader class="animate-spin" size={18} />
          {:else}
            <Save size={18} />
          {/if}
          Create Resource
        </button>
      </div>
    </div>
  </div>
{/if}

<!-- Edit Resource Modal -->
{#if showEditModal && selectedResource}
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
    <div class="bg-white dark:bg-gray-800 rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
      <div class="p-6 border-b border-gray-200 dark:border-gray-700">
        <div class="flex items-center justify-between">
          <h2 class="text-xl font-semibold text-gray-900 dark:text-white">Edit Resource</h2>
          <button on:click={closeModals} class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
            <X size={20} />
          </button>
        </div>
      </div>
      
      <div class="p-6 space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            URI (read-only)
          </label>
          <input
            type="text"
            value={selectedResource.uri}
            disabled
            class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white cursor-not-allowed"
          />
        </div>
        
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Name *
          </label>
          <input
            type="text"
            bind:value={formData.name}
            class="w-full px-4 py-2 border {formErrors.name ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'} rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
          />
          {#if formErrors.name}
            <p class="text-red-500 text-sm mt-1">{formErrors.name}</p>
          {/if}
        </div>
        
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Description
          </label>
          <textarea
            bind:value={formData.description}
            rows="3"
            class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
          />
        </div>
        
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Content
          </label>
          <textarea
            bind:value={formData.content}
            rows="6"
            class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 font-mono text-sm"
          />
        </div>
        
        {#if formErrors.submit}
          <div class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
            <p class="text-red-600 dark:text-red-400 text-sm">{formErrors.submit}</p>
          </div>
        {/if}
      </div>
      
      <div class="p-6 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-3">
        <button
          on:click={closeModals}
          class="px-4 py-2 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 font-medium rounded-lg transition-colors"
          disabled={submitting}
        >
          Cancel
        </button>
        <button
          on:click={handleUpdate}
          class="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-colors"
          disabled={submitting}
        >
          {#if submitting}
            <Loader class="animate-spin" size={18} />
          {:else}
            <Save size={18} />
          {/if}
          Update Resource
        </button>
      </div>
    </div>
  </div>
{/if}

<!-- Delete Confirmation Modal -->
{#if showDeleteModal && selectedResource}
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
    <div class="bg-white dark:bg-gray-800 rounded-lg max-w-md w-full">
      <div class="p-6">
        <div class="flex items-center gap-3 mb-4">
          <div class="w-12 h-12 bg-red-100 dark:bg-red-900 rounded-full flex items-center justify-center">
            <Trash2 class="text-red-600 dark:text-red-400" size={24} />
          </div>
          <div>
            <h2 class="text-xl font-semibold text-gray-900 dark:text-white">Delete Resource</h2>
          </div>
        </div>
        
        <p class="text-gray-600 dark:text-gray-400 mb-2">
          Are you sure you want to delete this resource?
        </p>
        <p class="text-sm text-gray-500 dark:text-gray-500 font-mono bg-gray-100 dark:bg-gray-700 p-2 rounded">
          {selectedResource.name}
        </p>
        <p class="text-red-600 dark:text-red-400 text-sm mt-3">
          This action cannot be undone.
        </p>
        
        {#if formErrors.submit}
          <div class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 mt-4">
            <p class="text-red-600 dark:text-red-400 text-sm">{formErrors.submit}</p>
          </div>
        {/if}
      </div>
      
      <div class="p-6 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-3">
        <button
          on:click={closeModals}
          class="px-4 py-2 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 font-medium rounded-lg transition-colors"
          disabled={submitting}
        >
          Cancel
        </button>
        <button
          on:click={handleDelete}
          class="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-colors"
          disabled={submitting}
        >
          {#if submitting}
            <Loader class="animate-spin" size={18} />
          {:else}
            <Trash2 size={18} />
          {/if}
          Delete Resource
        </button>
      </div>
    </div>
  </div>
{/if}
