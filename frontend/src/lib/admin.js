// Admin API helpers for Phase VII
import { fetchJSON } from './http';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

/**
 * Get system health metrics
 */
export async function getHealth() {
  const result = await fetchJSON(`${BACKEND_URL}/api/admin/health`, {
    credentials: 'include'
  });
  
  if (!result.ok) {
    throw new Error(result.text || 'Failed to fetch health metrics');
  }
  
  return result.data;
}

/**
 * List all users with their tier and credits
 */
export async function listUsers() {
  const result = await fetchJSON(`${BACKEND_URL}/api/admin/users`, {
    credentials: 'include'
  });
  
  if (!result.ok) {
    throw new Error(result.text || 'Failed to fetch users');
  }
  
  return result.data;
}

/**
 * Adjust user credits
 */
export async function adjustCredits(payload) {
  const result = await fetchJSON(`${BACKEND_URL}/api/admin/users/adjust-credits`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    credentials: 'include',
    body: JSON.stringify(payload)
  });
  
  if (!result.ok) {
    throw new Error(result.text || 'Failed to adjust credits');
  }
  
  return result.data;
}

/**
 * Set user tier
 */
export async function setTier(payload) {
  const result = await fetchJSON(`${BACKEND_URL}/api/admin/users/set-tier`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    credentials: 'include',
    body: JSON.stringify(payload)
  });
  
  if (!result.ok) {
    throw new Error(result.text || 'Failed to set tier');
  }
  
  return result.data;
}
