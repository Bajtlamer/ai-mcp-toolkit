/**
 * Authentication API service
 */

const API_BASE = 'http://localhost:8000';

/**
 * Register a new user
 */
export async function register(username, email, password, fullName = null) {
  const response = await fetch(`${API_BASE}/auth/register`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include', // Important: include cookies
    body: JSON.stringify({
      username,
      email,
      password,
      full_name: fullName
    }),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `Registration failed: ${response.statusText}`);
  }
  
  return await response.json();
}

/**
 * Login user
 */
export async function login(username, password) {
  const response = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include', // Important: include cookies
    body: JSON.stringify({
      username,
      password,
    }),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `Login failed: ${response.statusText}`);
  }
  
  return await response.json();
}

/**
 * Logout user
 */
export async function logout() {
  const response = await fetch(`${API_BASE}/auth/logout`, {
    method: 'POST',
    credentials: 'include', // Important: include cookies
  });
  
  if (!response.ok) {
    throw new Error(`Logout failed: ${response.statusText}`);
  }
  
  return await response.json();
}

/**
 * Get current user information
 */
export async function getCurrentUser() {
  const response = await fetch(`${API_BASE}/auth/me`, {
    credentials: 'include', // Important: include cookies
  });
  
  if (!response.ok) {
    if (response.status === 401) {
      return null; // Not authenticated
    }
    throw new Error(`Failed to get current user: ${response.statusText}`);
  }
  
  return await response.json();
}

/**
 * Check if user is authenticated
 */
export async function isAuthenticated() {
  try {
    const user = await getCurrentUser();
    return user !== null;
  } catch (error) {
    return false;
  }
}

/**
 * Check if current user is admin
 */
export async function isAdmin() {
  try {
    const user = await getCurrentUser();
    return user && user.role === 'admin';
  } catch (error) {
    return false;
  }
}
