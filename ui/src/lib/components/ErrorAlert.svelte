<script>
  import { AlertCircle, X } from 'lucide-svelte';
  
  export let message = 'An error occurred';
  export let onClose = null;
  export let dismissable = true;
</script>

<div class="rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 p-4" role="alert">
  <div class="flex">
    <div class="flex-shrink-0">
      <AlertCircle class="h-5 w-5 text-red-400 dark:text-red-500" />
    </div>
    <div class="ml-3 flex-1">
      <p class="text-sm text-red-800 dark:text-red-300">
        {message}
      </p>
    </div>
    {#if dismissable && onClose}
      <div class="ml-auto pl-3">
        <button
          type="button"
          on:click={onClose}
          class="inline-flex rounded-md bg-red-50 dark:bg-red-900/20 p-1.5 text-red-500 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-900/40 focus:outline-none focus:ring-2 focus:ring-red-600 focus:ring-offset-2 transition-colors"
        >
          <span class="sr-only">Dismiss</span>
          <X class="h-4 w-4" />
        </button>
      </div>
    {/if}
  </div>
</div>
