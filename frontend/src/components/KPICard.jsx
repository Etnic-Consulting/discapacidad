/* ============================================
   SMT-ONIC v2.0 — KPI Card Component
   ============================================ */

const styles = {
  card: (color) => ({
    background: '#fff',
    borderRadius: 'var(--radius-md)',
    boxShadow: 'var(--shadow-md)',
    padding: '18px 20px',
    borderLeft: `4px solid ${color || 'var(--color-green-mid)'}`,
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
    transition: 'transform 0.15s, box-shadow 0.15s',
    cursor: 'default',
  }),
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  title: {
    fontSize: '0.78rem',
    fontWeight: 600,
    textTransform: 'uppercase',
    letterSpacing: '0.4px',
    color: 'var(--color-gray-500)',
    lineHeight: 1.3,
  },
  icon: (color) => ({
    fontSize: '0.65rem',
    fontWeight: 700,
    opacity: 0.85,
    width: '28px',
    height: '28px',
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: '6px',
    background: color ? `${color}18` : 'rgba(2,67,45,0.08)',
    color: color || 'var(--color-primary)',
    letterSpacing: '0.3px',
    lineHeight: 1,
    flexShrink: 0,
  }),
  value: (color) => ({
    fontSize: '1.85rem',
    fontWeight: 700,
    fontFamily: 'var(--font-heading)',
    color: color || 'var(--color-primary)',
    lineHeight: 1.1,
    margin: '6px 0 2px',
  }),
  subtitle: {
    fontSize: '0.8rem',
    color: 'var(--color-gray-400)',
    lineHeight: 1.3,
  },
};

export default function KPICard({ title, value, subtitle, color, icon }) {
  return (
    <div
      style={styles.card(color)}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = 'translateY(-2px)';
        e.currentTarget.style.boxShadow = 'var(--shadow-lg)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = 'translateY(0)';
        e.currentTarget.style.boxShadow = 'var(--shadow-md)';
      }}
    >
      <div style={styles.header}>
        <div style={styles.title}>{title}</div>
        {icon && <span style={styles.icon(color)}>{icon}</span>}
      </div>
      <div style={styles.value(color)}>{value}</div>
      {subtitle && <div style={styles.subtitle}>{subtitle}</div>}
    </div>
  );
}
