// Safe HTTP utilities - prevents "Response body already used" errors
export type JsonResult<T = any> = 
  | { ok: true; data: T } 
  | { ok: false; status: number; text: string };

/**
 * Safe JSON fetch - reads response body exactly once
 * Returns result object instead of throwing
 */
export async function fetchJSON<T = any>(
  input: RequestInfo, 
  init?: RequestInit
): Promise<JsonResult<T>> {
  try {
    const response = await fetch(input, init);
    
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
    const data = await response.json() as T;
    return { 
      ok: true, 
      data 
    };
  } catch (error: any) {
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
export function redirectToLogin(next?: string) {
  const returnPath = next || window.location.pathname + window.location.search;
  const encodedNext = encodeURIComponent(returnPath);
  window.location.href = `/login?next=${encodedNext}`;
}
