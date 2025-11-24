/**
 * Admin Page - Admin panel for Feature Flags and system management
 * 
 * NOTE: Partner Shares feature has been deprecated and removed.
 * TODO: Future external sharing/export feature will be reintroduced as a dedicated export system.
 */

import React from 'react';
import FeatureFlagsPanel from '@/components/admin/FeatureFlagsPanel';

const AdminPage = () => {
  return (
    <div style={{ padding: '2rem', maxWidth: '1400px', margin: '0 auto' }}>
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '2rem', fontWeight: 'bold', marginBottom: '0.5rem' }}>
          Admin Panel
        </h1>
        <p style={{ color: '#666' }}>
          Manage feature flags and system settings
        </p>
      </div>

      {/* Feature Flags Panel */}
      <FeatureFlagsPanel />
    </div>
  );
};

export default AdminPage;
