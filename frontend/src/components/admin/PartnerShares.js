/**
 * DEPRECATED: Partner Shares Admin Interface
 * 
 * This component has been deprecated and is no longer used in the application.
 * Partner Shares feature has been removed.
 * 
 * TODO: Future external sharing/export will be implemented as a separate
 * "Export to PDF / Share Report" feature with a cleaner architecture.
 */

import React from 'react';

const PartnerSharesAdmin = () => {
  return (
    <div style={{ padding: '2rem', maxWidth: '800px', margin: '0 auto' }}>
      <div style={{ 
        background: '#fef3c7',
        border: '1px solid #f59e0b',
        borderRadius: '8px',
        padding: '1.5rem',
        marginBottom: '2rem'
      }}>
        <h3 style={{ color: '#92400e', marginBottom: '0.5rem', fontSize: '1.125rem', fontWeight: '600' }}>
          ⚠️ Feature Deprecated
        </h3>
        <p style={{ color: '#78350f', marginBottom: '0.5rem' }}>
          Partner Shares have been deprecated in this version.
        </p>
        <p style={{ color: '#78350f', fontSize: '0.875rem' }}>
          External sharing and export functionality will be reintroduced in a future release 
          with improved security and user experience.
        </p>
      </div>
    </div>
  );
};

export default PartnerSharesAdmin;
