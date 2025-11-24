/**
 * Partner Shares Admin Component (Phase IXf+)
 * Manage partner share links, view analytics, and control access
 */

import React, { useState, useEffect } from 'react';
import { fetchJSON } from '@/lib/http';
import './PartnerShares.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';

const PartnerSharesAdmin = () => {
  const [shares, setShares] = useState([]);
  const [exports, setExports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [selectedShare, setSelectedShare] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [filter, setFilter] = useState('all');

  // Form state
  const [formData, setFormData] = useState({
    file_id: '',
    recipient_email: '',
    recipient_first_name: '',
    company_or_project: '',
    expires_in_days: 14,
    max_downloads: 10,
    ip_allowlist: '',
    watermark_enabled: true,
    internal_notes: ''
  });

  useEffect(() => {
    // Create AbortController for cleanup on unmount or re-render
    const abortController = new AbortController();
    const signal = abortController.signal;
    
    const loadData = async () => {
      try {
        // Load shares first, then exports to avoid concurrent API calls
        // Pass signal for cleanup on unmount
        await fetchShares(signal);
        if (!signal.aborted) {
          await fetchExports(signal);
        }
      } catch (error) {
        if (error.name !== 'AbortError') {
          console.error('Error loading partner shares data:', error);
          setError('Failed to load data');
        }
      }
    };
    
    loadData();
    
    // Cleanup function to abort pending requests
    return () => {
      abortController.abort();
    };
  }, [filter]);

  const fetchShares = async (signal = null) => {
    setLoading(true);
    setError(null); // Clear previous errors
    
    try {
      const params = new URLSearchParams();
      if (filter !== 'all') {
        params.append('state', filter);
      }

      const result = await fetchJSON(
        `${BACKEND_URL}/api/patentpulse/partner/shares?${params.toString()}`,
        { 
          credentials: 'include',
          ...(signal && { signal })
        }
      );

      if (result.ok) {
        setShares(result.data.shares || []);
        setError(null);
      } else {
        // Provide user-friendly error message instead of technical details
        const errorMsg = result.status === 401 ? 'Authentication required' :
                        result.status === 403 ? 'Access denied' :
                        result.status >= 500 ? 'Server error - please try again' :
                        'Failed to load partner shares';
        setError(errorMsg);
      }
    } catch (error) {
      if (error.name !== 'AbortError') {
        console.error('Error fetching shares:', error);
        setError('Network error - please check your connection');
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchExports = async (signal = null) => {
    try {
      const result = await fetchJSON(`${BACKEND_URL}/api/patentpulse/reclaim/exports`, {
        credentials: 'include',
        ...(signal && { signal })
      });

      if (result.ok) {
        setExports(result.data.exports || []);
      } else {
        console.error('Failed to fetch exports:', result.text);
        // Don't set error state for exports failure as it's not critical
      }
    } catch (error) {
      console.error('Error fetching exports:', error);
      // Don't set error state for exports failure as it's not critical
    }
  };

  const createShare = async (e) => {
    e.preventDefault();

    try {
      const payload = {
        ...formData,
        ip_allowlist: formData.ip_allowlist
          ? formData.ip_allowlist.split(',').map(ip => ip.trim()).filter(Boolean)
          : []
      };

      // Use fetchJSON which reads response body exactly once
      const result = await fetchJSON(`${BACKEND_URL}/api/patentpulse/partner/shares`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(payload)
      });

      if (result.ok && result.data) {
        // Show share URL
        alert(`Share created successfully!\n\nShare URL:\n${result.data.share_url}\n\nThis link has been generated for ${formData.recipient_email}.`);

        // Reset form and refresh
        setShowCreateForm(false);
        setFormData({
          file_id: '',
          recipient_email: '',
          recipient_first_name: '',
          company_or_project: '',
          expires_in_days: 14,
          max_downloads: 10,
          ip_allowlist: '',
          watermark_enabled: true,
          internal_notes: ''
        });
        
        // Refresh shares list (await to ensure completion)
        await fetchShares();
      } else {
        // Safe error message - result.text is already a string from fetchJSON
        const errorMsg = result.text || 'Failed to create share';
        alert(`Error creating share: ${errorMsg}`);
      }
    } catch (error) {
      // Handle any unexpected errors
      console.error('Error creating share:', error);
      const errorMsg = error.message || 'An unexpected error occurred';
      alert(`Error creating share: ${errorMsg}`);
    }
  };

  const rotateToken = async (shareId) => {
    if (!confirm('This will invalidate the old token. The recipient will need a new link. Continue?')) {
      return;
    }

    try {
      const result = await fetchJSON(
        `${BACKEND_URL}/api/patentpulse/partner/shares/${shareId}/rotate`,
        {
          method: 'POST',
          credentials: 'include'
        }
      );

      if (result.ok && result.data) {
        const shareUrl = `${window.location.origin}/share/${result.data.new_token}`;
        alert(`Token rotated successfully!\n\nNew Share URL:\n${shareUrl}`);
        await fetchShares();
      } else {
        alert(`Error: ${result.text || 'Failed to rotate token'}`);
      }
    } catch (error) {
      console.error('Error rotating token:', error);
      alert(`Error: ${error.message || 'Failed to rotate token'}`);
    }
  };

  const revokeShare = async (shareId) => {
    const reason = prompt('Reason for revocation (optional):');
    if (reason === null) return; // User cancelled

    try {
      const result = await fetchJSON(
        `${BACKEND_URL}/api/patentpulse/partner/shares/${shareId}/revoke`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({ reason: reason || 'Revoked by admin' })
        }
      );

      if (result.ok) {
        alert('Share revoked successfully');
        await fetchShares();
      } else {
        alert(`Error: ${result.text || 'Failed to revoke share'}`);
      }
    } catch (error) {
      console.error('Error revoking share:', error);
      alert(`Error: ${error.message || 'Failed to revoke share'}`);
    }
  };

  const copyShareLink = (token) => {
    const shareUrl = `${window.location.origin}/share/${token}`;
    navigator.clipboard.writeText(shareUrl).then(() => {
      alert('Share link copied to clipboard!');
    }).catch(() => {
      alert(`Share link:\n${shareUrl}`);
    });
  };

  const viewAnalytics = async (shareId) => {
    const result = await fetchJSON(
      `${BACKEND_URL}/api/patentpulse/partner/shares/${shareId}/analytics`,
      { credentials: 'include' }
    );

    if (result.ok) {
      setAnalytics(result.data);
      const share = shares.find(s => s.share_id === shareId);
      setSelectedShare(share || null);
    } else {
      alert(`Error: ${result.text || 'Failed to fetch analytics'}`);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'Never';
    const date = new Date(dateStr);
    return date.toLocaleString();
  };

  const getStateColor = (state) => {
    switch (state) {
      case 'active': return 'green';
      case 'expired': return 'orange';
      case 'revoked': return 'red';
      default: return 'gray';
    }
  };

  return (
    <div className="partner-shares-admin">
      <div className="admin-header">
        <h2>Partner Shares Management</h2>
        <button
          className="btn btn-primary"
          onClick={() => setShowCreateForm(true)}
          data-testid="pp-partner-create"
        >
          + Create Share
        </button>
      </div>

      {error && (
        <div className="error-banner">
          <span>⚠️ {error}</span>
          <button onClick={() => setError(null)}>×</button>
        </div>
      )}

      {showCreateForm && (
        <div className="modal-overlay" onClick={() => setShowCreateForm(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Create Partner Share</h3>
              <button className="close-btn" onClick={() => setShowCreateForm(false)}>×</button>
            </div>

            <form onSubmit={createShare} className="share-form">
              <div className="form-group">
                <label>Export File *</label>
                <select
                  required
                  value={formData.file_id}
                  onChange={(e) => setFormData({ ...formData, file_id: e.target.value })}
                >
                  <option value="">Select an export...</option>
                  {exports.map(exp => (
                    <option key={exp.export_id} value={exp.export_id}>
                      {exp.filename} ({exp.format.toUpperCase()}) - {formatDate(exp.generated_at)}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Recipient Email *</label>
                  <input
                    type="email"
                    required
                    value={formData.recipient_email}
                    onChange={(e) => setFormData({ ...formData, recipient_email: e.target.value })}
                    placeholder="partner@company.com"
                  />
                </div>

                <div className="form-group">
                  <label>Recipient First Name *</label>
                  <input
                    type="text"
                    required
                    value={formData.recipient_first_name}
                    onChange={(e) => setFormData({ ...formData, recipient_first_name: e.target.value })}
                    placeholder="John"
                  />
                </div>
              </div>

              <div className="form-group">
                <label>Company / Project *</label>
                <input
                  type="text"
                  required
                  value={formData.company_or_project}
                  onChange={(e) => setFormData({ ...formData, company_or_project: e.target.value })}
                  placeholder="ACME Pharma R&D"
                />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Expires In (days) *</label>
                  <input
                    type="number"
                    required
                    min="1"
                    max="90"
                    value={formData.expires_in_days}
                    onChange={(e) => setFormData({ ...formData, expires_in_days: parseInt(e.target.value) })}
                  />
                </div>

                <div className="form-group">
                  <label>Max Downloads *</label>
                  <input
                    type="number"
                    required
                    min="1"
                    max="100"
                    value={formData.max_downloads}
                    onChange={(e) => setFormData({ ...formData, max_downloads: parseInt(e.target.value) })}
                  />
                </div>
              </div>

              <div className="form-group">
                <label>IP Allowlist (comma-separated, optional)</label>
                <input
                  type="text"
                  value={formData.ip_allowlist}
                  onChange={(e) => setFormData({ ...formData, ip_allowlist: e.target.value })}
                  placeholder="192.168.1.1, 10.0.0.0/8"
                />
                <small>Leave empty to allow all IPs</small>
              </div>

              <div className="form-group">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={formData.watermark_enabled}
                    onChange={(e) => setFormData({ ...formData, watermark_enabled: e.target.checked })}
                  />
                  <span>Enable Watermarking</span>
                </label>
              </div>

              <div className="form-group">
                <label>Internal Notes (optional)</label>
                <textarea
                  value={formData.internal_notes}
                  onChange={(e) => setFormData({ ...formData, internal_notes: e.target.value })}
                  placeholder="Internal tracking notes..."
                  rows={3}
                />
              </div>

              <div className="form-actions">
                <button type="button" className="btn btn-secondary" onClick={() => setShowCreateForm(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Create Share
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Analytics Modal */}
      {selectedShare && analytics && (
        <div className="modal-overlay" onClick={() => { setSelectedShare(null); setAnalytics(null); }}>
          <div className="modal-content analytics-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Share Analytics</h3>
              <button className="close-btn" onClick={() => { setSelectedShare(null); setAnalytics(null); }}>×</button>
            </div>

            <div className="analytics-content">
              <div className="analytics-summary">
                <div className="metric-card">
                  <div className="metric-value">{analytics.opens}</div>
                  <div className="metric-label">Opens</div>
                </div>
                <div className="metric-card">
                  <div className="metric-value">{analytics.downloads}</div>
                  <div className="metric-label">Downloads</div>
                </div>
                <div className="metric-card">
                  <div className="metric-value">{analytics.blocked}</div>
                  <div className="metric-label">Blocked</div>
                </div>
                <div className="metric-card">
                  <div className="metric-value">{analytics.expired + analytics.revoked}</div>
                  <div className="metric-label">Access Denied</div>
                </div>
              </div>

              <div className="analytics-section">
                <h4>Share Details</h4>
                <div className="detail-row">
                  <span>Recipient:</span>
                  <strong>{selectedShare.recipient_email}</strong>
                </div>
                <div className="detail-row">
                  <span>Company:</span>
                  <strong>{selectedShare.company_or_project}</strong>
                </div>
                <div className="detail-row">
                  <span>Last Accessed:</span>
                  <strong>{formatDate(analytics.last_access_at)}</strong>
                </div>
              </div>

              {analytics.top_ips.length > 0 && (
                <div className="analytics-section">
                  <h4>Top IPs</h4>
                  <table className="analytics-table">
                    <thead>
                      <tr>
                        <th>IP Address</th>
                        <th>Requests</th>
                        <th>Events</th>
                      </tr>
                    </thead>
                    <tbody>
                      {analytics.top_ips.map((item, idx) => (
                        <tr key={idx}>
                          <td>{item.ip}</td>
                          <td>{item.count}</td>
                          <td>{item.events.join(', ')}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {analytics.geo_breakdown.length > 0 && (
                <div className="analytics-section">
                  <h4>Geographic Distribution</h4>
                  <table className="analytics-table">
                    <thead>
                      <tr>
                        <th>Country</th>
                        <th>Requests</th>
                      </tr>
                    </thead>
                    <tbody>
                      {analytics.geo_breakdown.map((item, idx) => (
                        <tr key={idx}>
                          <td>{item.country}</td>
                          <td>{item.count}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Filter Tabs */}
      <div className="filter-tabs">
        <button
          className={filter === 'all' ? 'active' : ''}
          onClick={() => setFilter('all')}
        >
          All
        </button>
        <button
          className={filter === 'active' ? 'active' : ''}
          onClick={() => setFilter('active')}
        >
          Active
        </button>
        <button
          className={filter === 'expired' ? 'active' : ''}
          onClick={() => setFilter('expired')}
        >
          Expired
        </button>
        <button
          className={filter === 'revoked' ? 'active' : ''}
          onClick={() => setFilter('revoked')}
        >
          Revoked
        </button>
      </div>

      {loading ? (
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Loading shares...</p>
        </div>
      ) : shares.length === 0 ? (
        <div className="empty-state">
          <p>No partner shares found</p>
          <button className="btn btn-primary" onClick={() => setShowCreateForm(true)}>
            Create Your First Share
          </button>
        </div>
      ) : (
        <div className="shares-table-container">
          <table className="shares-table">
            <thead>
              <tr>
                <th>Recipient</th>
                <th>Company</th>
                <th>File</th>
                <th>State</th>
                <th>Expires</th>
                <th>Downloads</th>
                <th>Last Access</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {shares.map(share => (
                <tr key={share.share_id}>
                  <td>
                    <div className="recipient-cell">
                      <strong>{share.recipient_first_name}</strong>
                      <small>{share.recipient_email}</small>
                    </div>
                  </td>
                  <td>{share.company_or_project}</td>
                  <td>
                    <div className="file-cell">
                      <span>{share.file_name}</span>
                      <small>{share.format.toUpperCase()}</small>
                    </div>
                  </td>
                  <td>
                    <span className={`state-badge state-${share.state}`} style={{ color: getStateColor(share.state) }}>
                      {share.state}
                    </span>
                  </td>
                  <td>{formatDate(share.policy.expires_at)}</td>
                  <td>
                    {share.download_count} / {share.policy.max_downloads}
                  </td>
                  <td>{formatDate(share.last_accessed_at)}</td>
                  <td>
                    <div className="action-buttons">
                      {share.state === 'active' && (
                        <>
                          <button
                            className="btn-icon"
                            onClick={() => copyShareLink(share.share_token)}
                            title="Copy Link"
                            data-testid="pp-partner-copy"
                          >
                            📋
                          </button>
                          <button
                            className="btn-icon"
                            onClick={() => rotateToken(share.share_id)}
                            title="Rotate Token"
                            data-testid="pp-partner-rotate"
                          >
                            🔄
                          </button>
                          <button
                            className="btn-icon"
                            onClick={() => revokeShare(share.share_id)}
                            title="Revoke"
                            data-testid="pp-partner-revoke"
                          >
                            🚫
                          </button>
                        </>
                      )}
                      <button
                        className="btn-icon"
                        onClick={() => viewAnalytics(share.share_id)}
                        title="View Analytics"
                      >
                        📊
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default PartnerSharesAdmin;
