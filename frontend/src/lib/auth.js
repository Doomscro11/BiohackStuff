// Authentication utilities for Peptimancer Admin
import { fetchJSON } from './http';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

/**
 * Request a magic code (OTP) to be sent to the user's email
 */
export async function requestMagicCode(email): Promise<AuthResponse> {
  const result = await fetchJSON(`${BACKEND_URL}/api/auth/magic/request`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email })
  });

  if (!result.ok) {
    throw new Error(result.text || 'Failed to request magic code');
  }

  return result.data;
}

/**
 * Verify the magic code and authenticate the user
 */
export async function verifyMagicCode(email, code): Promise<VerifyResponse> {
  const result = await fetchJSON(`${BACKEND_URL}/api/auth/magic/verify`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include', // Include cookies
    body: JSON.stringify({ email, code })
  });

  if (!result.ok) {
    throw new Error(result.text || 'Failed to verify magic code');
  }

  return result.data;
}

/**
 * Get current user information
 */
export async function getCurrentUser(): Promise<UserInfo | null> {
  const result = await fetchJSON(`${BACKEND_URL}/api/auth/me`, {
    credentials: 'include'
  });

  if (!result.ok) {
    // Silently return null for unauthorized requests
    return null;
  }

  return result.data;
}

/**
 * Logout the current user
 */
export async function logout(): Promise<void> {
  const result = await fetchJSON(`${BACKEND_URL}/api/auth/logout`, {
    method: 'POST',
    credentials: 'include'
  });

  if (!result.ok) {
    throw new Error(result.text || 'Failed to logout');
  }
}

/**
 * Check admin configuration status
 */
export async function getAdminStatus() {
  const response = await fetch(`${BACKEND_URL}/api/auth/admin/status`);
  
  if (!response.ok) {
    throw new Error('Failed to get admin status');
  }

  return response.json();
}

/**
 * Validate email format
 */
export function isValidEmail(email) {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

/**
 * Validate OTP code format
 */
export function isValidOTP(code) {
  return /^\d{6}$/.test(code);
}

/**
 * Format time remaining for OTP expiry
 */
export function formatTimeRemaining(expiresInMinutes, startTime: Date) {
  const now = new Date();
  const elapsed = Math.floor((now.getTime() - startTime.getTime()) / 1000 / 60);
  const remaining = Math.max(0, expiresInMinutes - elapsed);
  
  if (remaining === 0) {
    return 'Expired';
  }
  
  return `${remaining} minute${remaining === 1 ? '' : 's'} remaining`;
}