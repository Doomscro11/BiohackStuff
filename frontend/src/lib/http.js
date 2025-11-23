// Safe HTTP utilities - prevents "Response body already used" errors

/**
 * Safe JSON fetch - reads response body exactly once
 * Returns result object instead of throwing
 * Always includes credentials by default
 * Supports AbortController for request cancellation (React StrictMode safe)
 */
export async function fetchJSON(input, init) {
  try {
    // Merge init with default credentials: 'include'
    const config = {
      credentials: 'include',
      ...init,
      // Support AbortController signal for request cancellation
      ...(init?.signal && { signal: init.signal })
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
    // Check if error is due to abort
    if (error.name === 'AbortError') {
      return {
        ok: false,
        status: 0,
        text: 'Request cancelled'
      };
    }
    
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
