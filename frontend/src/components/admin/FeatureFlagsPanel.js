/**
 * Feature Flags Admin Panel
 * UI for managing feature flags and user feature levels
 * Purely architectural - no biochemical functionality
 */

import React, { useState, useEffect } from 'react';
import './FeatureFlagsPanel.css';

function FeatureFlagsPanel() {
  const [flags, setFlags] = useState({});
  const [loading, setLoading] = useState(true);
  const [selectedUserId, setSelectedUserId] = useState('');
  const [selectedLevel, setSelectedLevel] = useState(0);
  const [message, setMessage] = useState('');

  useEffect(() => {
    loadFeatureFlags();
  }, []);

  const loadFeatureFlags = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/features/flags`, {
        credentials: 'include'
      });

      if (response.ok) {
        const data = await response.json();
        setFlags(data.flags || {});
      }
    } catch (error) {
      console.error('Failed to load feature flags:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleFlag = async (flagKey) => {
    try {
      const currentValue = flags[flagKey] || false;
      
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/features/flags`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify({
          flag_key: flagKey,
          enabled: !currentValue
        })
      });

      if (response.ok) {
        setFlags(prev => ({
          ...prev,
          [flagKey]: !currentValue
        }));
        setMessage(`Flag '${flagKey}' ${!currentValue ? 'enabled' : 'disabled'} successfully`);
      } else {
        setMessage(`Failed to update flag '${flagKey}'`);
      }
    } catch (error) {
      console.error('Failed to toggle flag:', error);
      setMessage('Error updating flag');
    }

    setTimeout(() => setMessage(''), 3000);
  };

  const updateUserLevel = async () => {
    if (!selectedUserId) {
      setMessage('Please enter a user ID');
      return;
    }

    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/features/user-level`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify({
          user_id: selectedUserId,
          feature_level: parseInt(selectedLevel)
        })
      });

      if (response.ok) {
        setMessage(`User ${selectedUserId} feature level set to ${selectedLevel}`);
        setSelectedUserId('');
        setSelectedLevel(0);
      } else {
        const error = await response.json();
        setMessage(`Failed: ${error.detail || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Failed to update user level:', error);
      setMessage('Error updating user level');
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
