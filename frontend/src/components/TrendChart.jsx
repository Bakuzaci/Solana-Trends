import { useMemo } from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';

/**
 * Format large numbers for display
 */
function formatValue(value) {
  if (value >= 1e9) {
    return `$${(value / 1e9).toFixed(2)}B`;
  }
  if (value >= 1e6) {
    return `$${(value / 1e6).toFixed(2)}M`;
  }
  if (value >= 1e3) {
    return `$${(value / 1e3).toFixed(2)}K`;
  }
  return `$${value.toFixed(2)}`;
}

/**
 * Format date for x-axis
 */
function formatDate(timestamp) {
  const date = new Date(timestamp);
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

/**
 * Custom tooltip component
 */
function CustomTooltip({ active, payload, label }) {
  if (!active || !payload || !payload.length) {
    return null;
  }

  const date = new Date(label);
  const formattedDate = date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });

  return (
    <div className="bg-gray-800 border border-gray-600 rounded-lg p-3 shadow-lg">
      <p className="text-gray-300 text-sm mb-2">{formattedDate}</p>
      {payload.map((entry, index) => (
        <p key={index} className="text-sm" style={{ color: entry.color }}>
          {entry.name}: {entry.name === 'Coin Count' ? entry.value : formatValue(entry.value)}
        </p>
      ))}
    </div>
  );
}

/**
 * TrendChart component - displays market cap over time with optional coin count
 */
export default function TrendChart({
  history = [],
  showCoinCount = false,
  height = 300
}) {
  const chartData = useMemo(() => {
    if (!history || history.length === 0) {
      return [];
    }

    return history.map((point) => ({
      timestamp: point.timestamp || point.recorded_at,
      marketCap: point.total_market_cap || point.market_cap || 0,
      coinCount: point.coin_count || 0,
    }));
  }, [history]);

  if (chartData.length === 0) {
    return (
      <div
        className="flex items-center justify-center bg-gray-800/50 rounded-lg border border-gray-700"
        style={{ height }}
      >
        <p className="text-gray-400">No historical data available</p>
      </div>
    );
  }

  return (
    <div className="w-full" style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart
          data={chartData}
          margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
        >
          <defs>
            <linearGradient id="colorMarketCap" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.8} />
              <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0.1} />
            </linearGradient>
            <linearGradient id="colorCoinCount" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#10b981" stopOpacity={0.8} />
              <stop offset="95%" stopColor="#10b981" stopOpacity={0.1} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis
            dataKey="timestamp"
            tickFormatter={formatDate}
            stroke="#9ca3af"
            tick={{ fill: '#9ca3af', fontSize: 12 }}
            axisLine={{ stroke: '#4b5563' }}
          />
          <YAxis
            yAxisId="left"
            tickFormatter={formatValue}
            stroke="#9ca3af"
            tick={{ fill: '#9ca3af', fontSize: 12 }}
            axisLine={{ stroke: '#4b5563' }}
            width={80}
          />
          {showCoinCount && (
            <YAxis
              yAxisId="right"
              orientation="right"
              stroke="#9ca3af"
              tick={{ fill: '#9ca3af', fontSize: 12 }}
              axisLine={{ stroke: '#4b5563' }}
              width={50}
            />
          )}
          <Tooltip content={<CustomTooltip />} />
          {showCoinCount && (
            <Legend
              wrapperStyle={{ paddingTop: '10px' }}
              formatter={(value) => (
                <span className="text-gray-300 text-sm">{value}</span>
              )}
            />
          )}
          <Area
            yAxisId="left"
            type="monotone"
            dataKey="marketCap"
            name="Market Cap"
            stroke="#8b5cf6"
            strokeWidth={2}
            fillOpacity={1}
            fill="url(#colorMarketCap)"
          />
          {showCoinCount && (
            <Area
              yAxisId="right"
              type="monotone"
              dataKey="coinCount"
              name="Coin Count"
              stroke="#10b981"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#colorCoinCount)"
            />
          )}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
