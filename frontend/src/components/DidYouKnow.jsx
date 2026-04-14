/* ============================================
   SMT-ONIC v2.0 — "Did You Know?" Callout Box
   Surprising data facts with source attribution.
   ============================================ */

const styles = {
  box: {
    background: 'var(--color-gold-light)',
    borderLeft: '4px solid var(--color-gold)',
    borderRadius: 'var(--radius-sm)',
    padding: '14px 18px',
    marginBottom: '20px',
  },
  header: {
    fontSize: '0.75rem',
    fontWeight: 700,
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
    color: 'var(--color-gold)',
    marginBottom: '6px',
  },
  fact: {
    fontSize: '0.9rem',
    fontStyle: 'italic',
    color: 'var(--color-charcoal)',
    lineHeight: 1.6,
    marginBottom: '6px',
  },
  source: {
    fontSize: '0.75rem',
    color: 'var(--color-gray-500)',
    fontWeight: 500,
  },
};

export default function DidYouKnow({ fact, source }) {
  return (
    <div style={styles.box}>
      <div style={styles.header}>Sabias que...</div>
      <div style={styles.fact}>{fact}</div>
      {source && <div style={styles.source}>Fuente: {source}</div>}
    </div>
  );
}
