// Safe HTTP utilities - prevents "Response body already used" errors

/**
 * Safe JSON fetch - reads response body exactly once
 * Returns result object instead of throwing
 * Always includes credentials by default
 */
export async function fetchJSON(input, init) {
  try {
    // Merge init with default credentials: 'include'
    const config = {
      credentials: 'include',
      ...init
    };
    
    const response = await fetch(input, config);
    
    if (!response.ok) {
      // Read text exactly once for errors
      const text = await response.text().catch(() => "");
      return { 
        ok: false, 
        status: response.status, 
        text 
      };
    }
    
    // Read JSON exactly once for success
    const data = await response.json();
    return { 
      ok: true, 
      data 
    };
  } catch (error) {
    return {
      ok: false,
      status: 0,
      text: error.message || "Network error"
    };
  }
}

/**
 * Redirect to login with return path
 */
export function redirectToLogin(next) {
  const returnPath = next || window.location.pathname + window.location.search;
  const encodedNext = encodeURIComponent(returnPath);
  window.location.href = `/admin?next=${encodedNext}`;
}
