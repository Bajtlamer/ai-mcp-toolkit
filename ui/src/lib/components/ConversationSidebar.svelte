<script>
  import { 
    Plus, 
    MessageSquare, 
    Trash2, 
    Edit3, 
    Check, 
    X, 
    Download, 
    Upload,
    Search,
    Calendar,
    MoreVertical
  } from 'lucide-svelte';
  import { conversations, currentConversationId } from '$lib/stores/conversations.js';
  import { createEventDispatcher, onMount } from 'svelte';
  
  const dispatch = createEventDispatcher();
  
  let searchTerm = '';
  let editingConversationId = null;
  let editingTitle = '';
  let showDeleteConfirm = null;
  let fileInput;
  
  // Filter conversations based on search term
  $: filteredConversations = $conversations.filter(conv => 
    conv.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    conv.messages.some(msg => 
      msg.content.toLowerCase().includes(searchTerm.toLowerCase())
    )
  );

  // Group conversations by date
  $: groupedConversations = groupConversationsByDate(filteredConversations);
  
  function groupConversationsByDate(convs) {
    const groups = {};
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const yesterday = new Date(today.getTime() - 24 * 60 * 60 * 1000);
    const lastWeek = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);
    
    convs.forEach(conv => {
      const convDate = new Date(conv.updatedAt);
      const convDateOnly = new Date(convDate.getFullYear(), convDate.getMonth(), convDate.getDate());
      
      let groupKey;
      if (convDateOnly.getTime() === today.getTime()) {
        groupKey = 'Today';
      } else if (convDateOnly.getTime() === yesterday.getTime()) {
        groupKey = 'Yesterday';
      } else if (convDate > lastWeek) {
        groupKey = 'This Week';
      } else {
        groupKey = convDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
      }
      
      if (!groups[groupKey]) {
        groups[groupKey] = [];
      }
      groups[groupKey].push(conv);
    });
    
    // Sort conversations within each group by updatedAt (newest first)
    Object.keys(groups).forEach(key => {
      groups[key].sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt));
    });
    
    return groups;
  }

  function createNewConversation() {
    const newId = conversations.createConversation();
    currentConversationId.set(newId);
    dispatch('conversationChanged');
  }

  function selectConversation(conversationId) {
    currentConversationId.set(conversationId);
    dispatch('conversationChanged');
  }

  function startEditing(conversation) {
    editingConversationId = conversation.id;
    editingTitle = conversation.title;
  }

  function saveTitle() {
    if (editingTitle.trim()) {
      conversations.updateTitle(editingConversationId, editingTitle.trim());
    }
    editingConversationId = null;
    editingTitle = '';
  }

  function cancelEditing() {
    editingConversationId = null;
    editingTitle = '';
  }

  function deleteConversation(conversationId) {
    conversations.deleteConversation(conversationId);
    showDeleteConfirm = null;
    
    // If we deleted the current conversation, select the first available one
    if ($currentConversationId === conversationId) {
      const remaining = $conversations.filter(c => c.id !== conversationId);
      if (remaining.length > 0) {
        currentConversationId.set(remaining[0].id);
      }
      dispatch('conversationChanged');
    }
  }

  function exportConversations() {
    const data = conversations.exportConversations();
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ai-conversations-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  function importConversations() {
    fileInput.click();
  }

  function handleFileImport(event) {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        const success = conversations.importConversations(e.target.result);
        if (success) {
          dispatch('showNotification', { type: 'success', message: 'Conversations imported successfully!' });
        } else {
          dispatch('showNotification', { type: 'error', message: 'Failed to import conversations. Please check the file format.' });
        }
      };
      reader.readAsText(file);
    }
    // Reset file input
    event.target.value = '';
  }

  function handleKeyDown(event) {
    if (event.key === 'Enter') {
      saveTitle();
    } else if (event.key === 'Escape') {
      cancelEditing();
    }
  }

  function formatRelativeTime(date) {
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  }
</script>

