import { Sparkles, Tag, TrendingUp, Clock } from 'lucide-react';

const formatMarketCap = (value) => {
  if (!value && value !== 0) return '-';
  if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
  if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
  if (value >= 1e3) return `$${(value / 1e3).toFixed(2)}K`;
  return `$${value.toFixed(2)}`;
};

const formatTimeAgo = (timestamp) => {
  if (!timestamp) return '';
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now - date;
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffDays = Math.floor(diffHours / 24);

  if (diffDays > 0) return `${diffDays}d ago`;
  if (diffHours > 0) return `${diffHours}h ago`;
  return 'Just now';
};

export default function BreakoutMetaCard({ meta }) {
  const {
    cluster_id,
    suggested_name,
    coin_count,
    common_terms = [],
    total_market_cap,
    avg_acceleration,
    sample_coins = [],
    detected_at
  } = meta;

  return (
    <div className="bg-gray-900 rounded-xl p-4 border border-purple-500/30 hover:border-purple-500/50 transition-all">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="p-1.5 bg-purple-500/20 rounded-lg">
            <Sparkles className="w-4 h-4 text-purple-400" />
          </div>
          <div>
            <h3 className="font-semibold text-white">{suggested_name || 'Emerging Cluster'}</h3>
            <p className="text-xs text-gray-500">ID: {cluster_id}</p>
          </div>
        </div>
        <div className="flex items-center gap-1 text-xs text-gray-400">
          <Clock className="w-3 h-3" />
          <span>{formatTimeAgo(detected_at)}</span>
        </div>
      </div>

      {/* Common Terms */}
      {common_terms.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-3">
          {common_terms.slice(0, 5).map((term, index) => (
            <span
              key={index}
              className="px-2 py-0.5 text-xs bg-purple-500/20 text-purple-300 rounded-full"
            >
              {term}
            </span>
          ))}
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-3 gap-2 mb-3 text-sm">
        <div>
          <p className="text-gray-500 text-xs">Coins</p>
          <p className="text-white font-medium">{coin_count || 0}</p>
        </div>
        <div>
          <p className="text-gray-500 text-xs">Market Cap</p>
          <p className="text-white font-medium">{formatMarketCap(total_market_cap)}</p>
        </div>
        <div>
          <p className="text-gray-500 text-xs">Avg Accel</p>
          <p className="text-purple-400 font-medium">{avg_acceleration?.toFixed(0) || 0}</p>
        </div>
      </div>

      {/* Sample Coins */}
      {sample_coins.length > 0 && (
        <div className="pt-3 border-t border-gray-800">
          <div className="flex items-center gap-1 text-xs text-gray-400 mb-2">
            <Tag className="w-3 h-3" />
            <span>Sample Coins:</span>
          </div>
          <div className="flex flex-wrap gap-1">
            {sample_coins.slice(0, 3).map((coin, index) => (
              <span
                key={index}
                className="px-2 py-0.5 text-xs bg-gray-800 text-gray-300 rounded font-mono"
              >
                ${coin}
              </span>
            ))}
            {sample_coins.length > 3 && (
              <span className="px-2 py-0.5 text-xs text-gray-500">
                +{sample_coins.length - 3} more
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
