export default function AccelerationBar({ score = 0, showLabel = true, size = 'md' }) {
  // Normalize score to 0-100 range
  const normalizedScore = Math.min(100, Math.max(0, score));

  // Determine color based on score
  const getColor = () => {
    if (normalizedScore >= 80) return 'from-green-500 to-emerald-400';
    if (normalizedScore >= 60) return 'from-lime-500 to-green-500';
    if (normalizedScore >= 40) return 'from-yellow-500 to-lime-500';
    if (normalizedScore >= 20) return 'from-orange-500 to-yellow-500';
    return 'from-red-500 to-orange-500';
  };

  const getTextColor = () => {
    if (normalizedScore >= 80) return 'text-green-400';
    if (normalizedScore >= 60) return 'text-lime-400';
    if (normalizedScore >= 40) return 'text-yellow-400';
    if (normalizedScore >= 20) return 'text-orange-400';
    return 'text-red-400';
  };

  const heightClass = size === 'sm' ? 'h-1.5' : size === 'lg' ? 'h-3' : 'h-2';

  return (
    <div className="w-full">
      {showLabel && (
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs text-gray-500">Acceleration</span>
          <span className={`text-sm font-bold ${getTextColor()}`}>
            {normalizedScore.toFixed(0)}
          </span>
        </div>
      )}
      <div className={`w-full bg-gray-800 rounded-full ${heightClass} overflow-hidden`}>
        <div
          className={`${heightClass} rounded-full bg-gradient-to-r ${getColor()} transition-all duration-500 ease-out`}
          style={{ width: `${normalizedScore}%` }}
        />
      </div>
    </div>
  );
}
