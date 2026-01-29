import { useQuery } from '@tanstack/react-query';
import {
  fetchTrends,
  fetchAcceleration,
  fetchCoins,
  fetchHistory,
  fetchBreakoutMetas,
  fetchTrendDetail
} from '../api/client';

// Hook to fetch all trends
export const useTrends = (timeWindow = '24h', sortBy = 'acceleration') => {
  return useQuery({
    queryKey: ['trends', timeWindow, sortBy],
    queryFn: () => fetchTrends(timeWindow, sortBy),
    staleTime: 30000, // 30 seconds
    refetchInterval: 60000, // Refetch every minute
  });
};

// Hook to fetch acceleration data
export const useAcceleration = (timeWindow = '24h') => {
  return useQuery({
    queryKey: ['acceleration', timeWindow],
    queryFn: () => fetchAcceleration(timeWindow),
    staleTime: 30000,
    refetchInterval: 60000,
  });
};

// Hook to fetch coins for a trend
export const useCoins = (category, subCategory = null, limit = 50) => {
  return useQuery({
    queryKey: ['coins', category, subCategory, limit],
    queryFn: () => fetchCoins(category, subCategory, limit),
    enabled: !!category,
    staleTime: 30000,
  });
};

// Hook to fetch historical data (aliased for compatibility)
export const useHistory = (category, subCategory = null, timeWindow = '7d') => {
  return useQuery({
    queryKey: ['history', category, subCategory, timeWindow],
    queryFn: () => fetchHistory(category, subCategory, timeWindow),
    enabled: !!category,
    staleTime: 60000,
  });
};

// Alias for useHistory
export const useTrendHistory = useHistory;

// Hook to fetch breakout metas
export const useBreakoutMetas = () => {
  return useQuery({
    queryKey: ['breakoutMetas'],
    queryFn: fetchBreakoutMetas,
    staleTime: 60000,
    refetchInterval: 120000, // Refetch every 2 minutes
  });
};

// Hook to fetch a single trend detail
export const useTrendDetail = (category, subCategory = null) => {
  return useQuery({
    queryKey: ['trendDetail', category, subCategory],
    queryFn: () => fetchTrendDetail(category, subCategory),
    enabled: !!category,
    staleTime: 30000,
  });
};

// Hook for top accelerating trends
export const useTopAccelerating = (timeWindow = '24h', limit = 5) => {
  return useQuery({
    queryKey: ['topAccelerating', timeWindow, limit],
    queryFn: async () => {
      const trends = await fetchTrends(timeWindow, 'acceleration');
      return trends.slice(0, limit);
    },
    staleTime: 30000,
    refetchInterval: 60000,
  });
};

// Hook for trend coins (alias)
export const useTrendCoins = (category, subCategory, timeWindow = '24h') => {
  return useCoins(category, subCategory);
};
