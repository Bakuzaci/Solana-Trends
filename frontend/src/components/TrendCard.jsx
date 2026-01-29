import { ArrowUpRight, ArrowDownRight, Minus, TrendingUp } from 'lucide-react';
import AccelerationBar from './AccelerationBar';

const formatMarketCap = (value) => {
  if (!value && value !== 0) return '-';
  if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
  if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
  if (value >= 1e3) return `$${(value / 1e3).toFixed(2)}K`;
  return `$${value.toFixed(2)}`;
};

const getTrendIcon = (direction) => {
  switch (direction) {
    case 'up':
      return <ArrowUpRight className="w-4 h-4 text-green-400" />;
    case 'down':
      return <ArrowDownRight className="w-4 h-4 text-red-400" />;
    default:
      return <Minus className="w-4 h-4 text-gray-400" />;
  }
};

const getTrendColor = (direction) => {
  switch (direction) {
    case 'up':
      return 'border-green-500/30 hover:border-green-500/50';
    case 'down':
      return 'border-red-500/30 hover:border-red-500/50';
    default:
      return 'border-gray-700 hover:border-purple-500/50';
  }
};

export default function TrendCard({ trend, onClick }) {
  const {
    emoji,
    name,
    category,
    sub_category,
    coin_count,
    total_market_cap,
    top_coin,
    acceleration_score,
    trend_direction,
    velocity
  } = trend;

  const displayName = name || sub_category || category;
  const displayEmoji = emoji || '📊';

  return (
    <div
      onClick={onClick}
      className={`bg-gray-900 rounded-xl p-4 border cursor-pointer transition-all duration-200 hover:bg-gray-800/80 ${getTrendColor(trend_direction)}`}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3 min-w-0">
          <span className="text-2xl flex-shrink-0">{displayEmoji}</span>
          <div className="min-w-0">
            <h3 className="font-semibold text-white truncate">{displayName}</h3>
            {category && sub_category && (
              <p className="text-xs text-gray-500 truncate">{category}</p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-1 flex-shrink-0">
          {getTrendIcon(trend_direction)}
          {velocity !== undefined && (
            <span className={`text-xs ${velocity > 0 ? 'text-green-400' : velocity < 0 ? 'text-red-400' : 'text-gray-400'}`}>
              {velocity > 0 ? '+' : ''}{velocity?.toFixed(1)}
            </span>
          )}
        </div>
      </div>

      {/* Acceleration Bar */}
      <div className="mb-3">
        <AccelerationBar score={acceleration_score} />
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-3 text-sm">
        <div>
          <p className="text-gray-500 text-xs">Coins</p>
          <p className="text-white font-medium">{coin_count || 0}</p>
        </div>
        <div>
          <p className="text-gray-500 text-xs">Market Cap</p>
          <p className="text-white font-medium">{formatMarketCap(total_market_cap)}</p>
        </div>
      </div>

      {/* Top Coin */}
      {top_coin && (
        <div className="mt-3 pt-3 border-t border-gray-800">
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-1 text-gray-400">
              <TrendingUp className="w-3 h-3" />
              <span className="text-xs">Top:</span>
              <span className="text-purple-400 font-medium">${top_coin.symbol}</span>
            </div>
            <span className="text-gray-400 text-xs">
              {formatMarketCap(top_coin.market_cap)}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
