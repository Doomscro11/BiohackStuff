// Admin Gate Component - Authentication for Admin Panel
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Shield, Mail, Lock, AlertCircle, CheckCircle, Clock, LogOut } from 'lucide-react';

import AdminModeSwitch from './AdminModeSwitch.tsx';
import AdminHealthCard from './AdminHealthCard.tsx';
import AdminUsersPanel from './AdminUsersPanel.tsx';
import Admin2FA from './Admin2FA.tsx';
import { 
  requestMagicCode, 
  verifyMagicCode, 
  getCurrentUser, 
  logout, 
  getAdminStatus,
  isValidEmail, 
  isValidOTP, 
  formatTimeRemaining,
  type UserInfo,
  type AuthResponse 
} from '../../lib/auth.ts';

interface AdminStatus {
  admin_emails_configured: boolean;
  demo_mode: boolean;
  otp_length: number;
  otp_expires_minutes: number;
}

export default function AdminGate() {
  // Authentication state
  const [email, setEmail] = useState('');
  const [code, setCode] = useState('');
  const [authResponse, setAuthResponse] = useState<AuthResponse | null>(null);
  const [user, setUser] = useState<UserInfo | null>(null);
  const [adminStatus, setAdminStatus] = useState<AdminStatus | null>(null);
  
  // UI state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [codeRequestTime, setCodeRequestTime] = useState<Date | null>(null);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);

  // Check for existing authentication on mount
  useEffect(() => {
    checkExistingAuth();
    loadAdminStatus();
  }, []);

  // Timer for OTP expiry countdown
  useEffect(() => {
    if (authResponse && codeRequestTime) {
      const timer = setInterval(() => {
        setAuthResponse(prev => prev ? {...prev} : null); // Trigger re-render
      }, 60000); // Update every minute

      return () => clearInterval(timer);
    }
  }, [authResponse, codeRequestTime]);

  const checkExistingAuth = async () => {
    try {
      const currentUser = await getCurrentUser();
      setUser(currentUser);
    } catch (error) {
      console.log('No existing authentication');
    } finally {
      setIsCheckingAuth(false);
    }
  };

  const loadAdminStatus = async () => {
    try {
      const status = await getAdminStatus();
      setAdminStatus(status);
    } catch (error) {
      console.error('Failed to load admin status:', error);
    }
  };

  const handleRequestCode = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!isValidEmail(email)) {
      setError('Please enter a valid email address');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await requestMagicCode(email);
      setAuthResponse(response);
      setCodeRequestTime(new Date());
    } catch (error: any) {
      setError(error.message || 'Failed to send magic code');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyCode = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!isValidOTP(code)) {
      setError('Please enter a valid 6-digit code');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await verifyMagicCode(email, code);
      
      // Refresh user info after successful verification
      const userInfo = await getCurrentUser();
      setUser(userInfo);
      
      // Clear form state
      setAuthResponse(null);
      setCode('');
      setCodeRequestTime(null);
      
    } catch (error: any) {
      setError(error.message || 'Failed to verify code');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    setLoading(true);
    try {
      await logout();
      setUser(null);
      setEmail('');
      setCode('');
      setAuthResponse(null);
      setCodeRequestTime(null);
    } catch (error: any) {
      setError(error.message || 'Failed to logout');
    } finally {
      setLoading(false);
    }
  };

  const handleResendCode = async () => {
    await handleRequestCode(new Event('submit') as any);
  };

  // Show loading state while checking existing auth
  if (isCheckingAuth) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600" />
        <span className="ml-2">Checking authentication...</span>
      </div>
    );
  }

  // Show admin panel if user is authenticated and is admin
  if (user?.is_admin) {
    return (
      <div className="space-y-6">
        {/* User info header */}
        <div className="flex items-center justify-between p-4 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-center gap-3">
            <CheckCircle className="h-5 w-5 text-green-600" />
            <div>
              <p className="font-medium text-green-800">Authenticated as Admin</p>
              <p className="text-sm text-green-600">{user.email}</p>
            </div>
          </div>
          <Button 
            variant="outline" 
            size="sm" 
            onClick={handleLogout}
            disabled={loading}
            className="text-gray-600"
          >
            <LogOut className="h-4 w-4 mr-1" />
            Logout
          </Button>
        </div>

        {/* Phase VII: System Health Monitoring */}
        <AdminHealthCard />

        {/* Admin Mode Switch Component */}
        <AdminModeSwitch />

        {/* Phase VII: User & Tier Management */}
        <AdminUsersPanel />
      </div>
    );
  }

  // Show access denied if user is authenticated but not admin
  if (user && !user.is_admin) {
    return (
      <Card className="max-w-md mx-auto">
        <CardContent className="pt-6">
          <div className="text-center space-y-4">
            <AlertCircle className="h-12 w-12 text-yellow-500 mx-auto" />
            <div>
              <h3 className="font-semibold text-lg">Access Denied</h3>
              <p className="text-gray-600">You are signed in as <strong>{user.email}</strong></p>
              <p className="text-sm text-gray-500">Admin access required for this panel.</p>
            </div>
            <Button 
              variant="outline" 
              onClick={handleLogout}
              disabled={loading}
            >
              <LogOut className="h-4 w-4 mr-1" />
              Sign Out
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Show authentication form
  return (
    <div className="max-w-md mx-auto space-y-4">
      {/* Admin Status Info */}
      {adminStatus && !adminStatus.admin_emails_configured && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Admin emails not configured. Contact system administrator.
          </AlertDescription>
        </Alert>
      )}

      {adminStatus?.demo_mode && (
        <Alert className="border-blue-200 bg-blue-50">
          <AlertCircle className="h-4 w-4 text-blue-600" />
          <AlertDescription className="text-blue-800">
            Demo mode enabled - OTP codes will be displayed for testing.
          </AlertDescription>
        </Alert>
      )}

      <Card>
        <CardHeader className="text-center">
          <div className="flex justify-center mb-2">
            <div className="p-3 bg-blue-100 rounded-full">
              <Shield className="h-6 w-6 text-blue-600" />
            </div>
          </div>
          <CardTitle>Admin Authentication</CardTitle>
          <CardDescription>
            Enter your admin email to receive a verification code
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-4">
          {!authResponse ? (
            // Email form
            <form onSubmit={handleRequestCode} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">Admin Email</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                  <Input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="admin@yourcompany.com"
                    className="pl-10"
                    disabled={loading}
                    required
                  />
                </div>
              </div>

              <Button 
                type="submit" 
                className="w-full" 
                disabled={loading || !email}
              >
                {loading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                    Sending Code...
                  </>
                ) : (
                  <>
                    <Mail className="h-4 w-4 mr-2" />
                    Send Verification Code
                  </>
                )}
              </Button>
            </form>
          ) : (
            // Verification code form
            <form onSubmit={handleVerifyCode} className="space-y-4">
              <div className="text-center space-y-2">
                <CheckCircle className="h-8 w-8 text-green-500 mx-auto" />
                <p className="font-medium">Code sent to {email}</p>
                {codeRequestTime && authResponse.expires_in_minutes && (
                  <p className="text-sm text-gray-500 flex items-center justify-center gap-1">
                    <Clock className="h-3 w-3" />
                    {formatTimeRemaining(authResponse.expires_in_minutes, codeRequestTime)}
                  </p>
                )}
              </div>

              {/* Demo code display */}
              {authResponse.demo_code && (
                <Alert className="border-yellow-200 bg-yellow-50">
                  <AlertCircle className="h-4 w-4 text-yellow-600" />
                  <AlertDescription className="text-yellow-800">
                    <strong>Demo Code:</strong> {authResponse.demo_code}
                  </AlertDescription>
                </Alert>
              )}

              <div className="space-y-2">
                <Label htmlFor="code">Verification Code</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                  <Input
                    id="code"
                    type="text"
                    value={code}
                    onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                    placeholder="000000"
                    className="pl-10 text-center text-lg tracking-widest"
                    disabled={loading}
                    maxLength={6}
                    required
                  />
                </div>
              </div>

              <Button 
                type="submit" 
                className="w-full" 
                disabled={loading || code.length !== 6}
              >
                {loading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                    Verifying...
                  </>
                ) : (
                  <>
                    <Lock className="h-4 w-4 mr-2" />
                    Verify & Sign In
                  </>
                )}
              </Button>

              <div className="flex justify-between items-center text-sm">
                <Button 
                  type="button"
                  variant="ghost" 
                  size="sm"
                  onClick={() => {
                    setAuthResponse(null);
                    setCode('');
                    setCodeRequestTime(null);
                  }}
                  className="text-gray-500"
                >
                  ← Change Email
                </Button>
                
                <Button 
                  type="button"
                  variant="ghost" 
                  size="sm"
                  onClick={handleResendCode}
                  disabled={loading}
                  className="text-blue-600"
                >
                  Resend Code
                </Button>
              </div>
            </form>
          )}

          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <div className="text-center pt-4 border-t">
            <p className="text-xs text-gray-500">
              Only authorized admin emails can access this panel.
              <br />
              Contact your system administrator for access.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}