<script>
  import '../app.css';
  import { onMount } from 'svelte';
  import { browser } from '$app/environment';
  import { Toaster } from 'svelte-french-toast';
  
  import Sidebar from '$lib/components/Sidebar.svelte';
  import Header from '$lib/components/Header.svelte';
  import { conversations } from '$lib/stores/conversations';
  
  // Get server-side user data from page data
  export let data;
  
  $: user = data.user;
  $: isAuthPage = data.isPublicRoute;
  
  let sidebarOpen = false;
  let conversationsLoaded = false;
  
  // Reactively load conversations when user changes (client-side only)
  $: if (browser && user && !conversationsLoaded) {
    conversations.loadConversations()
      .then(() => {
        conversationsLoaded = true;
      })
      .catch(error => {
        console.error('Failed to load conversations:', error);
      });
  }
  
  // Clear conversations when user logs out (client-side only)
  $: if (browser && !user && conversationsLoaded) {
    conversations.set([]);
    conversationsLoaded = false;
  }
  
  function toggleSidebar() {
    sidebarOpen = !sidebarOpen;
  }
  
  function closeSidebar() {
    sidebarOpen = false;
  }
  
  onMount(() => {
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
</script>

<svelte:head>
  <title>AI MCP Toolkit - Text Processing Made Easy</title>
</svelte:head>

{#if isAuthPage}
  <!-- Auth pages (login/register) - no sidebar/header -->
  <slot />
{:else}
  <!-- Authenticated layout with sidebar/header -->
  <div class="h-full flex">
    <!-- Sidebar -->
    <Sidebar bind:open={sidebarOpen} on:close={closeSidebar} />
    
    <!-- Main content area -->
    <div class="flex-1 flex flex-col overflow-hidden">
      <!-- Header -->
      <Header {user} on:toggle-sidebar={toggleSidebar} />
      
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
