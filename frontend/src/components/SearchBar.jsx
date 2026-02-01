import { useState, useCallback, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSearch } from '../hooks/useTrends';

/**
 * Debounce hook for search input
 */
function useDebounce(value, delay) {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => clearTimeout(handler);
  }, [value, delay]);

  return debouncedValue;
}

/**
 * Format currency values for display
 */
function formatCurrency(value) {
  if (!value && value !== 0) return '-';
  if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
  if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
  if (value >= 1e3) return `$${(value / 1e3).toFixed(1)}K`;
  return `$${value.toFixed(2)}`;
}

/**
 * SearchBar component with dropdown results
 */
export default function SearchBar() {
  const [query, setQuery] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const debouncedQuery = useDebounce(query, 300);
  const inputRef = useRef(null);
  const dropdownRef = useRef(null);
  const navigate = useNavigate();

  const { data: searchResults, isLoading } = useSearch(debouncedQuery);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target) &&
        !inputRef.current.contains(event.target)
      ) {
        setIsOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleInputChange = useCallback((e) => {
    setQuery(e.target.value);
    setIsOpen(true);
  }, []);

  const handleCoinClick = (coin) => {
    // Navigate to the trend detail page for the coin's category
    if (coin.primary_category) {
      const subCat = coin.sub_category || 'all';
      navigate(`/trend/${coin.primary_category}?sub=${subCat}`);
    }
    setIsOpen(false);
    setQuery('');
  };

  const handleMetaClick = (meta) => {
    // Search for the related keyword
    setQuery(meta.related_keyword);
  };

  const handleSuggestionClick = (suggestion) => {
    setQuery(suggestion);
  };

  const hasResults = searchResults && (
    searchResults.coins?.length > 0 ||
    searchResults.related_metas?.length > 0 ||
    searchResults.suggestions?.length > 0
  );

  return (
    <div className="relative w-full max-w-md">
      {/* Search Input */}
      <div className="relative">
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={handleInputChange}
          onFocus={() => setIsOpen(true)}
          placeholder="Search coins, metas (e.g., claw, molt, dog)..."
          className="w-full px-4 py-2 pl-10 bg-gray-800/50 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500 transition-colors"
        />
        <svg
          className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>
        {isLoading && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-purple-500"></div>
          </div>
        )}
      </div>

      {/* Dropdown Results */}
      {isOpen && query.length >= 2 && (
        <div
          ref={dropdownRef}
          className="absolute z-50 w-full mt-2 bg-gray-800 border border-gray-700 rounded-lg shadow-xl max-h-96 overflow-y-auto"
        >
          {isLoading && (
            <div className="p-4 text-center text-gray-400">
              <div className="inline-flex items-center gap-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-purple-500"></div>
                Searching...
              </div>
            </div>
          )}

          {!hasResults && !isLoading && (
            <div className="p-4 text-center text-gray-400">
              No results found for "{query}"
            </div>
          )}

          {/* Related Metas Section */}
          {searchResults?.related_metas?.length > 0 && (
            <div className="p-2 border-b border-gray-700">
              <h3 className="px-2 py-1 text-xs font-medium text-gray-500 uppercase">
                Related Metas
              </h3>
              {searchResults.related_metas.slice(0, 5).map((meta, idx) => (
                <button
                  key={idx}
                  onClick={() => handleMetaClick(meta)}
                  className="w-full px-3 py-2 flex items-center gap-3 hover:bg-gray-700/50 rounded-lg text-left transition-colors"
                >
                  <div className="w-8 h-8 rounded-full bg-purple-500/20 flex items-center justify-center">
                    <svg className="w-4 h-4 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                    </svg>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-white font-medium">{meta.source_keyword}</span>
                      <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                      </svg>
                      <span className="text-purple-400 font-medium">{meta.related_keyword}</span>
                    </div>
                    <p className="text-xs text-gray-500 truncate">
                      {meta.relationship_type} ({(meta.confidence * 100).toFixed(0)}% confidence)
                    </p>
                  </div>
                </button>
              ))}
            </div>
          )}

          {/* Coins Section */}
          {searchResults?.coins?.length > 0 && (
            <div className="p-2 border-b border-gray-700">
              <h3 className="px-2 py-1 text-xs font-medium text-gray-500 uppercase">
                Matching Coins ({searchResults.coins.length})
              </h3>
              {searchResults.coins.slice(0, 8).map((coin) => (
                <button
                  key={coin.token_address}
                  onClick={() => handleCoinClick(coin)}
                  className="w-full px-3 py-2 flex items-center gap-3 hover:bg-gray-700/50 rounded-lg text-left transition-colors"
                >
                  <div className="w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center">
                    <span className="text-blue-400 font-bold text-xs">
                      {coin.symbol?.slice(0, 2) || '?'}
                    </span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <span className="text-white font-medium truncate">{coin.name}</span>
                      <span className="text-gray-400 text-sm ml-2">
                        {formatCurrency(coin.market_cap)}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-xs">
                      <span className="text-gray-500 font-mono">{coin.symbol}</span>
                      {coin.primary_category && (
                        <span className="px-1.5 py-0.5 bg-gray-700 rounded text-gray-400">
                          {coin.primary_category}
                        </span>
                      )}
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}

          {/* Suggestions Section */}
          {searchResults?.suggestions?.length > 0 && (
            <div className="p-2">
              <h3 className="px-2 py-1 text-xs font-medium text-gray-500 uppercase">
                Try searching for
              </h3>
              <div className="flex flex-wrap gap-2 px-2">
                {searchResults.suggestions.map((suggestion, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSuggestionClick(suggestion)}
                    className="px-3 py-1 bg-gray-700/50 hover:bg-gray-700 rounded-full text-sm text-gray-300 hover:text-white transition-colors"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
