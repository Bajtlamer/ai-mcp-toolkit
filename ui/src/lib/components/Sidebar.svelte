<script>
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import { createEventDispatcher } from 'svelte';
  import { 
    Home, 
    Bot, 
    MessageSquare, 
    Settings, 
    Info, 
    Sparkles,
    FileText,
    Languages,
    Heart,
    Shield,
    Type,
    Zap,
    BarChart3,
    X,
    Cpu,
    Activity,
    Database,
    Search
  } from 'lucide-svelte';
  
  const dispatch = createEventDispatcher();
  
  export let open = false;
  
  let aiAgentsExpanded = false;
  
  // Get normalized current path
  $: normalizedPath = currentPath.endsWith('/') && currentPath !== '/' 
    ? currentPath.slice(0, -1) 
    : currentPath;
  
  // Reactive statements to handle menu state
  $: {
    // Update menu expansion state whenever the path changes
    aiAgentsExpanded = normalizedPath.startsWith('/agents');
  }
  
  const navigation = [
    { name: 'Dashboard', href: '/', icon: Home },
    { name: 'GPU Monitor', href: '/gpu', icon: Cpu },
    { name: 'AI Chat', href: '/chat', icon: MessageSquare },
    { name: 'Semantic Search', href: '/search', icon: Search },
    { name: 'Resources', href: '/resources', icon: Database },
    {
      name: 'AI Agents',
      href: '/agents',
      icon: Bot,
      children: [
        { name: 'Text Cleaner', href: '/agents/text-cleaner', icon: Sparkles },
        { name: 'Text Analyzer', href: '/agents/text-analyzer', icon: BarChart3 },
        { name: 'Grammar Checker', href: '/agents/grammar-checker', icon: FileText },
        { name: 'Text Summarizer', href: '/agents/text-summarizer', icon: Zap },
        { name: 'Language Detector', href: '/agents/language-detector', icon: Languages },
        { name: 'Sentiment Analyzer', href: '/agents/sentiment-analyzer', icon: Heart },
        { name: 'Text Anonymizer', href: '/agents/text-anonymizer', icon: Shield },
        { name: 'Diacritic Remover', href: '/agents/diacritic-remover', icon: Type },
        { name: 'PDF Text Extractor', href: '/agents/pdf-extractor', icon: FileText }
      ]
    }
  ];
  
  const bottomNavigation = [
    { name: 'Settings', href: '/settings', icon: Settings },
    { name: 'About', href: '/about', icon: Info }
  ];
  
  function closeSidebar() {
    dispatch('close');
  }
  
  $: currentPath = $page.url.pathname;
  
  // Strict active match for top-level nav items.
  // - For '/', only '/' is active.
  // - For other top-level hrefs, active only if exactly equal.
  $: isActive = (href) => {
    // Normalize the href for comparison
    const normalizedHref = href.endsWith('/') && href !== '/' ? href.slice(0, -1) : href;
    if (normalizedHref === '/') {
      return normalizedPath === '/';
    }
    return normalizedPath === normalizedHref;
  };
  
  // Children are active if any child path matches exactly or is a descendant.
  $: isChildActive = (children) => {
    return children?.some((child) => {
      const normalizedChildHref = child.href.endsWith('/') ? child.href.slice(0, -1) : child.href;
      return normalizedPath === normalizedChildHref || 
             normalizedPath.startsWith(normalizedChildHref + '/');
    });
  };
  
  // Close sidebar on navigation (for mobile)
  function handleNavigation() {
    if (open) {
      setTimeout(() => {
        dispatch('close');
      }, 100);
    }
  }
  
  // Toggle function for AI Agents menu
  async function toggleAiAgents() {
    const target = normalizedPath.startsWith('/agents') ? '/' : '/agents';
    await goto(target, { keepfocus: true, noscroll: true });
    // Handle sidebar closing on mobile
    handleNavigation();
  }
</script>

