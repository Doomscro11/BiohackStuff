/**
 * Error normalization utilities
 * Converts various error formats to human-readable strings safe for React rendering
 */

/**
 * Normalize error to a safe string for display
 * Handles Pydantic validation errors, axios errors, and plain strings
 * @param {any} err - Error object, string, or array
 * @returns {string} Human-readable error message
 */
export function normalizeError(err) {
  // Handle null/undefined
  if (!err) return "An unknown error occurred";

  // Handle string errors
  if (typeof err === "string") return err;

  // Handle Pydantic validation error array (FastAPI format)
  if (Array.isArray(err)) {
    return err.map(e => {
      if (e.msg) return e.msg;
      if (e.message) return e.message;
      return JSON.stringify(e);
    }).join("; ");
  }

  // Handle axios error response
  if (err.response?.data) {
    const data = err.response.data;
    
    // Check if detail is an array (Pydantic validation errors)
    if (Array.isArray(data.detail)) {
      return data.detail.map(e => {
        const field = e.loc ? e.loc.join('.') : 'field';
        const msg = e.msg || e.message || 'validation error';
        return `${field}: ${msg}`;
      }).join("; ");
    }
    
    // Check if detail is a string
    if (typeof data.detail === "string") {
      return data.detail;
    }
    
    // Check if detail is an object
    if (typeof data.detail === "object") {
      return data.detail.message || data.detail.msg || JSON.stringify(data.detail);
    }
    
    // Fallback to error or message
    if (data.error) return data.error;
    if (data.message) return data.message;
  }

  // Handle error with message property
  if (err.message) return err.message;
  if (err.msg) return err.msg;

  // Handle error with error property
  if (err.error) {
    if (typeof err.error === "string") return err.error;
    return normalizeError(err.error);
  }

  // Last resort: try to stringify
  try {
    return JSON.stringify(err);
  } catch {
    return "An unexpected error occurred";
  }
}

/**
 * Extract user-friendly error message from axios error
 * @param {any} error - Axios error object
 * @param {string} fallback - Fallback message if extraction fails
 * @returns {string} User-friendly error message
 */
export function getAxiosErrorMessage(error, fallback = "An error occurred") {
  if (!error) return fallback;
  
  // Handle axios error
  if (error.response) {
    return normalizeError(error.response.data?.detail || error.response.data);
  }
  
  // Handle network error
  if (error.request) {
    return "Network error. Please check your connection.";
  }
  
  // Handle other errors
  return normalizeError(error);
}

/**
 * Check if an error is a validation error
 * @param {any} error - Error to check
 * @returns {boolean} True if validation error
 */
export function isValidationError(error) {
  if (!error) return false;
  
  // Check for Pydantic validation error structure
  if (Array.isArray(error)) {
    return error.some(e => e.type && e.loc);
  }
  
  if (error.response?.data?.detail) {
    const detail = error.response.data.detail;
    return Array.isArray(detail) && detail.some(e => e.type && e.loc);
  }
  
  return false;
}
