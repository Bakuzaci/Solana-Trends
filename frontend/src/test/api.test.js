import { describe, it, expect, beforeEach, vi } from 'vitest';
import * as api from '../api/client';

// Mock fetch globally
global.fetch = vi.fn();

describe('API Client', () => {
  beforeEach(() => {
    fetch.mockClear();
  });

  it('fetchTrends returns data', async () => {
    const mockData = [
      { category: 'Animals', sub_category: 'Dogs', coin_count: 10 }
    ];

    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockData,
    });

    const result = await api.fetchTrends();
    expect(result).toEqual(mockData);
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/trends')
    );
  });

  it('handles API errors gracefully with fallback', async () => {
    fetch.mockRejectedValueOnce(new Error('Network error'));

    // Should fall back to mock data instead of throwing
    const result = await api.fetchTrends();
    expect(Array.isArray(result)).toBe(true);
  });
});
