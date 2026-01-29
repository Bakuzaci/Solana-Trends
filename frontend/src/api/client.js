const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

import { mockTrends, mockCoins, mockHistory, mockBreakoutMetas } from '../mock/data';

// Helper function to handle API responses
const handleResponse = async (response) => {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP error! status: ${response.status}`);
  }
  return response.json();
};

// Fetch trends with time window and sort options
export const fetchTrends = async (timeWindow = '24h', sortBy = 'acceleration') => {
  try {
    const response = await fetch(
      `${API_URL}/api/trends?time_window=${timeWindow}&sort_by=${sortBy}`
    );
    return handleResponse(response);
  } catch (error) {
    console.warn('API unavailable, using mock data:', error.message);
    // Return mock data sorted appropriately
    const sorted = [...mockTrends].sort((a, b) => {
      if (sortBy === 'acceleration') return b.acceleration_score - a.acceleration_score;
      if (sortBy === 'market_cap') return b.total_market_cap - a.total_market_cap;
      if (sortBy === 'coin_count') return b.coin_count - a.coin_count;
      return 0;
    });
    return sorted;
  }
};

// Fetch acceleration data for trends
export const fetchAcceleration = async (timeWindow = '24h') => {
  try {
    const response = await fetch(
      `${API_URL}/api/acceleration?time_window=${timeWindow}`
    );
    return handleResponse(response);
  } catch (error) {
    console.warn('API unavailable, using mock data:', error.message);
    return mockTrends.map(t => ({
      category: t.category,
      sub_category: t.sub_category,
      acceleration_score: t.acceleration_score,
      trend_direction: t.trend_direction,
      velocity: t.velocity
    }));
  }
};

// Fetch coins for a specific trend category
export const fetchCoins = async (category, subCategory = null, limit = 50) => {
  try {
    let url = `${API_URL}/api/coins?category=${encodeURIComponent(category)}&limit=${limit}`;
    if (subCategory) {
      url += `&sub_category=${encodeURIComponent(subCategory)}`;
    }
    const response = await fetch(url);
    return handleResponse(response);
  } catch (error) {
    console.warn('API unavailable, using mock data:', error.message);
    return mockCoins.filter(c => c.category === category);
  }
};

// Fetch historical trend data
export const fetchHistory = async (category, subCategory = null, timeWindow = '7d') => {
  try {
    let url = `${API_URL}/api/history?category=${encodeURIComponent(category)}&time_window=${timeWindow}`;
    if (subCategory) {
      url += `&sub_category=${encodeURIComponent(subCategory)}`;
    }
    const response = await fetch(url);
    return handleResponse(response);
  } catch (error) {
    console.warn('API unavailable, using mock data:', error.message);
    return mockHistory.filter(h => h.category === category);
  }
};

// Fetch breakout/emerging metas
export const fetchBreakoutMetas = async () => {
  try {
    const response = await fetch(`${API_URL}/api/breakout-metas`);
    return handleResponse(response);
  } catch (error) {
    console.warn('API unavailable, using mock data:', error.message);
    return mockBreakoutMetas;
  }
};

// Fetch a single trend detail
export const fetchTrendDetail = async (category, subCategory = null) => {
  try {
    let url = `${API_URL}/api/trends/${encodeURIComponent(category)}`;
    if (subCategory) {
      url += `/${encodeURIComponent(subCategory)}`;
    }
    const response = await fetch(url);
    return handleResponse(response);
  } catch (error) {
    console.warn('API unavailable, using mock data:', error.message);
    const trend = mockTrends.find(t =>
      t.category === category &&
      (!subCategory || t.sub_category === subCategory)
    );
    return trend || null;
  }
};
