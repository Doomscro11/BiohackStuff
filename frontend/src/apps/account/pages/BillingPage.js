// Billing Page - User subscription and credit management
import React from 'react';
import BillingWidget from '@/components/billing/BillingWidget';

export default function BillingPage() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="w-full max-w-screen-2xl mx-auto px-4 py-8">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            Billing & Credits
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Manage your subscription, purchase credits, and view transaction history
          </p>
        </div>
        
        <BillingWidget />
      </div>
    </div>
  );
}
