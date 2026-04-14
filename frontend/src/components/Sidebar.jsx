/* ============================================
   SMT-ONIC v2.0 — Sidebar Navigation
   ============================================ */

import { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';

const NAV_ITEMS = [
  { path: '/',             icon: 'PG', label: 'Panorama Nacional' },
  { path: '/pueblos',      icon: 'PI', label: 'Pueblos Indigenas' },
  { path: '/territorios',  icon: 'TE', label: 'Territorios y Resguardos' },
  { path: '/conflicto',    icon: 'CA', label: 'Conflicto Armado' },
  { path: '/proyecciones', icon: 'PR', label: 'Proyecciones Intercensales' },
  { path: '/voz-propia',   icon: 'VP', label: 'Voz Propia — SMT-ONIC' },
  { path: '/indicadores',  icon: 'IN', label: 'Sistema de Indicadores' },
  { path: '/informes',     icon: 'IF', label: 'Generacion de Informes' },
  { path: '/formulario',   icon: 'FR', label: 'Formulario de Recoleccion' },
];

const styles = {
  sidebar: (collapsed) => ({
    position: 'fixed',
    top: 0,
    left: 0,
    width: collapsed ? 'var(--sidebar-collapsed)' : 'var(--sidebar-width)',
    height: '100vh',
    background: 'var(--color-primary)',
    color: '#fff',
    display: 'flex',
    flexDirection: 'column',
    transition: 'width 0.3s ease',
    zIndex: 100,
    overflow: 'hidden',
    boxShadow: '2px 0 12px rgba(0,0,0,0.15)',
  }),
  logoArea: {
    padding: '20px 16px 12px',
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    borderBottom: '1px solid rgba(255,255,255,0.1)',
    minHeight: '80px',
  },
  logoBox: {
    width: '36px',
    height: '36px',
    borderRadius: '8px',
    background: 'var(--color-green-mid)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontWeight: 700,
    fontSize: '0.85rem',
    flexShrink: 0,
  },
  logoText: (collapsed) => ({
    opacity: collapsed ? 0 : 1,
    transition: 'opacity 0.2s',
    whiteSpace: 'nowrap',
    overflow: 'hidden',
  }),
  logoTitle: {
    fontFamily: 'var(--font-heading)',
    fontSize: '1.1rem',
    fontWeight: 700,
    letterSpacing: '1px',
    lineHeight: 1.2,
  },
  logoSubtitle: {
    fontSize: '0.7rem',
    opacity: 0.7,
    letterSpacing: '0.5px',
  },
  nav: {
    flex: 1,
    padding: '12px 0',
    overflowY: 'auto',
  },
  navLink: (isActive, collapsed) => ({
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: collapsed ? '12px 20px' : '10px 20px',
    color: isActive ? '#fff' : 'rgba(255,255,255,0.7)',
    background: isActive ? 'rgba(2, 171, 68, 0.25)' : 'transparent',
    borderLeft: isActive ? '3px solid var(--color-green-mid)' : '3px solid transparent',
    textDecoration: 'none',
    fontSize: '0.88rem',
    fontWeight: isActive ? 600 : 400,
    transition: 'all 0.15s',
    whiteSpace: 'nowrap',
    cursor: 'pointer',
  }),
  navIcon: {
    fontSize: '0.7rem',
    fontWeight: 700,
    flexShrink: 0,
    width: '26px',
    height: '26px',
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: '6px',
    background: 'rgba(255,255,255,0.12)',
    letterSpacing: '0.5px',
    lineHeight: 1,
  },
  navLabel: (collapsed) => ({
    opacity: collapsed ? 0 : 1,
    transition: 'opacity 0.2s',
    overflow: 'hidden',
  }),
  collapseBtn: {
    padding: '12px',
    border: 'none',
    background: 'rgba(255,255,255,0.05)',
    color: 'rgba(255,255,255,0.6)',
    cursor: 'pointer',
    fontSize: '1.1rem',
    textAlign: 'center',
    transition: 'background 0.15s',
    borderTop: '1px solid rgba(255,255,255,0.1)',
  },
  footer: (collapsed) => ({
    padding: collapsed ? '10px 6px' : '12px 16px',
    borderTop: '1px solid rgba(255,255,255,0.1)',
    fontSize: '0.7rem',
    opacity: 0.5,
    textAlign: 'center',
    whiteSpace: 'nowrap',
    overflow: 'hidden',
  }),
};

export default function Sidebar({ collapsed, onToggle }) {
  const location = useLocation();

  return (
    <aside style={styles.sidebar(collapsed)}>
      {/* Logo */}
      <div style={styles.logoArea}>
        <div style={styles.logoBox}>
          <span style={{ fontSize: '1rem' }}>O</span>
        </div>
        <div style={styles.logoText(collapsed)}>
          <div style={styles.logoTitle}>SMT-ONIC</div>
          <div style={styles.logoSubtitle}>Capacidades Diversas</div>
        </div>
      </div>

      {/* Navigation */}
      <nav style={styles.nav}>
        {NAV_ITEMS.map((item) => {
          const isActive = item.path === '/'
            ? location.pathname === '/'
            : location.pathname.startsWith(item.path);

          return (
            <NavLink
              key={item.path}
              to={item.path}
              style={() => styles.navLink(isActive, collapsed)}
              onMouseEnter={(e) => {
                if (!isActive) e.currentTarget.style.background = 'rgba(255,255,255,0.08)';
              }}
              onMouseLeave={(e) => {
                if (!isActive) e.currentTarget.style.background = 'transparent';
              }}
            >
              <span style={styles.navIcon}>{item.icon}</span>
              <span style={styles.navLabel(collapsed)}>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* Collapse Toggle */}
      <button
        style={styles.collapseBtn}
        onClick={onToggle}
        onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(255,255,255,0.1)'; }}
        onMouseLeave={(e) => { e.currentTarget.style.background = 'rgba(255,255,255,0.05)'; }}
        title={collapsed ? 'Expandir menu' : 'Colapsar menu'}
      >
        {collapsed ? '\u203A' : '\u2039'}
      </button>

      {/* Footer */}
      <div style={styles.footer(collapsed)}>
        {collapsed ? 'v2' : 'SMT-ONIC v2.0 \u2014 ONIC 2026'}
      </div>
    </aside>
  );
}
