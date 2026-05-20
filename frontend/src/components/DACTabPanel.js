/**
 * DAC Tab Panel Component
 * Empty UI scaffolding with tab navigation
 * Purely visual - no computational functionality
 */

import React, { useState, useEffect } from 'react';
import './DACTabPanel.css';

function DACTabPanel({ featureLevel = 0 }) {
  const [activeTab, setActiveTab] = useState('overview');
  const [mockJobStatus, setMockJobStatus] = useState(null);

  const tabs = [
    { id: 'overview', label: 'Overview', minLevel: 0 },
    { id: 'parameters', label: 'Parameters', minLevel: 1 },
    { id: 'analysis', label: 'Analysis', minLevel: 2 },
    { id: 'results', label: 'Results', minLevel: 2 },
    { id: 'advanced', label: 'Advanced', minLevel: 3 }
  ];

  const startMockJob = () => {
    setMockJobStatus({ status: 'running', progress: 0 });
    
    // Simulate progress
    let progress = 0;
    const interval = setInterval(() => {
      progress += 20;
      if (progress >= 100) {
        setMockJobStatus({ status: 'completed', progress: 100 });
        clearInterval(interval);
      } else {
        setMockJobStatus({ status: 'running', progress });
      }
    }, 500);
  };

  const renderTabContent = () => {
    switch (activeTab) {
      case 'overview':
        return (
          <div className="tab-content">
            <h3>Overview Panel</h3>
            <p className="disclaimer">
              This is a placeholder panel. No computational features are active.
            </p>
            <div className="info-cards">
              <div className="info-card">
                <div className="card-icon">📊</div>
                <h4>Feature Status</h4>
                <p>Current Level: {featureLevel}</p>
              </div>
              <div className="info-card">
                <div className="card-icon">🔧</div>
                <h4>Available Tools</h4>
                <p>{featureLevel >= 1 ? 'UI scaffolding visible' : 'Locked'}</p>
              </div>
              <div className="info-card">
                <div className="card-icon">📝</div>
                <h4>Mock Data</h4>
                <p>Placeholder responses enabled</p>
              </div>
            </div>
          </div>
        );

      case 'parameters':
        return (
          <div className="tab-content">
            <h3>Parameter Configuration</h3>
            <p className="disclaimer">
              Form inputs below are non-functional placeholders
            </p>
            <form className="mock-form" onSubmit={(e) => e.preventDefault()}>
              <div className="form-group">
                <label>Parameter Set</label>
                <select disabled={featureLevel < 1}>
                  <option>Preset A (Placeholder)</option>
                  <option>Preset B (Placeholder)</option>
                  <option>Preset C (Placeholder)</option>
                </select>
              </div>
              <div className="form-group">
                <label>Configuration Mode</label>
                <div className="radio-group">
                  <label>
                    <input type="radio" name="mode" disabled={featureLevel < 1} />
                    Mode 1 (Mock)
                  </label>
                  <label>
                    <input type="radio" name="mode" disabled={featureLevel < 1} />
                    Mode 2 (Mock)
                  </label>
                </div>
              </div>
              <div className="form-group">
                <label>Example Slider</label>
                <input 
                  type="range" 
                  min="0" 
                  max="100" 
                  disabled={featureLevel < 1}
                  className="mock-slider"
                />
              </div>
            </form>
          </div>
        );

      case 'analysis':
        return (
          <div className="tab-content">
            <h3>Analysis Panel</h3>
            {featureLevel >= 2 ? (
              <>
                <p className="disclaimer">
                  Mock analysis visualization - no actual computation
                </p>
                <div className="mock-chart">
                  <div className="chart-placeholder">
                    <div className="bar" style={{height: '60%'}}></div>
                    <div className="bar" style={{height: '80%'}}></div>
                    <div className="bar" style={{height: '40%'}}></div>
                    <div className="bar" style={{height: '90%'}}></div>
                    <div className="bar" style={{height: '50%'}}></div>
                  </div>
                  <p className="chart-label">Placeholder visualization</p>
                </div>
              </>
            ) : (
              <div className="locked-content">
                <div className="lock-icon">🔒</div>
                <p>Analysis panel requires Level 2+</p>
              </div>
            )}
          </div>
        );

      case 'results':
        return (
          <div className="tab-content">
            <h3>Results Panel</h3>
            {featureLevel >= 2 ? (
              <>
                <p className="disclaimer">
                  Mock results display - no data generated
                </p>
                {mockJobStatus && (
                  <div className="job-status">
                    <div className="status-header">
                      <span>Mock Job Status: {mockJobStatus.status}</span>
                      <span>{mockJobStatus.progress}%</span>
                    </div>
                    <div className="progress-bar">
                      <div 
                        className="progress-fill" 
                        style={{width: `${mockJobStatus.progress}%`}}
                      ></div>
                    </div>
                  </div>
                )}
                <button onClick={startMockJob} className="action-button">
                  Start Mock Process
                </button>
                <div className="results-table">
                  <div className="table-header">
                    <span>ID</span>
                    <span>Type</span>
                    <span>Value</span>
                  </div>
                  <div className="table-row">
                    <span>001</span>
                    <span>Placeholder</span>
                    <span>42.5</span>
                  </div>
                  <div className="table-row">
                    <span>002</span>
                    <span>Placeholder</span>
                    <span>38.2</span>
                  </div>
                  <div className="table-row">
                    <span>003</span>
                    <span>Placeholder</span>
                    <span>51.8</span>
                  </div>
                </div>
              </>
            ) : (
              <div className="locked-content">
                <div className="lock-icon">🔒</div>
                <p>Results panel requires Level 2+</p>
              </div>
            )}
          </div>
        );

      case 'advanced':
        return (
          <div className="tab-content">
            <h3>Advanced Options</h3>
            {featureLevel >= 3 ? (
              <>
                <p className="disclaimer">
                  Advanced UI scaffolding - fully non-functional
                </p>
                <div className="advanced-options">
                  <div className="option-group">
                    <h4>Option Set Alpha</h4>
                    <label>
                      <input type="checkbox" disabled />
                      Feature Alpha (Placeholder)
                    </label>
                    <label>
                      <input type="checkbox" disabled />
                      Feature Beta (Placeholder)
                    </label>
                  </div>
                  <div className="option-group">
                    <h4>Option Set Gamma</h4>
                    <label>
                      <input type="checkbox" disabled />
                      Feature Gamma (Placeholder)
                    </label>
                    <label>
                      <input type="checkbox" disabled />
                      Feature Delta (Placeholder)
                    </label>
                  </div>
                </div>
              </>
            ) : (
              <div className="locked-content">
                <div className="lock-icon">🔒</div>
                <p>Advanced panel requires Level 3+</p>
              </div>
            )}
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="dac-tab-panel">
      <div className="panel-header">
        <h2>Advanced Feature Panel</h2>
        <span className="level-badge">Level {featureLevel}</span>
      </div>

      <div className="tabs-container">
        <div className="tabs-list">
          {tabs.map(tab => {
            const isLocked = featureLevel < tab.minLevel;
            return (
              <button
                key={tab.id}
                className={`tab-button ${activeTab === tab.id ? 'active' : ''} ${isLocked ? 'locked' : ''}`}
                onClick={() => !isLocked && setActiveTab(tab.id)}
                disabled={isLocked}
              >
                {tab.label}
                {isLocked && ' 🔒'}
              </button>
            );
          })}
        </div>

        <div className="tab-content-area">
          {renderTabContent()}
        </div>
      </div>
    </div>
  );
}

export default DACTabPanel;
