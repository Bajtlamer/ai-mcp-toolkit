<script>
  import { marked } from 'marked';
  import { onMount } from 'svelte';
  import hljs from 'highlight.js';
  
  // Import highlight.js CSS for syntax highlighting
  import 'highlight.js/styles/github-dark.css';

  export let content = '';
  export let className = '';
  
  let renderedHtml = '';
  
  // Language mapping for better syntax highlighting
  function normalizeLanguage(lang) {
    const languageMap = {
      'js': 'javascript',
      'ts': 'typescript',
      'py': 'python',
      'sh': 'bash',
      'shell': 'bash',
      'yml': 'yaml',
      'htm': 'html',
      'c++': 'cpp',
      'csharp': 'cs',
      'c#': 'cs'
    };
    
    return languageMap[lang?.toLowerCase()] || lang;
  }
  
  // Safe string conversion function
  function toSafeString(value) {
    if (value === null || value === undefined) return '';
    if (typeof value === 'string') return value;
    if (typeof value === 'number' || typeof value === 'boolean') {
      return String(value);
    }
    if (typeof value === 'object') {
      try {
        // If it's an object, try to extract meaningful content
        if (value.content && typeof value.content === 'string') {
          return value.content;
        }
        if (value.message && typeof value.message === 'string') {
          return value.message;
        }
        if (value.text && typeof value.text === 'string') {
          return value.text;
        }
        // Otherwise, stringify it nicely
        return JSON.stringify(value, null, 2);
      } catch {
        return '[Object could not be converted to string]';
      }
    }
    return String(value);
  }
  
  // Safe HTML escaping (browser-safe)
  function escapeHtml(text) {
    if (typeof document === 'undefined') {
      // SSR fallback
      return String(text)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#x27;');
    }
    
    try {
      const div = document.createElement('div');
      div.textContent = text;
      return div.innerHTML;
    } catch {
      return String(text).replace(/[<>&"']/g, (char) => {
        switch (char) {
          case '<': return '&lt;';
          case '>': return '&gt;';
          case '&': return '&amp;';
          case '"': return '&quot;';
          case "'": return '&#x27;';
          default: return char;
        }
      });
    }
  }
  
  // Configure marked with basic settings
  function setupMarked() {
    try {
      // Reset marked to clean state
      marked.setOptions(marked.getDefaults());
      
      // Create custom renderer
      const renderer = new marked.Renderer();
      
      // Simple code block renderer with syntax highlighting
      renderer.code = function(code, language) {
        // Apply safe string extraction to code content
        const safeCodeContent = toSafeString(code);
        
        // Determine the language for highlighting
        let normalizedLang = normalizeLanguage(language) || 'text';
        let detectedLang = normalizedLang;
        let highlightedCode = '';
        
        try {
          if (detectedLang === 'text' || !detectedLang || detectedLang === 'auto') {
            // Try to auto-detect language
            const detected = hljs.highlightAuto(safeCodeContent);
            highlightedCode = detected.value;
            detectedLang = detected.language || 'text';
          } else {
            // Use specified language
            try {
              const result = hljs.highlight(safeCodeContent, { language: detectedLang });
              highlightedCode = result.value;
            } catch (langError) {
              // If the specific language fails, try auto-detection
              const detected = hljs.highlightAuto(safeCodeContent);
              highlightedCode = detected.value;
              detectedLang = detected.language || 'text';
            }
          }
        } catch (error) {
          // Fallback to escaped HTML without highlighting
          highlightedCode = escapeHtml(safeCodeContent);
        }
        
        return `<div class="code-block">
          <div class="code-header">
            <span class="code-lang">${escapeHtml(detectedLang)}</span>
            <button class="copy-btn" onclick="copyCode(this)" title="Copy code">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2 2v1"></path>
              </svg>
            </button>
          </div>
          <pre><code class="hljs language-${escapeHtml(detectedLang)}" data-lang="${escapeHtml(detectedLang)}">${highlightedCode}</code></pre>
        </div>`;
      };
      
      // Simple inline code renderer
      renderer.codespan = function(code) {
        const safeCodeContent = toSafeString(code);
        return `<code class="inline-code">${escapeHtml(safeCodeContent)}</code>`;
      };
      
      // Configure marked
      marked.setOptions({
        renderer: renderer,
        breaks: true,
        gfm: true,
        headerIds: false,
        mangle: false
      });
      
      return true;
    } catch (err) {
      return false;
    }
  }
  
  onMount(() => {
    // Initialize highlight.js
    try {
      // Configure highlight.js with common languages
      hljs.configure({
        ignoreUnescapedHTML: true,
        languages: ['javascript', 'typescript', 'python', 'java', 'cpp', 'c', 'html', 'css', 'json', 'xml', 'bash', 'shell', 'yaml', 'sql', 'php', 'go', 'rust', 'swift']
      });
    } catch (error) {
      // Silently handle highlight.js initialization failure
    }
    
    // Initialize marked with our custom renderer
    setupMarked();
    
    // Enhanced copy function with fallback for remote computers
    window.copyCode = function(button) {
      try {
        const codeBlock = button.closest('.code-block').querySelector('code');
        const text = codeBlock.textContent || codeBlock.innerText;
        
        // Modern clipboard API with fallback
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(text).then(() => {
            showCopySuccess(button);
          }).catch(err => {
            // Fallback to execCommand for remote computers
            fallbackCopyToClipboard(text, button);
          });
        } else {
          // Fallback for browsers without clipboard API or insecure contexts
          fallbackCopyToClipboard(text, button);
        }
      } catch (err) {
        console.warn('Copy failed:', err);
      }
    };
    
    // Fallback copy function for older browsers or insecure contexts
    function fallbackCopyToClipboard(text, button) {
      try {
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        const successful = document.execCommand('copy');
        document.body.removeChild(textArea);
        
        if (successful) {
          showCopySuccess(button);
        } else {
          showCopyError(button);
        }
      } catch (err) {
        showCopyError(button);
      }
    }
    
    // Show copy success feedback
    function showCopySuccess(button) {
      const originalColor = button.style.color;
      button.style.color = '#10b981';
      button.title = 'Copied!';
      setTimeout(() => {
        button.style.color = originalColor;
        button.title = 'Copy code';
      }, 1500);
    }
    
    // Show copy error feedback
    function showCopyError(button) {
      const originalColor = button.style.color;
      button.style.color = '#ef4444';
      button.title = 'Copy failed - select text manually';
      setTimeout(() => {
        button.style.color = originalColor;
        button.title = 'Copy code';
      }, 2000);
    };
  });
  
  // React to content changes with maximum safety
  $: {
    if (content) {
      try {
        const safeContent = toSafeString(content).trim();
        
        if (safeContent) {
          // Ensure marked is set up before use
          setupMarked();
          
          // Use the modern marked API
          const result = marked(safeContent);
          renderedHtml = result;
        } else {
          renderedHtml = '';
        }
      } catch (error) {
        // Ultra-safe fallback
        const escapedContent = escapeHtml(toSafeString(content));
        renderedHtml = `<div style="border: 1px solid #fbbf24; background: #fef3c7; padding: 1rem; border-radius: 4px; color: #92400e;">
          <p><strong>Markdown Rendering Error:</strong> ${error.message}</p>
          <details><summary>Raw Content:</summary><pre style="background: #f5f5f5; padding: 0.5rem; margin-top: 0.5rem; border-radius: 4px; overflow: auto; white-space: pre-wrap;">${escapedContent}</pre></details>
        </div>`;
      }
    } else {
      renderedHtml = '';
    }
  }
