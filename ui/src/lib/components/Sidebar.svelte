<script>
  import { page } from '$app/stores';
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
    X
  } from 'lucide-svelte';
  
  const dispatch = createEventDispatcher();
  
  export let open = false;
  
  const navigation = [
    { name: 'Dashboard', href: '/', icon: Home },
    { name: 'AI Chat', href: '/chat', icon: MessageSquare },
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
        { name: 'Diacritic Remover', href: '/agents/diacritic-remover', icon: Type }
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
  
  function isActive(href) {
    if (href === '/') {
      return $page.url.pathname === '/';
    }
    return $page.url.pathname.startsWith(href);
  }
  
  function isChildActive(children) {
    return children?.some(child => isActive(child.href));
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
    <div class="flex items-center justify-between px-4 py-4 border-b border-gray-200 dark:border-gray-700">
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
          <a
            href={item.href}
            class={`group flex items-center px-2 py-2 text-sm font-medium rounded-md transition-colors ${
              isActive(item.href) || isChildActive(item.children)
                ? 'bg-primary-50 text-primary-700 dark:bg-primary-900 dark:text-primary-200'
                : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900 dark:text-gray-300 dark:hover:bg-gray-700 dark:hover:text-white'
            }`}
          >
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
          </a>
          
          {#if item.children && (isActive(item.href) || isChildActive(item.children))}
            <div class="ml-6 mt-1 space-y-1">
              {#each item.children as child}
                <a
                  href={child.href}
                  class={`group flex items-center px-2 py-1.5 text-sm rounded-md transition-colors ${
                    isActive(child.href)
                      ? 'bg-primary-100 text-primary-800 dark:bg-primary-800 dark:text-primary-200'
                      : 'text-gray-500 hover:bg-gray-50 hover:text-gray-700 dark:text-gray-400 dark:hover:bg-gray-700 dark:hover:text-gray-300'
                  }`}
                >
                  <svelte:component 
                    this={child.icon} 
                    size={16} 
                    class={`mr-2 flex-shrink-0 ${
                      isActive(child.href)
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
        AI MCP Toolkit v0.1.0
      </p>
    </div>
  </div>
</div>
