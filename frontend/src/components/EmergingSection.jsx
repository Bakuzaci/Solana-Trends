/**
 * EmergingSection - Shows emerging meta clusters
 */
export default function EmergingSection({ clusters = [] }) {
  if (!clusters.length) return null;
  
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {clusters.slice(0, 6).map((cluster) => (
        <div 
          key={cluster.cluster_id}
          className="card-featured p-4"
        >
          <div className="flex items-start justify-between mb-3">
            <div>
              <div className="label-sm mb-1">Cluster #{cluster.cluster_id}</div>
              <h3 className="headline-md text-[var(--accent-highlight)]">
                {cluster.cluster_name || 'Unnamed Cluster'}
              </h3>
            </div>
            <span className="font-mono text-lg">
              {cluster.token_count}
            </span>
          </div>
          
          {/* Keywords */}
          {cluster.common_keywords?.length > 0 && (
            <div className="flex flex-wrap gap-1 mb-4">
              {cluster.common_keywords.slice(0, 4).map(kw => (
                <span key={kw} className="meta-chip text-xs">
                  {kw}
                </span>
              ))}
            </div>
          )}
          
          {/* Stats */}
          <div className="grid grid-cols-2 gap-4 pt-3 border-t border-[var(--border-subtle)]">
            <div>
              <div className="label-sm">Volume 24h</div>
              <div className="font-mono text-sm mt-1">
                ${cluster.total_volume_24h?.toLocaleString() || '—'}
              </div>
            </div>
            <div>
              <div className="label-sm">Market Cap</div>
              <div className="font-mono text-sm mt-1">
                ${cluster.total_market_cap?.toLocaleString() || '—'}
              </div>
            </div>
          </div>
          
          {/* Top tokens */}
          {cluster.tokens?.length > 0 && (
            <div className="mt-4 pt-3 border-t border-[var(--border-subtle)]">
              <div className="label-sm mb-2">Top Tokens</div>
              <div className="space-y-1">
                {cluster.tokens.slice(0, 3).map(token => (
                  <div key={token.token_address} className="flex items-center justify-between">
                    <span className="text-sm truncate max-w-[120px]">{token.name}</span>
                    <span className={`font-mono text-xs ${
                      token.price_change_24h >= 0 ? 'text-[var(--accent-up)]' : 'text-[var(--accent-down)]'
                    }`}>
                      {token.price_change_24h ? `${token.price_change_24h >= 0 ? '+' : ''}${token.price_change_24h.toFixed(0)}%` : '—'}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
