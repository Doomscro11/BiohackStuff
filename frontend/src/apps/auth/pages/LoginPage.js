import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { fetchJSON } from '@/lib/http';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

function LoginPage() {
  const [email, setEmail] = useState('');
  const [code, setCode] = useState('');
  const [step, setStep] = useState('email'); // 'email' or 'code'
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [demoCode, setDemoCode] = useState('');
  
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const returnTo = searchParams.get('returnTo') || '/';

  // Note: Session check removed to avoid race condition with MainApp
  // MainApp already handles session management and will redirect if authenticated

  const handleRequestCode = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const result = await fetchJSON(`${BACKEND_URL}/api/auth/magic/request`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email })
    });

    if (result.ok && result.data) {
      if (result.data.demo_code) {
        setDemoCode(result.data.demo_code);
      }
      setStep('code');
    } else {
      setError(result.text || 'Failed to send magic code');
    }

    setLoading(false);
  };

  const handleVerifyCode = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const result = await fetchJSON(`${BACKEND_URL}/api/auth/magic/verify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, code })
    });

    if (result.ok && result.data && result.data.success) {
      // Redirect based on role and returnTo
      if (result.data.role === 'admin' && returnTo === '/') {
        navigate('/admin');
      } else {
        navigate(returnTo);
      }
    } else {
      setError(result.text || 'Invalid or expired code');
      setCode('');
    }

    setLoading(false);
  };

  const handleBack = () => {
    setStep('email');
    setCode('');
    setDemoCode('');
    setError('');
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 px-4">
      <div className="max-w-md w-full">
        {/* Logo and Title */}
        <div className="text-center mb-8">
          <div className="text-5xl mb-4">🧬</div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            Welcome to Peptimancer
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Sign in with your email to continue
          </p>
        </div>

        {/* Login Form Card */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-8">
          {step === 'email' ? (
            <form onSubmit={handleRequestCode}>
              <div className="mb-6">
                <label htmlFor="email" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Email Address
                </label>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  required
                  className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
                  disabled={loading}
                />
              </div>

              {error && (
                <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-700 dark:text-red-400 text-sm">
                  {error}
                </div>
              )}

              <Button
                type="submit"
                className="w-full py-3 text-base"
                disabled={loading || !email}
              >
                {loading ? 'Sending...' : 'Send Magic Code'}
              </Button>

              <p className="mt-4 text-xs text-gray-500 dark:text-gray-400 text-center">
                We'll send a 6-digit code to your email. No passwords needed!
              </p>
            </form>
          ) : (
            <form onSubmit={handleVerifyCode}>
              <div className="mb-4">
                <button
                  type="button"
                  onClick={handleBack}
                  className="text-sm text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1"
                >
                  ← Change email
                </button>
              </div>

              <div className="mb-6">
                <label htmlFor="code" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Enter 6-Digit Code
                </label>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                  Sent to <strong>{email}</strong>
                </p>
                <input
                  id="code"
                  type="text"
                  value={code}
                  onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  placeholder="123456"
                  required
                  maxLength="6"
                  className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white text-center text-2xl tracking-widest font-mono"
                  disabled={loading}
                  autoFocus
                />
              </div>

              {demoCode && (
                <div className="mb-4 p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
                  <p className="text-sm text-yellow-800 dark:text-yellow-400 font-medium mb-1">
                    Demo Mode
                  </p>
                  <p className="text-sm text-yellow-700 dark:text-yellow-300">
                    Your code: <span className="font-mono font-bold text-lg">{demoCode}</span>
                  </p>
                </div>
              )}

              {error && (
                <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-700 dark:text-red-400 text-sm">
                  {error}
                </div>
              )}

              <Button
                type="submit"
                className="w-full py-3 text-base"
                disabled={loading || code.length !== 6}
              >
                {loading ? 'Verifying...' : 'Verify & Sign In'}
              </Button>

              <p className="mt-4 text-xs text-gray-500 dark:text-gray-400 text-center">
                Didn't receive a code?{' '}
                <button
                  type="button"
                  onClick={handleBack}
                  className="text-blue-600 dark:text-blue-400 hover:underline"
                >
                  Try again
                </button>
              </p>
            </form>
          )}
        </div>

        {/* Footer */}
        <p className="mt-6 text-center text-sm text-gray-600 dark:text-gray-400">
          By signing in, you agree to our Terms of Service and Privacy Policy
        </p>
      </div>
    </div>
  );
}

export default LoginPage;
