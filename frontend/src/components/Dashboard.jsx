import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTrends } from '../hooks/useTrends';
import TimeWindowToggle from './TimeWindowToggle';
import SortSelect from './SortSelect';
import TrendCard from './TrendCard';
import SearchBar from './SearchBar';

/**
 * Format currency values
 */
function formatCurrency(value) {
  if (!value && value !== 0) return '-';
  if (value >= 1e9) {
    return `$${(value / 1e9).toFixed(2)}B`;
  }
  if (value >= 1e6) {
    return `$${(value / 1e6).toFixed(2)}M`;
  }
  if (value >= 1e3) {
    return `$${(value / 1e3).toFixed(1)}K`;
  }
  return `$${value.toFixed(2)}`;
}

/**
 * Loading skeleton
 */
function LoadingSkeleton() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {[...Array(6)].map((_, i) => (
        <div
          key={i}
          className="bg-gray-800/50 rounded-lg border border-gray-700 p-5 animate-pulse"
        >
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-lg bg-gray-700"></div>
            <div className="flex-1">
              <div className="h-5 bg-gray-700 rounded w-2/3 mb-2"></div>
              <div className="h-3 bg-gray-700 rounded w-1/2"></div>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="h-10 bg-gray-700 rounded"></div>
            <div className="h-10 bg-gray-700 rounded"></div>
          </div>
        </div>
      ))}
    </div>
  );
}

/**
 * Dashboard component - main view showing all trends
 */
export default function Dashboard() {
  const navigate = useNavigate();
  const [timeWindow, setTimeWindow] = useState('24h');
  const [sortBy, setSortBy] = useState('acceleration');
  const [graduatedOnly, setGraduatedOnly] = useState(false);

  // Use React Query hook - destructure with renamed properties
  const { data: trends = [], isLoading: loading, error, refetch } = useTrends(timeWindow, sortBy, graduatedOnly);

  const handleTrendClick = (trend) => {
    const params = new URLSearchParams();
    if (trend.sub_category) {
      params.set('sub', trend.sub_category);
    }
    params.set('tw', timeWindow);
    navigate(`/trend/${encodeURIComponent(trend.category)}?${params}`);
  };

  return (
    <div className="min-h-screen bg-black text-white">
      {/* Header */}
      <header className="glass border-b border-white/5 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-6 py-4">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <h1 className="text-2xl font-semibold tracking-tight">
                <span className="text-purple-400">PayAttention</span><span className="text-gray-500">.Sol</span>
              </h1>
              <p className="text-gray-500 text-sm mt-1 font-light">
                Real-time Solana meme coin intelligence
              </p>
            </div>
            {/* Search Bar */}
            <SearchBar />
            <div className="flex items-center gap-4">
              {/* Graduated Only Toggle */}
              <button
                onClick={() => setGraduatedOnly(!graduatedOnly)}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                  graduatedOnly
                    ? 'bg-green-500/20 text-green-400 border border-green-500/30'
                    : 'bg-gray-800/50 text-gray-400 border border-gray-700 hover:border-gray-600'
                }`}
              >
                <span className={`w-2 h-2 rounded-full ${graduatedOnly ? 'bg-green-400' : 'bg-gray-600'}`}></span>
                Graduated
              </button>
              <SortSelect value={sortBy} onChange={setSortBy} />
              <TimeWindowToggle value={timeWindow} onChange={setTimeWindow} />
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-6 py-8">
        {/* Stats Bar */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="glass-card rounded-2xl p-4">
            <p className="text-gray-500 text-xs font-medium uppercase tracking-wider">Trends</p>
            <p className="text-2xl font-semibold text-white mt-1">{trends.length}</p>
          </div>
          <div className="glass-card rounded-2xl p-4">
            <p className="text-gray-500 text-xs font-medium uppercase tracking-wider">Window</p>
            <p className="text-2xl font-semibold text-purple-400 mt-1">{timeWindow}</p>
          </div>
          <div className="glass-card rounded-2xl p-4">
            <p className="text-gray-500 text-xs font-medium uppercase tracking-wider">Coins</p>
            <p className="text-2xl font-semibold text-white mt-1">
              {trends.reduce((sum, t) => sum + (t.coin_count || 0), 0)}
            </p>
          </div>
          <div className="glass-card rounded-2xl p-4">
            <p className="text-gray-500 text-xs font-medium uppercase tracking-wider">Market Cap</p>
            <p className="text-2xl font-semibold text-white mt-1">
              {formatCurrency(trends.reduce((sum, t) => sum + (t.total_market_cap || 0), 0))}
            </p>
          </div>
        </div>

        {/* Error State */}
        {error && (
          <div className="bg-red-900/20 border border-red-500/30 rounded-lg p-6 mb-8 flex items-center justify-between">
            <div>
              <p className="text-red-400 font-medium">Error loading trends</p>
              <p className="text-gray-400 text-sm mt-1">{error?.message || String(error)}</p>
            </div>
            <button
              onClick={() => refetch()}
              className="px-4 py-2 bg-red-600/20 text-red-400 rounded-lg hover:bg-red-600/30 transition-colors"
            >
              Retry
            </button>
          </div>
        )}

        {/* Loading State */}
        {loading && trends.length === 0 && <LoadingSkeleton />}

        {/* Trends Grid */}
        {!loading && trends.length === 0 && !error && (
          <div className="bg-gray-800/50 rounded-lg border border-gray-700 p-12 text-center">
            <svg
              className="w-16 h-16 text-gray-600 mx-auto mb-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <p className="text-gray-400 text-lg">No trends found</p>
            <p className="text-gray-500 text-sm mt-2">
              Check back later for emerging trends
            </p>
          </div>
        )}

        {trends.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {trends.map((trend, index) => (
              <TrendCard
                key={`${trend.category}-${trend.sub_category || ''}-${index}`}
                trend={trend}
                onClick={() => handleTrendClick(trend)}
              />
            ))}
          </div>
        )}

        {/* Refresh indicator */}
        {loading && trends.length > 0 && (
          <div className="fixed bottom-6 right-6 bg-gray-800 rounded-full p-3 shadow-lg border border-gray-700">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-purple-500"></div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-white/5 py-6">
        <div className="max-w-6xl mx-auto px-6 text-center text-gray-600 text-sm font-light">
          <p>PayAttention.Sol • Real-time data</p>
        </div>
      </footer>
    </div>
  );
}
