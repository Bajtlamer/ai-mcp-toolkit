/**
 * Error handling utilities for consistent error messages
 */

export class AppError extends Error {
  constructor(message, code = 'UNKNOWN_ERROR', details = null) {
    super(message);
    this.name = 'AppError';
    this.code = code;
    this.details = details;
  }
}

/**
 * Parse error from API response
 */
export function parseApiError(error) {
  if (error instanceof AppError) {
    return error.message;
  }
  
  if (error.response) {
    // Server responded with error
    const status = error.response.status;
    const data = error.response.data;
    
    if (status === 401) {
      return 'Authentication required. Please log in again.';
    }
    
    if (status === 403) {
      return 'You do not have permission to perform this action.';
    }
    
    if (status === 404) {
      return 'The requested resource was not found.';
    }
    
    if (status === 429) {
      return 'Too many requests. Please try again later.';
    }
    
    if (status >= 500) {
      return 'Server error. Please try again later.';
    }
    
    // Try to get error message from response
    if (data?.error) {
      return data.error;
    }
    
    if (data?.message) {
      return data.message;
    }
    
    return `Request failed with status ${status}`;
  }
  
  if (error.request) {
    // Request made but no response
    return 'Unable to connect to server. Please check your connection.';
  }
  
  // Something else went wrong
  return error.message || 'An unexpected error occurred';
}

/**
 * Handle async operations with consistent error handling
 */
export async function handleAsync(fn, errorCallback = null) {
  try {
    return await fn();
  } catch (error) {
    const message = parseApiError(error);
    console.error('Error:', error);
    
    if (errorCallback) {
      errorCallback(message, error);
    }
    
    throw new AppError(message, error.code, error);
  }
}

/**
 * Create a user-friendly error message
 */
export function formatError(error, context = '') {
  const message = parseApiError(error);
  return context ? `${context}: ${message}` : message;
}

/**
 * Check if error is a network error
 */
export function isNetworkError(error) {
  return !error.response && error.request;
}

/**
 * Check if error is an authentication error
 */
export function isAuthError(error) {
  return error.response?.status === 401 || error.response?.status === 403;
}

/**
 * Retry function with exponential backoff
 */
export async function retryWithBackoff(fn, maxRetries = 3, baseDelay = 1000) {
  let lastError;
  
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;
      
      // Don't retry on auth errors or 4xx errors
      if (isAuthError(error) || (error.response?.status >= 400 && error.response?.status < 500)) {
        throw error;
      }
      
      // Wait before retrying
      if (i < maxRetries - 1) {
        const delay = baseDelay * Math.pow(2, i);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }
  
  throw lastError;
}
