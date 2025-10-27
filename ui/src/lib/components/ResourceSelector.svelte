<script>
  import { onMount } from 'svelte';
  import { Database } from 'lucide-svelte';
  import * as resourceAPI from '$lib/services/resources';

  export let selectedResourceUri = '';
  export let filterMimeTypes = []; // Optional: filter resources by MIME types (e.g., ['application/pdf', 'text/plain'])
  export let label = 'Select a resource';
  export let infoText = 'Select any resource from your library';

  let resources = [];
  let loadingResources = false;
  let filteredResources = [];

  onMount(async () => {
    await loadResources();
  });

  async function loadResources() {
    try {
      loadingResources = true;
      const allResources = await resourceAPI.listResources();
      
      // Filter by MIME types if specified
      if (filterMimeTypes && filterMimeTypes.length > 0) {
        filteredResources = allResources.filter(r => filterMimeTypes.includes(r.mimeType));
      } else {
        filteredResources = allResources;
      }
      
      resources = filteredResources;
    } catch (err) {
      console.error('Error loading resources:', err);
    } finally {
      loadingResources = false;
    }
  }
</script>

<div class="h-full flex flex-col space-y-4">
  <select
    bind:value={selectedResourceUri}
    disabled={loadingResources}
    class="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-white disabled:opacity-50"
  >
    <option value="">-- {loadingResources ? 'Loading resources...' : label} --</option>
    {#each resources as resource}
      <option value={resource.uri}>
        {resource.name} ({resource.mimeType})
      </option>
    {/each}
  </select>

  <div class="flex-1 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
    <div class="flex items-start space-x-3">
      <div class="flex-shrink-0">
        <Database class="w-5 h-5 text-green-600 dark:text-green-400 mt-0.5" />
      </div>
      <div class="text-sm text-green-700 dark:text-green-300">
        <p class="font-medium">Process from Resources:</p>
        <ul class="mt-1 list-disc list-inside space-y-1">
          <li>{infoText}</li>
          <li>Content is automatically fetched (text files, PDFs, URLs)</li>
          <li>Supports all resource types in your library</li>
          <li>{resources.length} resource{resources.length !== 1 ? 's' : ''} available</li>
        </ul>
      </div>
    </div>
  </div>
</div>
