/**
 * MarqueeBar - Breaking news style ticker
 */
export default function MarqueeBar({ items = [] }) {
  if (!items.length) return null;
  
  // Double the items for seamless loop
  const content = [...items, ...items].join('   •   ');
  
  return (
    <div className="marquee-container overflow-hidden">
      <div className="marquee-content whitespace-nowrap">
        {content}
        <span className="mx-8">•</span>
        {content}
      </div>
    </div>
  );
}
