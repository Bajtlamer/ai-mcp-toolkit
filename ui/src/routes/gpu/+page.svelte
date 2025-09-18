<script>
  import { onMount, onDestroy } from 'svelte';
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
    console.log('Canvas elements available, initializing charts');
    initializeCharts();
  }
  
  // Reactive chart updates when metrics history changes
  $: if (metricsHistory.length > 0 && utilizationChart) {
    updateCharts();
  }
  
  onMount(async () => {
    await loadGPUData();
    
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
    
    console.log('Initializing charts...');
    
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
      console.log('Creating utilization chart');
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
      console.log('Utilization chart created:', !!utilizationChart);
    } else {
      console.log('Inference canvas not found');
    }
    
    console.log('All charts initialized successfully');
    
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
        if (dataPoints.length % 5 === 0) { // Log every 5 updates to avoid spam
          console.log(`Updated ${name} chart: ${dataPoints.length} points, latest: ${dataPoints[dataPoints.length-1]}`);
        }
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
        console.log('Metrics updated:', metricsHistory.length, 'points');
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
