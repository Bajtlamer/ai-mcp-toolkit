<script>
  import '../app.css';
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import { Toaster } from 'svelte-french-toast';
  
  import Sidebar from '$lib/components/Sidebar.svelte';
  import Header from '$lib/components/Header.svelte';
  import { auth } from '$lib/stores/auth';
  import { conversations } from '$lib/stores/conversations';
  
  let sidebarOpen = false;
  let isAuthPage = false;
  
  // Public routes that don't require authentication
  const publicRoutes = ['/login', '/register'];
  
  $: isAuthPage = publicRoutes.includes($page.url.pathname);
  
  function toggleSidebar() {
    sidebarOpen = !sidebarOpen;
  }
  
  function closeSidebar() {
    sidebarOpen = false;
  }
  
  onMount(async () => {
    // Initialize auth state
    const user = await auth.init();
    
    // Load conversations if authenticated
    if (user) {
      try {
        await conversations.loadConversations();
      } catch (error) {
        console.error('Failed to load conversations:', error);
      }
    }
    
    // Redirect to login if not authenticated and not on public route
    if (!user && !isAuthPage) {
      goto('/login');
    }
    
    // Close sidebar when clicking outside on mobile
    function handleClickOutside(event) {
      if (sidebarOpen && !event.target.closest('.sidebar') && !event.target.closest('.sidebar-toggle')) {
        closeSidebar();
      }
    }
    
    document.addEventListener('click', handleClickOutside);
    
    return () => {
      document.removeEventListener('click', handleClickOutside);
    };
  });
  
  // Watch for route changes and check auth
  $: if ($page.url && !$auth.user && !isAuthPage && !$auth.loading) {
    goto('/login');
  }
</script>

<svelte:head>
  <title>AI MCP Toolkit - Text Processing Made Easy</title>
</svelte:head>

{#if isAuthPage}
  <!-- Auth pages (login/register) - no sidebar/header -->
  <slot />
{:else if $auth.loading}
  <!-- Loading state -->
  <div class="h-full flex items-center justify-center bg-gray-50 dark:bg-gray-900">
    <div class="text-center">
      <svg class="animate-spin h-12 w-12 text-blue-600 mx-auto mb-4" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      <p class="text-gray-600 dark:text-gray-400">Loading...</p>
    </div>
  </div>
{:else if $auth.user}
  <!-- Authenticated layout with sidebar/header -->
  <div class="h-full flex">
    <!-- Sidebar -->
    <Sidebar bind:open={sidebarOpen} on:close={closeSidebar} />
    
    <!-- Main content area -->
    <div class="flex-1 flex flex-col overflow-hidden">
      <!-- Header -->
      <Header on:toggle-sidebar={toggleSidebar} />
      
      <!-- Page content -->
      <main class="flex-1 overflow-y-auto bg-gray-50 dark:bg-gray-900">
        <div class="container mx-auto px-4 py-6 max-w-full">
          <slot />
        </div>
      </main>
    </div>
  </div>
{/if}

<!-- Toast notifications -->
<Toaster />

<style>
  :global(html) {
    height: 100%;
  }
  
  :global(body) {
    height: 100%;
    margin: 0;
  }
  
  :global(#svelte) {
    height: 100%;
  }
</style>
