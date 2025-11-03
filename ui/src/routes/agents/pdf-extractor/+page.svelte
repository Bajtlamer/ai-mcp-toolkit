<script>
import { FileText, Play, Copy, Download, Database, Upload, X } from 'lucide-svelte';
  import ResourceSelector from '$lib/components/ResourceSelector.svelte';
  import * as resourceAPI from '$lib/services/resources';

  let inputMode = 'file'; // 'file' or 'resource'
  let selectedFile = null;
  let selectedResourceUri = '';
  let outputText = '';
  let isProcessing = false;
  let error = null;
  let includeMetadata = true;
  let pageRange = 'all';
  let fileInputElement;
  let isDragging = false;

  async function extractPdfText() {
    if (inputMode === 'file' && !selectedFile) return;
    if (inputMode === 'resource' && !selectedResourceUri) return;

    isProcessing = true;
    error = null;

    try {
      let pdfContent;

      if (inputMode === 'file') {
        // Read file and convert to base64
        const arrayBuffer = await selectedFile.arrayBuffer();
        const bytes = new Uint8Array(arrayBuffer);
        const binaryString = bytes.reduce((acc, byte) => acc + String.fromCharCode(byte), '');
        pdfContent = btoa(binaryString);
      } else {
        // Fetch PDF resource through backend API which extracts text automatically
        const response = await fetch(`/api/resources/${encodeURIComponent(selectedResourceUri)}`);
        
        if (!response.ok) {
          error = `Failed to fetch resource: ${response.statusText}`;
          isProcessing = false;
          return;
        }
        
        const resourceData = await response.json();
        console.log('Resource API response:', resourceData); // Debug
        
        // Backend returns flat resource object with content field
        if (resourceData.content) {
          const content = resourceData.content;
          
          // Check if content is already extracted text or needs to be fetched
          if (content.startsWith('[PDF file:') || content.startsWith('[Error extracting') || content.startsWith('[No text content')) {
            // This is a status message - need to fetch PDF file using file_id
            if (resourceData.file_id) {
              // Download the actual PDF file
              const downloadResponse = await fetch(`/api/resources/download/${resourceData.file_id}`);
              if (!downloadResponse.ok) {
                error = `Failed to download PDF file: ${downloadResponse.statusText}`;
                isProcessing = false;
                return;
              }
              
              // Convert to base64
              const arrayBuffer = await downloadResponse.arrayBuffer();
              const bytes = new Uint8Array(arrayBuffer);
              const binaryString = bytes.reduce((acc, byte) => acc + String.fromCharCode(byte), '');
              pdfContent = btoa(binaryString);
            } else {
              error = 'PDF file not available for this resource';
              isProcessing = false;
              return;
            }
          } else if (content.includes('--- Page')) {
            // Backend already extracted the text! Use it directly
            outputText = content;
            isProcessing = false;
            return;
          } else {
            // Assume it's base64 PDF content
            pdfContent = content;
          }
        } else if (resourceData.file_id) {
          // No content field - try to download the file directly
          const downloadResponse = await fetch(`/api/resources/download/${resourceData.file_id}`);
          if (!downloadResponse.ok) {
            error = `Failed to download PDF file: ${downloadResponse.statusText}`;
            isProcessing = false;
            return;
          }
          
          // Convert to base64
          const arrayBuffer = await downloadResponse.arrayBuffer();
          const bytes = new Uint8Array(arrayBuffer);
          const binaryString = bytes.reduce((acc, byte) => acc + String.fromCharCode(byte), '');
          pdfContent = btoa(binaryString);
        } else {
          error = 'Resource does not contain PDF content or file reference';
          isProcessing = false;
          return;
        }
      }

      // Call the PDF extraction tool via server endpoint
      const response = await fetch('/api/tools/execute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: 'extract_pdf_text',
          arguments: {
            pdf_content: pdfContent,
            page_range: pageRange,
            include_metadata: includeMetadata
          }
        })
      });

      const result = await response.json();

      if (result.success) {
        outputText = result.result;
      } else {
        error = result.error || 'Failed to extract PDF text';
      }
    } catch (err) {
      error = `Failed to extract PDF text: ${err.message}`;
      console.error('Error:', err);
    } finally {
      isProcessing = false;
    }
  }

  function handleFileSelect(event) {
    const file = event.target.files?.[0];
    if (!file) return;

    if (file.type !== 'application/pdf') {
      error = 'Please select a PDF file';
      return;
    }

    selectedFile = file;
    error = null;
  }

  function copyToClipboard() {
    navigator.clipboard.writeText(outputText);
  }

  function downloadText() {
    const blob = new Blob([outputText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'extracted_text.txt';
    a.click();
    URL.revokeObjectURL(url);
  }

  function clearText() {
    outputText = '';
    error = null;
  }

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

  function handleDrop(event) {
    event.preventDefault();
    event.stopPropagation();
    isDragging = false;

    const files = event.dataTransfer?.files;
    if (files && files.length > 0) {
      const file = files[0];
      if (file.type !== 'application/pdf') {
        error = 'Please drop a PDF file';
        return;
      }
      selectedFile = file;
      error = null;
    }
  }
</script>

<svelte:head>
  <title>PDF Text Extractor - AI MCP Toolkit</title>
</svelte:head>

<div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
  <!-- Header -->
  <div class="mb-8">
    <div class="flex items-center space-x-3 mb-4">
      <div class="w-12 h-12 bg-gradient-to-br from-red-500 to-red-600 rounded-xl flex items-center justify-center">
        <FileText size={24} class="text-white" />
      </div>
      <div>
        <h1 class="text-3xl font-bold text-gray-900 dark:text-white">PDF Text Extractor</h1>
        <p class="text-gray-600 dark:text-gray-400">Extract raw text content from PDF documents</p>
      </div>
    </div>

    <!-- Info Card -->
    <div class="p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
      <h3 class="text-sm font-medium text-blue-900 dark:text-blue-100 mb-2">How it works</h3>
      <p class="text-sm text-blue-800 dark:text-blue-200">
        Upload a PDF file or select from your resources to extract all text content. The extracted text preserves page structure and can be copied or downloaded for further use.
      </p>
    </div>
  </div>

  <!-- Input/Output Interface -->
  <div class="grid grid-cols-1 lg:grid-cols-2 gap-6" style="height: 600px;">
    <!-- Input -->
    <div class="flex flex-col h-full">
      <!-- Input Mode Tabs -->
      <div class="border-b border-gray-200 dark:border-gray-700 mb-4">
        <nav class="-mb-px flex space-x-8">
          <button
            on:click={() => inputMode = 'file'}
            class="{inputMode === 'file' ? 'border-red-500 text-red-600 dark:text-red-400' : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'} whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm transition-colors"
          >
            <Upload size={14} class="inline mr-1" />
            Upload PDF
          </button>
          <button
            on:click={() => inputMode = 'resource'}
            class="{inputMode === 'resource' ? 'border-red-500 text-red-600 dark:text-red-400' : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'} whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm transition-colors"
          >
            <Database size={14} class="inline mr-1" />
            From Resource
          </button>
        </nav>
      </div>

      <!-- Input Header -->
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-medium text-gray-900 dark:text-white">
          {inputMode === 'file' ? 'Upload PDF File' : 'Select PDF Resource'}
        </h3>
        <span class="text-sm text-gray-500 dark:text-gray-400">
          {inputMode === 'file' ? (selectedFile ? `✓ ${selectedFile.name}` : 'No file selected') : (selectedResourceUri ? '✓ Resource selected' : 'Choose resource')}
        </span>
      </div>

      <!-- Input Content Area -->
      <div class="flex-1 mb-4">
        {#if inputMode === 'file'}
          <!-- File Upload Mode -->
          <div class="h-full flex flex-col space-y-4">
            <div 
              class="flex-1 flex justify-center items-center border-2 border-dashed {isDragging ? 'border-red-500 bg-red-50 dark:bg-red-900/20' : 'border-gray-300 dark:border-gray-600'} rounded-lg hover:border-red-500 dark:hover:border-red-400 transition-colors"
              on:dragenter={handleDragEnter}
              on:dragleave={handleDragLeave}
              on:dragover={handleDragOver}
              on:drop={handleDrop}
            >
              <div class="text-center p-6">
                <Upload class="mx-auto h-12 w-12 {isDragging ? 'text-red-500' : 'text-gray-400'} mb-3" />
                <label class="cursor-pointer">
                  <span class="text-sm font-medium text-red-600 hover:text-red-500">Upload a PDF file</span>
                  <input
                    type="file"
                    bind:this={fileInputElement}
                    on:change={handleFileSelect}
                    accept=".pdf,application/pdf"
                    class="sr-only"
                  />
                </label>
                <p class="text-xs text-gray-500 dark:text-gray-400 mt-2">
                  PDF files up to 10MB
                </p>
                {#if selectedFile}
                  <div class="mt-4 p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
                    <div class="flex items-center justify-center gap-2">
                      <FileText size={16} class="text-green-600 dark:text-green-400" />
                      <span class="text-sm text-green-900 dark:text-green-100 font-medium">{selectedFile.name}</span>
                      <span class="text-xs text-green-600 dark:text-green-400">({(selectedFile.size / 1024).toFixed(1)} KB)</span>
                    </div>
                  </div>
                {/if}
              </div>
            </div>
          </div>
        {:else if inputMode === 'resource'}
          <!-- Resource Selection Mode -->
          <ResourceSelector 
            bind:selectedResourceUri
            filterMimeTypes={['application/pdf']}
            label="Select a PDF resource"
            infoText="Select any PDF resource from your library"
          />
        {/if}
      </div>

      <!-- Options -->
      <div class="grid grid-cols-2 gap-4 mb-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Page Range
          </label>
          <select
            bind:value={pageRange}
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm"
          >
            <option value="all">All Pages</option>
            <option value="1">First Page Only</option>
            <option value="1-5">Pages 1-5</option>
            <option value="1-10">Pages 1-10</option>
          </select>
        </div>

        <div class="flex items-end">
          <label class="flex items-center space-x-2 cursor-pointer">
            <input
              type="checkbox"
              bind:checked={includeMetadata}
              class="w-4 h-4 text-red-600 border-gray-300 rounded focus:ring-red-500"
            />
            <span class="text-sm text-gray-700 dark:text-gray-300">Include metadata</span>
          </label>
        </div>
      </div>

      <button
        on:click={extractPdfText}
        disabled={(inputMode === 'file' && !selectedFile) || (inputMode === 'resource' && !selectedResourceUri) || isProcessing}
        class="w-full flex items-center justify-center px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-gray-400 text-white font-medium rounded-lg transition-colors"
      >
        {#if isProcessing}
          <div class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
          Extracting...
        {:else}
          <Play size={16} class="mr-2" />
          Extract Text
        {/if}
      </button>
    </div>

    <!-- Output -->
    <div class="flex flex-col h-full min-h-0">
      <!-- Output Header -->
      <div class="flex items-center justify-between mb-4 flex-shrink-0">
        <div>
          <h3 class="text-lg font-medium text-gray-900 dark:text-white">Extracted Text</h3>
          {#if outputText}
            <div class="text-sm text-gray-500 dark:text-gray-400 mt-1">
              {outputText.length} characters
            </div>
          {/if}
        </div>
        {#if outputText}
          <div class="flex space-x-2">
            <button
              on:click={clearText}
              class="flex items-center px-3 py-1 text-sm bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-md transition-colors"
            >
              <X size={14} class="mr-1" />
              Clear
            </button>
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

      <!-- Output Content Area -->
      {#if error}
        <div class="flex-1 min-h-0 w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-800">
          <div class="text-red-600 dark:text-red-400">
            <strong>Error:</strong> {error}
          </div>
        </div>
      {:else if outputText}
        <textarea
          bind:value={outputText}
          class="flex-1 min-h-0 w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white text-sm font-mono resize-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
          readonly
        ></textarea>
      {:else}
        <div class="flex-1 min-h-0 w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-800">
          <p class="text-gray-500 dark:text-gray-400 italic">
            Extracted text will appear here...
          </p>
        </div>
      {/if}
    </div>
  </div>

  <!-- Features -->
  <div class="mt-12">
    <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-6">Features</h2>
    <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
      <div class="p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
        <h3 class="font-medium text-gray-900 dark:text-white mb-2">Raw Text Extraction</h3>
        <p class="text-sm text-gray-600 dark:text-gray-400">
          Extract pure text content without any AI processing or summarization.
        </p>
      </div>
      <div class="p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
        <h3 class="font-medium text-gray-900 dark:text-white mb-2">Page Control</h3>
        <p class="text-sm text-gray-600 dark:text-gray-400">
          Extract all pages or specify a custom page range to target specific sections.
        </p>
      </div>
      <div class="p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
        <h3 class="font-medium text-gray-900 dark:text-white mb-2">Metadata Support</h3>
        <p class="text-sm text-gray-600 dark:text-gray-400">
          Optionally include PDF metadata like title, author, and page count.
        </p>
      </div>
      <div class="p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
        <h3 class="font-medium text-gray-900 dark:text-white mb-2">Resource Integration</h3>
        <p class="text-sm text-gray-600 dark:text-gray-400">
          Extract text from any PDF resource in your library instantly.
        </p>
      </div>
    </div>
  </div>
</div>
