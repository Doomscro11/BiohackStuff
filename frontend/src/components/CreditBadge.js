// Credit Balance Indicator
import React, { useState, useEffect } from 'react';
import { Coins } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export default function CreditBadge() {
  const [credits, setCredits] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchCredits = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/billing/state`, {
        credentials: 'include'
      });
      
      if (response.ok) {
        const data = await response.json();
        setCredits(data.credits);
      }
    } catch (err) {
      // Silently fail - user might not be authenticated
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCredits();
    
    // Refresh every 30 seconds
    const interval = setInterval(fetchCredits, 30000);
    
    // Listen for credit updates (custom event)
    const handleCreditUpdate = () => fetchCredits();
    window.addEventListener('creditUpdate', handleCreditUpdate);
    
    return () => {
      clearInterval(interval);
      window.removeEventListener('creditUpdate', handleCreditUpdate);
    };
  }, []);

  if (loading || credits === null) {
    return null;
  }

  const getColorClass = () => {
    if (credits === 0) return 'bg-red-100 text-red-700 hover:bg-red-200';
    if (credits < 10) return 'bg-amber-100 text-amber-700 hover:bg-amber-200';
    return 'bg-green-100 text-green-700 hover:bg-green-200';
  };

  return (
    <div className="relative group">
      <Badge className={`${getColorClass()} flex items-center gap-1 cursor-pointer transition-colors px-3 py-1`}>
        <Coins className="h-4 w-4" />
        <span className="font-semibold">{credits}</span>
      </Badge>
      
      {/* Tooltip */}
      <div className="absolute right-0 mt-2 w-48 p-2 bg-gray-900 text-white text-xs rounded shadow-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50">
        <div className="font-semibold mb-1">Credit Balance</div>
        <div>{credits} credits available</div>
        {credits < 10 && (
          <div className="mt-1 text-amber-300">
            Running low! Consider purchasing more.
          </div>
        )}
      </div>
    </div>
  );
}

// Helper to trigger credit refresh from other components
export function triggerCreditUpdate() {
  window.dispatchEvent(new Event('creditUpdate'));
}
