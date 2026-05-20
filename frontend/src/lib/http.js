// Safe HTTP utilities - prevents "Response body already used" errors

/**
 * Safe JSON fetch - reads response body exactly once using text()
 * Returns result object instead of throwing
 * Always includes credentials by default
 * Supports AbortController for request cancellation (React StrictMode safe)
 * 
 * CRITICAL: Uses response.text() instead of response.json() to prevent
 * "Failed to execute 'clone' on 'Response': Response body is already used" errors
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
    
    // CRITICAL: Read body as text EXACTLY ONCE
    // This prevents "Response body is already used" errors that occur when
    // multiple .json() calls are made or when error handlers try to re-read the body
    let text = "";
    try {
      text = await response.text();
    } catch (textError) {
      // If response.text() fails (e.g., body already consumed), log and continue
      console.error('[fetchJSON] Failed to read response body:', textError.message);
      console.error('[fetchJSON] URL:', input, 'Status:', response.status);
      // Return a descriptive error instead of the cryptic clone message
      return {
        ok: false,
        status: response.status || 0,
        text: 'Failed to read server response. The response body may have been consumed prematurely.',
        data: null
      };
    }
    
    // Parse JSON from text (safe, doesn't touch Response object)
    let data = null;
    if (text) {
      try {
        data = JSON.parse(text);
      } catch (parseError) {
        // Non-JSON response - keep as raw text
        console.warn('[fetchJSON] Non-JSON response:', text.substring(0, 100));
        data = { raw: text };
      }
    }
    
    if (!response.ok) {
      return { 
        ok: false, 
        status: response.status, 
        text: typeof data === 'string' ? data : (data?.message || data?.detail || text || 'Request failed'),
        data
      };
    }
    
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
