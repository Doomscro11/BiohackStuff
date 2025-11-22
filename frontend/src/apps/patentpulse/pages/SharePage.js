/**
 * Partner Share Page (Phase IXf+)
 * Public-facing page for partners to access shared Reclaim Packs
 */

import React, { useState, useEffect } from 'react';
import { useParams, useLocation } from 'react-router-dom';
import { fetchJSON } from '@/lib/http';
import '../styles/SharePage.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';

const SharePage = () => {
  const { token } = useParams();
  const location = useLocation();
  const [metadata, setMetadata] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    fetchShareMetadata();
  }, [token]);

  const fetchShareMetadata = async () => {
    if (!token) {
      setError('Invalid share link');
      setLoading(false);
      return;
    }

    const result = await fetchJSON(`${BACKEND_URL}/api/patentpulse/partner/share/${token}`);

    if (!result.ok) {
      setError(result.text || 'Invalid or expired share link');
      setLoading(false);
      return;
    }
    
    setMetadata(result.data);
    setError(null);
    setLoading(false);
  };

  const handleDownload = async () => {
    if (!token || downloading) return;

    setDownloading(true);

    try {
      // For downloads, we still need to use native fetch to get blob
      const response = await fetch(`${BACKEND_URL}/api/patentpulse/partner/share/${token}/download`, {
        credentials: 'include'
      });

      if (!response.ok) {
        const result = await fetchJSON(`${BACKEND_URL}/api/patentpulse/partner/share/${token}/download`);
        throw new Error(result.text || `Error ${response.status}`);
      }

      // Get filename from Content-Disposition or use default
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = metadata?.file_name || 'reclaim_pack.pdf';
      
      if (contentDisposition) {
        const matches = /filename="?([^"]+)"?/.exec(contentDisposition);
        if (matches && matches[1]) {
          filename = matches[1];
        }
      }

      // Download file
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      // Refresh metadata to update download count
      setTimeout(fetchShareMetadata, 1000);
    } catch (err) {
      setError(err.message || 'Download failed');
    } finally {
      setDownloading(false);
    }
  };

  const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getDaysRemaining = (expiryStr) => {
    const expiry = new Date(expiryStr);
    const now = new Date();
    const diff = expiry.getTime() - now.getTime();
    const days = Math.ceil(diff / (1000 * 60 * 60 * 24));
    return days;
  };

  if (loading) {
    return (
      <div className="share-page">
        <div className="share-container">
          <div className="loading-state">
            <div className="spinner"></div>
            <p>Loading your Reclaim Pack...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="share-page">
        <div className="share-container">
          <div className="share-header">
            <div className="logo-section">
              <h1 data-testid="pp-partner-branding">PatentPulse</h1>
              <p className="tagline">Secure Preview</p>
            </div>
          </div>
          
          <div className="share-content">
            <div className="error-state">
              <div className="error-icon">⚠️</div>
              <h2>Access Error</h2>
              <p className="error-message">{error}</p>
            
            {error.includes('expired') && (
              <div className="error-details">
                <p>This share link has expired. Please contact the sender for a new link.</p>
              </div>
            )}
            
            {error.includes('revoked') && (
              <div className="error-details">
                <p>This share link has been revoked. Please contact the sender for more information.</p>
              </div>
            )}
            
            {error.includes('Maximum download') && (
              <div className="error-details">
                <p>You've reached the maximum download limit for this share.</p>
              </div>
            )}
            
            {error.includes('Rate limit') && (
              <div className="error-details">
                <p>Too many requests. Please wait a moment and try again.</p>
              </div>
            )}
            
              <p className="support-info">
                Need help? Contact <a href="mailto:support@peptologic.ai">support@peptologic.ai</a>
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!metadata) {
    return null;
  }

  const daysRemaining = getDaysRemaining(metadata.expires_at);
  const isExpiringSoon = daysRemaining <= 3;

  return (
    <div className="share-page">
      <div className="share-container">
        <div className="share-header">
          <div className="logo-section">
            <h1 data-testid="pp-partner-branding">PatentPulse</h1>
            <p className="tagline">Secure Preview</p>
          </div>
        </div>

        <div className="share-content">
          <div className="welcome-section">
            <h2>Welcome, {metadata.recipient_first_name}!</h2>
            <p className="company-name">{metadata.company_or_project}</p>
          </div>

          <div className="file-info-card">
            <div className="file-icon">
              {metadata.format === 'pdf' ? '📄' : '📊'}
            </div>
            <div className="file-details">
              <h3>{metadata.file_name}</h3>
              <p className="file-type">{metadata.format.toUpperCase()} Format</p>
            </div>
          </div>

          <div className="access-info">
            <div className="info-row">
              <span className="label">Downloads Remaining:</span>
              <span className="value">
                <strong>{metadata.downloads_remaining}</strong> of {metadata.max_downloads}
              </span>
            </div>
            
            <div className="info-row">
              <span className="label">Expires:</span>
              <span className={`value ${isExpiringSoon ? 'expiring-soon' : ''}`}>
                {formatDate(metadata.expires_at)}
                {isExpiringSoon && (
                  <span className="expiry-badge">⚠️ {daysRemaining} {daysRemaining === 1 ? 'day' : 'days'} left</span>
                )}
              </span>
            </div>
          </div>

          <div className="action-section">
            <button
              className="download-button"
              onClick={handleDownload}
              disabled={downloading || metadata.downloads_remaining === 0}
              data-testid="pp-partner-download"
            >
              {downloading ? (
                <>
                  <span className="button-spinner"></span>
                  Downloading...
                </>
              ) : (
                <>
                  <span className="download-icon">⬇️</span>
                  Download Reclaim Pack
                </>
              )}
            </button>
            
            {metadata.downloads_remaining === 0 && (
              <p className="warning-text">Maximum download limit reached</p>
            )}
          </div>

          <div className="landing-copy">
            <h3>What You'll Find</h3>
            <ul>
              <li><strong>Commercial Viability:</strong> Market-adjusted scores using real-time signals</li>
              <li><strong>FTO Snapshot:</strong> Family/claims context to inform diligence</li>
              <li><strong>Synthesis Complexity:</strong> Practical feasibility indicators</li>
              <li><strong>Sources:</strong> Public filings + PatentPulse analytics</li>
            </ul>

            <div className="important-notes">
              <h3>Important Notes</h3>
              <p className="note-item">
                ⚠️ <strong>Your preview is watermarked and time-limited.</strong>
              </p>
              <ul className="notes-list">
                <li>Personal, non-transferable link (downloads allowed: <strong>{metadata.max_downloads}</strong>)</li>
                <li>Expires on <strong>{formatDate(metadata.expires_at)}</strong> or when limits are reached</li>
                <li>For internal evaluation only — <strong>no license grant</strong> and <strong>not FTO clearance</strong></li>
              </ul>
            </div>

            <div className="legal-disclaimer">
              <p>
                <em>Legal:</em> PatentPulse provides analytics on public filings. It is <strong>not</strong> legal advice or FTO clearance. 
                Always verify with qualified counsel.
              </p>
            </div>
          </div>

          <div className="support-section">
            <p>
              Need help? Contact <a href={`mailto:${metadata.support_email}`}>{metadata.support_email}</a>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SharePage;
