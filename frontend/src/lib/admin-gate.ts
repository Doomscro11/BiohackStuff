// Admin 2FA Gate Helper
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

/**
 * Check if user has valid 2FA session
 * Returns true only if admin2fa cookie is present and valid
 */
export async function isAdmin2FA(): Promise<boolean> {
  try {
    const response = await fetch(`${BACKEND_URL}/api/admin/settings`, {
      method: 'GET',
      credentials: 'include'
    });
    
    // 200 only if 2FA cookie is present and valid
    return response.ok;
  } catch (err) {
    return false;
  }
}
