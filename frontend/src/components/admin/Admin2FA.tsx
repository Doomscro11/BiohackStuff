// Admin 2FA (TOTP) Component
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Shield, Key, CheckCircle, AlertCircle, QrCode } from 'lucide-react';
import AdminHealthCard from './AdminHealthCard.tsx';
import AdminModeSwitch from './AdminModeSwitch.tsx';
import AdminUsersPanel from './AdminUsersPanel.tsx';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export default function Admin2FA() {
  const [uri, setUri] = useState<string>('');
  const [code, setCode] = useState('');
  const [verified, setVerified] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [email, setEmail] = useState('');

  // Check if already verified (has admin2fa cookie)
  useEffect(() => {
    checkVerificationStatus();
  }, []);

  const checkVerificationStatus = async () => {
    // Check if admin2fa cookie exists by making a test request
    try {
      const response = await fetch(`${BACKEND_URL}/api/admin/settings`, {
        credentials: 'include'
      });
      
      if (response.ok) {
        setVerified(true);
      }
    } catch (err) {
      // Not verified yet
    }
  };

  const startSetup = async () => {
    try {
      setLoading(true);
      setError('');
      
      const response = await fetch(`${BACKEND_URL}/api/auth/2fa/start`, {
        method: 'POST',
        credentials: 'include'
      });

      if (!response.ok) {
        throw new Error('Failed to start 2FA setup');
      }

      const data = await response.json();
      setUri(data.otpauth);
      setEmail(data.email);
    } catch (err: any) {
      setError(err.message || 'Failed to start 2FA setup');
    } finally {
      setLoading(false);
    }
  };

  const verifyCode = async () => {
    if (!code || code.length !== 6) {
      setError('Please enter a 6-digit code');
      return;
    }

    try {
      setLoading(true);
      setError('');

      const response = await fetch(`${BACKEND_URL}/api/auth/2fa/verify`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify({ code })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Invalid 2FA code');
      }

      setVerified(true);
      setCode('');
      // No need to reload - state change will show admin panels
    } catch (err: any) {
      setError(err.message || 'Verification failed');
    } finally {
      setLoading(false);
    }
  };

  if (verified) {
    return (
      <>
        <Card className="border-green-200 bg-green-50">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <CheckCircle className="h-6 w-6 text-green-600" />
              <div>
                <p className="font-medium text-green-800">2FA Verified</p>
                <p className="text-sm text-green-600">You have elevated admin access for 30 minutes</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Phase VII & 7.1: Admin Panels - Only shown after 2FA */}
        <AdminHealthCard />
        <AdminModeSwitch />
        <AdminUsersPanel />
      </>
    );
  }

  return (
    <Card className="border-amber-200 bg-amber-50">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Shield className="h-5 w-5 text-amber-600" />
          Admin 2FA Required
        </CardTitle>
        <CardDescription>
          Two-factor authentication is required to access admin controls
        </CardDescription>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {!uri && (
          <div className="space-y-3">
            <p className="text-sm text-gray-600">
              Set up time-based one-time passwords (TOTP) using an authenticator app like:
            </p>
            <ul className="text-sm text-gray-600 list-disc list-inside space-y-1">
              <li>Google Authenticator</li>
              <li>1Password</li>
              <li>Authy</li>
              <li>Microsoft Authenticator</li>
            </ul>
            <Button 
              onClick={startSetup} 
              disabled={loading}
              className="w-full bg-emerald-600 hover:bg-emerald-700"
            >
              <Key className="h-4 w-4 mr-2" />
              {loading ? 'Loading...' : 'Generate 2FA Secret'}
            </Button>
          </div>
        )}

        {uri && (
          <div className="space-y-4">
            <div className="p-4 bg-white border rounded-lg">
              <div className="flex items-start gap-3 mb-3">
                <QrCode className="h-5 w-5 text-gray-500 mt-0.5" />
                <div className="flex-1">
                  <h4 className="font-semibold text-sm mb-1">Scan QR Code</h4>
                  <p className="text-xs text-gray-600">
                    Open your authenticator app and scan this code. If you can't scan, copy the text below.
                  </p>
                </div>
              </div>
              
              <div className="p-3 bg-gray-50 border rounded text-xs break-all font-mono">
                {uri}
              </div>
              
              {email && (
                <p className="text-xs text-gray-500 mt-2">
                  Account: <span className="font-medium">{email}</span>
                </p>
              )}
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-700">
                Enter 6-digit code from your authenticator app:
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  className="flex-1 px-4 py-2 border rounded-lg text-center text-lg font-mono tracking-widest"
                  placeholder="123456"
                  maxLength={6}
                  value={code}
                  onChange={(e) => {
                    const value = e.target.value.replace(/[^0-9]/g, '');
                    setCode(value);
                  }}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && code.length === 6) {
                      verifyCode();
                    }
                  }}
                />
                <Button 
                  onClick={verifyCode}
                  disabled={loading || code.length !== 6}
                  className="bg-emerald-600 hover:bg-emerald-700"
                >
                  {loading ? 'Verifying...' : 'Verify'}
                </Button>
              </div>
            </div>

            {error && (
              <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg">
                <AlertCircle className="h-4 w-4 text-red-600" />
                <p className="text-sm text-red-700">{error}</p>
              </div>
            )}

            <p className="text-xs text-gray-500">
              💡 Tip: The code changes every 30 seconds. Enter it quickly after it appears.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
