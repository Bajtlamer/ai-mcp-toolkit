<script>
  import { 
    Shield, 
    Play, 
    Copy, 
    Download, 
    Settings, 
    Eye, 
    EyeOff, 
    AlertTriangle,
    CheckCircle,
    Info,
    Zap,
    Lock,
    User,
    Phone,
    MapPin,
    CreditCard,
    Hash,
    Trash2
  } from 'lucide-svelte';
  
  let inputText = '';
  let outputText = '';
  let loading = false;
  let showOriginal = false;
  let analysisResults = null;
  let selectedWord = null;
  let detectionResults = null;
  let error = null;
  
  // Settings
  let anonymizationLevel = 'standard';
  let replacementStrategy = 'placeholder';
  let preserveStructure = true;
  let useSmartAnonymization = false;
  let showAdvancedSettings = false;
  
  const exampleTexts = [
    {
      title: 'Business Email',
      icon: User,
      text: 'Dear John Smith, your account number 4532-1234-5678-9012 has been updated. Please contact us at support@company.com or call (555) 123-4567 if you have any questions. Best regards, Sarah Johnson, Customer Service Manager.',
      sensitiveItems: ['Names', 'Email', 'Phone', 'Credit Card']
    },
    {
      title: 'Medical Record',
      icon: Shield,
      text: 'Patient: Mary Wilson, DOB: 03/15/1985, SSN: 123-45-6789. Address: 456 Oak Street, Springfield, IL. Emergency contact: Robert Wilson (husband) at 555-987-6543. Patient reports chest pain and shortness of breath.',
      sensitiveItems: ['Names', 'DOB', 'SSN', 'Address', 'Phone']
    },
    {
      title: 'HR Document',
      icon: CreditCard,
      text: 'Employee: David Chen (ID: EMP001234), hired on January 15, 2020. Salary: $75,000. Personal email: david.chen@gmail.com, Phone: 312-555-0123. Lives at 789 Pine Ave, Chicago, IL 60601.',
      sensitiveItems: ['Names', 'ID', 'Email', 'Phone', 'Address', 'Salary']
    }
  ];
  
  const anonymizationLevels = [
    { 
      value: 'basic', 
      label: 'Basic', 
      icon: Eye,
      color: 'blue',
      description: 'Remove emails and phone numbers only',
      protects: ['Email addresses', 'Phone numbers']
    },
    { 
      value: 'standard', 
      label: 'Standard', 
      icon: Shield,
      color: 'green',
      description: 'Remove common PII including SSN, credit cards',
      protects: ['Emails', 'Phones', 'SSN', 'Credit cards', 'IP addresses']
    },
    { 
      value: 'aggressive', 
      label: 'Aggressive', 
      icon: Lock,
      color: 'orange',
      description: 'Remove all detectable sensitive information',
      protects: ['All standard items', 'URLs', 'Dates', 'Addresses']
    },
    { 
      value: 'strict', 
      label: 'Strict', 
      icon: Lock,
      color: 'red',
      description: 'Maximum protection including names with pattern-based detection and chosen replacement strategy',
      protects: ['Everything above', 'Personal names', 'Pattern-based detection', 'Respects replacement strategy']
    }
  ];
  
  const replacementStrategies = [
    { 
      value: 'placeholder', 
      label: 'Placeholders', 
      icon: Hash,
      description: 'Replace with [EMAIL], [PHONE], etc.',
      example: '[EMAIL], [PHONE], [NAME]'
    },
    { 
      value: 'fake_data', 
      label: 'Fake Data', 
      icon: User,
      description: 'Replace with realistic fake data',
      example: 'user@example.com, (555) 123-4567'
    },
    { 
      value: 'hash', 
      label: 'Hash', 
      icon: Lock,
      description: 'Replace with cryptographic hashes',
      example: '[HASH_a1b2c3d4]'
    },
    { 
      value: 'remove', 
      label: 'Remove', 
      icon: Trash2,
      description: 'Simply remove sensitive content',
      example: '[REDACTED]'
    }
  ];
  
  async function anonymizeText() {
    if (!inputText.trim()) {
      error = 'Please enter some text to anonymize';
      return;
    }
    
    loading = true;
    outputText = '';
    analysisResults = null;
    error = null;
    
    try {
      // Use smart anonymization only when explicitly enabled (but not for strict level)
      // Strict level uses regular anonymization with all patterns enabled
      const useAI = useSmartAnonymization && anonymizationLevel !== 'strict';
      const endpoint = useAI ? 'smart_anonymize' : 'anonymize_text';
      
      const payload = useAI ? {
        text: inputText,
        preserve_meaning: preserveStructure,
        context: 'general'
      } : {
        text: inputText,
        anonymization_level: anonymizationLevel,
        replacement_strategy: replacementStrategy,
        preserve_structure: preserveStructure
      };
      
      const response = await fetch('/api/tools/execute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: endpoint,
          arguments: payload
        })
      });

      const result = await response.json();
      
      if (result.success) {
        outputText = result.result;
        
        // Generate analysis report
        await generateAnalysisReport();
        
      } else {
        error = result.error || 'Failed to anonymize text';
      }
    } catch (err) {
      error = 'Failed to connect to server. Make sure the MCP server is running on port 8000.';
    } finally {
      loading = false;
    }
  }
  
  async function generateAnalysisReport() {
    if (!outputText) return;
    
    try {
      const response = await fetch('/api/tools/execute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: 'create_anonymization_report',
          arguments: {
            original_text: inputText,
            anonymized_text: outputText
          }
        })
      });
      
      const result = await response.json();
      if (result.success) {
        analysisResults = JSON.parse(result.result);
      }
    } catch (err) {
    }
  }
  
  function mockAnonymizeText(text, options) {
    let result = text;
    
    // Simple mock anonymization
    if (options.replacement_strategy === 'placeholder') {
      result = result.replace(/\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g, '[EMAIL]');
      result = result.replace(/(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}/g, '[PHONE]');
      result = result.replace(/\b\d{3}-?\d{2}-?\d{4}\b/g, '[SSN]');
      result = result.replace(/\b(?:\d{4}[-\s]?){3}\d{4}\b/g, '[CREDIT_CARD]');
      result = result.replace(/\b[A-Z][a-z]+\s[A-Z][a-z]+\b/g, '[NAME]');
      result = result.replace(/\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Court|Ct)\b/g, '[ADDRESS]');
    } else if (options.replacement_strategy === 'fake_data') {
      result = result.replace(/\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g, 'user@example.com');
      result = result.replace(/(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}/g, '(555) 123-4567');
      result = result.replace(/\b\d{3}-?\d{2}-?\d{4}\b/g, '123-45-6789');
      result = result.replace(/\b(?:\d{4}[-\s]?){3}\d{4}\b/g, '1234 5678 9012 3456');
    }
    
    return result;
  }
  
  function loadExample(example) {
    inputText = example.text;
    outputText = '';
    analysisResults = null;
  }
  
  function copyToClipboard(text) {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard');
  }
  
  function downloadResult() {
    const blob = new Blob([outputText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'anonymized-text.txt';
    a.click();
    URL.revokeObjectURL(url);
    toast.success('File downloaded');
  }
  
  async function detectSensitiveInfo() {
    if (!inputText.trim()) {
      toast.error('Please enter some text to analyze');
      return;
    }
    
    loading = true;
    
    try {
      const response = await fetch('/api/tools/execute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: 'detect_sensitive_info',
          arguments: {
            text: inputText
          }
        })
      });

      const result = await response.json();
      
      if (result.success) {
        toast.success('Sensitive information detected');
        // You could display the results in a modal or analysis panel
      } else {
        toast.error(result.error || 'Failed to detect sensitive information');
      }
    } catch (error) {
      toast.error('Failed to connect to server. Make sure the MCP server is running on port 8000.');
    } finally {
      loading = false;
    }
  }
