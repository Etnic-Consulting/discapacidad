export function Stat({ label, value, sub, variant = '' }) {
  return (
    <div className={'stat ' + variant}>
      <div className="stat-label">{label}</div>
      <div className="stat-val">{value}</div>
      {sub && <div className="stat-sub">{sub}</div>}
    </div>
  );
}

export default function StatGrid({ children, cols = 6 }) {
  const cls = cols === 4 ? 'cols-4' : cols === 3 ? 'cols-3' : '';
  return (
    <div className={'stat-grid ' + cls}>
      {children}
    </div>
  );
}
