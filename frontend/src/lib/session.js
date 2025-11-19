// Session management utilities for Peptimancer
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export interface SessionData {
  email;
  role;
  tier;
  credits;
}

/**
 * Fetch current session data (user info, tier, credits)
 * Sets window.__USER_TIER__ for global access
 */
export async function fetchSession(): Promise<SessionData | null> {
  try {
    const response = await fetch(`${BACKEND_URL}/api/auth/session`, {
      credentials: 'include'
    });

    if (!response.ok) {
      // User not authenticated - this is expected
      return null;
    }

    const session: SessionData = await response.json();
    
    // Expose tier globally for frontend components
    (window).__USER_TIER__ = session.tier || 'basic';
    
    return session;
  } catch (error) {
    // Silently handle errors - expected when not authenticated
    console.debug('fetchSession: user not authenticated');
    return null;
  }
}
