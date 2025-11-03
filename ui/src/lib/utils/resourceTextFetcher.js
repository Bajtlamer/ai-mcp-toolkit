/**
 * Utility for fetching text content from resources, including automatic PDF extraction
 */

/**
 * Fetch text content from a resource, automatically extracting from PDFs if needed
 * @param {string} resourceUri - The resource URI
 * @param {Function} getResourceFn - The resourceAPI.getResource function
 * @returns {Promise<string>} - The extracted text content
 */
export async function fetchResourceText(resourceUri, getResourceFn) {
  const resource = await getResourceFn(resourceUri);
  console.log('DEBUG: Resource data:', resource);
  
  if (!resource) {
    throw new Error('Could not fetch resource');
  }
  
  // For PDF files with no extracted content, we need to extract it first
  if (resource.file_type === 'pdf' && (!resource.content || resource.content === null)) {
    // Download the PDF and extract text
    const downloadResponse = await fetch(`/api/resources/download/${resource.file_id}`);
    if (!downloadResponse.ok) {
      throw new Error('Failed to download PDF file');
    }
    
    // Convert to base64 for the PDF extraction tool
    const arrayBuffer = await downloadResponse.arrayBuffer();
    const bytes = new Uint8Array(arrayBuffer);
    const binaryString = bytes.reduce((acc, byte) => acc + String.fromCharCode(byte), '');
    const pdfContent = btoa(binaryString);
    
    // Extract text using the PDF extraction tool
    const extractResponse = await fetch('/api/tools/execute', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: 'extract_pdf_text',
        arguments: {
          pdf_content: pdfContent,
          page_range: 'all',
          include_metadata: false
        }
      })
    });
    
    const extractResult = await extractResponse.json();
    if (extractResult.success) {
      return extractResult.result;
    } else {
      throw new Error('Failed to extract text from PDF');
    }
  } else {
    // For non-PDF resources or PDFs with content already extracted
    if (resource.content && resource.content.trim()) {
      return resource.content;
    }
    
    // If content is empty but we have a file_id, try to download and extract
    if (resource.file_id && resource.file_type !== 'pdf') {
      console.log('DEBUG: Content is empty, attempting to download file:', resource.file_id);
      try {
        const downloadResponse = await fetch(`/api/resources/download/${resource.file_id}`);
        if (downloadResponse.ok) {
          const textContent = await downloadResponse.text();
          if (textContent && textContent.trim()) {
            return textContent;
          }
        }
      } catch (err) {
        console.error('DEBUG: Failed to download file:', err);
      }
    }
    
    throw new Error(`Resource does not contain text content. Resource type: ${resource.resource_type || 'unknown'}, MIME: ${resource.mime_type || 'unknown'}, has content: ${!!resource.content}`);
  }
}
