/**
 * Session Manager - Prevents concurrent session requests
 * Solves "Response body is already used" errors by deduplicating session checks
 */

import { fetchJSON } from './http';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

class SessionManager {
  constructor() {
    this.sessionCache = null;
    this.pendingRequest = null;
    this.cacheExpiry = null;
    this.CACHE_DURATION = 5000; // 5 seconds cache
  }

  /**
   * Get current session (with deduplication)
   * If a request is already in flight, return that promise
   * If cache is fresh, return cached value
   */
  async getSession(forceRefresh = false) {
    // Return cached session if still fresh
    if (!forceRefresh && this.sessionCache && this.cacheExpiry && Date.now() < this.cacheExpiry) {
      console.log('[SessionManager] Returning cached session');
      return this.sessionCache;
    }

    // If a request is already pending, return that promise
    if (this.pendingRequest) {
      console.log('[SessionManager] Request already in flight, reusing promise');
      return this.pendingRequest;
    }

    // Start new request
    console.log('[SessionManager] Starting new session request');
    this.pendingRequest = this.fetchSession();

    try {
      const result = await this.pendingRequest;
      
      // Cache successful result
      if (result.ok && result.data) {
        this.sessionCache = result;
        this.cacheExpiry = Date.now() + this.CACHE_DURATION;
      } else {
        // Don't cache failures
        this.sessionCache = null;
        this.cacheExpiry = null;
      }

      return result;
    } finally {
      // Clear pending request
      this.pendingRequest = null;
    }
  }

  async fetchSession() {
    const result = await fetchJSON(`${BACKEND_URL}/api/auth/session`, {
      credentials: 'include'
    });
    return result;
  }

  /**
   * Clear cached session (e.g., after logout)
   */
  clearSession() {
    this.sessionCache = null;
    this.cacheExpiry = null;
    this.pendingRequest = null;
  }

  /**
   * Update cached session (e.g., after successful login)
   */
  updateSession(sessionData) {
    this.sessionCache = { ok: true, data: sessionData };
    this.cacheExpiry = Date.now() + this.CACHE_DURATION;
  }
}

// Export singleton instance
export const sessionManager = new SessionManager();

// Convenience function for backward compatibility
export async function fetchSession(forceRefresh = false) {
  const result = await sessionManager.getSession(forceRefresh);
  return result.ok ? result.data : null;
}
