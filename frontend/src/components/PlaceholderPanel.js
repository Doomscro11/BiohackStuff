/**
 * Placeholder Panel Component
 * Empty UI scaffolding - displays when advanced features are "enabled"
 * No actual functionality - purely visual placeholder
 */

import React, { useState, useEffect } from 'react';
import { fetchJSON } from '@/lib/http';
import './PlaceholderPanel.css';

function PlaceholderPanel({ featureLevel = 0 }) {
  const [previewData, setPreviewData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (featureLevel > 0) {
      loadPreviewData();
    }
  }, [featureLevel]);

  const loadPreviewData = async () => {
    setLoading(true);
    const result = await fetchJSON(`${process.env.REACT_APP_BACKEND_URL}/api/placeholder/advanced-preview`);
    
    if (result.ok && result.data) {
      setPreviewData(result.data);
    } else {
      console.error('Failed to load preview data:', result.text);
    }
    
    setLoading(false);
  };

  const handlePlaceholderAction = async () => {
    setLoading(true);
    const result = await fetchJSON(`${process.env.REACT_APP_BACKEND_URL}/api/placeholder/advanced-action`, {
      method: 'POST'
    });
    
    if (result.ok && result.data) {
      alert(`Action completed: ${JSON.stringify(result.data.status)}\n\nThis is placeholder data only.`);
    } else {
      console.error('Action failed:', result.text);
    }
    
    setLoading(false);
  };

  if (featureLevel === 0) {
    return (
      <div className="placeholder-panel locked">
        <div className="lock-icon">🔒</div>
        <h3>Advanced Features Locked</h3>
        <p>Contact administrator to enable advanced feature access.</p>
      </div>
    );
  }

  return (
    <div className="placeholder-panel">
      <div className="panel-header">
        <h3>Advanced Feature Panel</h3>
        <span className="level-badge">Level {featureLevel}</span>
      </div>

      <div className="disclaimer-box">
        <strong>⚠️ Preview Mode:</strong> This panel contains UI scaffolding only.
        No actual computational features are implemented.
      </div>

      {loading && <div className="loading-spinner">Loading...</div>}

      {!loading && previewData && (
        <div className="preview-data">
          <h4>Available Features (Placeholder)</h4>
          <ul className="feature-list">
            {previewData.available_features.filter(Boolean).map((feature, idx) => (
              <li key={idx} className="feature-item">
                <span className="feature-icon">📊</span>
                <span className="feature-name">{feature}</span>
                <span className="feature-status">Placeholder</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="action-section">
        <button
          onClick={handlePlaceholderAction}
          className="placeholder-button"
          disabled={loading}
        >
          {loading ? 'Processing...' : 'Execute Placeholder Action'}
        </button>
        <p className="action-note">
          This button demonstrates UI interaction without performing actual computation.
        </p>
      </div>

      <div className="level-info">
        <h4>Current Access Level: {featureLevel}</h4>
        <div className="level-grid">
          <div className={`level-card ${featureLevel >= 1 ? 'active' : 'inactive'}`}>
            <strong>Level 1</strong>
            <p>Basic UI elements visible</p>
          </div>
          <div className={`level-card ${featureLevel >= 2 ? 'active' : 'inactive'}`}>
            <strong>Level 2</strong>
            <p>Extended panels accessible</p>
          </div>
          <div className={`level-card ${featureLevel >= 3 ? 'active' : 'inactive'}`}>
            <strong>Level 3</strong>
            <p>Advanced options shown</p>
          </div>
          <div className={`level-card ${featureLevel >= 4 ? 'active' : 'inactive'}`}>
            <strong>Level 4</strong>
            <p>Maximum UI framework</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default PlaceholderPanel;
