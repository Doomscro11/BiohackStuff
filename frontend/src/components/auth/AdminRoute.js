import React, { useState, useEffect } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { fetchJSON } from '@/lib/http';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

/**
 * AdminRoute component
 * Wraps routes that require admin role
 * Redirects to /login if not authenticated
 * Redirects to / if authenticated but not admin
 */
function AdminRoute({ children }) {
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);
  const [user, setUser] = useState(null);
  const location = useLocation();

  useEffect(() => {
    let mounted = true;
    
    checkAuth(mounted);
    
    // Cleanup function
    return () => {
      mounted = false;
    };
  }, []);

  const checkAuth = async (mounted, retryCount = 0) => {
    console.log('[AdminRoute] Starting auth check...', { retryCount });
    
    // Small delay before first check to allow MainApp session to initialize
    // This prevents race condition where AdminRoute checks before MainApp completes
    if (retryCount === 0) {
      await new Promise(resolve => setTimeout(resolve, 300));
    }
    
    // DO NOT use AbortController signal here - it causes premature request cancellation
    // Follow ProtectedRoute pattern for consistent behavior
    const result = await fetchJSON(`${BACKEND_URL}/api/auth/session`);
    
    console.log('[AdminRoute] Auth check result:', result);
    
    // Only update state if component is still mounted
    if (!mounted) {
      console.log('[AdminRoute] Component unmounted, skipping state update');
      return;
    }
    
    if (result.ok && result.data) {
      console.log('[AdminRoute] Auth check passed:', { 
        email: result.data.email, 
        role: result.data.role,
        isAdmin: result.data.role === 'admin'
      });
      setIsAuthenticated(true);
      setUser(result.data);
      setIsAdmin(result.data.role === 'admin');
      setLoading(false);
    } else {
      // If first attempt fails and we just logged in, retry once after a short delay
      // This handles the race condition between login redirect and session initialization
      if (retryCount === 0) {
        console.log('[AdminRoute] Initial auth check failed, retrying...');
        await new Promise(resolve => setTimeout(resolve, 500));
        return checkAuth(mounted, retryCount + 1);
      }
      
      console.log('[AdminRoute] Auth check failed after retry:', result);
      // After retry, if still no session, user is not authenticated
      setIsAuthenticated(false);
      setIsAdmin(false);
      setUser(null);
      setLoading(false);
    }
  };

  if (loading) {
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
    return <Navigate to={`/login?returnTo=${encodeURIComponent(returnTo)}`} replace />;
  }

  if (!isAdmin) {
    // Authenticated but not admin - redirect to home with error message
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="max-w-md w-full p-8 bg-white dark:bg-gray-800 rounded-lg shadow-lg text-center">
          <div className="text-5xl mb-4">🚫</div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
            Access Denied
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            You don't have permission to access this page. Admin access is required.
          </p>
          <a
            href="/"
            className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Go to Home
          </a>
        </div>
      </div>
    );
  }

  // Render children with user context
  return <>{children}</>;
}

export default AdminRoute;