<!-- Mobile overlay -->
{#if open}
  <div class="fixed inset-0 flex z-40 lg:hidden">
    <!-- svelte-ignore a11y-click-events-have-key-events -->
    <!-- svelte-ignore a11y-no-static-element-interactions -->
    <div class="fixed inset-0 bg-gray-600 bg-opacity-75" on:click={closeSidebar} role="button" tabindex="-1"></div>
  </div>
{/if}

<!-- Sidebar -->
<div class={`sidebar fixed inset-y-0 left-0 z-50 w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0 ${
  open ? 'translate-x-0' : '-translate-x-full'
}`}>
  <div class="flex flex-col h-full">
    <!-- Logo and close button -->
    <div class="flex items-center justify-between px-4 py-4 border-b border-gray-200 dark:border-gray-700 min-h-24">
      <div class="flex items-center space-x-2">
        <div class="w-8 h-8 bg-gradient-to-br from-primary-500 to-primary-600 rounded-lg flex items-center justify-center">
          <Bot size={18} class="text-white" />
        </div>
        <div>
          <h1 class="text-lg font-bold text-gray-900 dark:text-white">AI MCP</h1>
          <p class="text-xs text-gray-500 dark:text-gray-400">Toolkit</p>
        </div>
      </div>
      
      <!-- Mobile close button -->
      <button
        on:click={closeSidebar}
        class="lg:hidden p-1 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700"
        aria-label="Close sidebar"
      >
        <X size={20} />
      </button>
    </div>
    
    <!-- Navigation -->
    <nav class="flex-1 px-2 py-4 space-y-1 overflow-y-auto scrollbar-thin">
      {#each navigation as item}
        <div>
          {#if item.children}
            <!-- Parent item with children - clickable to expand/collapse -->
            <button
              on:click={toggleAiAgents}
              class={`group flex items-center justify-between w-full px-2 py-2 text-sm font-medium rounded-md transition-colors ${
                isActive(item.href) || isChildActive(item.children)
                  ? 'bg-primary-50 text-primary-700 dark:bg-primary-900 dark:text-primary-200'
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900 dark:text-gray-300 dark:hover:bg-gray-700 dark:hover:text-white'
              }`}
            >
              <div class="flex items-center">
                <svelte:component 
                  this={item.icon} 
                  size={18} 
                  class={`mr-3 flex-shrink-0 ${
                    isActive(item.href) || isChildActive(item.children)
                      ? 'text-primary-500'
                      : 'text-gray-400 group-hover:text-gray-500 dark:group-hover:text-gray-300'
                  }`}
                />
                {item.name}
              </div>
              <!-- Expand/Collapse indicator -->
              <svg 
                class={`w-4 h-4 transition-transform duration-200 ${
                  aiAgentsExpanded ? 'rotate-90' : ''
                } ${
                  isActive(item.href) || isChildActive(item.children)
                    ? 'text-primary-500'
                    : 'text-gray-400 group-hover:text-gray-500 dark:group-hover:text-gray-300'
                }`}
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
              </svg>
            </button>
          {:else}
            <!-- Regular navigation item without children -->
            <a
              href={item.href}
              on:click|preventDefault={() => { goto(item.href, { keepfocus: true, noscroll: true }); handleNavigation(); }}
              class={`group flex items-center px-2 py-2 text-sm font-medium rounded-md transition-colors ${
                isActive(item.href)
                  ? 'bg-primary-50 text-primary-700 dark:bg-primary-900 dark:text-primary-200'
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900 dark:text-gray-300 dark:hover:bg-gray-700 dark:hover:text-white'
              }`}
            >
              <svelte:component 
                this={item.icon} 
                size={18} 
                class={`mr-3 flex-shrink-0 ${
                  isActive(item.href)
                    ? 'text-primary-500'
                    : 'text-gray-400 group-hover:text-gray-500 dark:group-hover:text-gray-300'
                }`}
              />
              {item.name}
            </a>
          {/if}
          
          {#if item.children && currentPath.startsWith('/agents')}
            <div class="ml-6 mt-1 space-y-1">
              {#each item.children as child}
                <a
                  href={child.href}
                  on:click|preventDefault={() => { goto(child.href, { keepfocus: true, noscroll: true }); handleNavigation(); }}
                  class={`group flex items-center px-2 py-1.5 text-sm rounded-md transition-colors ${
                    normalizedPath === (child.href.endsWith('/') ? child.href.slice(0, -1) : child.href) || 
                    normalizedPath.startsWith((child.href.endsWith('/') ? child.href.slice(0, -1) : child.href) + '/')
                      ? 'bg-primary-100 text-primary-800 dark:bg-primary-800 dark:text-primary-200 font-medium'
                      : 'text-gray-500 hover:bg-gray-50 hover:text-gray-700 dark:text-gray-400 dark:hover:bg-gray-700 dark:hover:text-gray-300'
                  }`}
                >
                  <svelte:component 
                    this={child.icon} 
                    size={16} 
                    class={`mr-2 flex-shrink-0 ${
                      currentPath === child.href
                        ? 'text-primary-600 dark:text-primary-400'
                        : 'text-gray-400 group-hover:text-gray-500 dark:group-hover:text-gray-400'
                    }`} 
                  />
                  {child.name}
                </a>
              {/each}
            </div>
          {/if}
        </div>
      {/each}
    </nav>
    
    <!-- Bottom navigation -->
    <div class="px-2 py-4 border-t border-gray-200 dark:border-gray-700 space-y-1">
      {#each bottomNavigation as item}
        <a
          href={item.href}
          on:click|preventDefault={() => { goto(item.href, { keepfocus: true, noscroll: true }); handleNavigation(); }}
          class={`group flex items-center px-2 py-2 text-sm font-medium rounded-md transition-colors ${
            isActive(item.href)
              ? 'bg-primary-50 text-primary-700 dark:bg-primary-900 dark:text-primary-200'
              : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900 dark:text-gray-300 dark:hover:bg-gray-700 dark:hover:text-white'
          }`}
        >
          <svelte:component 
            this={item.icon} 
            size={18} 
            class={`mr-3 flex-shrink-0 ${
              isActive(item.href)
                ? 'text-primary-500'
                : 'text-gray-400 group-hover:text-gray-500 dark:group-hover:text-gray-300'
            }`} 
          />
          {item.name}
        </a>
      {/each}
    </div>
    
    <!-- Version info -->
    <div class="px-4 py-2 border-t border-gray-200 dark:border-gray-700">
      <p class="text-xs text-gray-500 dark:text-gray-400">
        AI MCP Toolkit v0.1.54-beta
      </p>
    </div>
  </div>
</div>
