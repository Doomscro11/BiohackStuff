// Admin API helpers for Phase VII
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

/**
 * Get system health metrics
 */
export async function getHealth() {
  const response = await fetch(`${BACKEND_URL}/api/admin/health`, {
    credentials: 'include'
  });
  
  if (!response.ok) {
    throw new Error('Failed to fetch health metrics');
  }
  
  return response.json();
}

/**
 * List all users with their tier and credits
 */
export async function listUsers() {
  const response = await fetch(`${BACKEND_URL}/api/admin/users`, {
    credentials: 'include'
  });
  
  if (!response.ok) {
    throw new Error('Failed to fetch users');
  }
  
  return response.json();
}

/**
 * Adjust user credits
 */
export async function adjustCredits(payload: {
  userId: string;
  delta: number;
  reason: string;
}) {
  const response = await fetch(`${BACKEND_URL}/api/admin/users/adjust-credits`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    credentials: 'include',
    body: JSON.stringify(payload)
  });
  
  if (!response.ok) {
    const error = await response.text();
    throw new Error(error || 'Failed to adjust credits');
  }
  
  return response.json();
}

/**
 * Set user tier
 */
export async function setTier(payload: {
  userId: string;
  tier: string;
}) {
  const response = await fetch(`${BACKEND_URL}/api/admin/users/set-tier`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    credentials: 'include',
    body: JSON.stringify(payload)
  });
  
  if (!response.ok) {
    const error = await response.text();
    throw new Error(error || 'Failed to set tier');
  }
  
  return response.json();
}
