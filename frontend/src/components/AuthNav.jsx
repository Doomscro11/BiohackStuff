// Session-aware authentication nav control.
import React, { useState, useEffect } from 'react';
import { LogIn, LogOut, User } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { getCurrentUser, logout } from '../lib/auth.ts';
import { fetchSession } from '../lib/session.ts';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export default function AuthNav() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loggingOut, setLoggingOut] = useState(false);

  useEffect(() => {
    loadUser();
  }, []);

  const loadUser = async () => {
    setLoading(true);
    try {
      const current = await getCurrentUser();
      setUser(current);
      if (current) {
        const session = await fetchSession();
        if (session && typeof session.credits === 'number') {
          window.dispatchEvent(new CustomEvent('credits:update', {
            detail: { credits: session.credits }
          }));
        }
      }
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    setLoggingOut(true);
    try {
      await logout();
      setUser(null);
      window.dispatchEvent(new CustomEvent('credits:update', {
        detail: { credits: 0 }
      }));
    } catch (err) {
      // Best-effort logout
      setUser(null);
    } finally {
      setLoggingOut(false);
    }
  };

  if (loading) {
    return null;
  }

  if (user) {
    return (
      <div className="flex items-center gap-2">
        <div className="flex items-center gap-1.5 px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded-full text-sm text-gray-700 dark:text-gray-200">
          <User className="h-4 w-4 text-gray-500" />
          <span className="max-w-[160px] truncate">{user.email}</span>
        </div>
        <Button variant="ghost" size="sm" onClick={handleLogout} disabled={loggingOut}>
          {loggingOut ? (
            <span className="animate-spin border-2 border-gray-400 h-4 w-4 rounded-full" />
          ) : (
            <>
              <LogOut className="h-4 w-4 mr-1" />
              Sign Out
            </>
          )}
        </Button>
      </div>
    );
  }

  return (
    <Button variant="ghost" size="sm" onClick={() => (window.location.href = '/admin')}>
      <LogIn className="h-4 w-4 mr-1" />
      Sign In
    </Button>
  );
}