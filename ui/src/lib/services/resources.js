/**
 * Resource management API service
 */

const API_BASE = 'http://localhost:8000';

/**
 * List all resources with optional filtering
 */
export async function listResources(options = {}) {
  const params = new URLSearchParams();
  if (options.resourceType) params.append('resource_type', options.resourceType);
  if (options.limit) params.append('limit', options.limit);
  if (options.offset) params.append('offset', options.offset);
  
  const url = `${API_BASE}/resources${params.toString() ? '?' + params.toString() : ''}`;
  const response = await fetch(url, { credentials: 'include' });
  
  if (!response.ok) {
    throw new Error(`Failed to list resources: ${response.statusText}`);
  }
  
  return await response.json();
}

/**
 * Get a specific resource by URI
 */
export async function getResource(uri) {
  const response = await fetch(`${API_BASE}/resources/${encodeURIComponent(uri)}`, {
    credentials: 'include'
  });
  
  if (!response.ok) {
    throw new Error(`Failed to get resource: ${response.statusText}`);
  }
  
  return await response.json();
}

/**
 * Upload a file as a resource
 */
export async function uploadResource(file, name, description) {
  const formData = new FormData();
  formData.append('file', file);
  if (name) formData.append('name', name);
  formData.append('description', description);
  
  const response = await fetch(`${API_BASE}/resources/upload`, {
    method: 'POST',
    credentials: 'include',
    body: formData, // Don't set Content-Type header - browser will set it with boundary
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `Failed to upload file: ${response.statusText}`);
  }
  
  return await response.json();
}

/**
 * Create a new resource
 */
export async function createResource(resourceData) {
  const response = await fetch(`${API_BASE}/resources`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify(resourceData),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `Failed to create resource: ${response.statusText}`);
  }
  
  return await response.json();
}

/**
 * Update an existing resource
 */
export async function updateResource(uri, updates) {
  const response = await fetch(`${API_BASE}/resources/${encodeURIComponent(uri)}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify(updates),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `Failed to update resource: ${response.statusText}`);
  }
  
  return await response.json();
}

/**
 * Delete a resource
 */
export async function deleteResource(uri) {
  const response = await fetch(`${API_BASE}/resources/${encodeURIComponent(uri)}`, {
    method: 'DELETE',
    credentials: 'include',
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `Failed to delete resource: ${response.statusText}`);
  }
  
  return true;
}

/**
 * Search resources
 */
export async function searchResources(query, limit = 100) {
  const response = await fetch(`${API_BASE}/resources/search/${encodeURIComponent(query)}?limit=${limit}`, {
    credentials: 'include'
  });
  
  if (!response.ok) {
    throw new Error(`Failed to search resources: ${response.statusText}`);
  }
  
  return await response.json();
}

/**
 * Get resource count
 */
export async function getResourceCount(resourceType = null) {
  const params = resourceType ? `?resource_type=${resourceType}` : '';
  const response = await fetch(`${API_BASE}/resources/stats/count${params}`, {
    credentials: 'include'
  });
  
  if (!response.ok) {
    throw new Error(`Failed to get resource count: ${response.statusText}`);
  }
  
  return await response.json();
}
