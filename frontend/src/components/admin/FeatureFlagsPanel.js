/**
 * Feature Flags Admin Panel
 * UI for managing feature flags and user feature levels
 * Purely architectural - no biochemical functionality
 */

import React, { useState, useEffect } from 'react';
import { fetchJSON } from '@/lib/http';
import './FeatureFlagsPanel.css';

function FeatureFlagsPanel() {
  const [flags, setFlags] = useState({});
  const [loading, setLoading] = useState(true);
  const [selectedUserId, setSelectedUserId] = useState('');
  const [selectedLevel, setSelectedLevel] = useState(0);
  const [message, setMessage] = useState('');
  
  // Use ref to prevent concurrent calls across renders (React StrictMode)
  const isLoadingRef = React.useRef(false);
  const isMountedRef = React.useRef(false);

  useEffect(() => {
    // Prevent double-loading in React StrictMode
    if (isMountedRef.current) {
      return;
    }
    isMountedRef.current = true;
    
    loadFeatureFlags();
  }, []);

  const loadFeatureFlags = async () => {
    // Prevent concurrent calls using ref (persists across renders)
    if (isLoadingRef.current) {
      console.log('[FeatureFlagsPanel] Already loading, skipping duplicate request');
      return;
    }
    
    isLoadingRef.current = true;
    
    try {
      const result = await fetchJSON(`${process.env.REACT_APP_BACKEND_URL}/api/admin/features/flags`);

      if (result.ok && result.data) {
        setFlags(result.data.flags || {});
      } else {
        console.error('[FeatureFlagsPanel] Failed to load feature flags:', result.text);
      }
    } finally {
      setLoading(false);
      isLoadingRef.current = false;
    }
  };

  const toggleFlag = async (flagKey) => {
    const currentValue = flags[flagKey] || false;
    
    const result = await fetchJSON(`${process.env.REACT_APP_BACKEND_URL}/api/admin/features/flags`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        flag_key: flagKey,
        enabled: !currentValue
      })
    });

    if (result.ok) {
      setFlags(prev => ({
        ...prev,
        [flagKey]: !currentValue
      }));
      setMessage(`Flag '${flagKey}' ${!currentValue ? 'enabled' : 'disabled'} successfully`);
    } else {
      setMessage(`Failed to update flag '${flagKey}'`);
    }

    setTimeout(() => setMessage(''), 3000);
  };

  const updateUserLevel = async () => {
    if (!selectedUserId) {
      setMessage('Please enter a user ID');
      return;
    }

    const result = await fetchJSON(`${process.env.REACT_APP_BACKEND_URL}/api/admin/features/user-level`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        user_id: selectedUserId,
        feature_level: parseInt(selectedLevel)
      })
    });

    if (result.ok) {
      setMessage(`User ${selectedUserId} feature level set to ${selectedLevel}`);
      setSelectedUserId('');
      setSelectedLevel(0);
    } else {
      setMessage(`Failed: ${result.text || 'Unknown error'}`);
    }

    setTimeout(() => setMessage(''), 3000);
  };

  const applyPreset = async (presetName) => {
    const result = await fetchJSON(`${process.env.REACT_APP_BACKEND_URL}/api/admin/features/apply-preset?preset_name=${presetName}`, {
      method: 'POST'
    });

    if (result.ok) {
      setMessage(`Preset '${presetName}' applied successfully`);
      loadFeatureFlags(); // Reload flags
    } else {
      setMessage(`Failed to apply preset '${presetName}'`);
    }

    setTimeout(() => setMessage(''), 3000);
  };

  if (loading) {
    return <div className="feature-flags-panel">Loading feature flags...</div>;
  }

  return (
    <div className="feature-flags-panel">
      <h2>Feature Flags Management</h2>
      <p className="disclaimer">
        ⚠️ Architectural framework only - no biochemical functionality
      </p>

      {message && (
        <div className={`message ${message.includes('Failed') || message.includes('Error') ? 'error' : 'success'}`}>
          {message}
        </div>
      )}

      <div className="flags-section">
        <h3>Global Feature Flags</h3>
        <div className="flags-list">
          {Object.entries(flags).map(([key, value]) => (
            <div key={key} className="flag-item">
              <label>
                <input
                  type="checkbox"
                  checked={value}
                  onChange={() => toggleFlag(key)}
                />
                <span className="flag-name">{key}</span>
              </label>
              <span className={`flag-status ${value ? 'enabled' : 'disabled'}`}>
                {value ? 'Enabled' : 'Disabled'}
              </span>
            </div>
          ))}
        </div>
      </div>

      <div className="user-level-section">
        <h3>User Feature Level</h3>
        <div className="user-level-form">
          <input
            type="text"
            placeholder="User ID"
            value={selectedUserId}
            onChange={(e) => setSelectedUserId(e.target.value)}
            className="user-id-input"
          />
          <select
            value={selectedLevel}
            onChange={(e) => setSelectedLevel(e.target.value)}
            className="level-select"
          >
            <option value="0">Level 0 - Baseline</option>
            <option value="1">Level 1 - Preview</option>
            <option value="2">Level 2 - Extended</option>
            <option value="3">Level 3 - Advanced</option>
            <option value="4">Level 4 - Maximum</option>
          </select>
          <button onClick={updateUserLevel} className="update-btn">
            Update Level
          </button>
        </div>
      </div>

      <div className="presets-section">
        <h3>Feature Flag Presets</h3>
        <p className="section-description">
          Quick apply predefined feature flag configurations
        </p>
        <div className="preset-buttons">
          <button onClick={() => applyPreset('baseline')} className="preset-btn baseline">
            Baseline
            <span className="preset-desc">All features off</span>
          </button>
          <button onClick={() => applyPreset('preview')} className="preset-btn preview">
            Preview Mode
            <span className="preset-desc">Basic UI scaffolding</span>
          </button>
          <button onClick={() => applyPreset('extended')} className="preset-btn extended">
            Extended UI
            <span className="preset-desc">Additional panels</span>
          </button>
          <button onClick={() => applyPreset('full_scaffold')} className="preset-btn full">
            Full Scaffold
            <span className="preset-desc">Complete framework</span>
          </button>
        </div>
      </div>

      <div className="level-descriptions">
        <h4>Feature Level Descriptions</h4>
        <ul>
          <li><strong>Level 0:</strong> Baseline access - standard features only</li>
          <li><strong>Level 1:</strong> Preview mode - UI placeholders visible</li>
          <li><strong>Level 2:</strong> Extended UI - additional panels accessible</li>
          <li><strong>Level 3:</strong> Advanced UI - all UI components visible</li>
          <li><strong>Level 4:</strong> Maximum - full architectural framework access</li>
        </ul>
        <p className="note">
          Note: These levels control UI visibility only. No computational or biochemical features are included.
        </p>
      </div>
    </div>
  );
}

export default FeatureFlagsPanel;
