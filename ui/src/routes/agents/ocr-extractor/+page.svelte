<script>
  import { ScanText, Upload, Copy, Download, Image as ImageIcon, CheckCircle, AlertCircle, Loader, X } from 'lucide-svelte';
  import { onMount } from 'svelte';

  let imageFile = null;
  let imagePreview = null;
  let extractedText = '';
  let isProcessing = false;
  let error = null;
  let success = false;

  function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file && file.type.startsWith('image/')) {
      imageFile = file;
      error = null;
      success = false;
      
      // Create preview
      const reader = new FileReader();
      reader.onload = (e) => {
        imagePreview = e.target.result;
      };
      reader.readAsDataURL(file);
    } else {
      error = 'Please select a valid image file (PNG, JPEG, etc.)';
      imageFile = null;
      imagePreview = null;
    }
  }

  function handleDrop(event) {
    event.preventDefault();
    const file = event.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
      imageFile = file;
      error = null;
      success = false;
      
      const reader = new FileReader();
      reader.onload = (e) => {
        imagePreview = e.target.result;
      };
      reader.readAsDataURL(file);
    } else {
      error = 'Please drop a valid image file';
    }
  }

  function handleDragOver(event) {
    event.preventDefault();
  }

  async function extractText() {
    if (!imageFile) {
      error = 'Please select an image first';
      return;
    }

    isProcessing = true;
    error = null;
    success = false;
    extractedText = '';

    try {
      // Create FormData for file upload
      const formData = new FormData();
      formData.append('file', imageFile);

      // Call OCR API endpoint
      const response = await fetch('/api/ocr/extract', {
        method: 'POST',
        body: formData,
        credentials: 'include'
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'OCR extraction failed');
      }

      const result = await response.json();
      
      if (!result.success) {
        throw new Error(result.error || 'OCR extraction failed');
      }
      
      // Use ocr_text from backend response
      extractedText = result.ocr_text || result.description || '';
      
      if (extractedText) {
        success = true;
      } else {
        error = 'No text found in the image';
      }
    } catch (err) {
      error = err.message || 'Failed to extract text from image';
      console.error('OCR error:', err);
    } finally {
      isProcessing = false;
    }
  }

  function copyToClipboard() {
    navigator.clipboard.writeText(extractedText);
    // Show a brief success message
    const btn = event.target.closest('button');
    const originalText = btn.innerHTML;
    btn.innerHTML = '<svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"/></svg> Copied!';
    setTimeout(() => {
      btn.innerHTML = originalText;
    }, 2000);
  }

  function downloadText() {
    const blob = new Blob([extractedText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'extracted-text.txt';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  function clearAll() {
    imageFile = null;
    imagePreview = null;
    extractedText = '';
    error = null;
    success = false;
  }
</script>

<svelte:head>
  <title>OCR Text Extractor - AI MCP Toolkit</title>
  <meta name="description" content="Extract text from images using advanced Optical Character Recognition" />
</svelte:head>

<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
  <!-- Header -->
  <div class="mb-8">
    <div class="flex items-center gap-3 mb-4">
      <div class="w-12 h-12 bg-gradient-to-br from-orange-500 to-orange-600 rounded-xl flex items-center justify-center">
        <ScanText size={24} class="text-white" />
      </div>
      <div>
        <h1 class="text-3xl font-bold text-gray-900 dark:text-white">
          OCR Text Extractor
        </h1>
        <p class="text-gray-600 dark:text-gray-400">
          Extract text from images using Tesseract OCR
        </p>
      </div>
    </div>
    
    <!-- Features -->
    <div class="flex flex-wrap gap-2">
      <span class="badge badge-primary text-xs px-3 py-1">Multi-language Support</span>
      <span class="badge badge-success text-xs px-3 py-1">High Accuracy</span>
      <span class="badge badge-info text-xs px-3 py-1">Fast Processing</span>
      <span class="badge badge-secondary text-xs px-3 py-1">Layout Preservation</span>
    </div>
  </div>

  <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
    <!-- Left Column - Input -->
    <div class="space-y-6">
      <!-- Upload Area -->
      <div class="card">
        <div class="card-header px-6 py-4">
          <h2 class="card-title flex items-center gap-2 text-gray-900 dark:text-white">
            <Upload class="w-5 h-5" />
            Upload Image
          </h2>
        </div>
        <div class="p-6">
          {#if !imagePreview}
            <div
              class="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-12 text-center hover:border-primary-500 dark:hover:border-primary-400 transition-colors cursor-pointer"
              on:drop={handleDrop}
              on:dragover={handleDragOver}
              on:click={() => document.getElementById('file-input').click()}
            >
              <ImageIcon size={48} class="mx-auto text-gray-400 mb-4" />
              <p class="text-lg font-medium text-gray-900 dark:text-white mb-2">
                Drop an image here or click to browse
              </p>
              <p class="text-sm text-gray-500 dark:text-gray-400">
                Supports PNG, JPEG, GIF, BMP, TIFF
              </p>
            </div>
            <input
              id="file-input"
              type="file"
              accept="image/*"
              class="hidden"
              on:change={handleFileSelect}
            />
          {:else}
            <div class="space-y-4">
              <img
                src={imagePreview}
                alt="Preview"
                class="w-full rounded-lg border border-gray-200 dark:border-gray-700"
              />
              <div class="flex gap-3">
                <button
                  class="btn btn-secondary flex-1 flex items-center justify-center"
                  on:click={() => document.getElementById('file-input').click()}
                >
                  <Upload class="w-4 h-4 mr-2" />
                  Change Image
                </button>
                <button
                  class="btn btn-secondary flex items-center justify-center"
                  on:click={clearAll}
                >
                  <X class="w-4 h-4 mr-2" />
                  Clear
                </button>
              </div>
              <input
                id="file-input"
                type="file"
                accept="image/*"
                class="hidden"
                on:change={handleFileSelect}
              />
            </div>
          {/if}
        </div>
      </div>

      <!-- Extract Button -->
      {#if imageFile}
        <button
          class="btn btn-primary w-full text-lg py-4 flex items-center justify-center"
          on:click={extractText}
          disabled={isProcessing}
        >
          {#if isProcessing}
            <Loader class="w-5 h-5 mr-2 animate-spin" />
            Extracting Text...
          {:else}
            <ScanText class="w-5 h-5 mr-2" />
            Extract Text from Image
          {/if}
        </button>
      {/if}

      <!-- Messages -->
      {#if error}
        <div class="alert alert-error flex items-center gap-3 text-gray-900 dark:text-white">
          <AlertCircle class="w-5 h-5" />
          <span>{error}</span>
        </div>
      {/if}

      {#if success}
        <div class="alert alert-success flex items-center gap-3 text-gray-900 dark:text-white">
          <CheckCircle class="w-5 h-5" />
          <span>Text extracted successfully!</span>
        </div>
      {/if}
    </div>

    <!-- Right Column - Output -->
    <div class="card">
      <div class="card-header px-6 py-4">
        <h2 class="card-title text-gray-900 dark:text-white">Extracted Text</h2>
        {#if extractedText}
          <div class="flex gap-2">
            <button
              class="btn btn-sm btn-secondary flex items-center justify-center text-gray-900 dark:text-white"
              on:click={copyToClipboard}
              title="Copy to clipboard"
            >
              <Copy class="w-4 h-4" />
            </button>
            <button
              class="btn btn-sm btn-secondary flex items-center justify-center text-gray-900 dark:text-white"
              on:click={downloadText}
              title="Download as text file"
            >
              <Download class="w-4 h-4" />
            </button>
          </div>
        {/if}
      </div>
      <div class="p-6">
        {#if extractedText}
          <textarea
            class="textarea-field w-full"
            rows="20"
            bind:value={extractedText}
            placeholder="Extracted text will appear here..."
          />
          <div class="mt-4 text-sm text-gray-500 dark:text-gray-400">
            {extractedText.length} characters, {extractedText.split(/\s+/).filter(w => w).length} words
          </div>
        {:else}
          <div class="text-center py-12 text-gray-400">
            <ScanText size={48} class="mx-auto mb-4 opacity-50" />
            <p>No text extracted yet</p>
            <p class="text-sm mt-2">Upload an image and click "Extract Text" to begin</p>
          </div>
        {/if}
      </div>
    </div>
  </div>

  <!-- How it Works -->
  <div class="card mt-8">
    <div class="card-header px-6 py-4">
      <h2 class="card-title text-gray-900 dark:text-white">How It Works</h2>
    </div>
    <div class="p-6">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div class="text-center">
          <div class="w-12 h-12 bg-orange-100 dark:bg-orange-900/30 rounded-lg flex items-center justify-center mx-auto mb-3">
            <Upload class="w-6 h-6 text-orange-600 dark:text-orange-400" />
          </div>
          <h3 class="font-semibold text-gray-900 dark:text-white mb-2">1. Upload Image</h3>
          <p class="text-sm text-gray-600 dark:text-gray-400">
            Select or drag & drop an image containing text
          </p>
        </div>
        <div class="text-center">
          <div class="w-12 h-12 bg-orange-100 dark:bg-orange-900/30 rounded-lg flex items-center justify-center mx-auto mb-3">
            <ScanText class="w-6 h-6 text-orange-600 dark:text-orange-400" />
          </div>
          <h3 class="font-semibold text-gray-900 dark:text-white mb-2">2. Extract Text</h3>
          <p class="text-sm text-gray-600 dark:text-gray-400">
            Tesseract OCR analyzes and extracts all readable text
          </p>
        </div>
        <div class="text-center">
          <div class="w-12 h-12 bg-orange-100 dark:bg-orange-900/30 rounded-lg flex items-center justify-center mx-auto mb-3">
            <Copy class="w-6 h-6 text-orange-600 dark:text-orange-400" />
          </div>
          <h3 class="font-semibold text-gray-900 dark:text-white mb-2">3. Copy or Download</h3>
          <p class="text-sm text-gray-600 dark:text-gray-400">
            Copy to clipboard or download as a text file
          </p>
        </div>
      </div>
    </div>
  </div>
</div>
