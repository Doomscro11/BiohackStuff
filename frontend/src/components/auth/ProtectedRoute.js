import React, { useState, useEffect } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { fetchJSON } from '@/lib/http';

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
    try {
      const session = await fetchJSON('/api/auth/session');
      setIsAuthenticated(true);
      setUser(session);
    } catch (err) {
      setIsAuthenticated(false);
      setUser(null);
    } finally {
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

  // Render children with user context
  return <>{children}</>;
}

export default ProtectedRoute;
