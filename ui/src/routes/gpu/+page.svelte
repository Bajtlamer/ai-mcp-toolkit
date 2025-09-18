<script>
  import { onMount, onDestroy } from 'svelte';
  import { 
    Cpu, 
    Activity, 
    Thermometer, 
    Zap, 
    HardDrive, 
    Clock,
    TrendingUp,
    AlertTriangle,
    CheckCircle,
    XCircle,
    RefreshCw,
    Download,
    Bot,
    Gauge
  } from 'lucide-svelte';
  
  let gpuHealth = null;
  let gpuMetrics = null;
  let recommendations = [];
  let loading = true;
  let error = null;
  let autoRefresh = true;
  let refreshInterval = null;
  let lastUpdated = null;
  let statusInfo = { icon: XCircle, class: 'text-gray-400' };
  
  // Real-time metrics history for charts
  let metricsHistory = [];
  const maxHistorySize = 50;
  
  onMount(async () => {
    await loadGPUData();
    if (autoRefresh) {
      startAutoRefresh();
    }
  });
  
  onDestroy(() => {
    stopAutoRefresh();
  });
  
  async function loadGPUData() {
    try {
      loading = true;
      error = null;
      
      // Parallel fetch of all GPU data
      const [healthResponse, metricsResponse, recommendationsResponse] = await Promise.all([
        fetch('/api/gpu/health'),
        fetch('/api/gpu/metrics'), 
        fetch('/api/gpu/recommendations')
      ]);
      
      if (!healthResponse.ok) throw new Error(`Health API error: ${healthResponse.status}`);
      if (!metricsResponse.ok) throw new Error(`Metrics API error: ${metricsResponse.status}`);
      if (!recommendationsResponse.ok) throw new Error(`Recommendations API error: ${recommendationsResponse.status}`);
      
      gpuHealth = await healthResponse.json();
      gpuMetrics = await metricsResponse.json();
      const recData = await recommendationsResponse.json();
      recommendations = recData.recommendations || [];
      
      // Update status info when health data changes
      if (gpuHealth) {
        statusInfo = getStatusIcon(gpuHealth.gpu_available, gpuHealth.ollama_gpu_accelerated);
      }
      
      // Add current metrics to history
      if (gpuMetrics && gpuMetrics.current_metrics) {
        const timestamp = new Date().toLocaleTimeString();
        metricsHistory = [...metricsHistory, {
          timestamp,
          utilization: gpuMetrics.current_metrics.gpu_utilization || 0,
          memory: gpuMetrics.current_metrics.gpu_memory_usage || 0,
          temperature: gpuHealth?.gpu_temperature || 0,
          inferenceSpeed: gpuMetrics.current_metrics.inference_speed || 0
        }].slice(-maxHistorySize);
      }
      
      lastUpdated = new Date();
      loading = false;
      
    } catch (err) {
      console.error('Failed to load GPU data:', err);
      error = err.message;
      loading = false;
      
      // Simulate data for development if API not available
      if (err.message.includes('fetch')) {
        gpuHealth = {
          gpu_available: true,
          gpu_name: 'NVIDIA GeForce RTX 3070 Ti',
          gpu_utilization: Math.round(Math.random() * 100),
          gpu_memory_usage: '5400/8192 MB',
          gpu_temperature: Math.round(Math.random() * 30 + 40),
          ollama_gpu_accelerated: true,
          ollama_model: 'llama3.1:8b',
          ollama_memory_usage: '5416 MB'
        };
        
        gpuMetrics = {
          performance_summary: {
            average_gpu_utilization: 87.5,
            average_memory_usage: 65.8,
            total_requests: 156,
            total_tokens_processed: 12847,
            average_response_time: 1.245
          },
          current_metrics: {
            gpu_utilization: Math.round(Math.random() * 100),
            gpu_memory_usage: Math.round(Math.random() * 100),
            ollama_memory_usage: 5416,
            inference_speed: Math.round(Math.random() * 100 + 50)
          }
        };
        
        recommendations = [
          '✅ Ollama is successfully using GPU acceleration',
          '🔥 GPU utilization is excellent - maximum performance achieved',
          '📊 Moderate GPU memory available - suitable for 3B models'
        ];
        
        // Update status info for simulated data
        statusInfo = getStatusIcon(gpuHealth.gpu_available, gpuHealth.ollama_gpu_accelerated);
        
        error = 'Using simulated data - API not available';
      }
    }
  }
  
  function startAutoRefresh() {
    refreshInterval = setInterval(loadGPUData, 5000); // Refresh every 5 seconds
  }
  
  function stopAutoRefresh() {
    if (refreshInterval) {
      clearInterval(refreshInterval);
      refreshInterval = null;
    }
  }
  
  function toggleAutoRefresh() {
    autoRefresh = !autoRefresh;
    if (autoRefresh) {
      startAutoRefresh();
    } else {
      stopAutoRefresh();
    }
  }
  
  async function refreshData() {
    await loadGPUData();
  }
  
  async function downloadReport() {
    try {
      const response = await fetch('/api/gpu/report');
      if (!response.ok) throw new Error('Failed to generate report');
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `gpu-report-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Failed to download report:', err);
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

<svelte:head>
  <title>GPU Monitor - AI MCP Toolkit</title>
</svelte:head>

<div class="space-y-6">
  <!-- Header with Controls -->
  <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between">
    <div>
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white flex items-center">
        <Cpu class="mr-3 text-primary-500" size={32} />
        GPU Performance Monitor
      </h1>
      <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
        Real-time monitoring of your NVIDIA RTX 3070 Ti GPU acceleration
      </p>
    </div>
    
    <div class="mt-4 sm:mt-0 flex items-center space-x-3">
      <button
        on:click={toggleAutoRefresh}
        class={`inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md transition-colors ${
          autoRefresh 
            ? 'text-primary-700 bg-primary-100 hover:bg-primary-200 dark:bg-primary-900 dark:text-primary-200' 
            : 'text-gray-700 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300'
        }`}
      >
        <Activity size={16} class="mr-2" />
        Auto Refresh {autoRefresh ? 'ON' : 'OFF'}
      </button>
      
      <button
        on:click={refreshData}
        disabled={loading}
        class="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 disabled:opacity-50 transition-colors"
      >
        <RefreshCw size={16} class={`mr-2 ${loading ? 'animate-spin' : ''}`} />
        Refresh
      </button>
      
      <button
        on:click={downloadReport}
        class="inline-flex items-center px-3 py-2 border border-gray-300 text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-600 transition-colors"
      >
        <Download size={16} class="mr-2" />
        Report
      </button>
    </div>
  </div>
  
  <!-- Error/Status Banner -->
  {#if error}
    <div class="rounded-md bg-yellow-50 dark:bg-yellow-900 p-4">
      <div class="flex">
        <div class="flex-shrink-0">
          <AlertTriangle class="h-5 w-5 text-yellow-400" />
        </div>
        <div class="ml-3">
          <p class="text-sm text-yellow-700 dark:text-yellow-200">
            {error}
          </p>
        </div>
      </div>
    </div>
  {/if}
  
  {#if lastUpdated}
    <div class="text-xs text-gray-500 dark:text-gray-400">
      Last updated: {lastUpdated.toLocaleTimeString()}
    </div>
  {/if}
  
  <!-- GPU Status Cards -->
  {#if loading && !gpuHealth}
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {#each Array(4) as _}
        <div class="card p-6 animate-pulse">
          <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2 mb-4"></div>
          <div class="h-8 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
        </div>
      {/each}
    </div>
  {:else if gpuHealth}
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <!-- GPU Status -->
      <div class="card p-6">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-gray-600 dark:text-gray-400">GPU Status</p>
            <p class="text-2xl font-bold text-gray-900 dark:text-white">
              {gpuHealth.gpu_available ? 'Active' : 'Inactive'}
            </p>
            <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
              {gpuHealth.gpu_name || 'Unknown GPU'}
            </p>
          </div>
          <div class="w-12 h-12 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center">
            <svelte:component this={statusInfo.icon} class={`w-6 h-6 ${statusInfo.class}`} />
          </div>
        </div>
      </div>
      
      <!-- GPU Utilization -->
      <div class="card p-6">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-gray-600 dark:text-gray-400">GPU Utilization</p>
            <p class={`text-2xl font-bold ${getUtilizationColor(gpuHealth.gpu_utilization)}`}>
              {gpuHealth.gpu_utilization}%
            </p>
          </div>
          <div class="w-12 h-12 bg-green-100 dark:bg-green-900 rounded-lg flex items-center justify-center">
            <Gauge class="w-6 h-6 text-green-600 dark:text-green-400" />
          </div>
        </div>
        <!-- Utilization Bar -->
        <div class="mt-4">
          <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
            <div 
              class={`h-2 rounded-full transition-all duration-500 ${
                gpuHealth.gpu_utilization >= 90 ? 'bg-red-500' :
                gpuHealth.gpu_utilization >= 70 ? 'bg-yellow-500' :
                gpuHealth.gpu_utilization >= 50 ? 'bg-green-500' : 'bg-blue-500'
              }`}
              style="width: {Math.min(100, Math.max(0, gpuHealth.gpu_utilization))}%"
            ></div>
          </div>
        </div>
      </div>
      
      <!-- Memory Usage -->
      <div class="card p-6">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-gray-600 dark:text-gray-400">Memory Usage</p>
            <p class="text-2xl font-bold text-gray-900 dark:text-white">
              {gpuHealth.gpu_memory_usage}
            </p>
            <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Ollama: {gpuHealth.ollama_memory_usage}
            </p>
          </div>
          <div class="w-12 h-12 bg-purple-100 dark:bg-purple-900 rounded-lg flex items-center justify-center">
            <HardDrive class="w-6 h-6 text-purple-600 dark:text-purple-400" />
          </div>
        </div>
      </div>
      
      <!-- Temperature -->
      <div class="card p-6">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-gray-600 dark:text-gray-400">Temperature</p>
            <p class={`text-2xl font-bold ${getTemperatureColor(gpuHealth.gpu_temperature)}`}>
              {gpuHealth.gpu_temperature}°C
            </p>
          </div>
          <div class="w-12 h-12 bg-orange-100 dark:bg-orange-900 rounded-lg flex items-center justify-center">
            <Thermometer class="w-6 h-6 text-orange-600 dark:text-orange-400" />
          </div>
        </div>
      </div>
    </div>
  {/if}
  
  <!-- Performance Metrics -->
  {#if gpuMetrics}
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Real-time Performance -->
      <div class="card">
        <div class="p-6 border-b border-gray-200 dark:border-gray-700">
          <div class="flex items-center justify-between">
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
              <TrendingUp class="mr-2 text-green-500" size={20} />
              Current Performance
            </h2>
          </div>
        </div>
        
        <div class="p-6">
          <div class="grid grid-cols-2 gap-4">
            <div class="text-center">
              <div class="text-2xl font-bold text-blue-600 dark:text-blue-400">
                {gpuMetrics.current_metrics.inference_speed?.toFixed(1) || '0.0'}
              </div>
              <div class="text-sm text-gray-500 dark:text-gray-400">Tokens/sec</div>
            </div>
            
            <div class="text-center">
              <div class="text-2xl font-bold text-green-600 dark:text-green-400">
                {gpuMetrics.current_metrics.gpu_utilization?.toFixed(1) || '0.0'}%
              </div>
              <div class="text-sm text-gray-500 dark:text-gray-400">GPU Usage</div>
            </div>
            
            <div class="text-center">
              <div class="text-2xl font-bold text-purple-600 dark:text-purple-400">
                {gpuMetrics.current_metrics.ollama_memory_usage || 0} MB
              </div>
              <div class="text-sm text-gray-500 dark:text-gray-400">Memory</div>
            </div>
            
            <div class="text-center">
              <div class="text-2xl font-bold text-orange-600 dark:text-orange-400">
                {gpuMetrics.performance_summary.total_requests || 0}
              </div>
              <div class="text-sm text-gray-500 dark:text-gray-400">Requests</div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Model Information -->
      <div class="card">
        <div class="p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
            <Bot class="mr-2 text-primary-500" size={20} />
            AI Model Status
          </h2>
        </div>
        
        <div class="p-6">
          <div class="space-y-4">
            <div class="flex items-center justify-between">
              <span class="text-sm font-medium text-gray-600 dark:text-gray-400">Active Model</span>
              <span class="text-sm text-gray-900 dark:text-white font-mono">
                {gpuHealth?.ollama_model || 'None'}
              </span>
            </div>
            
            <div class="flex items-center justify-between">
              <span class="text-sm font-medium text-gray-600 dark:text-gray-400">GPU Acceleration</span>
              <span class={`text-sm font-medium ${
                gpuHealth?.ollama_gpu_accelerated ? 'text-green-600' : 'text-red-600'
              }`}>
                {gpuHealth?.ollama_gpu_accelerated ? '✓ Enabled' : '✗ Disabled'}
              </span>
            </div>
            
            <div class="flex items-center justify-between">
              <span class="text-sm font-medium text-gray-600 dark:text-gray-400">Avg Response Time</span>
              <span class="text-sm text-gray-900 dark:text-white">
                {gpuMetrics.performance_summary.average_response_time?.toFixed(3) || '0.000'}s
              </span>
            </div>
            
            <div class="flex items-center justify-between">
              <span class="text-sm font-medium text-gray-600 dark:text-gray-400">Total Tokens</span>
              <span class="text-sm text-gray-900 dark:text-white">
                {gpuMetrics.performance_summary.total_tokens_processed?.toLocaleString() || '0'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  {/if}
  
  <!-- Recommendations -->
  {#if recommendations.length > 0}
    <div class="card">
      <div class="p-6 border-b border-gray-200 dark:border-gray-700">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
          <Zap class="mr-2 text-yellow-500" size={20} />
          Optimization Recommendations
        </h2>
      </div>
      
      <div class="p-6">
        <div class="space-y-3">
          {#each recommendations as rec, i}
            <div class="flex items-start space-x-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <div class="flex-shrink-0 w-6 h-6 bg-primary-100 dark:bg-primary-900 rounded-full flex items-center justify-center">
                <span class="text-xs font-medium text-primary-600 dark:text-primary-400">
                  {i + 1}
                </span>
              </div>
              <p class="text-sm text-gray-700 dark:text-gray-300">
                {rec}
              </p>
            </div>
          {/each}
        </div>
      </div>
    </div>
  {/if}
  
  <!-- Performance History Chart Placeholder -->
  {#if metricsHistory.length > 5}
    <div class="card">
      <div class="p-6 border-b border-gray-200 dark:border-gray-700">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
          <Activity class="mr-2 text-indigo-500" size={20} />
          Performance Trends
        </h2>
      </div>
      
      <div class="p-6">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <h3 class="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
              GPU Utilization History
            </h3>
            <div class="h-32 bg-gray-100 dark:bg-gray-800 rounded-lg flex items-center justify-center">
              <p class="text-sm text-gray-500 dark:text-gray-400">
                Chart visualization (last {metricsHistory.length} readings)
              </p>
            </div>
          </div>
          
          <div>
            <h3 class="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
              Temperature History
            </h3>
            <div class="h-32 bg-gray-100 dark:bg-gray-800 rounded-lg flex items-center justify-center">
              <p class="text-sm text-gray-500 dark:text-gray-400">
                Chart visualization (last {metricsHistory.length} readings)
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  {/if}
</div>

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
