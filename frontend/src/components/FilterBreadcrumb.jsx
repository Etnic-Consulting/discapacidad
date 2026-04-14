/* ============================================
   SMT-ONIC v2.0 — Filter Breadcrumb
   Shows the current filter chain:
   Nacional > Cauca > Toribio > Nasa
   Clickable to navigate back up the hierarchy.
   ============================================ */

import { useFilters } from '../context/FilterContext';

const styles = {
  wrapper: {
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
    fontSize: '0.85rem',
    fontWeight: 500,
    color: 'var(--color-gray-500)',
    marginBottom: '12px',
    flexWrap: 'wrap',
  },
  crumb: {
    cursor: 'pointer',
    color: 'var(--color-green-mid)',
    fontWeight: 600,
    background: 'none',
    border: 'none',
    padding: '2px 4px',
    fontFamily: 'var(--font-body)',
    fontSize: '0.85rem',
    borderRadius: 'var(--radius-sm)',
    transition: 'background 0.15s',
  },
  crumbActive: {
    cursor: 'default',
    color: 'var(--color-primary)',
    fontWeight: 700,
    background: 'none',
    border: 'none',
    padding: '2px 4px',
    fontFamily: 'var(--font-body)',
    fontSize: '0.85rem',
  },
  separator: {
    color: 'var(--color-gray-300)',
    fontSize: '0.75rem',
    userSelect: 'none',
  },
};

export default function FilterBreadcrumb() {
  const { breadcrumbs, setDpto, setMpio, setPueblo, setResguardo, clearAll } = useFilters();

  if (breadcrumbs.length <= 1) return null; // Only "Nacional", no active filters

  const handleClick = (crumb) => {
    switch (crumb.level) {
      case 'nacional':
        clearAll();
        break;
      case 'dpto':
        // Keep dpto, clear mpio + pueblo + resguardo
        setMpio('');
        break;
      case 'mpio':
        // Keep dpto + mpio, clear pueblo + resguardo
        setPueblo('');
        setResguardo('');
        break;
      case 'pueblo':
        // Keep dpto + mpio + pueblo, clear resguardo
        setResguardo('');
        break;
      // 'resguardo' is the last level, no action needed
      default:
        break;
    }
  };

  return (
    <div style={styles.wrapper}>
      {breadcrumbs.map((crumb, i) => {
        const isLast = i === breadcrumbs.length - 1;
        return (
          <span key={crumb.level} style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            {i > 0 && <span style={styles.separator}>&rsaquo;</span>}
            <button
              style={isLast ? styles.crumbActive : styles.crumb}
              onClick={isLast ? undefined : () => handleClick(crumb)}
              onMouseEnter={
                isLast
                  ? undefined
                  : (e) => {
                      e.currentTarget.style.background = 'var(--color-gray-100)';
                    }
              }
              onMouseLeave={
                isLast
                  ? undefined
                  : (e) => {
                      e.currentTarget.style.background = 'none';
                    }
              }
              disabled={isLast}
            >
              {crumb.label}
            </button>
          </span>
        );
      })}
    </div>
  );
}
