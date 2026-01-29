/**
 * SortSelect component - dropdown for selecting sort criteria
 */
export default function SortSelect({ value, onChange }) {
  const options = [
    { value: 'acceleration', label: 'Acceleration' },
    { value: 'market_cap', label: 'Market Cap' },
    { value: 'coin_count', label: 'Coin Count' },
  ];

  return (
    <div className="relative inline-block">
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="appearance-none bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 pr-10 text-sm font-medium text-gray-200 hover:border-gray-600 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent cursor-pointer transition-colors"
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            Sort by: {option.label}
          </option>
        ))}
      </select>
      <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
        <svg
          className="w-4 h-4 text-gray-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </div>
    </div>
  );
}
