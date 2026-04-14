/* ============================================
   SMT-ONIC v2.0 — Reusable Tooltip Component
   Appears on hover as a small card with source info.
   ============================================ */

import { useState, useRef } from 'react';

const styles = {
  wrapper: {
    position: 'relative',
    display: 'inline-flex',
    alignItems: 'center',
    cursor: 'help',
  },
  trigger: {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    width: '16px',
    height: '16px',
    borderRadius: '50%',
    background: 'var(--color-gray-200)',
    color: 'var(--color-gray-500)',
    fontSize: '0.65rem',
    fontWeight: 700,
    marginLeft: '4px',
    lineHeight: 1,
    flexShrink: 0,
  },
  card: (visible) => ({
    position: 'absolute',
    bottom: 'calc(100% + 10px)',
    left: '50%',
    transform: 'translateX(-50%)',
    background: '#fff',
    borderRadius: 'var(--radius-sm)',
    boxShadow: '0 4px 20px rgba(0,0,0,0.15)',
    padding: '12px 16px',
    minWidth: '220px',
    maxWidth: '320px',
    zIndex: 1000,
    opacity: visible ? 1 : 0,
    pointerEvents: visible ? 'auto' : 'none',
    transition: 'opacity 0.2s ease',
  }),
  arrow: {
    position: 'absolute',
    bottom: '-6px',
    left: '50%',
    transform: 'translateX(-50%) rotate(45deg)',
    width: '12px',
    height: '12px',
    background: '#fff',
    boxShadow: '2px 2px 4px rgba(0,0,0,0.08)',
  },
  text: {
    fontSize: '0.82rem',
    color: 'var(--color-charcoal)',
    lineHeight: 1.5,
    marginBottom: '4px',
    fontWeight: 500,
  },
  detail: {
    fontSize: '0.78rem',
    color: 'var(--color-gray-500)',
    lineHeight: 1.5,
    marginBottom: '6px',
  },
  source: {
    fontSize: '0.72rem',
    color: 'var(--color-green-mid)',
    fontWeight: 600,
    borderTop: '1px solid var(--color-gray-200)',
    paddingTop: '6px',
    marginTop: '4px',
  },
};

export default function Tooltip({ text, detail, source, children }) {
  const [visible, setVisible] = useState(false);
  const timeoutRef = useRef(null);

  const handleEnter = () => {
    clearTimeout(timeoutRef.current);
    setVisible(true);
  };

  const handleLeave = () => {
    timeoutRef.current = setTimeout(() => setVisible(false), 150);
  };

  return (
    <span
      style={styles.wrapper}
      onMouseEnter={handleEnter}
      onMouseLeave={handleLeave}
    >
      {children || <span style={styles.trigger}>?</span>}

      <span style={styles.card(visible)}>
        <span style={styles.arrow} />
        {text && <div style={styles.text}>{text}</div>}
        {detail && <div style={styles.detail}>{detail}</div>}
        {source && <div style={styles.source}>Fuente: {source}</div>}
      </span>
    </span>
  );
}
