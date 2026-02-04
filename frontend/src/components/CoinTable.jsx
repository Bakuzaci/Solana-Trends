import { useState, useMemo } from 'react';

/**
 * Format market cap/liquidity values
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
 * Format percentage change
 */
function formatChange(value) {
  if (!value && value !== 0) return '-';
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(2)}%`;
}

/**
 * Format coin age
 */
function formatAge(createdAt) {
  if (!createdAt) return '-';
  const now = new Date();
  const created = new Date(createdAt);
  const diffMs = now - created;
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffDays = Math.floor(diffHours / 24);

  if (diffDays > 30) {
    const months = Math.floor(diffDays / 30);
    return `${months}mo`;
  }
  if (diffDays > 0) {
    return `${diffDays}d`;
  }
  return `${diffHours}h`;
}

/**
 * Sort icon component
 */
function SortIcon({ direction }) {
  if (!direction) {
    return (
      <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
      </svg>
    );
  }
  return direction === 'asc' ? (
    <svg className="w-4 h-4 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
    </svg>
  ) : (
    <svg className="w-4 h-4 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
    </svg>
  );
}

/**
 * External link icon
 */
function ExternalLinkIcon() {
  return (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
    </svg>
  );
}

/**
 * Column definitions
 */
const COLUMNS = [
  { key: 'name', label: 'Name', sortable: true },
  { key: 'symbol', label: 'Symbol', sortable: true },
  { key: 'market_cap', label: 'Market Cap', sortable: true },
  { key: 'liquidity', label: 'Liquidity', sortable: true },
  { key: 'created_at', label: 'Age', sortable: true },
  { key: 'price_change', label: '24h Change', sortable: true },
  { key: 'links', label: 'Links', sortable: false },
];

/**
 * Get price change value from coin (handles different field names)
 */
function getPriceChange(coin) {
  return coin.change_1h ?? coin.price_change_24h ?? coin.price_change ?? 0;
}

const ITEMS_PER_PAGE = 20;

/**
 * CoinTable component - sortable table with pagination
 */
export default function CoinTable({ coins = [], averageMarketCap = 0 }) {
  const [sortConfig, setSortConfig] = useState({ key: 'market_cap', direction: 'desc' });
  const [currentPage, setCurrentPage] = useState(1);

  // Handle column sorting
  const handleSort = (key) => {
    if (!COLUMNS.find(col => col.key === key)?.sortable) return;

    setSortConfig((prev) => ({
      key,
      direction: prev.key === key && prev.direction === 'desc' ? 'asc' : 'desc',
    }));
    setCurrentPage(1);
  };

  // Sort and paginate coins
  const { sortedCoins, totalPages, displayedCoins } = useMemo(() => {
    const sorted = [...coins].sort((a, b) => {
      // Handle price_change specially since it can come from different fields
      let aVal, bVal;
      if (sortConfig.key === 'price_change') {
        aVal = getPriceChange(a);
        bVal = getPriceChange(b);
      } else {
        aVal = a[sortConfig.key];
        bVal = b[sortConfig.key];
      }

      // Handle null/undefined values
      if (aVal == null && bVal == null) return 0;
      if (aVal == null) return sortConfig.direction === 'asc' ? 1 : -1;
      if (bVal == null) return sortConfig.direction === 'asc' ? -1 : 1;

      // Handle dates
      if (sortConfig.key === 'created_at') {
        const dateA = new Date(aVal).getTime();
        const dateB = new Date(bVal).getTime();
        return sortConfig.direction === 'asc' ? dateA - dateB : dateB - dateA;
      }

      // Handle strings
      if (typeof aVal === 'string') {
        return sortConfig.direction === 'asc'
          ? aVal.localeCompare(bVal)
          : bVal.localeCompare(aVal);
      }

      // Handle numbers
      return sortConfig.direction === 'asc' ? aVal - bVal : bVal - aVal;
    });

    const total = Math.ceil(sorted.length / ITEMS_PER_PAGE);
    const start = (currentPage - 1) * ITEMS_PER_PAGE;
    const displayed = sorted.slice(start, start + ITEMS_PER_PAGE);

    return { sortedCoins: sorted, totalPages: total, displayedCoins: displayed };
  }, [coins, sortConfig, currentPage]);

  // Check if coin is a breakout (>5x average)
  const isBreakout = (marketCap) => {
    return averageMarketCap > 0 && marketCap > averageMarketCap * 5;
  };

  if (coins.length === 0) {
    return (
      <div className="bg-gray-800/50 rounded-lg border border-gray-700 p-8 text-center">
        <p className="text-gray-400">No coins found for this trend</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-800/50 rounded-lg border border-gray-700 overflow-hidden">
      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-gray-900/50">
              {COLUMNS.map((column) => (
                <th
                  key={column.key}
                  onClick={() => handleSort(column.key)}
                  className={`px-4 py-3 text-left text-sm font-medium text-gray-300 ${
                    column.sortable ? 'cursor-pointer hover:bg-gray-700/50 select-none' : ''
                  }`}
                >
                  <div className="flex items-center gap-2">
                    {column.label}
                    {column.sortable && (
                      <SortIcon
                        direction={sortConfig.key === column.key ? sortConfig.direction : null}
                      />
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-700/50">
            {displayedCoins.map((coin, index) => {
              const breakout = isBreakout(coin.market_cap);
              return (
                <tr
                  key={coin.address || index}
                  className={`hover:bg-gray-700/30 transition-colors ${
                    breakout ? 'bg-purple-900/20' : ''
                  }`}
                >
                  {/* Name */}
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      {breakout && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-500/20 text-purple-300 border border-purple-500/30">
                          BREAKOUT
                        </span>
                      )}
                      <span className="text-white font-medium">{coin.name || '-'}</span>
                    </div>
                  </td>

                  {/* Symbol */}
                  <td className="px-4 py-3 text-gray-300 font-mono">
                    {coin.symbol || '-'}
                  </td>

                  {/* Market Cap */}
                  <td className="px-4 py-3 text-gray-200 font-medium">
                    {formatCurrency(coin.market_cap)}
                  </td>

                  {/* Liquidity */}
                  <td className="px-4 py-3 text-gray-300">
                    {formatCurrency(coin.liquidity)}
                  </td>

                  {/* Age */}
                  <td className="px-4 py-3 text-gray-400">
                    {formatAge(coin.created_at)}
                  </td>

                  {/* Price Change */}
                  <td className={`px-4 py-3 font-medium ${
                    getPriceChange(coin) >= 0 ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {formatChange(getPriceChange(coin))}
                  </td>

                  {/* Links */}
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      {/* Social links */}
                      {coin.twitter_url && (
                        <a
                          href={coin.twitter_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-400 hover:text-blue-300 transition-colors"
                          title="Twitter/X"
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
                      {coin.website_url && (
                        <a
                          href={coin.website_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-gray-400 hover:text-gray-300 transition-colors"
                          title="Website"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9"/>
                          </svg>
                        </a>
                      )}
                      {/* Trading/explorer links */}
                      {coin.address && (
                        <>
                          <a
                            href={`https://dexscreener.com/solana/${coin.address}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-green-400 hover:text-green-300 transition-colors"
                            title="DexScreener"
                          >
                            <ExternalLinkIcon />
                          </a>
                        </>
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
        <div className="px-4 py-3 bg-gray-900/50 border-t border-gray-700 flex items-center justify-between">
          <div className="text-sm text-gray-400">
            Showing {(currentPage - 1) * ITEMS_PER_PAGE + 1} to{' '}
            {Math.min(currentPage * ITEMS_PER_PAGE, coins.length)} of {coins.length} coins
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="px-3 py-1 rounded bg-gray-700 text-gray-300 hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Previous
            </button>
            <span className="text-gray-400 text-sm">
              Page {currentPage} of {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="px-3 py-1 rounded bg-gray-700 text-gray-300 hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
