import React, { useState, useEffect } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { fetchJSON } from '@/lib/http';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

/**
 * ProtectedRoute component
 * Wraps routes that require authentication
 * Redirects to /login if user is not authenticated
 */
function ProtectedRoute({ children }) {
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const location = useLocation();

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    const result = await fetchJSON(`${BACKEND_URL}/api/auth/session`);
    
    if (result.ok && result.data) {
      console.log('[ProtectedRoute] Auth check passed:', result.data);
      setIsAuthenticated(true);
      setUser(result.data);
    } else {
      console.log('[ProtectedRoute] Auth check failed:', result);
      setIsAuthenticated(false);
      setUser(null);
    }
    
    setLoading(false);
  };

  if (loading) {
    console.log('[ProtectedRoute] Loading auth state...');
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    // Redirect to login with returnTo parameter
    const returnTo = location.pathname + location.search;
    console.log('[ProtectedRoute] Redirecting to login, returnTo:', returnTo);
    return <Navigate to={`/login?returnTo=${encodeURIComponent(returnTo)}`} replace />;
  }

  console.log('[ProtectedRoute] User authenticated, rendering children');

  // Render children with user context
  return <>{children}</>;
}

export default ProtectedRoute;
