/**
 * PatentPulse Reclaim Pack Exporter UI (Phase IXe)
 * Generates investor-ready PDF/JSON reports of top patent opportunities
 */

import React, { useState, useEffect } from 'react';
import { fetchJSON } from '../lib/http';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

interface ReclaimExport {
  file_id: string;
  file_name: string;
  format: 'pdf' | 'json';
  items: number;
  viability_avg: number;
  generated_at: string;
  expires_at: string;
  size_kb: number;
}

interface ExportCriteria {
  format: 'pdf' | 'json';
  limit: number;
  country?: string;
  status?: string;
}

export default function PatentPulseReclaim() {
  const [loading, setLoading] = useState(false);
  const [exports, setExports] = useState<ReclaimExport[]>([]);
  const [featureEnabled, setFeatureEnabled] = useState(true);
  const [requires2FA, setRequires2FA] = useState(false);
  
  // Form state
  const [format, setFormat] = useState<'pdf' | 'json'>('pdf');
  const [limit, setLimit] = useState(10);
  const [country, setCountry] = useState('');
  const [status, setStatus] = useState('');
  
  // Toast state
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  
  useEffect(() => {
    loadExports();
  }, []);
  
  const showToast = (message: string, type: 'success' | 'error') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 5000);
  };
  
  const loadExports = async () => {
    try {
      const result = await fetchJSON<{ exports: ReclaimExport[] }>(
        `${BACKEND_URL}/api/patentpulse/reclaim/list?limit=20`,
        { credentials: 'include' }
      );
      
      if (result.ok) {
        setExports(result.data.exports);
      } else {
        if (result.status === 503) {
          setFeatureEnabled(false);
        } else if (result.status === 403) {
          setRequires2FA(true);
        }
      }
    } catch (error: any) {
      console.error('Failed to load exports:', error);
    }
  };
  
  const generateExport = async () => {
    if (!status) {
      showToast('Please select at least one status filter', 'error');
      return;
    }
    
    setLoading(true);
    
    try {
      const params = new URLSearchParams({
        format,
        limit: limit.toString(),
      });
      
      if (country) params.append('country', country);
      if (status) params.append('status', status);
      
      const result = await fetchJSON<ReclaimExport>(
        `${BACKEND_URL}/api/patentpulse/reclaim/export?${params.toString()}`,
        { 
          credentials: 'include',
          headers: { 'Content-Type': 'application/json' }
        }
      );
      
      if (result.ok) {
        showToast(
          `✅ ${format.toUpperCase()} export generated: ${result.data.items} items`,
          'success'
        );
        await loadExports();
      } else {
        if (result.status === 503) {
          setFeatureEnabled(false);
          showToast('Reclaim Pack feature not enabled', 'error');
        } else if (result.status === 403) {
          setRequires2FA(true);
          showToast('Admin 2FA required', 'error');
        } else {
          showToast(`Export failed: ${result.text || 'Unknown error'}`, 'error');
        }
      }
    } catch (error: any) {
      showToast(`Export failed: ${error.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };
  
  const deleteExport = async (fileId: string) => {
    if (!confirm('Delete this export?')) return;
    
    try {
      const result = await fetchJSON(
        `${BACKEND_URL}/api/patentpulse/reclaim/${fileId}`,
        {
          method: 'DELETE',
          credentials: 'include'
        }
      );
      
      if (result.ok) {
        showToast('Export deleted', 'success');
        await loadExports();
      } else {
        showToast('Delete failed', 'error');
      }
    } catch (error: any) {
      showToast(`Delete failed: ${error.message}`, 'error');
    }
  };
  
  const formatDate = (isoString: string) => {
    return new Date(isoString).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };
  
  const isExpired = (expiresAt: string) => {
    return new Date(expiresAt) < new Date();
  };
  
  // Feature gated view
  if (!featureEnabled) {
    return (
      <div className="p-6 bg-yellow-50 border border-yellow-200 rounded-lg">
        <h3 className="text-lg font-semibold text-yellow-800 mb-2">
          🔒 Feature Not Enabled
        </h3>
        <p className="text-yellow-700">
          The Reclaim Pack export feature is not enabled. 
          Set <code className="bg-yellow-100 px-2 py-1 rounded">FEATURE_PATENTPULSE_RECLAIM=true</code> to activate.
        </p>
      </div>
    );
  }
  
  // 2FA required view
  if (requires2FA) {
    return (
      <div className="p-6 bg-blue-50 border border-blue-200 rounded-lg">
        <h3 className="text-lg font-semibold text-blue-800 mb-2">
          🔐 Two-Factor Authentication Required
        </h3>
        <p className="text-blue-700">
          Reclaim Pack exports require Admin 2FA. Please complete 2FA setup to access this feature.
        </p>
      </div>
    );
  }
  
  return (
    <div className="space-y-6">
      {/* Toast Notification */}
      {toast && (
        <div 
          className={`fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 ${
            toast.type === 'success' ? 'bg-green-500' : 'bg-red-500'
          } text-white`}
        >
          {toast.message}
        </div>
      )}
      
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900">
          📦 Reclaim Pack Exporter
        </h2>
        <p className="text-gray-600 mt-1">
          Generate investor-ready reports of top patent opportunities
        </p>
      </div>
      
      {/* Export Generation Form */}
      <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
        <h3 className="text-lg font-semibold mb-4">Generate Export</h3>
        
        <div className="grid grid-cols-2 gap-4 mb-4">
          {/* Format */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Format
            </label>
            <select
              data-testid="pp-reclaim-format"
              value={format}
              onChange={(e) => setFormat(e.target.value as 'pdf' | 'json')}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
            >
              <option value="pdf">PDF</option>
              <option value="json">JSON</option>
            </select>
          </div>
          
          {/* Limit */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Number of Patents
            </label>
            <select
              data-testid="pp-reclaim-limit"
              value={limit}
              onChange={(e) => setLimit(parseInt(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
            >
              <option value={5}>Top 5</option>
              <option value={10}>Top 10</option>
              <option value={25}>Top 25</option>
              <option value={50}>Top 50</option>
            </select>
          </div>
          
          {/* Country Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Country (Optional)
            </label>
            <select
              data-testid="pp-reclaim-country"
              value={country}
              onChange={(e) => setCountry(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Countries</option>
              <option value="US">United States</option>
              <option value="EP">Europe (EP)</option>
              <option value="JP">Japan</option>
              <option value="CA">Canada</option>
              <option value="WO">WIPO</option>
            </select>
          </div>
          
          {/* Status Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Status *
            </label>
            <select
              data-testid="pp-reclaim-status"
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select Status</option>
              <option value="Expired">Expired</option>
              <option value="ExpiringSoon">Expiring Soon</option>
              <option value="Lapsed">Lapsed</option>
            </select>
          </div>
        </div>
        
        <button
          data-testid="pp-reclaim-generate"
          onClick={generateExport}
          disabled={loading || !status}
          className={`w-full py-3 px-4 rounded-md font-semibold text-white ${
            loading || !status
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-700 active:bg-blue-800'
          } transition-colors`}
        >
          {loading ? (
            <span className="flex items-center justify-center">
              <svg className="animate-spin h-5 w-5 mr-2" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              Generating...
            </span>
          ) : (
            `Generate ${format.toUpperCase()} Export`
          )}
        </button>
      </div>
      
      {/* Recent Exports Table */}
      <div className="bg-white rounded-lg shadow border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold">Recent Exports</h3>
        </div>
        
        <div className="overflow-x-auto">
          {exports.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              No exports yet. Generate your first reclaim pack above.
            </div>
          ) : (
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">File</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Format</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Items</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Avg Viability</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Generated</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Expires</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {exports.map((exp) => (
                  <tr key={exp.file_id} data-testid="pp-reclaim-row" className="hover:bg-gray-50">
                    <td className="px-6 py-4 text-sm text-gray-900">
                      {exp.file_name}
                      <div className="text-xs text-gray-500">{exp.size_kb} KB</div>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        exp.format === 'pdf' ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'
                      }`}>
                        {exp.format.toUpperCase()}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">{exp.items}</td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      <span className="font-mono">{exp.viability_avg.toFixed(3)}</span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {formatDate(exp.generated_at)}
                    </td>
                    <td className="px-6 py-4 text-sm">
                      {isExpired(exp.expires_at) ? (
                        <span className="text-red-600 font-medium">Expired</span>
                      ) : (
                        <span className="text-gray-600">{formatDate(exp.expires_at)}</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-sm space-x-2">
                      <a
                        data-testid="pp-reclaim-download"
                        href={`${BACKEND_URL}/api/patentpulse/reclaim/${exp.file_id}/download`}
                        className="text-blue-600 hover:text-blue-800 font-medium"
                        download
                      >
                        Download
                      </a>
                      <button
                        onClick={() => deleteExport(exp.file_id)}
                        className="text-red-600 hover:text-red-800 font-medium"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
      
      {/* Disclaimer */}
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
        <h4 className="font-semibold text-amber-900 mb-2">⚠️ Legal Disclaimer</h4>
        <p className="text-sm text-amber-800">
          Reclaim Pack exports are for <strong>internal intelligence purposes only</strong>. 
          They do not constitute legal advice or FTO clearance. Always verify freedom-to-operate 
          with qualified patent counsel before commercialization.
        </p>
      </div>
    </div>
  );
}
