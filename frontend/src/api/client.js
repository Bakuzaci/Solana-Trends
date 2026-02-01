// Use Railway backend in production, localhost in development
const API_URL = import.meta.env.VITE_API_URL ||
  (window.location.hostname === 'localhost'
    ? 'http://localhost:8000'
    : 'https://solana-trends-backend-production.up.railway.app');

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
export const fetchTrends = async (timeWindow = '24h', sortBy = 'acceleration', graduatedOnly = false) => {
  try {
    const response = await fetch(
      `${API_URL}/api/trends?time_window=${timeWindow}&sort_by=${sortBy}&graduated_only=${graduatedOnly}`
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
      `${API_URL}/api/acceleration/top?time_window=${timeWindow}`
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
export const fetchCoins = async (category, subCategory, limit = 50, graduatedOnly = false) => {
  try {
    const url = `${API_URL}/api/trends/${encodeURIComponent(category)}/${encodeURIComponent(subCategory)}/coins?limit=${limit}&graduated_only=${graduatedOnly}`;
    const response = await fetch(url);
    const data = await handleResponse(response);
    // Map API field names to what CoinTable expects
    return data.map(coin => ({
      ...coin,
      address: coin.token_address,
      market_cap: coin.market_cap_usd,
      liquidity: coin.liquidity_usd,
      price_change: coin.price_change_24h,
      volume: coin.volume_24h,
    }));
  } catch (error) {
    console.warn('API unavailable, using mock data:', error.message);
    return mockCoins.filter(c => c.category === category);
  }
};

// Fetch historical trend data
export const fetchHistory = async (category, subCategory, timeWindow = '7d') => {
  try {
    const url = `${API_URL}/api/history/${encodeURIComponent(category)}/${encodeURIComponent(subCategory)}?period=${timeWindow}`;
    const response = await fetch(url);
    const data = await handleResponse(response);
    // Return just the data_points array for TrendChart
    return data.data_points || [];
  } catch (error) {
    console.warn('API unavailable, using mock data:', error.message);
    return mockHistory.filter(h => h.category === category);
  }
};

// Fetch breakout/emerging metas
export const fetchBreakoutMetas = async () => {
  try {
    const response = await fetch(`${API_URL}/api/acceleration/breakout-metas`);
    return handleResponse(response);
  } catch (error) {
    console.warn('API unavailable, using mock data:', error.message);
    return mockBreakoutMetas;
  }
};

// Fetch a single trend detail
export const fetchTrendDetail = async (category, subCategory) => {
  try {
    // Fetch all trends and filter to the specific one
    const response = await fetch(`${API_URL}/api/trends`);
    const trends = await handleResponse(response);
    const trend = trends.find(t =>
      t.category === category && t.sub_category === subCategory
    );
    return trend || null;
  } catch (error) {
    console.warn('API unavailable, using mock data:', error.message);
    const trend = mockTrends.find(t =>
      t.category === category &&
      (!subCategory || t.sub_category === subCategory)
    );
    return trend || null;
  }
};

// Search for coins and related metas
export const searchCoins = async (query, graduatedOnly = false) => {
  try {
    const response = await fetch(
      `${API_URL}/api/search/coins?q=${encodeURIComponent(query)}&graduated_only=${graduatedOnly}`
    );
    const data = await handleResponse(response);
    // Map API field names to what components expect
    return {
      ...data,
      coins: (data.coins || []).map(coin => ({
        ...coin,
        address: coin.token_address,
        market_cap: coin.market_cap_usd,
        liquidity: coin.liquidity_usd,
        price_change: coin.price_change_24h,
        volume: coin.volume_24h,
      })),
    };
  } catch (error) {
    console.warn('Search API unavailable:', error.message);
    return { query, coins: [], related_metas: [], suggestions: [] };
  }
};

// Fetch meta relationships
export const fetchMetaRelationships = async (source = null) => {
  try {
    const url = source
      ? `${API_URL}/api/search/metas?source=${encodeURIComponent(source)}`
      : `${API_URL}/api/search/metas`;
    const response = await fetch(url);
    return handleResponse(response);
  } catch (error) {
    console.warn('Meta relationships API unavailable:', error.message);
    return [];
  }
};

// Fetch trending metas
export const fetchTrendingMetas = async () => {
  try {
    const response = await fetch(`${API_URL}/api/search/trending`);
    return handleResponse(response);
  } catch (error) {
    console.warn('Trending metas API unavailable:', error.message);
    return [];
  }
};
