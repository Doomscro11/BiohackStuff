/**
 * Auth API Unit Tests
 * Tests email validation, OTP validation, and request/verify flow wiring.
 */

import { describe, it, expect, beforeEach, jest } from '@jest/globals';

// Mock fetch globally
global.fetch = jest.fn() as jest.MockedFunction<typeof fetch>;

// Import after mocking
import {
  requestMagicCode,
  verifyMagicCode,
  getCurrentUser,
  logout,
  isValidEmail,
  isValidOTP,
} from '../../src/lib/auth';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

describe('Auth API Module', () => {
  beforeEach(() => {
    (global.fetch as jest.MockedFunction<typeof fetch>).mockReset();
  });

  describe('validation helpers', () => {
    it('validates email format', () => {
      expect(isValidEmail('admin@example.com')).toBe(true);
      expect(isValidEmail('not-an-email')).toBe(false);
      expect(isValidEmail('')).toBe(false);
    });

    it('validates 6-digit OTP format', () => {
      expect(isValidOTP('123456')).toBe(true);
      expect(isValidOTP('12345')).toBe(false);
      expect(isValidOTP('abcdef')).toBe(false);
      expect(isValidOTP('1234567')).toBe(false);
    });
  });

  describe('requestMagicCode', () => {
    it('posts email to the magic request endpoint', async () => {
      (global.fetch as jest.MockedFunction<typeof fetch>).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true, message: 'Magic code sent' }),
      } as Response);

      await requestMagicCode('admin@example.com');

      const [url, init] = (global.fetch as jest.MockedFunction<typeof fetch>)
        .mock.calls[0];
      expect(url).toBe(`${BACKEND_URL}/api/auth/magic/request`);
      expect((init as RequestInit).method).toBe('POST');
      expect(JSON.parse((init as RequestInit).body as string)).toEqual({
        email: 'admin@example.com',
      });
    });

    it('surfaces backend error detail on failure', async () => {
      (global.fetch as jest.MockedFunction<typeof fetch>).mockResolvedValueOnce({
        ok: false,
        status: 429,
        json: async () => ({
          detail: 'Please wait 60 seconds before requesting another code.',
        }),
      } as Response);

      await expect(requestMagicCode('admin@example.com')).rejects.toThrow(
        'Please wait 60 seconds before requesting another code.'
      );
    });
  });

  describe('verifyMagicCode', () => {
    it('posts email and code with credentials include', async () => {
      (global.fetch as jest.MockedFunction<typeof fetch>).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true, role: 'admin' }),
      } as Response);

      await verifyMagicCode('admin@example.com', '123456');

      const [url, init] = (global.fetch as jest.MockedFunction<typeof fetch>)
        .mock.calls[0];
      expect(url).toBe(`${BACKEND_URL}/api/auth/magic/verify`);
      expect((init as RequestInit).method).toBe('POST');
      expect((init as RequestInit).credentials).toBe('include');
      expect(JSON.parse((init as RequestInit).body as string)).toEqual({
        email: 'admin@example.com',
        code: '123456',
      });
    });
  });

  describe('getCurrentUser', () => {
    it('returns user info when authenticated', async () => {
      (global.fetch as jest.MockedFunction<typeof fetch>).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ id: '1', email: 'a@b.com', role: 'researcher' }),
      } as Response);

      const user = await getCurrentUser();
      expect(user?.email).toBe('a@b.com');
    });

    it('returns null without error when not authenticated', async () => {
      (global.fetch as jest.MockedFunction<typeof fetch>).mockResolvedValueOnce({
        ok: false,
        status: 401,
      } as Response);

      const user = await getCurrentUser();
      expect(user).toBeNull();
    });
  });

  describe('logout', () => {
    it('posts to the logout endpoint', async () => {
      (global.fetch as jest.MockedFunction<typeof fetch>).mockResolvedValueOnce({
        ok: true,
      } as Response);

      await logout();

      const [url, init] = (global.fetch as jest.MockedFunction<typeof fetch>)
        .mock.calls[0];
      expect(url).toBe(`${BACKEND_URL}/api/auth/logout`);
      expect((init as RequestInit).method).toBe('POST');
    });
  });
});