/**
 * TimeWindowToggle component - button group for selecting time window
 */
export default function TimeWindowToggle({ value, onChange }) {
  const options = [
    { value: '12h', label: '12h' },
    { value: '24h', label: '24h' },
    { value: '7d', label: '7d' },
  ];

  return (
    <div className="inline-flex rounded-lg bg-gray-800 p-1 border border-gray-700">
      {options.map((option) => (
        <button
          key={option.value}
          onClick={() => onChange(option.value)}
          className={`px-4 py-2 text-sm font-medium rounded-md transition-all duration-200 ${
            value === option.value
              ? 'bg-purple-600 text-white shadow-lg'
              : 'text-gray-400 hover:text-white hover:bg-gray-700/50'
          }`}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
