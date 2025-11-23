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
    let mounted = true;
    
    checkAuth(null, mounted);
    
    // Cleanup function
    return () => {
      mounted = false;
    };
  }, []);

  const checkAuth = async (signal, mounted, retryCount = 0) => {
    console.log('[ProtectedRoute] Starting auth check...');
    
    // Small delay before first check to allow MainApp session to initialize
    if (retryCount === 0) {
      await new Promise(resolve => setTimeout(resolve, 200));
    }
    
    const result = await fetchJSON(`${BACKEND_URL}/api/auth/session`);
    
    console.log('[ProtectedRoute] Auth check result:', result);
    
    // Only update state if component is still mounted
    if (!mounted) {
      console.log('[ProtectedRoute] Component unmounted, skipping state update');
      return;
    }
    
    if (result.ok && result.data) {
      console.log('[ProtectedRoute] Auth check passed:', result.data);
      setIsAuthenticated(true);
      setUser(result.data);
      setLoading(false);
    } else {
      // If first attempt fails, retry once after a short delay
      if (retryCount === 0) {
        console.log('[ProtectedRoute] Initial auth check failed, retrying...');
        await new Promise(resolve => setTimeout(resolve, 500));
        return checkAuth(signal, mounted, retryCount + 1);
      }
      
      console.log('[ProtectedRoute] Auth check failed after retry:', result);
      setIsAuthenticated(false);
      setUser(null);
      setLoading(false);
    }
    
    console.log('[ProtectedRoute] Auth check completed, loading set to false');
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
