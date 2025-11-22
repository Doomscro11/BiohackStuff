// Session management utilities for Peptimancer
import { fetchJSON } from './http';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

/**
 * Fetch current session data (user info, tier, credits)
 * Sets window.__USER_TIER__ for global access
 */
export async function fetchSession(): Promise<SessionData | null> {
  const result = await fetchJSON(`${BACKEND_URL}/api/auth/session`);

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
