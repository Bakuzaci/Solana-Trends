import { useState, useMemo } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { useTrendDetail, useTrendCoins, useTrendHistory } from '../hooks/useTrends';
import TrendChart from './TrendChart';
import CoinTable from './CoinTable';

/**
 * Format currency values
 */
function formatCurrency(value) {
  if (!value && value !== 0) return '—';
  if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
  if (value >= 1e6) return `$${(value / 1e6).toFixed(1)}M`;
  if (value >= 1e3) return `$${(value / 1e3).toFixed(0)}K`;
  return `$${value.toFixed(0)}`;
}

/**
 * Loading skeleton
 */
function LoadingSkeleton() {
  return (
    <div className="space-y-6">
      <div className="h-12 bg-[var(--bg-tertiary)] w-1/3"></div>
      <div className="grid grid-cols-3 gap-4">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="h-24 bg-[var(--bg-tertiary)]"></div>
        ))}
      </div>
      <div className="h-64 bg-[var(--bg-tertiary)]"></div>
      <div className="h-96 bg-[var(--bg-tertiary)]"></div>
    </div>
  );
}

/**
 * Breakout highlight for top performing coin
 */
function BreakoutHighlight({ coin, averageMarketCap }) {
  if (!coin) return null;
  
  const multiple = averageMarketCap > 0 ? (coin.market_cap / averageMarketCap).toFixed(1) : '?';

  return (
    <div className="border-2 border-[var(--accent-highlight)] p-6 mb-8 relative">
      <span className="absolute top-0 right-0 bg-[var(--accent-highlight)] text-black text-xs font-bold px-2 py-1">
        BREAKOUT
      </span>
      
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div>
          <div className="label-sm mb-1">Token</div>
          <div className="headline-md">{coin.name}</div>
          <div className="font-mono text-[var(--text-muted)]">{coin.symbol}</div>
        </div>
        
        <div>
          <div className="label-sm mb-1">Market Cap</div>
          <div className="font-mono text-xl font-semibold">{formatCurrency(coin.market_cap)}</div>
        </div>
        
        <div>
          <div className="label-sm mb-1">vs Average</div>
          <div className="font-mono text-xl font-semibold text-[var(--accent-highlight)]">{multiple}×</div>
        </div>
        
        <div className="flex items-end gap-3">
          {coin.twitter_url && (
            <a href={coin.twitter_url} target="_blank" rel="noopener noreferrer" 
               className="btn text-xs">Twitter</a>
          )}
          {coin.address && (
            <a href={`https://dexscreener.com/solana/${coin.address}`} target="_blank" 
               rel="noopener noreferrer" className="btn text-xs">Trade</a>
          )}
        </div>
      </div>
    </div>
  );
}

/**
 * TrendDetail - Full detail view for a category/trend
 */
