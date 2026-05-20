// Admin 2FA Gate Helper
import { fetchJSON } from './http';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

/**
 * Check if user has valid 2FA session
 * Returns true only if admin2fa cookie is present and valid
 */
export async function isAdmin2FA(): Promise<boolean> {
  const result = await fetchJSON(`${BACKEND_URL}/api/admin/settings`, {
    method: 'GET'
  });
  
  // 200 only if 2FA cookie is present and valid
  return result.ok;
}
