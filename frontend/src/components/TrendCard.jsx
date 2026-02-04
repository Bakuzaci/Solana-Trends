/**
 * TrendCard - Editorial style category card
 */
export default function TrendCard({ trend, onClick, rank }) {
  const {
    emoji,
    category,
    sub_category,
    coin_count,
    total_market_cap,
    acceleration_score,
    is_breakout_meta,
    change_24h,
  } = trend;

  const displayName = sub_category || category;
  const displayEmoji = emoji || '📊';
  
  const formatMcap = (value) => {
    if (!value) return '—';
    if (value >= 1e6) return `$${(value / 1e6).toFixed(1)}M`;
    if (value >= 1e3) return `$${(value / 1e3).toFixed(0)}K`;
    return `$${value.toFixed(0)}`;
  };

  return (
    <div
      onClick={onClick}
      className={`card cursor-pointer group ${is_breakout_meta ? 'card-featured' : ''}`}
    >
      <div className="p-4">
        {/* Rank & Category */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            {rank && (
              <span className="font-mono text-2xl font-semibold text-[var(--text-muted)]">
                {String(rank).padStart(2, '0')}
              </span>
            )}
            <span className="text-3xl">{displayEmoji}</span>
          </div>
          
          {is_breakout_meta && (
            <span className="meta-chip hot">Breakout</span>
          )}
        </div>
        
        {/* Name */}
        <div className="mb-4">
          <h3 className="headline-md text-white group-hover:text-[var(--accent-highlight)] transition-colors">
            {displayName}
          </h3>
          {sub_category && (
            <p className="text-xs text-[var(--text-muted)] mt-1">{category}</p>
          )}
        </div>
        
        {/* Stats */}
        <div className="grid grid-cols-3 gap-4 pt-4 border-t border-[var(--border-subtle)]">
          <div>
            <div className="label-sm mb-1">Tokens</div>
            <div className="font-mono text-lg font-medium">{coin_count || 0}</div>
          </div>
          
          <div>
            <div className="label-sm mb-1">MCap</div>
            <div className="font-mono text-lg font-medium">{formatMcap(total_market_cap)}</div>
          </div>
          
          <div>
            <div className="label-sm mb-1">Accel</div>
            <div className={`font-mono text-lg font-medium ${
              acceleration_score >= 70 ? 'text-[var(--accent-hot)]' : 
              acceleration_score >= 40 ? 'text-[var(--accent-up)]' : 
              'text-[var(--text-secondary)]'
            }`}>
              {acceleration_score?.toFixed(0) || '—'}
            </div>
          </div>
        </div>
        
        {/* 24h Change */}
        {change_24h !== null && change_24h !== undefined && (
          <div className="mt-4 pt-4 border-t border-[var(--border-subtle)] flex items-center justify-between">
            <span className="label-sm">24h Change</span>
            <span className={`font-mono text-sm font-medium ${
              change_24h >= 0 ? 'text-[var(--accent-up)]' : 'text-[var(--accent-down)]'
            }`}>
              {change_24h >= 0 ? '+' : ''}{change_24h.toFixed(1)}%
            </span>
          </div>
        )}
      </div>
      
      {/* Bottom accent bar for acceleration */}
      <div 
        className="h-1 transition-all"
        style={{
          background: `linear-gradient(90deg, 
            ${acceleration_score >= 70 ? 'var(--accent-hot)' : 'var(--accent-up)'} ${Math.min(acceleration_score || 0, 100)}%, 
            var(--bg-tertiary) ${Math.min(acceleration_score || 0, 100)}%
          )`
        }}
      />
    </div>
  );
}
