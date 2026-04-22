import { useFilters } from '../context/FilterContext';

export default function CrumbRow() {
  const { breadcrumbs, clearAll, setMpio, setPueblo } = useFilters();

  if (!breadcrumbs || breadcrumbs.length <= 1) return null;

  const go = (level) => {
    if (level === 'nacional') clearAll();
    else if (level === 'dpto') setMpio('');
    else if (level === 'mpio') setPueblo('');
  };

  return (
    <div className="crumb-row">
      {breadcrumbs.map((c, i) => (
        <span key={c.level} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          {i > 0 && <span className="crumb-sep">›</span>}
          {i === breadcrumbs.length - 1
            ? <span className="crumb-active">{c.label}</span>
            : <button className="crumb-btn" onClick={() => go(c.level)}>{c.label}</button>
          }
        </span>
      ))}
    </div>
  );
}
