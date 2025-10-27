<script>
  import { page } from '$app/stores';
  import { Home, ArrowLeft, Search } from 'lucide-svelte';
  
  $: status = $page.status;
  $: message = $page.error?.message || 'An unexpected error occurred';
</script>

<svelte:head>
  <title>{status} - AI MCP Toolkit</title>
</svelte:head>

<div class="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center px-4">
  <div class="max-w-2xl w-full text-center">
    <!-- Error Code -->
    <div class="mb-8">
      <h1 class="text-9xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
        {status}
      </h1>
    </div>
    
    <!-- Error Message -->
    <div class="mb-12">
      <h2 class="text-3xl font-bold text-gray-900 dark:text-white mb-4">
        {#if status === 404}
          Page Not Found
        {:else if status === 403}
          Access Denied
        {:else if status === 500}
          Server Error
        {:else}
          Something Went Wrong
        {/if}
      </h2>
      <p class="text-lg text-gray-600 dark:text-gray-400 max-w-lg mx-auto">
        {#if status === 404}
          The page you're looking for doesn't exist or has been moved.
        {:else if status === 403}
          You don't have permission to access this resource.
        {:else if status === 500}
          Our servers encountered an error. Please try again later.
        {:else}
          {message}
        {/if}
      </p>
    </div>
    
    <!-- Illustration -->
    <div class="mb-12">
      <div class="inline-flex items-center justify-center w-32 h-32 bg-gradient-to-br from-blue-100 to-purple-100 dark:from-blue-900/20 dark:to-purple-900/20 rounded-full">
        <Search class="w-16 h-16 text-gray-400 dark:text-gray-600" />
      </div>
    </div>
    
    <!-- Action Buttons -->
    <div class="flex flex-col sm:flex-row gap-4 justify-center items-center">
      <a
        href="/"
        class="inline-flex items-center space-x-2 px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl hover:from-blue-700 hover:to-purple-700 transition-all shadow-lg hover:shadow-xl font-medium"
      >
        <Home class="w-5 h-5" />
        <span>Go Home</span>
      </a>
      
      <button
        on:click={() => window.history.back()}
        class="inline-flex items-center space-x-2 px-6 py-3 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-700 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors font-medium"
      >
        <ArrowLeft class="w-5 h-5" />
        <span>Go Back</span>
      </button>
    </div>
    
    <!-- Help Text -->
    <div class="mt-12 text-sm text-gray-500 dark:text-gray-400">
      <p>
        Need help? Check out our <a href="/about" class="text-blue-600 dark:text-blue-400 hover:underline">About page</a>
        or return to the <a href="/" class="text-blue-600 dark:text-blue-400 hover:underline">homepage</a>.
      </p>
    </div>
  </div>
</div>
