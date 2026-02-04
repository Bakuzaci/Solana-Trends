import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTrends, useEmergingClusters, useTrendingNames } from '../hooks/useTrends';
import TimeWindowToggle from './TimeWindowToggle';
import TrendCard from './TrendCard';
import EmergingSection from './EmergingSection';
import MarqueeBar from './MarqueeBar';

/**
 * Format currency with precision
 */
function formatCurrency(value) {
  if (!value && value !== 0) return '—';
  if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
  if (value >= 1e6) return `$${(value / 1e6).toFixed(1)}M`;
  if (value >= 1e3) return `$${(value / 1e3).toFixed(0)}K`;
  return `$${value.toFixed(0)}`;
}

/**
 * Format percentage change
 */
function formatChange(value) {
  if (!value && value !== 0) return '—';
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(1)}%`;
}

/**
 * Current time display
 */
function LiveClock() {
  const [time, setTime] = useState(new Date());
  
  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);
  
  return (
    <span className="font-mono text-xs text-[var(--text-muted)]">
      {time.toISOString().slice(11, 19)} UTC
    </span>
  );
}

/**
 * Stats bar showing key metrics
 */
function StatsBar({ trends }) {
  const totalCoins = trends.reduce((sum, t) => sum + (t.coin_count || 0), 0);
  const totalMcap = trends.reduce((sum, t) => sum + (t.total_market_cap || 0), 0);
  const breakoutCount = trends.filter(t => t.is_breakout_meta).length;
  
  return (
    <div className="grid grid-cols-4 gap-px bg-[var(--border-subtle)]">
      <div className="bg-[var(--bg-primary)] p-4">
        <div className="label-sm mb-1">Categories</div>
        <div className="font-mono text-2xl font-semibold">{trends.length}</div>
      </div>
      <div className="bg-[var(--bg-primary)] p-4">
        <div className="label-sm mb-1">Tokens</div>
        <div className="font-mono text-2xl font-semibold">{totalCoins}</div>
      </div>
      <div className="bg-[var(--bg-primary)] p-4">
        <div className="label-sm mb-1">Market Cap</div>
        <div className="font-mono text-2xl font-semibold">{formatCurrency(totalMcap)}</div>
      </div>
      <div className="bg-[var(--bg-primary)] p-4">
        <div className="label-sm mb-1">Breakouts</div>
        <div className="font-mono text-2xl font-semibold text-[var(--accent-hot)]">{breakoutCount}</div>
      </div>
    </div>
  );
}

/**
 * Trending words section
 */
function TrendingWords({ words = [] }) {
  if (!words.length) return null;
  
  return (
    <div className="border-t border-[var(--border-subtle)] py-4">
      <div className="label-sm mb-3">Trending Terms</div>
      <div className="flex flex-wrap gap-2">
        {words.slice(0, 12).map(({ word, count }) => (
          <span 
            key={word}
            className="meta-chip"
          >
            {word}
            <span className="text-[var(--text-muted)] ml-1">×{count}</span>
          </span>
        ))}
      </div>
    </div>
  );
}

/**
 * Main Dashboard
 */
export default function Dashboard() {
  const navigate = useNavigate();
  const [timeWindow, setTimeWindow] = useState('24h');
  const [sortBy, setSortBy] = useState('acceleration');
  const [view, setView] = useState('grid'); // 'grid' | 'list'
  
  const { data: trends = [], isLoading, error, refetch } = useTrends(timeWindow, sortBy, false);
  const { data: emergingClusters = [] } = useEmergingClusters(24);
  const { data: trendingNames = [] } = useTrendingNames(6);
  
  // Get top breakout metas
  const breakoutMetas = trends.filter(t => t.is_breakout_meta).slice(0, 3);
  
  const handleTrendClick = (trend) => {
    const params = new URLSearchParams();
    if (trend.sub_category) params.set('sub', trend.sub_category);
    params.set('tw', timeWindow);
    navigate(`/trend/${encodeURIComponent(trend.category)}?${params}`);
  };

  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      {/* Breaking Marquee */}
      {breakoutMetas.length > 0 && (
        <MarqueeBar items={breakoutMetas.map(t => 
          `${t.emoji} ${t.sub_category || t.category} ${formatChange(t.change_24h)}`
        )} />
      )}
      
      {/* Header */}
      <header className="border-b border-[var(--border-subtle)]">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            {/* Masthead */}
            <div className="flex items-center gap-6">
              <h1 className="headline-lg">
                <span className="text-[var(--accent-highlight)]">PAY</span>
                <span className="text-white">ATTENTION</span>
              </h1>
              <div className="flex items-center gap-2">
                <div className="status-dot live"></div>
                <LiveClock />
              </div>
            </div>
            
            {/* Controls */}
            <div className="flex items-center gap-4">
              <div className="flex border border-[var(--border-strong)]">
                {['12h', '24h', '7d'].map(tw => (
                  <button
                    key={tw}
                    onClick={() => setTimeWindow(tw)}
                    className={`btn border-0 ${timeWindow === tw ? 'btn-active' : ''}`}
                  >
                    {tw}
                  </button>
                ))}
              </div>
              
              <div className="flex border border-[var(--border-strong)]">
                <button
                  onClick={() => setSortBy('acceleration')}
                  className={`btn border-0 ${sortBy === 'acceleration' ? 'btn-active' : ''}`}
                >
                  Accel
                </button>
                <button
                  onClick={() => setSortBy('market_cap')}
                  className={`btn border-0 ${sortBy === 'market_cap' ? 'btn-active' : ''}`}
                >
                  MCap
                </button>
              </div>
            </div>
          </div>
        </div>
      </header>
      
      {/* Stats Bar */}
      {!isLoading && <StatsBar trends={trends} />}
      
      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Error State */}
        {error && (
          <div className="border border-[var(--accent-down)] p-6 mb-8">
            <div className="label-sm text-[var(--accent-down)] mb-2">Error</div>
            <p className="text-white mb-4">{error?.message || String(error)}</p>
            <button onClick={() => refetch()} className="btn">
              Retry
            </button>
          </div>
        )}
        
        {/* Loading State */}
        {isLoading && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[...Array(9)].map((_, i) => (
              <div key={i} className="card h-48 animate-pulse">
                <div className="p-4">
                  <div className="h-4 bg-[var(--bg-tertiary)] w-1/3 mb-4"></div>
                  <div className="h-8 bg-[var(--bg-tertiary)] w-2/3 mb-2"></div>
                  <div className="h-4 bg-[var(--bg-tertiary)] w-1/2"></div>
                </div>
              </div>
            ))}
          </div>
        )}
        
        {/* Emerging Metas Section */}
        {emergingClusters.length > 0 && (
          <section className="mb-12">
            <div className="flex items-center gap-3 mb-6">
              <h2 className="headline-md">Emerging</h2>
              <span className="meta-chip hot">New</span>
            </div>
            <EmergingSection clusters={emergingClusters} />
          </section>
        )}
        
        {/* Trending Words */}
        <TrendingWords words={trendingNames} />
        
        {/* Main Trends Grid */}
        {!isLoading && trends.length > 0 && (
          <section className="mt-8">
            <div className="flex items-center justify-between mb-6">
              <h2 className="headline-md">All Categories</h2>
              <span className="label-sm">{trends.length} Active</span>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {trends.map((trend, index) => (
                <TrendCard
                  key={`${trend.category}-${trend.sub_category || ''}-${index}`}
                  trend={trend}
                  onClick={() => handleTrendClick(trend)}
                  rank={index + 1}
                />
              ))}
            </div>
          </section>
        )}
        
        {/* Empty State */}
        {!isLoading && trends.length === 0 && !error && (
          <div className="border border-[var(--border-subtle)] p-12 text-center">
            <div className="label-sm mb-4">No Data</div>
            <p className="text-[var(--text-secondary)]">
              No trends found for this time window
            </p>
          </div>
        )}
      </main>
      
      {/* Footer */}
      <footer className="border-t border-[var(--border-subtle)] py-6 mt-12">
        <div className="max-w-7xl mx-auto px-6 flex items-center justify-between">
          <div className="label-sm">PAYATTENTION.SOL</div>
          <div className="label-sm">SOLANA MEMECOIN INTELLIGENCE</div>
          <div className="flex items-center gap-2">
            <div className="status-dot live"></div>
            <span className="label-sm">Live</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
