import { useState, useMemo } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { useTrendDetail, useTrendCoins, useTrendHistory } from '../hooks/useTrends';
import TrendChart from './TrendChart';
import CoinTable from './CoinTable';
import TimeWindowToggle from './TimeWindowToggle';

/**
 * Category icons mapping
 */
const CATEGORY_ICONS = {
  meme: 'M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
  ai: 'M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z',
  defi: 'M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
  gaming: 'M11 4a2 2 0 114 0v1a1 1 0 001 1h3a1 1 0 011 1v3a1 1 0 01-1 1h-1a2 2 0 100 4h1a1 1 0 011 1v3a1 1 0 01-1 1h-3a1 1 0 01-1-1v-1a2 2 0 10-4 0v1a1 1 0 01-1 1H7a1 1 0 01-1-1v-3a1 1 0 00-1-1H4a2 2 0 110-4h1a1 1 0 001-1V7a1 1 0 011-1h3a1 1 0 001-1V4z',
  nft: 'M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z',
  default: 'M13 10V3L4 14h7v7l9-11h-7z',
};

/**
 * Get icon path for category
 */
function getCategoryIcon(category) {
  const lowerCategory = (category || '').toLowerCase();
  for (const [key, path] of Object.entries(CATEGORY_ICONS)) {
    if (lowerCategory.includes(key)) {
      return path;
    }
  }
  return CATEGORY_ICONS.default;
}

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
 * Loading skeleton component
 */
function LoadingSkeleton() {
  return (
    <div className="animate-pulse">
      <div className="h-8 bg-gray-700 rounded w-1/3 mb-4"></div>
      <div className="h-4 bg-gray-700 rounded w-1/2 mb-8"></div>
      <div className="grid grid-cols-3 gap-4 mb-8">
        <div className="h-24 bg-gray-700 rounded"></div>
        <div className="h-24 bg-gray-700 rounded"></div>
        <div className="h-24 bg-gray-700 rounded"></div>
      </div>
      <div className="h-64 bg-gray-700 rounded mb-8"></div>
      <div className="h-96 bg-gray-700 rounded"></div>
    </div>
  );
}

/**
 * Stat card component
 */
function StatCard({ label, value, subValue, highlight = false }) {
  return (
    <div
      className={`bg-gray-800/50 rounded-lg border p-4 ${
        highlight ? 'border-purple-500/50 bg-purple-900/20' : 'border-gray-700'
      }`}
    >
      <p className="text-gray-400 text-sm mb-1">{label}</p>
      <p className={`text-2xl font-bold ${highlight ? 'text-purple-400' : 'text-white'}`}>
        {value}
      </p>
      {subValue && <p className="text-gray-500 text-sm mt-1">{subValue}</p>}
    </div>
  );
}

/**
 * Breakout highlight component
 */
function BreakoutHighlight({ coin, averageMarketCap }) {
  if (!coin) return null;

  const multiple = averageMarketCap > 0 ? (coin.market_cap / averageMarketCap).toFixed(1) : '?';

  return (
    <div className="bg-gradient-to-r from-purple-900/50 to-pink-900/50 rounded-lg border border-purple-500/30 p-6 mb-6">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-10 h-10 rounded-full bg-purple-500/20 flex items-center justify-center">
          <svg className="w-6 h-6 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
          </svg>
        </div>
        <div>
          <h3 className="text-lg font-bold text-white">Breakout Coin</h3>
          <p className="text-purple-300 text-sm">{multiple}x above category average</p>
        </div>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div>
          <p className="text-gray-400 text-sm">Name</p>
          <p className="text-white font-medium">{coin.name}</p>
        </div>
        <div>
          <p className="text-gray-400 text-sm">Symbol</p>
          <p className="text-white font-mono">{coin.symbol}</p>
        </div>
        <div>
          <p className="text-gray-400 text-sm">Market Cap</p>
          <p className="text-white font-medium">{formatCurrency(coin.market_cap)}</p>
        </div>
        <div>
          <p className="text-gray-400 text-sm">Liquidity</p>
          <p className="text-white font-medium">{formatCurrency(coin.liquidity)}</p>
        </div>
      </div>
      <div className="flex gap-3 mt-4">
        {coin.address && (
          <>
            <a
              href={`https://vertigo.sh/tokens/${coin.address}`}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-4 py-2 bg-green-600/20 text-green-400 rounded-lg hover:bg-green-600/30 transition-colors text-sm"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
              Vertigo
            </a>
            <a
              href={`https://solscan.io/token/${coin.address}`}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-4 py-2 bg-purple-600/20 text-purple-400 rounded-lg hover:bg-purple-600/30 transition-colors text-sm"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
              Solscan
            </a>
          </>
        )}
      </div>
    </div>
  );
}

/**
 * TrendDetail component - full detail view for a trend category
 */
