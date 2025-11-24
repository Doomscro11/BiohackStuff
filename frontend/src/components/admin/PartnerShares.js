/**
 * DEPRECATED: Partner Shares Admin Interface
 * 
 * This component has been deprecated and is no longer used.
 * Partner Shares feature has been removed from the application.
 * 
 * TODO: Future external sharing/export will be implemented as a separate
 * "Export to PDF / Share Report" feature with a cleaner architecture.
 */

import React from 'react';

const PartnerSharesAdmin = () => {
  return (
    <div className="partner-shares-admin">
      <div className="admin-header">
        <h2>Partner Shares (Deprecated)</h2>
      </div>
      
      <div className="deprecation-notice" style={{
        padding: '20px',
        backgroundColor: '#fff3cd',
        border: '1px solid #ffeaa7',
        borderRadius: '4px',
        margin: '20px 0'
      }}>
        <h3>⚠️ Feature Deprecated</h3>
        <p>
          The Partner Shares feature has been deprecated and is no longer available.
          This functionality will be replaced with a new "Export to PDF / Share Report" 
          feature in a future release.
        </p>
        <p>
          If you need to share reports externally, please use the standard export 
          functionality and share files through your preferred secure channels.
        </p>
      </div>
    </div>
  );
};

export default PartnerSharesAdmin;
