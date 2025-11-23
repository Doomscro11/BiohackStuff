import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import App from './apps/peptimancer/pages/HomePage';
import TestPage from './pages/TestPage';
import AdminPage from './apps/admin/pages/AdminPage';
import BillingPage from './apps/account/pages/BillingPage';
import AnalyticsPage from './apps/admin/pages/AnalyticsPage';
import PatentPulsePage from './apps/patentpulse/pages/PatentPulsePage';
import SharePage from './apps/patentpulse/pages/SharePage';
import LoginPage from './apps/auth/pages/LoginPage';
import CreditBadge from './components/CreditBadge';
import RoleBadge from './components/auth/RoleBadge';
import ProtectedRoute from './components/auth/ProtectedRoute';
import AdminRoute from './components/auth/AdminRoute';
import { Shield, CreditCard, BarChart3, FileText, LogOut } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { fetchSession } from './lib/session';
import { fetchJSON } from './lib/http';
import { canAccessAdmin } from './lib/roles';

function MainApp() {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  // Bootstrap: fetch session on app load
  // Note: No AbortController here - MainApp is top-level and should complete its session fetch
  useEffect(() => {
    let mounted = true;
    
    const loadSession = async () => {
      try {
        const session = await fetchSession();
        if (mounted) {
          console.log('[MainApp] Session loaded:', session);
          if (session) {
            setUser(session);
          } else {
            setUser(null);
          }
        }
      } catch (err) {
        if (mounted) {
          console.log('[MainApp] Session load failed:', err);
          setUser(null);
        }
      } finally {
        if (mounted) {
          setIsLoading(false);
        }
      }
    };
    
    loadSession();
    
    // Cleanup function - just mark as unmounted
    return () => {
      mounted = false;
    };
  }, []);

  const handleLogout = async () => {
    const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
    const result = await fetchJSON(`${BACKEND_URL}/api/auth/logout`, { method: 'POST' });
    if (result.ok) {
      setUser(null);
      window.location.href = '/login';
    } else {
      console.error('Logout failed:', result);
    }
  };

  return (
    <Router>
      <div className="min-h-screen">
        {/* Global Navigation */}
        <nav className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
          <div className="w-full mx-auto px-4 py-3 flex items-center justify-between">
            <Link to="/" className="flex items-center gap-2 text-lg font-semibold">
              🧬 Peptimancer
            </Link>
            <div className="flex items-center gap-3">
              {!isLoading && user && (
                <>
                  {/* Role Badge - shows current user role */}
                  <RoleBadge user={user} size="sm" />
                  
                  <CreditBadge />
                  
                  {/* Standard User Navigation */}
                  <Link to="/billing">
                    <Button variant="ghost" size="sm" className="flex items-center gap-2">
                      <CreditCard className="h-4 w-4" />
                      Billing & Credits
                    </Button>
                  </Link>
                  
                  {/* Admin-Only Navigation - hidden for non-admins */}
                  {canAccessAdmin(user) && (
                    <>
                      <Link to="/admin/analytics">
                        <Button variant="ghost" size="sm" className="flex items-center gap-2">
                          <BarChart3 className="h-4 w-4" />
                          Analytics
                        </Button>
                      </Link>
                      <Link to="/admin/patentpulse">
                        <Button variant="ghost" size="sm" className="flex items-center gap-2">
                          <FileText className="h-4 w-4" />
                          PatentPulse
                        </Button>
                      </Link>
                      <Link to="/admin">
                        <Button variant="ghost" size="sm" className="flex items-center gap-2">
                          <Shield className="h-4 w-4" />
                          Admin
                        </Button>
                      </Link>
                    </>
                  )}
                  
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleLogout}
                    className="flex items-center gap-2"
                  >
                    <LogOut className="h-4 w-4" />
                    Logout
                  </Button>
                </>
              )}
              {!isLoading && !user && (
                <Link to="/login">
                  <Button size="sm">Sign In</Button>
                </Link>
              )}
            </div>
          </div>
        </nav>

        {/* Routes */}
        <Routes>
          {/* Public Routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/share/:token" element={<SharePage />} />
          
          {/* Protected Routes - Any authenticated user */}
          <Route path="/" element={<ProtectedRoute><App /></ProtectedRoute>} />
          <Route path="/test" element={<ProtectedRoute><TestPage /></ProtectedRoute>} />
          <Route path="/billing" element={<ProtectedRoute><BillingPage /></ProtectedRoute>} />
          
          {/* Admin-Only Routes - Require admin role */}
          <Route path="/admin" element={<AdminRoute><AdminPage /></AdminRoute>} />
          <Route path="/admin/analytics" element={<AdminRoute><AnalyticsPage /></AdminRoute>} />
          <Route path="/admin/patentpulse" element={<AdminRoute><PatentPulsePage /></AdminRoute>} />
        </Routes>
      </div>
    </Router>
  );
}

export default MainApp;
