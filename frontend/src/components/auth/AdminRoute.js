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
    const abortController = new AbortController();
    let mounted = true;
    
    checkAuth(abortController.signal, mounted);
    
    // Cleanup function
    return () => {
      mounted = false;
      abortController.abort();
    };
  }, []);

  const checkAuth = async (signal, mounted) => {
    const result = await fetchJSON(`${BACKEND_URL}/api/auth/session`, {
      ...(signal && { signal })
    });
    
    // Only update state if component is still mounted
    if (!mounted) return;
    
    if (result.ok && result.data) {
      setIsAuthenticated(true);
      setUser(result.data);
      setIsAdmin(result.data.role === 'admin');
    } else {
      setIsAuthenticated(false);
      setIsAdmin(false);
      setUser(null);
    }
    
    setLoading(false);
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
