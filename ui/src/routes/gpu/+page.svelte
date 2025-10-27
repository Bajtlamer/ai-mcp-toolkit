<script>
  import { onMount, onDestroy } from 'svelte';
  import { auth } from '$lib/stores/auth';
  import {
    Chart,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    LineController,
    Title,
    Tooltip,
    Legend,
    Filler
  } from 'chart.js';
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
    Gauge,
    BarChart3
  } from 'lucide-svelte';
  
  // Get current user to check admin status
  let currentUser = null;
  let isAdmin = false;
  
  auth.subscribe(state => {
    currentUser = state.user;
    isAdmin = state.user?.role === 'admin';
  });
  
  // Register Chart.js components
  Chart.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    LineController,
    Title,
    Tooltip,
    Legend,
    Filler
  );
  
  let gpuHealth = null;
  let gpuMetrics = null;
  let recommendations = [];
  let loading = true;
  let error = null;
  let autoRefresh = true;
  let refreshInterval = null;
  let lastUpdated = null;
  let statusInfo = { icon: XCircle, class: 'text-gray-400' };
  
  // Available models management
  let availableModels = [];
  let loadingModels = false;
  let switching = false;
  
  // Real-time metrics history for charts
  let metricsHistory = [];
  const maxHistorySize = 50;
  
  // Chart instances and elements
  let utilizationChart = null;
  let temperatureChart = null;
  let memoryChart = null;
  let inferenceChart = null;
  let utilizationCanvas = null;
  let temperatureCanvas = null;
  let memoryCanvas = null;
  let inferenceCanvas = null;
  
  // Reactive chart initialization when canvas elements are available
  $: if (utilizationCanvas && temperatureCanvas && memoryCanvas && inferenceCanvas && !utilizationChart) {
    initializeCharts();
  }
  
  // Reactive chart updates when metrics history changes
  $: if (metricsHistory.length > 0 && utilizationChart) {
    updateCharts();
  }
  
  onMount(async () => {
    await loadGPUData();
    await refreshModels();
    
    if (autoRefresh) {
      startAutoRefresh();
    }
  });
  
  onDestroy(() => {
    stopAutoRefresh();
    destroyCharts();
  });
  
  function destroyCharts() {
    [utilizationChart, temperatureChart, memoryChart, inferenceChart].forEach(chart => {
      if (chart) {
        chart.destroy();
      }
    });
    // Reset chart instances
    utilizationChart = null;
    temperatureChart = null;
    memoryChart = null;
    inferenceChart = null;
  }
  
  function initializeCharts() {
    if (typeof window === 'undefined') return;
    
    // Destroy any existing charts first
    destroyCharts();
    
    
    const commonOptions = {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        intersect: false,
      },
      plugins: {
        legend: {
          display: false
        }
      },
      scales: {
        x: {
          type: 'category',
          grid: {
            display: false
          },
          ticks: {
            maxTicksLimit: 10
          }
        },
        y: {
          beginAtZero: true,
          grid: {
            color: 'rgba(156, 163, 175, 0.1)'
          }
        }
      },
      elements: {
        point: {
          radius: 2,
          hoverRadius: 4
        },
        line: {
          tension: 0.4,
          borderWidth: 2
        }
      }
    };
    
    // GPU Utilization Chart
    if (utilizationCanvas) {
      utilizationChart = new Chart(utilizationCanvas, {
        type: 'line',
        data: {
          datasets: [{
            label: 'GPU Utilization (%)',
            data: [],
            borderColor: 'rgb(59, 130, 246)',
            backgroundColor: 'rgba(59, 130, 246, 0.1)',
            fill: true
          }]
        },
        options: {
          ...commonOptions,
          scales: {
            ...commonOptions.scales,
            y: {
              ...commonOptions.scales.y,
              max: 100
            }
          }
        }
      });
    }
    
    // Temperature Chart
    if (temperatureCanvas) {
      temperatureChart = new Chart(temperatureCanvas, {
        type: 'line',
        data: {
          datasets: [{
            label: 'Temperature (°C)',
            data: [],
            borderColor: 'rgb(245, 101, 101)',
            backgroundColor: 'rgba(245, 101, 101, 0.1)',
            fill: true
          }]
        },
        options: {
          ...commonOptions,
          scales: {
            ...commonOptions.scales,
            y: {
              ...commonOptions.scales.y,
              max: 100
            }
          }
        }
      });
    }
    
    // Memory Usage Chart
    if (memoryCanvas) {
      memoryChart = new Chart(memoryCanvas, {
        type: 'line',
        data: {
          datasets: [{
            label: 'Memory Usage (%)',
            data: [],
            borderColor: 'rgb(139, 69, 193)',
            backgroundColor: 'rgba(139, 69, 193, 0.1)',
            fill: true
          }]
        },
        options: {
          ...commonOptions,
          scales: {
            ...commonOptions.scales,
            y: {
              ...commonOptions.scales.y,
              max: 100
            }
          }
        }
      });
    }
    
    // Inference Speed Chart
    if (inferenceCanvas) {
      inferenceChart = new Chart(inferenceCanvas, {
        type: 'line',
        data: {
          datasets: [{
            label: 'Inference Speed (tok/s)',
            data: [],
            borderColor: 'rgb(16, 185, 129)',
            backgroundColor: 'rgba(16, 185, 129, 0.1)',
            fill: true
          }]
        },
        options: commonOptions
      });
    }
  }
  
  function updateCharts() {
    if (metricsHistory.length === 0) return;
    
    const charts = [
      { chart: utilizationChart, key: 'utilization', name: 'utilization' },
      { chart: temperatureChart, key: 'temperature', name: 'temperature' },
      { chart: memoryChart, key: 'memory', name: 'memory' },
      { chart: inferenceChart, key: 'inferenceSpeed', name: 'inference' }
    ];
    
    charts.forEach(({ chart, key, name }) => {
      if (chart && chart.data.datasets[0]) {
        // Use simple array format for category scale
        const dataPoints = metricsHistory.map(point => point[key]);
        const labels = metricsHistory.map(point => {
          const date = new Date(point.timestamp);
          return date.toLocaleTimeString('en-US', { 
            hour12: false, 
            minute: '2-digit', 
            second: '2-digit' 
          });
        });
        
        chart.data.labels = labels;
        chart.data.datasets[0].data = dataPoints;
        chart.update('none'); // No animation for real-time updates
      }
    });
  }
  
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
        const now = new Date();
        const newPoint = {
          timestamp: now.toISOString(),
          utilization: gpuMetrics.current_metrics.gpu_utilization || 0,
          memory: gpuMetrics.current_metrics.gpu_memory_usage || 0,
          temperature: gpuHealth?.gpu_temperature || 0,
          inferenceSpeed: gpuMetrics.current_metrics.inference_speed || 0
        };
        
        metricsHistory = [...metricsHistory, newPoint].slice(-maxHistorySize);
      }
      
      lastUpdated = new Date();
      loading = false;
      
    } catch (err) {
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
      // Silently handle download error
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
  
  // Model management helpers
  function getModelType(name) {
    if (!name) return 'Unknown';
    if (name.includes('qwen')) return 'Qwen';
    if (name.includes('llama')) return 'Llama';
    if (name.includes('mistral')) return 'Mistral';
    return 'Other';
  }
  
  function getModelSize(name) {
    if (!name) return 'Unknown';
    const match = name.match(/:(\d+)([a-zA-Z]+)/);
    if (match) return match[1] + match[2].toUpperCase();
    if (name.includes(':3b')) return '3B';
    if (name.includes(':7b')) return '7B';
    if (name.includes(':8b')) return '8B';
    if (name.includes(':13b')) return '13B';
    if (name.includes(':14b')) return '14B';
    return 'Unknown';
  }
  
  async function refreshModels() {
    try {
      loadingModels = true;
      // Fetch from UI API proxy (handles auth cookies automatically)
      const res = await fetch('/api/models');
      if (res.ok) {
        const data = await res.json();
        availableModels = data.available_models || [];
      } else {
        // If not authenticated or error, clear the list
        availableModels = [];
      }
    } catch (e) {
      // Silently handle model fetch error
      availableModels = [];
    } finally {
      loadingModels = false;
    }
  }
  
  async function switchToModel(name) {
    try {
      switching = name;
      // Call UI API proxy (handles auth cookies automatically)
      const res = await fetch('/api/models/switch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model: name })
      });
      const data = await res.json();
      if (data.success) {
        await loadGPUData();
        await refreshModels();
      } else {
        // Show error if switch fails
        error = data.error || 'Failed to switch model';
        setTimeout(() => error = null, 5000);
      }
    } catch (e) {
      // Handle model switch error
      error = 'Failed to switch model. Admin privileges required.';
      setTimeout(() => error = null, 5000);
    } finally {
      switching = false;
    }
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
      
      <!-- Active Model Information -->
      <div class="card">
        <div class="p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
            <Bot class="mr-2 text-primary-500" size={20} />
            Active AI Model
          </h2>
        </div>
        
        <div class="p-6">
          <div class="space-y-4">
            <div class="flex items-center justify-between">
              <span class="text-sm font-medium text-gray-600 dark:text-gray-400">Current Model</span>
              <span class="text-sm text-gray-900 dark:text-white font-mono bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">
                {gpuHealth?.ollama_model || 'None'}
              </span>
            </div>
            
            <div class="flex items-center justify-between">
              <span class="text-sm font-medium text-gray-600 dark:text-gray-400">GPU Acceleration</span>
              <span class={`text-sm font-medium flex items-center ${
                gpuHealth?.ollama_gpu_accelerated ? 'text-green-600' : 'text-red-600'
              }`}>
                <div class={`w-2 h-2 rounded-full mr-2 ${
                  gpuHealth?.ollama_gpu_accelerated ? 'bg-green-500' : 'bg-red-500'
                }`}></div>
                {gpuHealth?.ollama_gpu_accelerated ? 'Enabled' : 'Disabled'}
              </span>
            </div>
            
            <div class="flex items-center justify-between">
              <span class="text-sm font-medium text-gray-600 dark:text-gray-400">Avg Response Time</span>
              <span class="text-sm text-gray-900 dark:text-white font-mono">
                {gpuMetrics.performance_summary.average_response_time?.toFixed(3) || '0.000'}s
              </span>
            </div>
            
            <div class="flex items-center justify-between">
              <span class="text-sm font-medium text-gray-600 dark:text-gray-400">Total Tokens Processed</span>
              <span class="text-sm text-gray-900 dark:text-white font-mono">
                {gpuMetrics.performance_summary.total_tokens_processed?.toLocaleString() || '0'}
              </span>
            </div>
          </div>
          
          <div class="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
            <a href="/settings" class="inline-flex items-center text-sm text-primary-600 hover:text-primary-500 dark:text-primary-400 dark:hover:text-primary-300">
              <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 9l4-4 4 4m0 6l-4 4-4-4"></path>
              </svg>
              Switch Model
            </a>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Available Models Section -->
    <div class="card">
      <div class="p-6 border-b border-gray-200 dark:border-gray-700">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
          <svg class="mr-2 text-indigo-500 w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path>
          </svg>
          Available Models
        </h2>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
          All downloaded models ready for use
        </p>
      </div>
      
      <div class="p-6">
        {#if availableModels.length > 0}
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            {#each availableModels as model}
              <div class={`p-4 rounded-lg border transition-all duration-200 ${
                (model.name === gpuHealth?.ollama_model_configured || model.name === gpuHealth?.ollama_model?.replace(' (configured)', ''))
                  ? 'border-primary-300 bg-primary-50 dark:bg-primary-900/20 dark:border-primary-600' 
                  : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'
              }`}>
                <div class="flex items-center justify-between">
                  <div class="flex-1">
                    <div class="flex items-center space-x-2">
                      <div class={`w-3 h-3 rounded-full ${
                        (model.name === gpuHealth?.ollama_model_configured || model.name === gpuHealth?.ollama_model?.replace(' (configured)', '')) ? 'bg-green-500' : 'bg-gray-400'
                      }`}></div>
                      <h3 class={`text-sm font-medium ${
                        (model.name === gpuHealth?.ollama_model_configured || model.name === gpuHealth?.ollama_model?.replace(' (configured)', '')) 
                          ? 'text-primary-700 dark:text-primary-300' 
                          : 'text-gray-900 dark:text-white'
                      }`}>
                        {model.name}
                      </h3>
                      {#if model.name === gpuHealth?.ollama_model_configured || model.name === gpuHealth?.ollama_model?.replace(' (configured)', '')}
                        <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-200">
                          Active
                        </span>
                      {/if}
                    </div>
                    
                    <div class="mt-2 flex items-center space-x-4 text-xs text-gray-500 dark:text-gray-400">
                      <span class="flex items-center">
                        <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 4V2a1 1 0 011-1h8a1 1 0 011 1v2"></path>
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 4h10l1 16H6L7 4z"></path>
                        </svg>
                        {model.size}
                      </span>
                      <span class="flex items-center">
                        <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                        </svg>
                        {model.modified}
                      </span>
                    </div>
                    
                    <div class="mt-2">
                      <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">
                        Model Type: 
                        <span class={`font-medium ${
                          getModelType(model.name) === 'Qwen' ? 'text-blue-600 dark:text-blue-400' :
                          getModelType(model.name) === 'Llama' ? 'text-green-600 dark:text-green-400' :
                          'text-purple-600 dark:text-purple-400'
                        }`}>
                          {getModelType(model.name)}
                        </span>
                        • 
                        <span class="font-medium text-gray-700 dark:text-gray-300">
                          {getModelSize(model.name)}
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  {#if (model.name !== gpuHealth?.ollama_model_configured && model.name !== gpuHealth?.ollama_model?.replace(' (configured)', '')) && isAdmin}
                    <div class="flex-shrink-0 ml-3">
                      <button 
                        on:click={() => switchToModel(model.name)}
                        disabled={switching}
                        class="px-3 py-1 text-xs font-medium text-primary-600 hover:text-primary-500 dark:text-primary-400 dark:hover:text-primary-300 border border-primary-300 hover:border-primary-400 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        title="Switch to this model"
                      >
                        {switching === model.name ? 'Switching...' : 'Switch'}
                      </button>
                    </div>
                  {:else if (model.name !== gpuHealth?.ollama_model_configured && model.name !== gpuHealth?.ollama_model?.replace(' (configured)', '')) && !isAdmin}
                    <div class="flex-shrink-0 ml-3">
                      <span class="px-3 py-1 text-xs font-medium text-gray-400 dark:text-gray-500" title="Admin privileges required to switch models">
                        Switch (Admin Only)
                      </span>
                    </div>
                  {/if}
                </div>
              </div>
            {/each}
          </div>
        {:else}
          <div class="text-center py-8">
            <div class="w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012 2v2M7 7h10"></path>
              </svg>
            </div>
            <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">
              No Models Available
            </h3>
            <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">
              No Ollama models found. Please ensure Ollama is running and models are installed.
            </p>
            <div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 max-w-md mx-auto">
              <p class="text-xs text-gray-600 dark:text-gray-400 mb-2">Example commands to download models:</p>
              <code class="text-xs bg-white dark:bg-gray-700 px-2 py-1 rounded block mb-1 text-left">
                ollama pull llama3.2:3b
              </code>
              <code class="text-xs bg-white dark:bg-gray-700 px-2 py-1 rounded block text-left">
                ollama pull llama3.1:8b
              </code>
            </div>
          </div>
        {/if}
        
        <!-- Model Management Actions -->
        <div class="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700 flex items-center justify-between">
          <div class="flex items-center space-x-4 text-sm text-gray-500 dark:text-gray-400">
            <span>Total Models: {availableModels.length}</span>
            <span>•</span>
            <span>Last Updated: {new Date().toLocaleTimeString()}</span>
          </div>
          
          <div class="flex items-center space-x-2">
            <button 
              on:click={refreshModels}
              disabled={loadingModels}
              class="inline-flex items-center px-3 py-1 text-xs font-medium text-gray-600 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-200 border border-gray-300 dark:border-gray-600 rounded hover:border-gray-400 dark:hover:border-gray-500 transition-colors disabled:opacity-50"
            >
              <svg class={`w-3 h-3 mr-1 ${loadingModels ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
              </svg>
              Refresh
            </button>
            
            <a href="/settings" class="inline-flex items-center px-3 py-1 text-xs font-medium text-primary-600 hover:text-primary-500 dark:text-primary-400 dark:hover:text-primary-300 border border-primary-300 hover:border-primary-400 rounded transition-colors">
              <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
              </svg>
              Model Settings
            </a>
          </div>
        </div>
      </div>
    </div>
  {/if}
  
  <!-- Performance History Charts -->
  {#if metricsHistory.length > 3}
    <div class="card">
      <div class="p-6 border-b border-gray-200 dark:border-gray-700">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
          <BarChart3 class="mr-2 text-indigo-500" size={20} />
          Performance History
        </h2>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Real-time monitoring of GPU metrics over the last {metricsHistory.length} readings
        </p>
      </div>
      
      <div class="p-6">
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <!-- GPU Utilization Chart -->
          <div>
            <div class="flex items-center justify-between mb-3">
              <h3 class="text-sm font-medium text-gray-700 dark:text-gray-300">GPU Utilization</h3>
              <div class="flex items-center space-x-2">
                <div class="w-3 h-3 bg-blue-500 rounded-full"></div>
                <span class="text-xs text-gray-500 dark:text-gray-400">Current: {gpuHealth?.gpu_utilization || 0}%</span>
              </div>
            </div>
            <div class="h-48 bg-gray-50 dark:bg-gray-800 rounded-lg p-2">
              <canvas bind:this={utilizationCanvas}></canvas>
            </div>
          </div>
          
          <!-- Temperature Chart -->
          <div>
            <div class="flex items-center justify-between mb-3">
              <h3 class="text-sm font-medium text-gray-700 dark:text-gray-300">Temperature</h3>
              <div class="flex items-center space-x-2">
                <div class="w-3 h-3 bg-red-400 rounded-full"></div>
                <span class="text-xs text-gray-500 dark:text-gray-400">Current: {gpuHealth?.gpu_temperature || 0}°C</span>
              </div>
            </div>
            <div class="h-48 bg-gray-50 dark:bg-gray-800 rounded-lg p-2">
              <canvas bind:this={temperatureCanvas}></canvas>
            </div>
          </div>
          
          <!-- Memory Usage Chart -->
          <div>
            <div class="flex items-center justify-between mb-3">
              <h3 class="text-sm font-medium text-gray-700 dark:text-gray-300">Memory Usage</h3>
              <div class="flex items-center space-x-2">
                <div class="w-3 h-3 bg-purple-500 rounded-full"></div>
                <span class="text-xs text-gray-500 dark:text-gray-400">Current: {gpuMetrics?.current_metrics?.gpu_memory_usage || 0}%</span>
              </div>
            </div>
            <div class="h-48 bg-gray-50 dark:bg-gray-800 rounded-lg p-2">
              <canvas bind:this={memoryCanvas}></canvas>
            </div>
          </div>
          
          <!-- Inference Speed Chart -->
          <div>
            <div class="flex items-center justify-between mb-3">
              <h3 class="text-sm font-medium text-gray-700 dark:text-gray-300">Inference Speed</h3>
              <div class="flex items-center space-x-2">
                <div class="w-3 h-3 bg-green-500 rounded-full"></div>
                <span class="text-xs text-gray-500 dark:text-gray-400">Current: {gpuMetrics?.current_metrics?.inference_speed?.toFixed(1) || 0} tok/s</span>
              </div>
            </div>
            <div class="h-48 bg-gray-50 dark:bg-gray-800 rounded-lg p-2">
              <canvas bind:this={inferenceCanvas}></canvas>
            </div>
          </div>
        </div>
        
        <!-- Chart Legend and Controls -->
        <div class="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
          <div class="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
            <div class="flex items-center space-x-4">
              <span>Showing last {metricsHistory.length} data points</span>
              <span>Updates every 5 seconds</span>
            </div>
            <div class="flex items-center space-x-2">
              <span>Auto-refresh:</span>
              <span class={autoRefresh ? 'text-green-600' : 'text-gray-400'}>
                {autoRefresh ? 'ON' : 'OFF'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  {:else}
    <div class="card">
      <div class="p-6 text-center">
        <div class="w-16 h-16 bg-indigo-100 dark:bg-indigo-900 rounded-full flex items-center justify-center mx-auto mb-4">
          <BarChart3 class="w-8 h-8 text-indigo-600 dark:text-indigo-400" />
        </div>
        <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">
          Collecting Performance Data
        </h3>
        <p class="text-sm text-gray-500 dark:text-gray-400">
          Charts will appear after collecting at least 3 data points. Please wait...
        </p>
        <div class="mt-4">
          <div class="bg-gray-200 dark:bg-gray-700 rounded-full h-2">
            <div 
              class="bg-indigo-600 h-2 rounded-full transition-all duration-500" 
              style="width: {Math.min(100, (metricsHistory.length / 3) * 100)}%"
            ></div>
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
