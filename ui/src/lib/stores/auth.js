/**
 * Authentication store
 * Manages user authentication state across the application
 */

import { writable } from 'svelte/store';
import { goto } from '$app/navigation';
import * as authService from '$lib/services/auth';
import { conversations } from './conversations';

// Create a writable store for the current user
function createAuthStore() {
  const { subscribe, set, update } = writable({
    user: null,
    loading: true,
    error: null
  });

  return {
    subscribe,
    
    /**
     * Initialize auth state by checking current user
     */
    init: async () => {
      try {
        update(state => ({ ...state, loading: true, error: null }));
        const user = await authService.getCurrentUser();
        set({ user, loading: false, error: null });
        return user;
      } catch (error) {
        set({ user: null, loading: false, error: error.message });
        return null;
      }
    },
    
    /**
     * Login user
     */
    login: async (username, password) => {
      try {
        update(state => ({ ...state, loading: true, error: null }));
        const response = await authService.login(username, password);
        const user = response.user;
        set({ user, loading: false, error: null });
        return user;
      } catch (error) {
        set({ user: null, loading: false, error: error.message });
        throw error;
      }
    },
    
    /**
     * Register new user
     */
    register: async (username, email, password, fullName = null) => {
      try {
        update(state => ({ ...state, loading: true, error: null }));
        const user = await authService.register(username, email, password, fullName);
        // After registration, user needs to login
        set({ user: null, loading: false, error: null });
        return user;
      } catch (error) {
        set({ user: null, loading: false, error: error.message });
        throw error;
      }
    },
    
    /**
     * Logout user
     */
    logout: async () => {
      try {
        // Clear user state first to prevent 401 errors
        set({ user: null, loading: false, error: null });
        // Clear conversations to prevent showing stale data
        conversations.set([]);
        // Then logout on backend (may fail with 401, that's ok)
        try {
          await authService.logout();
        } catch (e) {
          // Ignore 401 errors during logout
        }
        goto('/login');
      } catch (error) {
        console.error('Logout error:', error);
        // Force logout on frontend even if backend fails
        set({ user: null, loading: false, error: null });
        conversations.set([]);
        goto('/login');
      }
    },
    
    /**
     * Check if user is authenticated
     */
    isAuthenticated: () => {
      let authenticated = false;
      subscribe(state => {
        authenticated = state.user !== null;
      })();
      return authenticated;
    },
    
    /**
     * Check if user is admin
     */
    isAdmin: () => {
      let isAdmin = false;
      subscribe(state => {
        isAdmin = state.user?.role === 'admin';
      })();
      return isAdmin;
    },
    
    /**
     * Require authentication (redirect to login if not authenticated)
     */
    requireAuth: async () => {
      let currentState;
      subscribe(state => {
        currentState = state;
      })();
      
      if (!currentState.user && !currentState.loading) {
        goto('/login');
        return false;
      }
      return true;
    },
    
    /**
     * Require admin (redirect if not admin)
     */
    requireAdmin: async () => {
      let currentState;
      subscribe(state => {
        currentState = state;
      })();
      
      if (!currentState.user) {
        goto('/login');
        return false;
      }
      
      if (currentState.user.role !== 'admin') {
        goto('/');
        return false;
      }
      
      return true;
    }
  };
}

export const auth = createAuthStore();
