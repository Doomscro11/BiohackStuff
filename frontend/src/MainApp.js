import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import App from './App';
import AdminGate from './components/admin/AdminGate.tsx';
import BillingPage from './pages/BillingPage';
import { Shield, CreditCard } from 'lucide-react';
import { Button } from '@/components/ui/button';

function MainApp() {
  return (
    <Router>
      <div className="min-h-screen">
        {/* Global Navigation */}
        <nav className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
          <div className="w-full mx-auto px-4 py-3 flex items-center justify-between">
            <Link to="/" className="flex items-center gap-2 text-lg font-semibold">
              🧬 Peptimancer
            </Link>
            <div className="flex items-center gap-2">
              <Link to="/billing">
                <Button variant="ghost" size="sm" className="flex items-center gap-2">
                  <CreditCard className="h-4 w-4" />
                  Billing & Credits
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
          <Route path="/billing" element={<BillingPage />} />
          <Route path="/admin" element={<AdminGate />} />
        </Routes>
      </div>
    </Router>
  );
}

export default MainApp;
