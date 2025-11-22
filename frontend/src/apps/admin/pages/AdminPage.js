/**
 * Admin Page - Admin panel with Partner Shares and Feature Flags management
 */

import React, { useState } from 'react';
import PartnerSharesAdmin from '@/components/admin/PartnerShares';
import FeatureFlagsPanel from '@/components/admin/FeatureFlagsPanel';

const AdminPage = () => {
  const [activeSection, setActiveSection] = useState('partner-shares');

  return (
    <div style={{ padding: '2rem', maxWidth: '1400px', margin: '0 auto' }}>
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '2rem', fontWeight: 'bold', marginBottom: '0.5rem' }}>
          Admin Panel
        </h1>
        <p style={{ color: '#666' }}>
          Manage partner shares, feature flags, and access analytics
        </p>
      </div>

      {/* Section Navigation */}
      <div style={{ 
        display: 'flex', 
        gap: '1rem', 
        marginBottom: '2rem', 
        borderBottom: '1px solid #e5e7eb',
        paddingBottom: '0.5rem'
      }}>
        <button
          onClick={() => setActiveSection('partner-shares')}
          style={{
            padding: '0.5rem 1rem',
            border: 'none',
            background: activeSection === 'partner-shares' ? '#3b82f6' : 'transparent',
            color: activeSection === 'partner-shares' ? 'white' : '#6b7280',
            borderRadius: '6px',
            cursor: 'pointer',
            fontWeight: activeSection === 'partner-shares' ? '600' : '400',
            transition: 'all 0.2s'
          }}
        >
          Partner Shares
        </button>
        <button
          onClick={() => setActiveSection('feature-flags')}
          style={{
            padding: '0.5rem 1rem',
            border: 'none',
            background: activeSection === 'feature-flags' ? '#3b82f6' : 'transparent',
            color: activeSection === 'feature-flags' ? 'white' : '#6b7280',
            borderRadius: '6px',
            cursor: 'pointer',
            fontWeight: activeSection === 'feature-flags' ? '600' : '400',
            transition: 'all 0.2s'
          }}
        >
          Feature Flags
        </button>
      </div>

      {/* Content */}
      {activeSection === 'partner-shares' && <PartnerSharesAdmin />}
      {activeSection === 'feature-flags' && <FeatureFlagsPanel />}
    </div>
  );
};

export default AdminPage;
