import { useState, useMemo } from 'react';

/**
 * Format market cap/liquidity values
 */
function formatCurrency(value) {
  if (!value && value !== 0) return '—';
  if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
  if (value >= 1e6) return `$${(value / 1e6).toFixed(1)}M`;
  if (value >= 1e3) return `$${(value / 1e3).toFixed(0)}K`;
  return `$${value.toFixed(2)}`;
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
 * Format coin age
 */
function formatAge(createdAt) {
  if (!createdAt) return '—';
  const now = new Date();
  const created = new Date(createdAt);
  const diffMs = now - created;
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffDays = Math.floor(diffHours / 24);

  if (diffDays > 30) return `${Math.floor(diffDays / 30)}mo`;
  if (diffDays > 0) return `${diffDays}d`;
  return `${diffHours}h`;
}

/**
 * Get price change value from coin
 */
function getPriceChange(coin) {
  return coin.change_1h ?? coin.price_change_24h ?? coin.price_change ?? 0;
}

const COLUMNS = [
  { key: 'name', label: 'Token', sortable: true },
  { key: 'market_cap', label: 'MCap', sortable: true },
  { key: 'volume', label: 'Vol 24h', sortable: true },
  { key: 'created_at', label: 'Age', sortable: true },
  { key: 'price_change', label: 'Chg', sortable: true },
  { key: 'links', label: 'Links', sortable: false },
];

const ITEMS_PER_PAGE = 25;

/**
 * CoinTable - Data table for token listing
 */
export default function CoinTable({ coins = [], averageMarketCap = 0 }) {
  const [sortConfig, setSortConfig] = useState({ key: 'market_cap', direction: 'desc' });
  const [currentPage, setCurrentPage] = useState(1);

  const handleSort = (key) => {
    if (!COLUMNS.find(col => col.key === key)?.sortable) return;
    setSortConfig((prev) => ({
      key,
      direction: prev.key === key && prev.direction === 'desc' ? 'asc' : 'desc',
    }));
    setCurrentPage(1);
  };

  const { totalPages, displayedCoins } = useMemo(() => {
    const sorted = [...coins].sort((a, b) => {
      let aVal, bVal;
      if (sortConfig.key === 'price_change') {
        aVal = getPriceChange(a);
        bVal = getPriceChange(b);
      } else if (sortConfig.key === 'volume') {
        aVal = a.volume || a.volume_24h || 0;
        bVal = b.volume || b.volume_24h || 0;
      } else {
        aVal = a[sortConfig.key];
        bVal = b[sortConfig.key];
      }

      if (aVal == null && bVal == null) return 0;
      if (aVal == null) return sortConfig.direction === 'asc' ? 1 : -1;
      if (bVal == null) return sortConfig.direction === 'asc' ? -1 : 1;

      if (sortConfig.key === 'created_at') {
        const dateA = new Date(aVal).getTime();
        const dateB = new Date(bVal).getTime();
        return sortConfig.direction === 'asc' ? dateA - dateB : dateB - dateA;
      }

      if (typeof aVal === 'string') {
        return sortConfig.direction === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
      }

      return sortConfig.direction === 'asc' ? aVal - bVal : bVal - aVal;
    });

    const total = Math.ceil(sorted.length / ITEMS_PER_PAGE);
    const start = (currentPage - 1) * ITEMS_PER_PAGE;
    return { totalPages: total, displayedCoins: sorted.slice(start, start + ITEMS_PER_PAGE) };
  }, [coins, sortConfig, currentPage]);

  const isBreakout = (marketCap) => averageMarketCap > 0 && marketCap > averageMarketCap * 5;

  if (coins.length === 0) {
    return (
      <div className="card p-8 text-center">
        <p className="text-[var(--text-muted)]">No tokens found</p>
      </div>
    );
  }

  return (
    <div className="card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="data-table">
          <thead>
            <tr>
              <th className="w-8">#</th>
              {COLUMNS.map((column) => (
                <th
                  key={column.key}
                  onClick={() => handleSort(column.key)}
                  className={column.sortable ? 'cursor-pointer hover:text-white' : ''}
                >
                  {column.label}
                  {sortConfig.key === column.key && (
                    <span className="ml-1">{sortConfig.direction === 'asc' ? '↑' : '↓'}</span>
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {displayedCoins.map((coin, index) => {
              const breakout = isBreakout(coin.market_cap);
              const change = getPriceChange(coin);
              const rank = (currentPage - 1) * ITEMS_PER_PAGE + index + 1;

              return (
                <tr key={coin.address || index} className={breakout ? 'bg-[var(--accent-highlight)]/5' : ''}>
                  {/* Rank */}
                  <td className="text-[var(--text-muted)]">{rank}</td>

                  {/* Token Name */}
                  <td>
                    <div className="flex items-center gap-2">
                      {breakout && (
                        <span className="meta-chip hot text-[0.5rem]">HOT</span>
                      )}
                      <div>
                        <span className="text-white font-medium">{coin.name || '—'}</span>
                        <span className="text-[var(--text-muted)] ml-2 font-mono text-xs">{coin.symbol}</span>
                      </div>
                    </div>
                  </td>

                  {/* Market Cap */}
                  <td className="font-mono">{formatCurrency(coin.market_cap)}</td>

                  {/* Volume */}
                  <td className="font-mono text-[var(--text-secondary)]">
                    {formatCurrency(coin.volume || coin.volume_24h)}
                  </td>

                  {/* Age */}
                  <td className="text-[var(--text-muted)]">{formatAge(coin.created_at)}</td>

                  {/* Price Change */}
                  <td className={`font-mono font-medium ${
                    change >= 0 ? 'text-[var(--accent-up)]' : 'text-[var(--accent-down)]'
                  }`}>
                    {formatChange(change)}
                  </td>

                  {/* Links */}
                  <td>
                    <div className="flex items-center gap-3">
                      {coin.twitter_url && (
                        <a
                          href={coin.twitter_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-400 hover:text-blue-300 transition-colors"
                          title="Twitter"
                        >
                          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                            <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
                          </svg>
                        </a>
                      )}
                      {coin.telegram_url && (
                        <a
                          href={coin.telegram_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-sky-400 hover:text-sky-300 transition-colors"
                          title="Telegram"
                        >
                          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                            <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/>
                          </svg>
                        </a>
                      )}
                      {coin.address && (
                        <a
                          href={`https://dexscreener.com/solana/${coin.address}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-[var(--accent-up)] hover:text-white transition-colors font-mono text-xs"
                          title="DexScreener"
                        >
                          DEX
                        </a>
                      )}
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="border-t border-[var(--border-subtle)] px-4 py-3 flex items-center justify-between">
          <div className="text-xs text-[var(--text-muted)]">
            {(currentPage - 1) * ITEMS_PER_PAGE + 1}–{Math.min(currentPage * ITEMS_PER_PAGE, coins.length)} of {coins.length}
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="btn text-xs disabled:opacity-30"
            >
              Prev
            </button>
            <span className="font-mono text-xs text-[var(--text-muted)]">
              {currentPage}/{totalPages}
            </span>
            <button
              onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="btn text-xs disabled:opacity-30"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
