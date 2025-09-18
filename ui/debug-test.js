// Simple test to see what marked is generating
const { marked } = require('marked');

const testMarkdown = `Here's a code block:

\`\`\`bash
npm install -g @angular/cli
\`\`\`

And inline code: \`console.log("test")\``;

console.log('=== INPUT ===');
console.log(testMarkdown);

console.log('\n=== DEFAULT MARKED OUTPUT ===');
console.log(marked(testMarkdown));

// Test with custom renderer
const renderer = new marked.Renderer();
renderer.code = function(code, language) {
  const lang = language || 'plaintext';
  return `<div class="code-block">
    <div class="code-header">
      <span class="code-lang">${lang}</span>
      <button class="copy-btn">Copy</button>
    </div>
    <pre><code data-lang="${lang}">${code}</code></pre>
  </div>`;
};

marked.use({ renderer });

console.log('\n=== CUSTOM RENDERER OUTPUT ===');
console.log(marked(testMarkdown));