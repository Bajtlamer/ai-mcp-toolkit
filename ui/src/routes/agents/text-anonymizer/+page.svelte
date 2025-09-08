<script>
  import { onMount } from 'svelte';
  import { toast } from 'svelte-french-toast';
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
    Zap
  } from 'lucide-svelte';
  
  let inputText = '';
  let outputText = '';
  let loading = false;
  let showOriginal = true;
  let analysisResults = null;
  
  // Settings
  let anonymizationLevel = 'standard';
  let replacementStrategy = 'placeholder';
  let preserveStructure = true;
  let useSmartAnonymization = false;
  let showAdvancedSettings = false;
  
  const exampleTexts = [
    {
      title: 'Business Email',
      text: 'Dear John Smith, your account number 4532-1234-5678-9012 has been updated. Please contact us at support@company.com or call (555) 123-4567 if you have any questions. Best regards, Sarah Johnson, Customer Service Manager.'
    },
    {
      title: 'Medical Record',
      text: 'Patient: Mary Wilson, DOB: 03/15/1985, SSN: 123-45-6789. Address: 456 Oak Street, Springfield, IL. Emergency contact: Robert Wilson (husband) at 555-987-6543. Patient reports chest pain and shortness of breath.'
    },
    {
      title: 'HR Document',
      text: 'Employee: David Chen (ID: EMP001234), hired on January 15, 2020. Salary: $75,000. Personal email: david.chen@gmail.com, Phone: 312-555-0123. Lives at 789 Pine Ave, Chicago, IL 60601.'
    }
  ];
  
  const anonymizationLevels = [
    { value: 'basic', label: 'Basic', description: 'Remove emails and phone numbers only' },
    { value: 'standard', label: 'Standard', description: 'Remove common PII including SSN, credit cards' },
    { value: 'aggressive', label: 'Aggressive', description: 'Remove all detectable sensitive information' }
  ];
  
  const replacementStrategies = [
    { value: 'placeholder', label: 'Placeholders', description: 'Replace with [EMAIL], [PHONE], etc.' },
    { value: 'fake_data', label: 'Fake Data', description: 'Replace with realistic fake data' },
    { value: 'hash', label: 'Hash', description: 'Replace with cryptographic hashes' },
    { value: 'remove', label: 'Remove', description: 'Simply remove sensitive content' }
  ];
  
  async function anonymizeText() {
    if (!inputText.trim()) {
      toast.error('Please enter some text to anonymize');
      return;
    }
    
    loading = true;
    outputText = '';
    analysisResults = null;
    
    try {
      const endpoint = useSmartAnonymization ? 'smart_anonymize' : 'anonymize_text';
      const payload = {
        text: inputText,
        ...(useSmartAnonymization ? {
          preserve_meaning: preserveStructure
        } : {
          anonymization_level: anonymizationLevel,
          replacement_strategy: replacementStrategy,
          preserve_structure: preserveStructure
        })
      };
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Mock response based on settings
      outputText = mockAnonymizeText(inputText, payload);
      
      // Mock analysis results
      analysisResults = {
        items_anonymized: 5,
        anonymization_ratio: 0.15,
        readability_preserved: preserveStructure,
        anonymization_by_type: {
          names: 2,
          emails: 1,
          phones: 1,
          addresses: 1
        }
      };
      
      toast.success('Text anonymized successfully');
    } catch (error) {
      console.error('Anonymization error:', error);
      toast.error('Failed to anonymize text. Please try again.');
    } finally {
      loading = false;
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
  
  function detectSensitiveInfo() {
    // This would call the detect_sensitive_info tool
    toast.info('Sensitive information detection coming soon!');
  }
</script>

<svelte:head>
  <title>Text Anonymizer - AI MCP Toolkit</title>
</svelte:head>

<div class="space-y-6">
  <!-- Header -->
  <div class="flex items-center justify-between">
    <div class="flex items-center space-x-3">
      <div class="w-10 h-10 bg-red-100 dark:bg-red-900 rounded-lg flex items-center justify-center">
        <Shield class="w-5 h-5 text-red-600 dark:text-red-400" />
      </div>
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Text Anonymizer</h1>
        <p class="text-gray-600 dark:text-gray-400">Remove sensitive personal information from text</p>
      </div>
    </div>
    
    <div class="flex items-center space-x-2">
      <button
        on:click={detectSensitiveInfo}
        class="btn btn-secondary"
      >
        <Eye class="w-4 h-4 mr-2" />
        Detect PII
      </button>
      
      <button
        on:click={() => showAdvancedSettings = !showAdvancedSettings}
        class="btn btn-secondary"
      >
        <Settings class="w-4 h-4 mr-2" />
        Settings
      </button>
    </div>
  </div>
  
  <!-- Settings Panel -->
  {#if showAdvancedSettings}
    <div class="card p-6 animate-slide-down">
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Anonymization Settings</h3>
      
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Anonymization Level
            </label>
            <div class="space-y-2">
              {#each anonymizationLevels as level}
                <label class="flex items-start space-x-3">
                  <input
                    type="radio"
                    bind:group={anonymizationLevel}
                    value={level.value}
                    class="mt-1"
                  />
                  <div>
                    <div class="font-medium text-gray-900 dark:text-white">{level.label}</div>
                    <div class="text-sm text-gray-500 dark:text-gray-400">{level.description}</div>
                  </div>
                </label>
              {/each}
            </div>
          </div>
        </div>
        
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Replacement Strategy
            </label>
            <div class="space-y-2">
              {#each replacementStrategies as strategy}
                <label class="flex items-start space-x-3">
                  <input
                    type="radio"
                    bind:group={replacementStrategy}
                    value={strategy.value}
                    class="mt-1"
                  />
                  <div>
                    <div class="font-medium text-gray-900 dark:text-white">{strategy.label}</div>
                    <div class="text-sm text-gray-500 dark:text-gray-400">{strategy.description}</div>
                  </div>
                </label>
              {/each}
            </div>
          </div>
        </div>
      </div>
      
      <div class="mt-6 space-y-4">
        <label class="flex items-center space-x-3">
          <input type="checkbox" bind:checked={preserveStructure} />
          <span class="text-sm font-medium text-gray-700 dark:text-gray-300">
            Preserve text structure and readability
          </span>
        </label>
        
        <label class="flex items-center space-x-3">
          <input type="checkbox" bind:checked={useSmartAnonymization} />
          <div class="flex items-center space-x-2">
            <Zap class="w-4 h-4 text-yellow-500" />
            <span class="text-sm font-medium text-gray-700 dark:text-gray-300">
              Use AI-powered smart anonymization
            </span>
          </div>
        </label>
      </div>
    </div>
  {/if}
  
  <!-- Example Texts -->
  <div class="card">
    <div class="p-4 border-b border-gray-200 dark:border-gray-700">
      <h3 class="text-lg font-medium text-gray-900 dark:text-white">Example Texts</h3>
    </div>
    <div class="p-4">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        {#each exampleTexts as example}
          <button
            on:click={() => loadExample(example)}
            class="text-left p-4 rounded-lg border border-gray-200 dark:border-gray-700 hover:border-primary-300 dark:hover:border-primary-600 hover:shadow-sm transition-all"
          >
            <h4 class="font-medium text-gray-900 dark:text-white mb-2">{example.title}</h4>
            <p class="text-sm text-gray-500 dark:text-gray-400 line-clamp-3">
              {example.text}
            </p>
          </button>
        {/each}
      </div>
    </div>
  </div>
  
  <!-- Input/Output Section -->
  <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
    <!-- Input -->
    <div class="card">
      <div class="p-4 border-b border-gray-200 dark:border-gray-700">
        <div class="flex items-center justify-between">
          <h3 class="text-lg font-medium text-gray-900 dark:text-white">Input Text</h3>
          <div class="text-sm text-gray-500 dark:text-gray-400">
            {inputText.length} characters
          </div>
        </div>
      </div>
      
      <div class="p-4">
        <textarea
          bind:value={inputText}
          placeholder="Enter text containing sensitive information to anonymize..."
          class="textarea-field h-64 resize-none"
          disabled={loading}
        ></textarea>
        
        <div class="mt-4 flex justify-center">
          <button
            on:click={anonymizeText}
            disabled={loading || !inputText.trim()}
            class="btn btn-primary {loading ? 'opacity-50 cursor-not-allowed' : ''}"
          >
            {#if loading}
              <div class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
              Processing...
            {:else}
              <Play class="w-4 h-4 mr-2" />
              Anonymize Text
            {/if}
          </button>
        </div>
      </div>
    </div>
    
    <!-- Output -->
    <div class="card">
      <div class="p-4 border-b border-gray-200 dark:border-gray-700">
        <div class="flex items-center justify-between">
          <h3 class="text-lg font-medium text-gray-900 dark:text-white">Anonymized Output</h3>
          {#if outputText}
            <div class="flex items-center space-x-2">
              <button
                on:click={() => showOriginal = !showOriginal}
                class="text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
              >
                {#if showOriginal}
                  <EyeOff class="w-4 h-4 mr-1 inline" />
                  Hide Original
                {:else}
                  <Eye class="w-4 h-4 mr-1 inline" />
                  Show Original
                {/if}
              </button>
              
              <button
                on:click={() => copyToClipboard(outputText)}
                class="btn-secondary p-2"
                title="Copy to clipboard"
              >
                <Copy class="w-4 h-4" />
              </button>
              
              <button
                on:click={downloadResult}
                class="btn-secondary p-2"
                title="Download result"
              >
                <Download class="w-4 h-4" />
              </button>
            </div>
          {/if}
        </div>
      </div>
      
      <div class="p-4">
        {#if loading}
          <div class="h-64 flex items-center justify-center">
            <div class="text-center">
              <div class="w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
              <p class="text-gray-500 dark:text-gray-400">Anonymizing text...</p>
            </div>
          </div>
        {:else if outputText}
          <div class="space-y-4">
            <div class={`p-4 rounded-lg font-mono text-sm whitespace-pre-wrap bg-gray-50 dark:bg-gray-900 border ${
              showOriginal ? 'border-warning-200 dark:border-warning-800' : 'border-success-200 dark:border-success-800'
            }`}>
              {showOriginal ? inputText : outputText}
            </div>
            
            {#if showOriginal}
              <div class="flex items-center text-sm text-warning-600 dark:text-warning-400">
                <AlertTriangle class="w-4 h-4 mr-2" />
                Showing original text with sensitive information
              </div>
            {:else}
              <div class="flex items-center text-sm text-success-600 dark:text-success-400">
                <CheckCircle class="w-4 h-4 mr-2" />
                Showing anonymized text - safe to share
              </div>
            {/if}
          </div>
        {:else}
          <div class="h-64 flex items-center justify-center text-gray-500 dark:text-gray-400">
            <div class="text-center">
              <Shield class="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>Anonymized text will appear here</p>
            </div>
          </div>
        {/if}
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