</script>

<svelte:head>
  <title>Text Anonymizer - AI MCP Toolkit</title>
</svelte:head>

<div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
  <!-- Header -->
  <div class="mb-8">
    <div class="flex items-center space-x-3 mb-4">
      <div class="w-12 h-12 bg-gradient-to-br from-red-500 to-red-600 rounded-xl flex items-center justify-center">
        <Shield size={24} class="text-white" />
      </div>
      <div>
        <h1 class="text-3xl font-bold text-gray-900 dark:text-white">Text Anonymizer</h1>
        <p class="text-gray-600 dark:text-gray-400">Protect sensitive information with intelligent anonymization</p>
      </div>
    </div>
  </div>
  
  <!-- Quick Examples -->
  <div class="mb-6">
    <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-3">Quick Examples</h2>
    <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
      {#each exampleTexts as example}
        <button
          on:click={() => loadExample(example)}
          class="p-4 text-left bg-gray-50 dark:bg-gray-800 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 border border-gray-200 dark:border-gray-700 transition-all duration-200 group"
        >
          <div class="flex items-center space-x-3 mb-3">
            <div class="w-8 h-8 bg-red-100 dark:bg-red-900/50 rounded-lg flex items-center justify-center">
              <svelte:component this={example.icon} size={16} class="text-red-600 dark:text-red-400" />
            </div>
            <div>
              <h3 class="font-medium text-gray-900 dark:text-white">{example.title}</h3>
            </div>
          </div>
          <p class="text-sm text-gray-600 dark:text-gray-400 line-clamp-3 mb-3">
            {example.text}
          </p>
          <div class="flex flex-wrap gap-1">
            {#each example.sensitiveItems.slice(0, 3) as item}
              <span class="px-2 py-1 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 text-xs rounded-full">
                {item}
              </span>
            {/each}
            {#if example.sensitiveItems.length > 3}
              <span class="px-2 py-1 bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-400 text-xs rounded-full">
                +{example.sensitiveItems.length - 3}
              </span>
            {/if}
          </div>
        </button>
      {/each}
    </div>
  </div>
  
  <!-- Anonymization Settings -->
  <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
    <!-- Anonymization Level -->
    <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Anonymization Level</h3>
      <div class="space-y-3">
        {#each anonymizationLevels as level}
          <label class="flex items-start space-x-3 p-3 rounded-lg border cursor-pointer transition-colors {
            anonymizationLevel === level.value 
              ? `border-${level.color}-200 dark:border-${level.color}-800 bg-${level.color}-50 dark:bg-${level.color}-900/20` 
              : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
          }">
            <input
              type="radio"
              bind:group={anonymizationLevel}
              value={level.value}
              class="mt-1"
            />
            <div class="flex-1">
              <div class="flex items-center space-x-2 mb-2">
                <svelte:component this={level.icon} size={16} class="text-{level.color}-600 dark:text-{level.color}-400" />
                <div class="font-medium text-gray-900 dark:text-white">{level.label}</div>
                {#if level.value === 'strict'}
                  <span class="px-2 py-1 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 text-xs rounded-full font-medium">
                    All Patterns
                  </span>
                {/if}
              </div>
              <div class="text-sm text-gray-600 dark:text-gray-400 mb-2">{level.description}</div>
              <div class="flex flex-wrap gap-1">
                {#each level.protects.slice(0, 3) as item}
                  <span class="px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 text-xs rounded">
                    {item}
                  </span>
                {/each}
                {#if level.protects.length > 3}
                  <span class="px-2 py-1 bg-gray-200 dark:bg-gray-600 text-gray-500 dark:text-gray-400 text-xs rounded">
                    +{level.protects.length - 3} more
                  </span>
                {/if}
              </div>
            </div>
          </label>
        {/each}
      </div>
    </div>
    
    <!-- Replacement Strategy -->
    <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Replacement Strategy</h3>
      <div class="space-y-3">
        {#each replacementStrategies as strategy}
          <label class="flex items-start space-x-3 p-3 rounded-lg border cursor-pointer transition-colors {
            replacementStrategy === strategy.value 
              ? 'border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-900/20' 
              : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
          }">
            <input
              type="radio"
              bind:group={replacementStrategy}
              value={strategy.value}
              class="mt-1"
            />
            <div class="flex-1">
              <div class="flex items-center space-x-2 mb-2">
                <svelte:component this={strategy.icon} size={16} class="text-blue-600 dark:text-blue-400" />
                <div class="font-medium text-gray-900 dark:text-white">{strategy.label}</div>
              </div>
              <div class="text-sm text-gray-600 dark:text-gray-400 mb-2">{strategy.description}</div>
              <div class="text-xs text-gray-500 dark:text-gray-400 font-mono bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">
                Example: {strategy.example}
              </div>
            </div>
          </label>
        {/each}
      </div>
      
      <div class="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700 space-y-3">
        <label class="flex items-center space-x-3">
          <input type="checkbox" bind:checked={preserveStructure} class="rounded" />
          <span class="text-sm text-gray-700 dark:text-gray-300">Preserve text structure and readability</span>
        </label>
        
        <label class="flex items-center space-x-3">
          <input type="checkbox" bind:checked={useSmartAnonymization} class="rounded" />
          <div class="flex items-center space-x-2">
            <Zap size={14} class="text-yellow-500" />
            <span class="text-sm text-gray-700 dark:text-gray-300">Use AI-powered smart anonymization</span>
          </div>
        </label>
        
        {#if useSmartAnonymization}
          <div class="ml-6 text-xs text-yellow-600 dark:text-yellow-400">
            ⚠️ AI mode ignores replacement strategy and uses its own placeholders
          </div>
        {/if}
      </div>
    </div>
  </div>
  
  <!-- Input/Output Section -->
  <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-sm mb-6">
    <div class="border-b border-gray-200 dark:border-gray-700 p-4">
      <div class="flex items-center justify-between">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Text Anonymization</h3>
        <div class="flex items-center space-x-2">
          <span class="text-sm text-gray-500 dark:text-gray-400">{inputText.length} characters</span>
          {#if outputText}
            <button
              on:click={() => showOriginal = !showOriginal}
              class="flex items-center px-3 py-1.5 text-xs bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-md transition-colors"
            >
              {#if showOriginal}
                <EyeOff size={12} class="mr-1" />
                Hide Original
              {:else}
                <Eye size={12} class="mr-1" />
                Show Original
              {/if}
            </button>
          {/if}
        </div>
      </div>
    </div>
    
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-0">
      <!-- Input -->
      <div class="p-4 border-r border-gray-200 dark:border-gray-700">
        <textarea
          bind:value={inputText}
          placeholder="Enter text containing sensitive information to anonymize...\n\nExample:\nDear John Smith, please contact me at john.smith@company.com or call (555) 123-4567."
          class="w-full h-80 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent resize-none bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
          disabled={loading}
        ></textarea>
      </div>
      
      <!-- Output -->
      <div class="p-4">
        {#if loading}
          <div class="h-80 flex items-center justify-center">
            <div class="text-center">
              <div class="w-8 h-8 border-2 border-red-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
              <p class="text-gray-500 dark:text-gray-400">Anonymizing text...</p>
              {#if anonymizationLevel === 'strict'}
                <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">Using all patterns including names...</p>
              {/if}
            </div>
          </div>
        {:else if outputText}
          <div class="space-y-4">
            <div class="relative">
              <div class="w-full h-80 p-3 border rounded-lg font-mono text-sm whitespace-pre-wrap overflow-y-auto {
                showOriginal 
                  ? 'border-orange-200 dark:border-orange-800 bg-orange-50 dark:bg-orange-900/10' 
                  : 'border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-900/10'
              }">
                {showOriginal ? inputText : outputText}
              </div>
              
              <div class="absolute top-2 right-2 flex space-x-1">
                <button
                  on:click={() => copyToClipboard(showOriginal ? inputText : outputText)}
                  class="p-1.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                  title="Copy to clipboard"
                >
                  <Copy size={14} />
                </button>
                
                <button
                  on:click={downloadResult}
                  class="p-1.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                  title="Download result"
                >
                  <Download size={14} />
                </button>
              </div>
            </div>
            
            <div class="flex items-center text-sm {
              showOriginal 
                ? 'text-orange-600 dark:text-orange-400' 
                : 'text-green-600 dark:text-green-400'
            }">
              {#if showOriginal}
                <AlertTriangle size={16} class="mr-2" />
                Showing original text with sensitive information
              {:else}
                <CheckCircle size={16} class="mr-2" />
                Showing anonymized text - safe to share
              {/if}
            </div>
          </div>
        {:else if error}
          <div class="h-80 flex items-center justify-center">
            <div class="text-center">
              <AlertTriangle size={48} class="mx-auto mb-4 text-red-400 opacity-50" />
              <p class="text-red-600 dark:text-red-400">{error}</p>
            </div>
          </div>
        {:else}
          <div class="h-80 flex items-center justify-center text-gray-500 dark:text-gray-400">
            <div class="text-center">
              <Shield size={48} class="mx-auto mb-4 opacity-50" />
              <p>Anonymized text will appear here</p>
              <p class="text-sm mt-2">Enter text on the left and click "Anonymize Text"</p>
            </div>
          </div>
        {/if}
      </div>
    </div>
    
    <!-- Action Button -->
    <div class="border-t border-gray-200 dark:border-gray-700 p-4">
      <div class="flex justify-center">
        <button
          on:click={anonymizeText}
          disabled={loading || !inputText.trim()}
          class="flex items-center px-6 py-3 bg-gradient-to-r from-red-600 to-red-500 hover:from-red-700 hover:to-red-600 disabled:from-gray-400 disabled:to-gray-400 text-white font-medium rounded-lg transition-all duration-200 transform hover:scale-105 disabled:hover:scale-100 shadow-lg"
        >
          {#if loading}
            <div class="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
            {anonymizationLevel === 'strict' ? 'Processing All Patterns...' : 'Processing...'}
          {:else}
            <Shield size={18} class="mr-2" />
            Anonymize Text
          {/if}
        </button>
      </div>
    </div>
  </div>
  
  <!-- Analysis Results -->
  {#if analysisResults}
    <div class="card animate-slide-up">
      <div class="p-4 border-b border-gray-200 dark:border-gray-700">
        <h3 class="text-lg font-medium text-gray-900 dark:text-white">Anonymization Report</h3>
      </div>
      
      <div class="p-6">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div class="text-center">
            <div class="text-2xl font-bold text-primary-600 dark:text-primary-400 mb-1">
              {analysisResults.items_anonymized}
            </div>
            <div class="text-sm text-gray-500 dark:text-gray-400">Items Anonymized</div>
          </div>
          
          <div class="text-center">
            <div class="text-2xl font-bold text-success-600 dark:text-success-400 mb-1">
              {Math.round(analysisResults.anonymization_ratio * 100)}%
            </div>
            <div class="text-sm text-gray-500 dark:text-gray-400">Content Anonymized</div>
          </div>
          
          <div class="text-center">
            <div class="text-2xl font-bold text-blue-600 dark:text-blue-400 mb-1">
              {analysisResults.readability_preserved ? '✓' : '✗'}
            </div>
            <div class="text-sm text-gray-500 dark:text-gray-400">Structure Preserved</div>
          </div>
        </div>
        
        <div class="mt-6">
          <h4 class="font-medium text-gray-900 dark:text-white mb-3">Anonymized by Type</h4>
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
            {#each Object.entries(analysisResults.anonymization_by_type) as [type, count]}
              <div class="text-center p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
                <div class="font-semibold text-gray-900 dark:text-white">{count}</div>
                <div class="text-sm text-gray-500 dark:text-gray-400 capitalize">
                  {type.replace('_', ' ')}
                </div>
              </div>
            {/each}
          </div>
        </div>
      </div>
    </div>
  {/if}
  
  <!-- Help Section -->
  <div class="card">
    <div class="p-4 border-b border-gray-200 dark:border-gray-700">
      <div class="flex items-center space-x-2">
        <Info class="w-5 h-5 text-blue-500" />
        <h3 class="text-lg font-medium text-gray-900 dark:text-white">How It Works</h3>
      </div>
    </div>
    
    <div class="p-6">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <h4 class="font-medium text-gray-900 dark:text-white mb-3">What Gets Anonymized</h4>
          <ul class="space-y-2 text-sm text-gray-600 dark:text-gray-400">
            <li>• Personal names and identities</li>
            <li>• Email addresses</li>
            <li>• Phone numbers</li>
            <li>• Physical addresses</li>
            <li>• Social Security Numbers</li>
            <li>• Credit card numbers</li>
            <li>• IP addresses and URLs</li>
            <li>• Custom patterns you define</li>
          </ul>
        </div>
        
        <div>
          <h4 class="font-medium text-gray-900 dark:text-white mb-3">Replacement Options</h4>
          <ul class="space-y-2 text-sm text-gray-600 dark:text-gray-400">
            <li>• <strong>Placeholders:</strong> [EMAIL], [PHONE], [NAME]</li>
            <li>• <strong>Fake Data:</strong> Realistic but false information</li>
            <li>• <strong>Hash:</strong> Cryptographic hash values</li>
            <li>• <strong>Remove:</strong> Simply delete sensitive content</li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</div>

<style>
  .line-clamp-3 {
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
</style>
