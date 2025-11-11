/**
 * PatentPulse API Unit Tests
 * Tests API module correctness, credentials, and response handling
 */

import { describe, it, expect, beforeEach, jest } from '@jest/globals';

// Mock fetch globally
global.fetch = jest.fn() as jest.MockedFunction<typeof fetch>;

// Import after mocking
import { 
  getPatentItems, 
  getPatentStats, 
  getTopOpportunities 
} from '../../src/lib/patentpulse';

describe('PatentPulse API Module', () => {
  beforeEach(() => {
    // Reset mocks
    (global.fetch as jest.MockedFunction<typeof fetch>).mockReset();
  });
  
  describe('getPatentStats', () => {
    it('should call with credentials:include', async () => {
      const mockResponse = {
        total: 42,
        by_status: { Expired: 20, Lapsed: 15 },
        top_assignees: [],
        avg_commercial_score: 0.7,
        avg_synthesis_score: 0.4,
        avg_fto_risk: 0.3,
        expiring_soon_24mo: 7
      };
      
      (global.fetch as jest.MockedFunction<typeof fetch>).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      } as Response);
      
      await getPatentStats();
      
      expect(global.fetch).toHaveBeenCalledTimes(1);
      const callArgs = (global.fetch as jest.MockedFunction<typeof fetch>).mock.calls[0];
      const options = callArgs[1] as RequestInit;
      
      expect(options.credentials).toBe('include');
    });
    
    it('should include Content-Type header', async () => {
      (global.fetch as jest.MockedFunction<typeof fetch>).mockResolvedValueOnce({
        ok: true,
        json: async () => ({})
      } as Response);
      
      await getPatentStats();
      
      const callArgs = (global.fetch as jest.MockedFunction<typeof fetch>).mock.calls[0];
      const options = callArgs[1] as RequestInit;
      const headers = options.headers as Record<string, string>;
      
      expect(headers['Content-Type']).toBe('application/json');
    });
    
    it('should parse response JSON exactly once', async () => {
      const jsonMock = jest.fn().mockResolvedValue({ total: 10 });
      
      (global.fetch as jest.MockedFunction<typeof fetch>).mockResolvedValueOnce({
        ok: true,
        json: jsonMock
      } as any);
      
      const result = await getPatentStats();
      
      expect(jsonMock).toHaveBeenCalledTimes(1);
      expect(result.ok).toBe(true);
      if (result.ok) {
        expect(result.data.total).toBe(10);
      }
    });
    
    it('should handle errors without double-reading response', async () => {
      const textMock = jest.fn().mockResolvedValue('Error message');
      
      (global.fetch as jest.MockedFunction<typeof fetch>).mockResolvedValueOnce({
        ok: false,
        status: 503,
        text: textMock
      } as any);
      
      const result = await getPatentStats();
      
      expect(textMock).toHaveBeenCalledTimes(1);
      expect(result.ok).toBe(false);
      if (!result.ok) {
        expect(result.status).toBe(503);
      }
    });
  });
  
  describe('getTopOpportunities', () => {
    it('should call with credentials:include', async () => {
      (global.fetch as jest.MockedFunction<typeof fetch>).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ opportunities: [], count: 0 })
      } as Response);
      
      await getTopOpportunities(5);
      
      const callArgs = (global.fetch as jest.MockedFunction<typeof fetch>).mock.calls[0];
      const options = callArgs[1] as RequestInit;
      
      expect(options.credentials).toBe('include');
    });
    
    it('should include limit parameter in URL', async () => {
      (global.fetch as jest.MockedFunction<typeof fetch>).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ opportunities: [], count: 0 })
      } as Response);
      
      await getTopOpportunities(10);
      
      const callArgs = (global.fetch as jest.MockedFunction<typeof fetch>).mock.calls[0];
      const url = callArgs[0] as string;
      
      expect(url).toContain('limit=10');
    });
  });
  
  describe('getPatentItems', () => {
    it('should call with credentials:include', async () => {
      (global.fetch as jest.MockedFunction<typeof fetch>).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ items: [], count: 0, total: 0, skip: 0, limit: 20 })
      } as Response);
      
      await getPatentItems({ limit: 20 });
      
      const callArgs = (global.fetch as jest.MockedFunction<typeof fetch>).mock.calls[0];
      const options = callArgs[1] as RequestInit;
      
      expect(options.credentials).toBe('include');
    });
    
    it('should build query params correctly', async () => {
      (global.fetch as jest.MockedFunction<typeof fetch>).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ items: [], count: 0, total: 0, skip: 0, limit: 20 })
      } as Response);
      
      await getPatentItems({ 
        status: 'Expired', 
        country: 'US',
        min_commercial_score: 0.7,
        limit: 50 
      });
      
      const callArgs = (global.fetch as jest.MockedFunction<typeof fetch>).mock.calls[0];
      const url = callArgs[0] as string;
      
      expect(url).toContain('status_filter=Expired');
      expect(url).toContain('country=US');
      expect(url).toContain('min_commercial_score=0.7');
      expect(url).toContain('limit=50');
    });
  });
  
  describe('Error Handling', () => {
    it('should handle network errors gracefully', async () => {
      (global.fetch as jest.MockedFunction<typeof fetch>).mockRejectedValueOnce(
        new Error('Network error')
      );
      
      const result = await getPatentStats();
      
      expect(result.ok).toBe(false);
      if (!result.ok) {
        expect(result.text).toContain('Network error');
      }
    });
    
    it('should handle malformed JSON', async () => {
      (global.fetch as jest.MockedFunction<typeof fetch>).mockResolvedValueOnce({
        ok: true,
        json: async () => {
          throw new Error('Unexpected token');
        }
      } as Response);
      
      const result = await getPatentStats();
      
      expect(result.ok).toBe(false);
    });
  });
  
  describe('Response Body Consumption', () => {
    it('should not attempt to read response body twice', async () => {
      const jsonMock = jest.fn()
        .mockResolvedValueOnce({ total: 10 })
        .mockRejectedValueOnce(new Error('Body already used'));
      
      (global.fetch as jest.MockedFunction<typeof fetch>).mockResolvedValueOnce({
        ok: true,
        json: jsonMock
      } as any);
      
      const result = await getPatentStats();
      
      // Should only call json() once
      expect(jsonMock).toHaveBeenCalledTimes(1);
      expect(result.ok).toBe(true);
    });
    
    it('should handle text() call for errors without double-read', async () => {
      const textMock = jest.fn()
        .mockResolvedValueOnce('Error details')
        .mockRejectedValueOnce(new Error('Body already used'));
      
      (global.fetch as jest.MockedFunction<typeof fetch>).mockResolvedValueOnce({
        ok: false,
        status: 500,
        text: textMock
      } as any);
      
      const result = await getPatentStats();
      
      // Should only call text() once
      expect(textMock).toHaveBeenCalledTimes(1);
      expect(result.ok).toBe(false);
    });
  });
});

describe('fetchJSON base utility', () => {
  it('should merge credentials with custom options', async () => {
    (global.fetch as jest.MockedFunction<typeof fetch>).mockResolvedValueOnce({
      ok: true,
      json: async () => ({})
    } as Response);
    
    const { fetchJSON } = await import('../../src/lib/http');
    
    await fetchJSON('http://example.com/api/test', {
      method: 'POST',
      headers: { 'X-Custom': 'value' }
    });
    
    const callArgs = (global.fetch as jest.MockedFunction<typeof fetch>).mock.calls[0];
    const options = callArgs[1] as RequestInit;
    
    // Should have both credentials and custom options
    expect(options.credentials).toBe('include');
    expect(options.method).toBe('POST');
    expect((options.headers as any)['X-Custom']).toBe('value');
  });
});