<div class="h-full flex flex-col bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700">
  <!-- Header -->
  <div class="flex-shrink-0 p-4 border-b border-gray-200 dark:border-gray-700">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Conversations</h2>
      <button
        on:click={createNewConversation}
        class="flex items-center justify-center w-9 h-9 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors shadow-sm hover:shadow-md"
        title="New conversation"
      >
        <Plus size={18} />
      </button>
    </div>
    
    <!-- Search -->
    <div class="relative">
      <Search size={16} class="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
      <input
        bind:value={searchTerm}
        type="text"
        placeholder="Search conversations..."
        class="w-full pl-10 pr-4 py-2.5 border border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 text-sm"
      />
    </div>
  </div>

  <!-- Conversations List -->
  <div class="flex-1 overflow-y-auto">
    {#if Object.keys(groupedConversations).length === 0}
      <div class="p-4 text-center">
        <div class="text-gray-400 dark:text-gray-500 mb-2">
          <MessageSquare size={32} class="mx-auto mb-2 opacity-50" />
        </div>
        <p class="text-sm text-gray-500 dark:text-gray-400">
          {searchTerm ? 'No conversations found' : 'No conversations yet'}
        </p>
      </div>
    {:else}
      {#each Object.entries(groupedConversations) as [groupName, groupConversations]}
        <div class="px-4 py-2">
          <div class="flex items-center text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">
            <Calendar size={12} class="mr-1" />
            {groupName}
          </div>
          
          {#each groupConversations as conversation (conversation.id)}
            <div 
              class="group relative mb-2 rounded-lg transition-all duration-200 {$currentConversationId === conversation.id 
                ? 'bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-700' 
                : 'hover:bg-gray-50 dark:hover:bg-gray-800 border border-transparent'}"
            >
              <button
                on:click={() => selectConversation(conversation.id)}
                class="w-full text-left p-3 rounded-lg transition-colors"
              >
                <div class="flex items-start justify-between">
                  <div class="flex-1 min-w-0">
                    {#if editingConversationId === conversation.id}
                      <div class="flex items-center space-x-2" on:click|stopPropagation>
                        <input
                          bind:value={editingTitle}
                          on:keydown={handleKeyDown}
                          class="flex-1 px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          placeholder="Conversation title"
                          autofocus
                        />
                        <button
                          on:click={saveTitle}
                          class="p-1 text-green-600 hover:text-green-700 dark:text-green-400 dark:hover:text-green-300"
                          title="Save"
                        >
                          <Check size={14} />
                        </button>
                        <button
                          on:click={cancelEditing}
                          class="p-1 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                          title="Cancel"
                        >
                          <X size={14} />
                        </button>
                      </div>
                    {:else}
                      <div class="flex items-center space-x-2">
                        <MessageSquare 
                          size={14} 
                          class="{$currentConversationId === conversation.id 
                            ? 'text-blue-600 dark:text-blue-400' 
                            : 'text-gray-400 dark:text-gray-500'}"
                        />
                        <h3 class="font-medium text-sm {$currentConversationId === conversation.id 
                          ? 'text-blue-900 dark:text-blue-100' 
                          : 'text-gray-900 dark:text-white'} truncate">
                          {conversation.title}
                        </h3>
                      </div>
                      
                      <div class="flex items-center justify-between mt-1">
                        <div class="flex items-center space-x-2 text-xs text-gray-500 dark:text-gray-400">
                          <span class="truncate">
                            {conversation.messages.length} message{conversation.messages.length !== 1 ? 's' : ''}
                          </span>
                          {#if conversation.averageThinkingTime && conversation.averageThinkingTime > 0}
                            <div class="flex items-center space-x-1 text-green-600 dark:text-green-400" title="Average AI thinking time">
                              <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <circle cx="12" cy="12" r="10"/>
                                <polyline points="12,6 12,12 16,14"/>
                              </svg>
                              <span>{conversation.averageThinkingTime}s</span>
                            </div>
                          {/if}
                        </div>
                        <span class="text-xs text-gray-400 dark:text-gray-500">
                          {formatRelativeTime(conversation.updatedAt)}
                        </span>
                      </div>
                    {/if}
                  </div>
                </div>
              </button>

              <!-- Conversation Actions -->
              {#if !editingConversationId && $currentConversationId === conversation.id}
                <div class="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                  <div class="flex items-center space-x-1">
                    <button
                      on:click|stopPropagation={() => startEditing(conversation)}
                      class="p-1.5 text-gray-500 hover:text-blue-600 dark:text-gray-400 dark:hover:text-blue-400 hover:bg-white dark:hover:bg-gray-700 rounded"
                      title="Rename conversation"
                    >
                      <Edit3 size={12} />
                    </button>
                    
                    {#if showDeleteConfirm === conversation.id}
                      <div class="flex items-center space-x-1 bg-red-50 dark:bg-red-900/50 rounded px-2 py-1">
                        <span class="text-xs text-red-700 dark:text-red-300">Delete?</span>
                        <button
                          on:click|stopPropagation={() => deleteConversation(conversation.id)}
                          class="p-0.5 text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
                          title="Confirm delete"
                        >
                          <Check size={10} />
                        </button>
                        <button
                          on:click|stopPropagation={() => showDeleteConfirm = null}
                          class="p-0.5 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                          title="Cancel"
                        >
                          <X size={10} />
                        </button>
                      </div>
                    {:else}
                      <button
                        on:click|stopPropagation={() => showDeleteConfirm = conversation.id}
                        class="p-1.5 text-gray-500 hover:text-red-600 dark:text-gray-400 dark:hover:text-red-400 hover:bg-white dark:hover:bg-gray-700 rounded"
                        title="Delete conversation"
                      >
                        <Trash2 size={12} />
                      </button>
                    {/if}
                  </div>
                </div>
              {/if}
            </div>
          {/each}
        </div>
      {/each}
    {/if}
  </div>

  <!-- Footer Actions -->
  <div class="flex-shrink-0 p-4 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
    <div class="flex items-center space-x-2">
      <button
        on:click={exportConversations}
        class="flex-1 flex items-center justify-center px-3 py-2 text-xs bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 border border-gray-200 dark:border-gray-600 rounded-lg transition-colors"
        title="Export all conversations"
      >
        <Download size={14} class="mr-1" />
        Export
      </button>
      
      <button
        on:click={importConversations}
        class="flex-1 flex items-center justify-center px-3 py-2 text-xs bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 border border-gray-200 dark:border-gray-600 rounded-lg transition-colors"
        title="Import conversations"
      >
        <Upload size={14} class="mr-1" />
        Import
      </button>
    </div>
    
    <div class="mt-2 text-center">
      <p class="text-xs text-gray-500 dark:text-gray-400">
        {$conversations.length} conversation{$conversations.length !== 1 ? 's' : ''}
        {#if $currentConversationId}
          {@const currentConv = $conversations.find(c => c.id === $currentConversationId)}
          {#if currentConv && currentConv.averageThinkingTime > 0}
            <br>
            <span class="inline-flex items-center space-x-1 text-green-600 dark:text-green-400 mt-1" title="Current conversation thinking time stats">
              <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <polyline points="12,6 12,12 16,14"/>
              </svg>
              <span>Avg: {currentConv.averageThinkingTime}s • {currentConv.responseCount} AI responses</span>
            </span>
          {/if}
        {/if}
      </p>
    </div>
  </div>
</div>

<!-- Hidden file input for import -->
<input
  bind:this={fileInput}
  type="file"
  accept=".json"
  on:change={handleFileImport}
  class="hidden"
/>

<style>
  /* Smooth scrollbar */
  .overflow-y-auto::-webkit-scrollbar {
    width: 4px;
  }
  
  .overflow-y-auto::-webkit-scrollbar-track {
    background: transparent;
  }
  
  .overflow-y-auto::-webkit-scrollbar-thumb {
    background: rgba(156, 163, 175, 0.3);
    border-radius: 2px;
  }
  
  .overflow-y-auto::-webkit-scrollbar-thumb:hover {
    background: rgba(156, 163, 175, 0.5);
  }
</style>