export default function TrendDetail() {
  const { category } = useParams();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [graduatedOnly, setGraduatedOnly] = useState(false);

  const subCategory = searchParams.get('sub') || null;
  const timeWindow = searchParams.get('tw') || '24h';

  // Fetch data using React Query hooks
  const { data: trend, isLoading: trendLoading, error: trendError } = useTrendDetail(
    category,
    subCategory
  );
  const { data: coins = [], isLoading: coinsLoading } = useTrendCoins(category, subCategory, timeWindow, graduatedOnly);
  const { data: history = [], isLoading: historyLoading } = useTrendHistory(category, subCategory, '7d');

  // Update time window
  const handleTimeWindowChange = (newTimeWindow) => {
    const newParams = new URLSearchParams(searchParams);
    newParams.set('tw', newTimeWindow);
    setSearchParams(newParams);
  };

  // Calculate average market cap and find breakout coin
  const { averageMarketCap, breakoutCoin } = useMemo(() => {
    if (!coins || coins.length === 0) {
      return { averageMarketCap: 0, breakoutCoin: null };
    }

    const totalMarketCap = coins.reduce((sum, coin) => sum + (coin.market_cap || 0), 0);
    const avg = totalMarketCap / coins.length;

    // Find coin with highest market cap that's > 5x average
    const breakout = coins
      .filter((coin) => coin.market_cap > avg * 5)
      .sort((a, b) => b.market_cap - a.market_cap)[0] || null;

    return { averageMarketCap: avg, breakoutCoin: breakout };
  }, [coins]);

  // Display category name nicely
  const displayCategory = category
    ? category.charAt(0).toUpperCase() + category.slice(1).replace(/-/g, ' ')
    : '';

  // Loading state
  if (trendLoading && !trend) {
    return (
      <div className="min-h-screen bg-gray-900 text-white p-6">
        <div className="max-w-6xl mx-auto">
          <LoadingSkeleton />
        </div>
      </div>
    );
  }

  // Error state
  if (trendError) {
    return (
      <div className="min-h-screen bg-gray-900 text-white p-6">
        <div className="max-w-6xl mx-auto">
          <button
            onClick={() => navigate('/')}
            className="flex items-center gap-2 text-gray-400 hover:text-white mb-6 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Back to Dashboard
          </button>
          <div className="bg-red-900/20 border border-red-500/30 rounded-lg p-6 text-center">
            <p className="text-red-400 text-lg">Error loading trend data</p>
            <p className="text-gray-400 mt-2">{trendError?.message || String(trendError)}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <div className="max-w-6xl mx-auto">
        {/* Back Button */}
        <button
          onClick={() => navigate('/')}
          className="flex items-center gap-2 text-gray-400 hover:text-white mb-6 transition-colors"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          Back to Dashboard
        </button>

        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-8">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-xl bg-purple-600/20 flex items-center justify-center">
              <svg
                className="w-8 h-8 text-purple-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d={getCategoryIcon(category)}
                />
              </svg>
            </div>
            <div>
              <h1 className="text-3xl font-bold">{displayCategory}</h1>
              {subCategory && (
                <p className="text-gray-400 mt-1">Subcategory: {subCategory}</p>
              )}
            </div>
          </div>
          <TimeWindowToggle value={timeWindow} onChange={handleTimeWindowChange} />
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <StatCard
            label="Total Coins"
            value={trend?.coin_count || coins.length || 0}
            subValue="In this category"
          />
          <StatCard
            label="Total Market Cap"
            value={formatCurrency(trend?.total_market_cap || 0)}
            subValue="Combined value"
          />
          <StatCard
            label="Acceleration Score"
            value={trend?.acceleration_score?.toFixed(2) || '0.00'}
            subValue="Growth momentum"
            highlight={trend?.acceleration_score > 1}
          />
        </div>

        {/* Breakout Coin Highlight */}
        {breakoutCoin && (
          <BreakoutHighlight coin={breakoutCoin} averageMarketCap={averageMarketCap} />
        )}

        {/* Chart Section */}
        <div className="bg-gray-800/50 rounded-lg border border-gray-700 p-6 mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">7-Day History</h2>
            <div className="flex items-center gap-4 text-sm text-gray-400">
              <span className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-purple-500"></span>
                Market Cap
              </span>
              <span className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-green-500"></span>
                Coin Count
              </span>
            </div>
          </div>
          {historyLoading ? (
            <div className="h-[300px] flex items-center justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500"></div>
            </div>
          ) : (
            <TrendChart history={history} showCoinCount={true} height={300} />
          )}
        </div>

        {/* Coins Table */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">
              {graduatedOnly ? 'Graduated' : 'All'} Coins ({coins.length})
            </h2>
            <button
              onClick={() => setGraduatedOnly(!graduatedOnly)}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                graduatedOnly
                  ? 'bg-green-500/20 text-green-400 border border-green-500/30'
                  : 'bg-gray-800/50 text-gray-400 border border-gray-700 hover:border-gray-600'
              }`}
            >
              <span className={`w-2 h-2 rounded-full ${graduatedOnly ? 'bg-green-400' : 'bg-gray-600'}`}></span>
              Graduated Only
            </button>
          </div>
          {coinsLoading ? (
            <div className="bg-gray-800/50 rounded-lg border border-gray-700 p-8 flex items-center justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500"></div>
            </div>
          ) : (
            <CoinTable coins={coins} averageMarketCap={averageMarketCap} />
          )}
        </div>
      </div>
    </div>
  );
}
