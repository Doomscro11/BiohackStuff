/**
 * Admin Page - Simple admin panel with Partner Shares management
 */

import React from 'react';
import PartnerSharesAdmin from '@/components/admin/PartnerShares';

const AdminPage = () => {
  return (
    <div style={{ padding: '2rem', maxWidth: '1400px', margin: '0 auto' }}>
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '2rem', fontWeight: 'bold', marginBottom: '0.5rem' }}>
          Admin Panel
        </h1>
        <p style={{ color: '#666' }}>
          Manage partner shares and access analytics
        </p>
      </div>
      
      <PartnerSharesAdmin />
    </div>
  );
};

export default AdminPage;
