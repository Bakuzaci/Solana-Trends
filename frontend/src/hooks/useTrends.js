import { useQuery } from '@tanstack/react-query';
import {
  fetchTrends,
  fetchAcceleration,
  fetchCoins,
  fetchHistory,
  fetchBreakoutMetas,
  fetchTrendDetail,
  searchCoins,
  fetchMetaRelationships,
  fetchTrendingMetas,
  fetchEmergingClusters,
  fetchTrendingNames,
  fetchUncategorizedTokens,
} from '../api/client';

// Hook to fetch all trends
export const useTrends = (timeWindow = '24h', sortBy = 'acceleration', graduatedOnly = false) => {
  return useQuery({
    queryKey: ['trends', timeWindow, sortBy, graduatedOnly],
    queryFn: () => fetchTrends(timeWindow, sortBy, graduatedOnly),
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
export const useCoins = (category, subCategory = null, limit = 50, graduatedOnly = false) => {
  return useQuery({
    queryKey: ['coins', category, subCategory, limit, graduatedOnly],
    queryFn: () => fetchCoins(category, subCategory, limit, graduatedOnly),
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
export const useTrendCoins = (category, subCategory, timeWindow = '24h', graduatedOnly = false) => {
  return useCoins(category, subCategory, 50, graduatedOnly);
};

// Hook to search for coins and related metas
export const useSearch = (query, graduatedOnly = false) => {
  return useQuery({
    queryKey: ['search', query, graduatedOnly],
    queryFn: () => searchCoins(query, graduatedOnly),
    enabled: query && query.length >= 2,
    staleTime: 30000,
  });
};

// Hook to fetch meta relationships
export const useMetaRelationships = (source = null) => {
  return useQuery({
    queryKey: ['metaRelationships', source],
    queryFn: () => fetchMetaRelationships(source),
    staleTime: 60000,
  });
};

// Hook to fetch trending metas
export const useTrendingMetas = () => {
  return useQuery({
    queryKey: ['trendingMetas'],
    queryFn: fetchTrendingMetas,
    staleTime: 60000,
    refetchInterval: 120000,
  });
};

// Hook to fetch emerging clusters (new metas)
export const useEmergingClusters = (hours = 24) => {
  return useQuery({
    queryKey: ['emergingClusters', hours],
    queryFn: () => fetchEmergingClusters(hours),
    staleTime: 60000,
    refetchInterval: 120000,
  });
};

// Hook to fetch trending token names/words
export const useTrendingNames = (hours = 6) => {
  return useQuery({
    queryKey: ['trendingNames', hours],
    queryFn: () => fetchTrendingNames(hours),
    staleTime: 60000,
    refetchInterval: 120000,
  });
};

// Hook to fetch uncategorized tokens
export const useUncategorizedTokens = (hours = 24, minVolume = 0) => {
  return useQuery({
    queryKey: ['uncategorizedTokens', hours, minVolume],
    queryFn: () => fetchUncategorizedTokens(hours, minVolume),
    staleTime: 60000,
    refetchInterval: 120000,
  });
};