</script>

<div class="markdown-content {className}" class:empty={!renderedHtml}>
  {@html renderedHtml}
</div>

<style>
  .markdown-content {
    line-height: 1.6;
    color: inherit;
    max-width: 100%;
    overflow-wrap: break-word;
    word-wrap: break-word;
  }
  
  .markdown-content.empty {
    display: none;
  }
  
  /* Copy all the same styles from the original MarkdownRenderer but make them more defensive */
  .markdown-content :global(h1) {
    font-size: 1.75rem;
    font-weight: 700;
    margin: 1.5rem 0 1rem 0;
    /* border-bottom: 2px solid #e5e7eb; */
    /* padding-bottom: 0.5rem; */
  }
  
  .markdown-content :global(h2) {
    font-size: 1.5rem;
    font-weight: 600;
    margin: 1.25rem 0 0.75rem 0;
    /* border-bottom: 1px solid #e5e7eb; */
    /* padding-bottom: 0.25rem; */
  }
  
  .markdown-content :global(h3) {
    font-size: 1.25rem;
    font-weight: 600;
    margin: 1rem 0 0.5rem 0;
  }
  
  .markdown-content :global(.inline-code) {
    background: #f3f4f6;
    color: #dc2626;
    padding: 0.125rem 0.25rem;
    border-radius: 0.25rem;
    font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
    font-size: 0.875em;
    border: 1px solid #e5e7eb;
  }
  
  .markdown-content :global(.code-block) {
    margin: 1rem 0;
    border-radius: 0.5rem;
    overflow: hidden;
    border: 1px solid #30363d;
    background: #0d1117;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
  }
  
  .markdown-content :global(.code-header) {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #161b22;
    padding: 0.5rem 1rem;
    border-bottom: 1px solid #30363d;
    font-size: 0.75rem;
    color: #7d8590;
    font-weight: 500;
    border-radius: 0.5rem 0.5rem 0 0;
  }
  
  .markdown-content :global(.code-lang) {
    color: #58a6ff;
    font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
  }
  
  .markdown-content :global(.copy-btn) {
    background: none;
    border: none;
    color: #7d8590;
    cursor: pointer;
    padding: 0.25rem;
    border-radius: 0.25rem;
    display: flex;
    align-items: center;
    transition: all 0.2s;
  }
  
  .markdown-content :global(.copy-btn:hover) {
    color: #58a6ff;
    background: #21262d;
  }
  
  .markdown-content :global(.copy-btn:active) {
    background: #30363d;
  }
  
  .markdown-content :global(.code-block pre) {
    margin: 0;
    padding: 1rem;
    overflow-x: auto;
    background: #0d1117;
    font-family: 'JetBrains Mono', 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
    font-size: 0.875rem;
    line-height: 1.5;
    white-space: pre;
    tab-size: 2;
    border-radius: 0 0 0.5rem 0.5rem;
  }
  
  .markdown-content :global(.code-block code) {
    background: none !important;
    color: inherit;
    padding: 0;
    border: none;
    border-radius: 0;
    white-space: pre;
    font-family: inherit;
  }
  
  /* Override highlight.js theme colors for better integration */
  .markdown-content :global(.hljs) {
    background: #0d1117 !important;
    color: #c9d1d9 !important;
    padding: 0 !important;
  }
  
  /* Ensure syntax highlighting colors work well */
  .markdown-content :global(.hljs-keyword) { color: #ff7b72 !important; }
  .markdown-content :global(.hljs-string) { color: #a5d6ff !important; }
  .markdown-content :global(.hljs-function) { color: #d2a8ff !important; }
  .markdown-content :global(.hljs-number) { color: #79c0ff !important; }
  .markdown-content :global(.hljs-comment) { color: #8b949e !important; }
  .markdown-content :global(.hljs-variable) { color: #ffa657 !important; }
  .markdown-content :global(.hljs-built_in) { color: #79c0ff !important; }
  .markdown-content :global(.hljs-title) { color: #d2a8ff !important; }
  .markdown-content :global(.hljs-type) { color: #79c0ff !important; }
  .markdown-content :global(.hljs-literal) { color: #79c0ff !important; }
  .markdown-content :global(.hljs-attr) { color: #79c0ff !important; }
  .markdown-content :global(.hljs-tag) { color: #7ee787 !important; }
  
  /* Dark mode support - these styles are now default */
  :global(.dark) .markdown-content :global(.inline-code) {
    background: #21262d;
    color: #ffa657;
    border-color: #30363d;
  }
  
  /* Light mode overrides for code blocks */
  :global(.light) .markdown-content :global(.code-block) {
    border-color: #e5e7eb;
    background: #f8fafc;
  }
  
  :global(.light) .markdown-content :global(.code-header) {
    background: #f1f5f9;
    border-color: #e2e8f0;
    color: #374151;
  }
  
  :global(.light) .markdown-content :global(.code-lang) {
    color: #4f46e5;
  }
  
  :global(.light) .markdown-content :global(.copy-btn) {
    color: #64748b;
  }
  
  :global(.light) .markdown-content :global(.copy-btn:hover) {
    color: #374151;
    background: #e2e8f0;
  }
  
  :global(.light) .markdown-content :global(.code-block pre) {
    background: #f8fafc;
  }
  
  :global(.light) .markdown-content :global(.hljs) {
    background: #f8fafc !important;
    color: #24292f !important;
  }
</style>