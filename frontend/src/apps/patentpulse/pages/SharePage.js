/**
 * SharePage - Deprecated
 * 
 * This page is a static deprecation notice.
 * The Partner Shares feature has been completely deprecated.
 * No network calls are made from this component to avoid any
 * "response body already used" errors.
 */

import React from 'react';

export default function SharePageDeprecated() {
  return (
    <div style={{ 
      maxWidth: '640px', 
      margin: '3rem auto', 
      padding: '1.5rem',
      fontFamily: 'system-ui, -apple-system, sans-serif'
    }}>
      <div style={{
        background: '#fef3c7',
        border: '2px solid #f59e0b',
        borderRadius: '8px',
        padding: '1.5rem',
        marginBottom: '2rem'
      }}>
        <h1 style={{ 
          fontSize: '1.5rem', 
          fontWeight: 'bold', 
          color: '#92400e',
          marginBottom: '1rem'
        }}>
          ⚠️ PatentPulse Share Links Deprecated
        </h1>
        <p style={{ 
          color: '#78350f', 
          marginBottom: '1rem',
          lineHeight: '1.6'
        }}>
          The public sharing feature for PatentPulse exports has been deprecated and is no longer available.
        </p>
        <p style={{ 
          color: '#78350f',
          lineHeight: '1.6'
        }}>
          If you believe you reached this page in error, please contact support or your platform administrator.
        </p>
      </div>
      
      <div style={{
        background: '#f3f4f6',
        padding: '1rem',
        borderRadius: '6px',
        fontSize: '0.875rem',
        color: '#6b7280'
      }}>
        <p style={{ marginBottom: '0.5rem' }}>
          <strong>Note for administrators:</strong>
        </p>
        <p>
          External sharing and export functionality will be reintroduced in a future release 
          with improved security and user experience.
        </p>
      </div>
    </div>
  );
}