export default function TrendDetail() {
  const { category } = useParams();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [graduatedOnly, setGraduatedOnly] = useState(false);

  const subCategory = searchParams.get('sub') || null;
  const timeWindow = searchParams.get('tw') || '24h';

  // Fetch data
  const { data: trend, isLoading: trendLoading, error: trendError } = useTrendDetail(category, subCategory);
  const { data: coins = [], isLoading: coinsLoading } = useTrendCoins(category, subCategory, timeWindow, graduatedOnly);
  const { data: history = [], isLoading: historyLoading } = useTrendHistory(category, subCategory, '7d');

  // Time window handler
  const handleTimeWindowChange = (newTimeWindow) => {
    const newParams = new URLSearchParams(searchParams);
    newParams.set('tw', newTimeWindow);
    setSearchParams(newParams);
  };

  // Calculate stats
  const { averageMarketCap, breakoutCoin, totalVolume } = useMemo(() => {
    if (!coins || coins.length === 0) {
      return { averageMarketCap: 0, breakoutCoin: null, totalVolume: 0 };
    }

    const totalMarketCap = coins.reduce((sum, coin) => sum + (coin.market_cap || 0), 0);
    const avg = totalMarketCap / coins.length;
    const vol = coins.reduce((sum, coin) => sum + (coin.volume || coin.volume_24h || 0), 0);

    const breakout = coins
      .filter((coin) => coin.market_cap > avg * 5)
      .sort((a, b) => b.market_cap - a.market_cap)[0] || null;

    return { averageMarketCap: avg, breakoutCoin: breakout, totalVolume: vol };
  }, [coins]);

  const displayCategory = subCategory || category || '';

  // Loading
  if (trendLoading && !trend) {
    return (
      <div className="min-h-screen bg-[var(--bg-primary)] p-6">
        <div className="max-w-6xl mx-auto">
          <LoadingSkeleton />
        </div>
      </div>
    );
  }

  // Error
  if (trendError) {
    return (
      <div className="min-h-screen bg-[var(--bg-primary)] p-6">
        <div className="max-w-6xl mx-auto">
          <button onClick={() => navigate('/')} className="btn mb-6">← Back</button>
          <div className="border border-[var(--accent-down)] p-6">
            <div className="label-sm text-[var(--accent-down)] mb-2">Error</div>
            <p>{trendError?.message || String(trendError)}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      {/* Header */}
      <header className="border-b border-[var(--border-subtle)]">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <button 
            onClick={() => navigate('/')} 
            className="text-[var(--text-muted)] hover:text-white transition-colors"
          >
            ← Back
          </button>
          
          <div className="flex gap-2">
            {['12h', '24h', '7d'].map(tw => (
              <button
                key={tw}
                onClick={() => handleTimeWindowChange(tw)}
                className={`btn ${timeWindow === tw ? 'btn-active' : ''}`}
              >
                {tw}
              </button>
            ))}
          </div>
        </div>
      </header>
      
      <main className="max-w-6xl mx-auto px-6 py-8">
        {/* Title */}
        <div className="mb-8">
          <div className="label-sm mb-2">{category}</div>
          <h1 className="headline-xl flex items-center gap-4">
            {trend?.emoji && <span className="text-5xl">{trend.emoji}</span>}
            {displayCategory}
          </h1>
          {trend?.is_breakout_meta && (
            <span className="meta-chip hot mt-4 inline-block">Breakout Meta</span>
          )}
        </div>
        
        {/* Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-px bg-[var(--border-subtle)] mb-8">
          <div className="bg-[var(--bg-primary)] p-4">
            <div className="label-sm mb-1">Tokens</div>
            <div className="font-mono text-2xl font-semibold">{coins.length}</div>
          </div>
          <div className="bg-[var(--bg-primary)] p-4">
            <div className="label-sm mb-1">Total MCap</div>
            <div className="font-mono text-2xl font-semibold">{formatCurrency(trend?.total_market_cap)}</div>
          </div>
          <div className="bg-[var(--bg-primary)] p-4">
            <div className="label-sm mb-1">Volume 24h</div>
            <div className="font-mono text-2xl font-semibold">{formatCurrency(totalVolume)}</div>
          </div>
          <div className="bg-[var(--bg-primary)] p-4">
            <div className="label-sm mb-1">Accel Score</div>
            <div className={`font-mono text-2xl font-semibold ${
              (trend?.acceleration_score || 0) >= 70 ? 'text-[var(--accent-hot)]' : ''
            }`}>
              {trend?.acceleration_score?.toFixed(0) || '—'}
            </div>
          </div>
        </div>
        
        {/* Breakout Highlight */}
        {breakoutCoin && (
          <BreakoutHighlight coin={breakoutCoin} averageMarketCap={averageMarketCap} />
        )}
        
        {/* Chart */}
        <section className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="headline-md">7-Day History</h2>
            <div className="flex items-center gap-4 text-xs text-[var(--text-muted)]">
              <span className="flex items-center gap-2">
                <span className="w-2 h-2 bg-[var(--accent-up)]"></span>
                MCap
              </span>
              <span className="flex items-center gap-2">
                <span className="w-2 h-2 bg-[var(--accent-highlight)]"></span>
                Count
              </span>
            </div>
          </div>
          <div className="card p-6">
            {historyLoading ? (
              <div className="h-[300px] flex items-center justify-center">
                <div className="animate-spin h-6 w-6 border-2 border-[var(--text-muted)] border-t-transparent"></div>
              </div>
            ) : (
              <TrendChart history={history} showCoinCount={true} height={300} />
            )}
          </div>
        </section>
        
        {/* Coins Table */}
        <section>
          <div className="flex items-center justify-between mb-4">
            <h2 className="headline-md">
              {graduatedOnly ? 'Graduated' : 'All'} Tokens
              <span className="text-[var(--text-muted)] ml-2 font-mono text-base">{coins.length}</span>
            </h2>
            <button
              onClick={() => setGraduatedOnly(!graduatedOnly)}
              className={`btn ${graduatedOnly ? 'btn-active' : ''}`}
            >
              {graduatedOnly ? '✓ Graduated' : 'Graduated Only'}
            </button>
          </div>
          
          {coinsLoading ? (
            <div className="card p-8 flex items-center justify-center">
              <div className="animate-spin h-6 w-6 border-2 border-[var(--text-muted)] border-t-transparent"></div>
            </div>
          ) : (
            <CoinTable coins={coins} averageMarketCap={averageMarketCap} />
          )}
        </section>
      </main>
      
      {/* Footer */}
      <footer className="border-t border-[var(--border-subtle)] py-6 mt-12">
        <div className="max-w-6xl mx-auto px-6 flex items-center justify-between">
          <button onClick={() => navigate('/')} className="label-sm hover:text-white transition-colors">
            ← Dashboard
          </button>
          <div className="label-sm">PAYATTENTION.SOL</div>
        </div>
      </footer>
    </div>
  );
}
