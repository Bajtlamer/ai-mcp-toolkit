<script>
  import { marked } from 'marked';
  import { onMount } from 'svelte';
  import hljs from 'highlight.js';

  export let content = '';
  export let className = '';
  
  let renderedHtml = '';
  
  // Configure marked options with safe defaults
  marked.setOptions({
    highlight: function(code, lang) {
      try {
        const codeStr = String(code || '');
        if (lang && hljs.getLanguage(lang)) {
          return hljs.highlight(codeStr, { language: lang }).value;
        }
        return hljs.highlightAuto(codeStr).value;
      } catch (err) {
        console.error('Syntax highlighting error:', err);
        return String(code || ''); // Return safe fallback
      }
    },
    breaks: true,
    gfm: true,
    tables: true,
    sanitize: false // We trust the AI responses
  });
  
  // Custom renderer for better styling
  const renderer = new marked.Renderer();
  
  // Custom code block renderer
  renderer.code = function(code, language, escaped) {
    const lang = language || 'text';
    const codeString = String(code || ''); // Ensure code is always a string
    const highlighted = hljs.getLanguage(lang) 
      ? hljs.highlight(codeString, { language: lang }).value
      : hljs.highlightAuto(codeString).value;
    
    return `<div class="code-block-wrapper">
      <div class="code-block-header">
        <span class="code-block-lang">${lang}</span>
        <button class="code-copy-btn" onclick="copyCodeBlock(this)" title="Copy code">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
            <path d="m5 15-4-4 4-4"></path>
          </svg>
        </button>
      </div>
      <pre><code class="hljs language-${lang}">${highlighted || codeString}</code></pre>
    </div>`;
  };
  
  // Custom inline code renderer
  renderer.codespan = function(code) {
    const codeString = String(code || ''); // Ensure code is always a string
    return `<code class="inline-code">${codeString}</code>`;
  };
  
  // Custom blockquote renderer
  renderer.blockquote = function(quote) {
    return `<blockquote class="custom-blockquote">${quote}</blockquote>`;
  };
  
  // Custom table renderer
  renderer.table = function(header, body) {
    return `<div class="table-wrapper">
      <table class="custom-table">
        <thead>${header}</thead>
        <tbody>${body}</tbody>
      </table>
    </div>`;
  };
  
  // Custom link renderer (security)
  renderer.link = function(href, title, text) {
    const titleAttr = title ? ` title="${title}"` : '';
    return `<a href="${href}" target="_blank" rel="noopener noreferrer" class="custom-link"${titleAttr}>${text}</a>`;
  };
  
  marked.use({ renderer });
  
  // React to content changes
  $: {
    if (content) {
      try {
        // Ensure content is always a string
        const contentString = String(content || '');
        if (contentString.trim()) {
          renderedHtml = marked(contentString);
        } else {
          renderedHtml = '';
        }
      } catch (error) {
        console.error('Markdown parsing error:', error);
        console.error('Content that caused error:', content);
        // Fallback to escaped plain text
        const safeContent = String(content || '').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        renderedHtml = `<p>${safeContent}</p>`;
      }
    } else {
      renderedHtml = '';
    }
  }
  
  // Global function for copying code blocks
  onMount(() => {
    window.copyCodeBlock = function(button) {
      const codeBlock = button.closest('.code-block-wrapper').querySelector('code');
      const text = codeBlock.textContent;
      
      navigator.clipboard.writeText(text).then(() => {
        const originalHTML = button.innerHTML;
        button.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="20,6 9,17 4,12"></polyline>
        </svg>`;
        button.style.color = '#10b981';
        
        setTimeout(() => {
          button.innerHTML = originalHTML;
          button.style.color = '';
        }, 2000);
      }).catch(err => {
        console.error('Failed to copy code:', err);
      });
    };
  });
</script>

<div class="markdown-content {className}" class:empty={!content}>
  {@html renderedHtml}
</div>

<style>
  .markdown-content {
    line-height: 1.6;
    color: inherit;
  }
  
  .markdown-content.empty {
    display: none;
  }
  
  /* Typography */
  .markdown-content :global(h1) {
    font-size: 1.75rem;
    font-weight: 700;
    margin: 1.5rem 0 1rem 0;
    border-bottom: 2px solid #e5e7eb;
    padding-bottom: 0.5rem;
  }
  
  .markdown-content :global(h2) {
    font-size: 1.5rem;
    font-weight: 600;
    margin: 1.25rem 0 0.75rem 0;
    border-bottom: 1px solid #e5e7eb;
    padding-bottom: 0.25rem;
  }
  
  .markdown-content :global(h3) {
    font-size: 1.25rem;
    font-weight: 600;
    margin: 1rem 0 0.5rem 0;
  }
  
  .markdown-content :global(h4),
  .markdown-content :global(h5),
  .markdown-content :global(h6) {
    font-size: 1.1rem;
    font-weight: 600;
    margin: 0.75rem 0 0.25rem 0;
  }
  
  .markdown-content :global(p) {
    margin: 0.75rem 0;
  }
  
  /* Lists */
  .markdown-content :global(ul),
  .markdown-content :global(ol) {
    margin: 0.75rem 0;
    padding-left: 1.5rem;
  }
  
  .markdown-content :global(li) {
    margin: 0.25rem 0;
  }
  
  .markdown-content :global(li > ul),
  .markdown-content :global(li > ol) {
    margin: 0.25rem 0;
  }
  
  /* Emphasis */
  .markdown-content :global(strong) {
    font-weight: 700;
    color: #1f2937;
  }
  
  .markdown-content :global(em) {
    font-style: italic;
  }
  
  /* Code */
  .markdown-content :global(.inline-code) {
    background: #f3f4f6;
    color: #dc2626;
    padding: 0.125rem 0.25rem;
    border-radius: 0.25rem;
    font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
    font-size: 0.875em;
    border: 1px solid #e5e7eb;
  }
  
  .markdown-content :global(.code-block-wrapper) {
    margin: 1rem 0;
    border-radius: 0.5rem;
    overflow: hidden;
    border: 1px solid #e5e7eb;
    background: #f8fafc;
  }
  
  .markdown-content :global(.code-block-header) {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #f1f5f9;
    padding: 0.5rem 1rem;
    border-bottom: 1px solid #e2e8f0;
    font-size: 0.75rem;
  }
  
  .markdown-content :global(.code-block-lang) {
    color: #64748b;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }
  
  .markdown-content :global(.code-copy-btn) {
    background: none;
    border: none;
    color: #64748b;
    cursor: pointer;
    padding: 0.25rem;
    border-radius: 0.25rem;
    display: flex;
    align-items: center;
    transition: color 0.2s;
  }
  
  .markdown-content :global(.code-copy-btn:hover) {
    color: #374151;
    background: #e2e8f0;
  }
  
  .markdown-content :global(pre) {
    margin: 0;
    padding: 1rem;
    overflow-x: auto;
    background: #1e293b !important;
    color: #e2e8f0;
    font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
    font-size: 0.875rem;
    line-height: 1.5;
  }
  
  .markdown-content :global(pre code) {
    background: none !important;
    color: inherit !important;
    padding: 0 !important;
    border: none !important;
    border-radius: 0 !important;
  }
  
  /* Blockquotes */
  .markdown-content :global(.custom-blockquote) {
    border-left: 4px solid #3b82f6;
    background: #eff6ff;
    margin: 1rem 0;
    padding: 0.75rem 1rem;
    border-radius: 0 0.375rem 0.375rem 0;
    color: #1e40af;
  }
  
  .markdown-content :global(.custom-blockquote p) {
    margin: 0;
  }
  
  /* Links */
  .markdown-content :global(.custom-link) {
    color: #2563eb;
    text-decoration: underline;
    text-decoration-color: #93c5fd;
    transition: all 0.2s;
  }
  
  .markdown-content :global(.custom-link:hover) {
    color: #1d4ed8;
    text-decoration-color: #2563eb;
  }
  
  /* Tables */
  .markdown-content :global(.table-wrapper) {
    margin: 1rem 0;
    overflow-x: auto;
    border-radius: 0.5rem;
    border: 1px solid #e5e7eb;
  }
  
  .markdown-content :global(.custom-table) {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.875rem;
  }
  
  .markdown-content :global(.custom-table th) {
    background: #f9fafb;
    font-weight: 600;
    text-align: left;
    padding: 0.75rem;
    border-bottom: 1px solid #e5e7eb;
  }
  
  .markdown-content :global(.custom-table td) {
    padding: 0.75rem;
    border-bottom: 1px solid #f3f4f6;
  }
  
  .markdown-content :global(.custom-table tbody tr:hover) {
    background: #f9fafb;
  }
  
  /* Horizontal Rules */
  .markdown-content :global(hr) {
    border: none;
    height: 1px;
    background: linear-gradient(to right, transparent, #e5e7eb, transparent);
    margin: 2rem 0;
  }
  
  /* Dark mode support */
  :global(.dark) .markdown-content :global(strong) {
    color: #f3f4f6;
  }
  
  :global(.dark) .markdown-content :global(.inline-code) {
    background: #374151;
    color: #fbbf24;
    border-color: #4b5563;
  }
  
  :global(.dark) .markdown-content :global(.code-block-wrapper) {
    border-color: #4b5563;
    background: #1f2937;
  }
  
  :global(.dark) .markdown-content :global(.code-block-header) {
    background: #374151;
    border-color: #4b5563;
  }
  
  :global(.dark) .markdown-content :global(.code-block-lang) {
    color: #9ca3af;
  }
  
  :global(.dark) .markdown-content :global(.code-copy-btn) {
    color: #9ca3af;
  }
  
  :global(.dark) .markdown-content :global(.code-copy-btn:hover) {
    color: #d1d5db;
    background: #4b5563;
  }
  
  :global(.dark) .markdown-content :global(.custom-blockquote) {
    background: #1e3a8a;
    border-color: #3b82f6;
    color: #dbeafe;
  }
  
  :global(.dark) .markdown-content :global(.custom-link) {
    color: #60a5fa;
    text-decoration-color: #1e40af;
  }
  
  :global(.dark) .markdown-content :global(.custom-link:hover) {
    color: #93c5fd;
    text-decoration-color: #60a5fa;
  }
  
  :global(.dark) .markdown-content :global(.table-wrapper) {
    border-color: #4b5563;
  }
  
  :global(.dark) .markdown-content :global(.custom-table th) {
    background: #374151;
    border-color: #4b5563;
  }
  
  :global(.dark) .markdown-content :global(.custom-table td) {
    border-color: #374151;
  }
  
  :global(.dark) .markdown-content :global(.custom-table tbody tr:hover) {
    background: #374151;
  }
  
  :global(.dark) .markdown-content :global(hr) {
    background: linear-gradient(to right, transparent, #4b5563, transparent);
  }
  
  :global(.dark) .markdown-content :global(h1),
  :global(.dark) .markdown-content :global(h2) {
    border-color: #4b5563;
  }
</style>