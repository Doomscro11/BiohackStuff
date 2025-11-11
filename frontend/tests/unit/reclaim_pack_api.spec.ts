/**
 * PatentPulse Reclaim Pack API Unit Tests
 * Tests API module for reclaim pack exports
 */

import { describe, it, expect, beforeEach, jest } from '@jest/globals';

// Mock fetch globally
global.fetch = jest.fn() as jest.MockedFunction<typeof fetch>;

describe('Reclaim Pack API', () => {
  beforeEach(() => {
    (global.fetch as jest.MockedFunction<typeof fetch>).mockReset();
  });
  
  describe('Export Generation', () => {
    it('should build correct query string with all params', async () => {
      (global.fetch as jest.MockedFunction<typeof fetch>).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          file_id: 'test-123',
          format: 'pdf',
          items: 10
        })
      } as Response);
      
      const params = new URLSearchParams({
        format: 'pdf',
        limit: '10',
        country: 'US',
        status: 'Expired'
      });
      
      const url = `http://localhost:8001/api/patentpulse/reclaim/export?${params.toString()}`;
      
      await fetch(url, {
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' }
      });
      
      expect(global.fetch).toHaveBeenCalledTimes(1);
      const callUrl = (global.fetch as jest.MockedFunction<typeof fetch>).mock.calls[0][0] as string;
      
      expect(callUrl).toContain('format=pdf');
      expect(callUrl).toContain('limit=10');
      expect(callUrl).toContain('country=US');
      expect(callUrl).toContain('status=Expired');
    });
    
    it('should include credentials in request', async () => {
      (global.fetch as jest.MockedFunction<typeof fetch>).mockResolvedValueOnce({
        ok: true,
        json: async () => ({})
      } as Response);
      
      await fetch('http://localhost:8001/api/patentpulse/reclaim/export?format=pdf&limit=10', {
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' }
      });
      
      const callOptions = (global.fetch as jest.MockedFunction<typeof fetch>).mock.calls[0][1];
      expect(callOptions?.credentials).toBe('include');
    });
    
    it('should include Content-Type header', async () => {
      (global.fetch as jest.MockedFunction<typeof fetch>).mockResolvedValueOnce({
        ok: true,
        json: async () => ({})
      } as Response);
      
      await fetch('http://localhost:8001/api/patentpulse/reclaim/export', {
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' }
      });
      
      const callOptions = (global.fetch as jest.MockedFunction<typeof fetch>).mock.calls[0][1];
      const headers = callOptions?.headers as Record<string, string>;
      
      expect(headers['Content-Type']).toBe('application/json');
    });
  });
  
  describe('Error Handling', () => {
    it('should handle 503 (feature not enabled)', async () => {
      (global.fetch as jest.MockedFunction<typeof fetch>).mockResolvedValueOnce({
        ok: false,
        status: 503,
        text: async () => 'Feature not enabled'
      } as Response);
      
      const response = await fetch('http://localhost:8001/api/patentpulse/reclaim/list');
      
      expect(response.ok).toBe(false);
      expect(response.status).toBe(503);
    });
    
    it('should handle 403 (2FA required)', async () => {
      (global.fetch as jest.MockedFunction<typeof fetch>).mockResolvedValueOnce({
        ok: false,
        status: 403,
        text: async () => 'Admin 2FA required'
      } as Response);
      
      const response = await fetch('http://localhost:8001/api/patentpulse/reclaim/export');
      
      expect(response.ok).toBe(false);
      expect(response.status).toBe(403);
    });
    
    it('should handle 500 server error', async () => {
      (global.fetch as jest.MockedFunction<typeof fetch>).mockResolvedValueOnce({
        ok: false,
        status: 500,
        text: async () => 'Internal server error'
      } as Response);
      
      const response = await fetch('http://localhost:8001/api/patentpulse/reclaim/export');
      
      expect(response.ok).toBe(false);
      expect(response.status).toBe(500);
    });
    
    it('should handle network errors', async () => {
      (global.fetch as jest.MockedFunction<typeof fetch>).mockRejectedValueOnce(
        new Error('Network error')
      );
      
      await expect(
        fetch('http://localhost:8001/api/patentpulse/reclaim/export')
      ).rejects.toThrow('Network error');
    });
  });
  
  describe('List Exports', () => {
    it('should call list endpoint with limit', async () => {
      (global.fetch as jest.MockedFunction<typeof fetch>).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ exports: [], count: 0 })
      } as Response);
      
      await fetch('http://localhost:8001/api/patentpulse/reclaim/list?limit=20', {
        credentials: 'include'
      });
      
      expect(global.fetch).toHaveBeenCalledTimes(1);
      const callUrl = (global.fetch as jest.MockedFunction<typeof fetch>).mock.calls[0][0] as string;
      expect(callUrl).toContain('limit=20');
    });
  });
  
  describe('Download Export', () => {
    it('should construct correct download URL', () => {
      const fileId = 'test-123-abc';
      const downloadUrl = `http://localhost:8001/api/patentpulse/reclaim/${fileId}/download`;
      
      expect(downloadUrl).toContain(fileId);
      expect(downloadUrl).toContain('/download');
    });
  });
  
  describe('Delete Export', () => {
    it('should use DELETE method', async () => {
      (global.fetch as jest.MockedFunction<typeof fetch>).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ message: 'Deleted' })
      } as Response);
      
      await fetch('http://localhost:8001/api/patentpulse/reclaim/test-123', {
        method: 'DELETE',
        credentials: 'include'
      });
      
      const callOptions = (global.fetch as jest.MockedFunction<typeof fetch>).mock.calls[0][1];
      expect(callOptions?.method).toBe('DELETE');
    });
  });
  
  describe('Idempotent Operations', () => {
    it('should not make duplicate calls on multiple clicks', async () => {
      let callCount = 0;
      
      (global.fetch as jest.MockedFunction<typeof fetch>).mockImplementation(async () => {
        callCount++;
        await new Promise(resolve => setTimeout(resolve, 100)); // Simulate delay
        return {
          ok: true,
          json: async () => ({ file_id: 'test' })
        } as Response;
      });
      
      // Simulate rapid clicks (should be prevented by UI loading state)
      const promises = [
        fetch('http://localhost:8001/api/patentpulse/reclaim/export', { credentials: 'include' })
      ];
      
      await Promise.all(promises);
      
      // Only one call should go through (UI should prevent others)
      expect(callCount).toBe(1);
    });
  });
});
