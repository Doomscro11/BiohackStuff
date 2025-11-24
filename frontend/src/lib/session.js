// Session management utilities for Peptimancer - now uses SessionManager to prevent concurrent requests
import { sessionManager } from './sessionManager';

/**
 * Fetch current session data (user info, tier, credits)
 * Sets window.__USER_TIER__ for global access
 * 
 * IMPORTANT: This now uses SessionManager to prevent concurrent requests
 * that were causing "Response body is already used" errors
 */
export async function fetchSession(forceRefresh = false): Promise<SessionData | null> {
  const result = await sessionManager.getSession(forceRefresh);

  if (!result.ok || !result.data) {
    // User not authenticated - this is expected
    console.debug('fetchSession: user not authenticated');
    return null;
  }

  const session: SessionData = result.data;
  
  // Expose tier globally for frontend components
  (window).__USER_TIER__ = session.tier || 'basic';
  
  return session;
}

/**
 * Clear session cache (call after logout)
 */
export function clearSessionCache() {
  sessionManager.clearSession();
}

/**
 * Update session cache (call after successful login)
 */
export function updateSessionCache(sessionData) {
  sessionManager.updateSession(sessionData);
}
