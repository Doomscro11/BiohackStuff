import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import App from './App';
import TestPage from './pages/TestPage';
import AdminGate from './components/admin/AdminGate';
import BillingPage from './pages/BillingPage';
import AnalyticsPage from './pages/AnalyticsPage';
import PatentPulsePage from './pages/PatentPulsePage';
import SharePage from './pages/partner/SharePage';
import CreditBadge from './components/CreditBadge';
import { Shield, CreditCard, BarChart3, FileText } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { fetchSession } from './lib/session';

function MainApp() {
  // Bootstrap: fetch session on app load
  useEffect(() => {
    fetchSession().catch(() => {
      // User not authenticated - this is fine
    });
  }, []);

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
              <CreditBadge />
              <Link to="/billing">
                <Button variant="ghost" size="sm" className="flex items-center gap-2">
                  <CreditCard className="h-4 w-4" />
                  Billing & Credits
                </Button>
              </Link>
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
            </div>
          </div>
        </nav>

        {/* Routes */}
        <Routes>
          <Route path="/" element={<App />} />
          <Route path="/test" element={<TestPage />} />
          <Route path="/billing" element={<BillingPage />} />
          <Route path="/admin" element={<AdminGate />} />
          <Route path="/admin/analytics" element={<AnalyticsPage />} />
          <Route path="/admin/patentpulse" element={<PatentPulsePage />} />
          <Route path="/share/:token" element={<SharePage />} />
        </Routes>
      </div>
    </Router>
  );
}

export default MainApp;
