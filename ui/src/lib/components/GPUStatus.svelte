<script>
  import { onMount, onDestroy } from 'svelte';
  import { 
    Cpu, 
    Activity, 
    Thermometer, 
    CheckCircle, 
    XCircle, 
    AlertTriangle,
    ArrowRight,
    Gauge
  } from 'lucide-svelte';
  
  export let compact = false;
  
  let gpuHealth = null;
  let loading = true;
  let refreshInterval = null;
  let statusInfo = { icon: XCircle, class: 'text-gray-400' };
  
  onMount(async () => {
    await loadGPUHealth();
    // Refresh every 30 seconds for dashboard
    refreshInterval = setInterval(loadGPUHealth, 30000);
  });
  
  onDestroy(() => {
    if (refreshInterval) {
      clearInterval(refreshInterval);
    }
  });
  
  async function loadGPUHealth() {
    try {
      const response = await fetch('/api/gpu/health');
      if (response.ok) {
        gpuHealth = await response.json();
        // Update status info when health data changes
        statusInfo = getStatusIcon(gpuHealth.gpu_available, gpuHealth.ollama_gpu_accelerated);
      }
      loading = false;
    } catch (error) {
      console.error('Failed to load GPU health:', error);
      loading = false;
    }
  }
  
  function getStatusIcon(available, accelerated) {
    if (!available) return { icon: XCircle, class: 'text-red-500' };
    if (accelerated) return { icon: CheckCircle, class: 'text-green-500' };
    return { icon: AlertTriangle, class: 'text-yellow-500' };
  }
  
  function getUtilizationColor(utilization) {
    if (utilization >= 90) return 'text-red-500';
    if (utilization >= 70) return 'text-yellow-500';
    if (utilization >= 50) return 'text-green-500';
    return 'text-blue-500';
  }
  
  function getTemperatureColor(temp) {
    if (temp >= 80) return 'text-red-500';
    if (temp >= 70) return 'text-yellow-500';
    return 'text-green-500';
  }
</script>

{#if compact}
  <!-- Compact version for dashboard -->
  <div class="card p-4">
    <div class="flex items-center justify-between mb-3">
      <h3 class="text-sm font-semibold text-gray-900 dark:text-white flex items-center">
        <Cpu class="mr-2 text-primary-500" size={16} />
        GPU Status
      </h3>
      <a
        href="/gpu"
        class="inline-flex items-center text-xs text-primary-600 hover:text-primary-500 dark:text-primary-400 dark:hover:text-primary-300"
      >
        Details
        <ArrowRight class="ml-1 w-3 h-3" />
      </a>
    </div>
    
    {#if loading}
      <div class="animate-pulse">
        <div class="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/2 mb-2"></div>
        <div class="h-6 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
      </div>
    {:else if gpuHealth}
      <div class="space-y-3">
        <!-- Status -->
        <div class="flex items-center justify-between">
          <span class="text-xs text-gray-600 dark:text-gray-400">Status</span>
          <div class="flex items-center space-x-1">
            <svelte:component this={statusInfo.icon} class={`w-4 h-4 ${statusInfo.class}`} />
            <span class="text-xs font-medium text-gray-900 dark:text-white">
              {gpuHealth.gpu_available ? 'Active' : 'Inactive'}
            </span>
          </div>
        </div>
        
        <!-- Utilization -->
        <div class="flex items-center justify-between">
          <span class="text-xs text-gray-600 dark:text-gray-400">Usage</span>
          <span class={`text-xs font-semibold ${getUtilizationColor(gpuHealth.gpu_utilization)}`}>
            {gpuHealth.gpu_utilization}%
          </span>
        </div>
        
        <!-- Temperature -->
        <div class="flex items-center justify-between">
          <span class="text-xs text-gray-600 dark:text-gray-400">Temp</span>
          <span class={`text-xs font-semibold ${getTemperatureColor(gpuHealth.gpu_temperature)}`}>
            {gpuHealth.gpu_temperature}°C
          </span>
        </div>
        
        <!-- Model -->
        {#if gpuHealth.ollama_model}
          <div class="flex items-center justify-between">
            <span class="text-xs text-gray-600 dark:text-gray-400">Model</span>
            <span class="text-xs font-mono text-gray-900 dark:text-white">
              {gpuHealth.ollama_model}
            </span>
          </div>
        {/if}
      </div>
    {:else}
      <div class="text-center text-xs text-gray-500 dark:text-gray-400">
        GPU data unavailable
      </div>
    {/if}
  </div>
{:else}
  <!-- Full version for dedicated sections -->
  <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
    {#if loading}
      {#each Array(3) as _}
        <div class="card p-4 animate-pulse">
          <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2 mb-3"></div>
          <div class="h-6 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
        </div>
      {/each}
    {:else if gpuHealth}
      <!-- GPU Status Card -->
      <div class="card p-4">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">GPU Status</p>
            <p class="text-lg font-bold text-gray-900 dark:text-white">
              {gpuHealth.gpu_available ? 'Active' : 'Inactive'}
            </p>
            <p class="text-xs text-gray-500 dark:text-gray-400">
              {gpuHealth.gpu_name || 'Unknown GPU'}
            </p>
          </div>
          <div class="flex-shrink-0">
            <svelte:component this={statusInfo.icon} class={`w-8 h-8 ${statusInfo.class}`} />
          </div>
        </div>
      </div>
      
      <!-- GPU Utilization Card -->
      <div class="card p-4">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Utilization</p>
            <p class={`text-lg font-bold ${getUtilizationColor(gpuHealth.gpu_utilization)}`}>
              {gpuHealth.gpu_utilization}%
            </p>
          </div>
          <div class="flex-shrink-0">
            <Gauge class="w-8 h-8 text-blue-500" />
          </div>
        </div>
        <!-- Progress bar -->
        <div class="mt-3">
          <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5">
            <div 
              class={`h-1.5 rounded-full transition-all duration-500 ${
                gpuHealth.gpu_utilization >= 90 ? 'bg-red-500' :
                gpuHealth.gpu_utilization >= 70 ? 'bg-yellow-500' :
                gpuHealth.gpu_utilization >= 50 ? 'bg-green-500' : 'bg-blue-500'
              }`}
              style="width: {Math.min(100, Math.max(0, gpuHealth.gpu_utilization))}%"
            ></div>
          </div>
        </div>
      </div>
      
      <!-- Temperature Card -->
      <div class="card p-4">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Temperature</p>
            <p class={`text-lg font-bold ${getTemperatureColor(gpuHealth.gpu_temperature)}`}>
              {gpuHealth.gpu_temperature}°C
            </p>
          </div>
          <div class="flex-shrink-0">
            <Thermometer class="w-8 h-8 text-orange-500" />
          </div>
        </div>
      </div>
    {:else}
      <div class="card p-4 col-span-full">
        <div class="text-center text-gray-500 dark:text-gray-400">
          <Cpu class="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p class="text-sm">GPU data unavailable</p>
        </div>
      </div>
    {/if}
  </div>
{/if}

<style>
  .card {
    background-color: white;
    box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    border-width: 1px;
    border-color: rgb(229, 231, 235);
    border-radius: 0.5rem;
  }
  
  :global(.dark) .card {
    background-color: rgb(31, 41, 55);
    border-color: rgb(75, 85, 99);
  }
</style>
