/* ============================================
   <ColorPaletteToggle /> · T26 Sprint S1.E
   ============================================
   Toggle accesibilidad cromática.
   Cuando está ON, aplica `data-colorblind="true"` al <body>
   activando la paleta Viridis-inspired definida en index.css.

   Persiste preferencia en localStorage.
   Doctrina: _docs/DOCTRINA_DISENO_VISUAL_v1.md §2.2
   ============================================ */

import { useEffect, useState } from 'react';

const STORAGE_KEY = 'smt_onic_colorblind_palette';

const triggerStyle = (active) => ({
  position: 'fixed',
  bottom: 84, // arriba del glosario (que está en bottom: 24)
  right: 24,
  width: 48,
  height: 48,
  borderRadius: '50%',
  background: active ? '#1F968B' : 'var(--color-gold, #C4920A)',
  color: 'white',
  border: '2px solid white',
  cursor: 'pointer',
  fontSize: '1.25rem',
  fontWeight: 600,
  boxShadow: '0 4px 12px rgba(0,0,0,0.2)',
  zIndex: 999,
  transition: 'background 0.2s, transform 0.15s',
});

const labelStyle = {
  position: 'fixed',
  bottom: 88,
  right: 80,
  background: 'rgba(0,0,0,0.78)',
  color: 'white',
  fontSize: '0.75rem',
  padding: '4px 10px',
  borderRadius: 12,
  zIndex: 998,
  pointerEvents: 'none',
  whiteSpace: 'nowrap',
};

export default function ColorPaletteToggle() {
  const [active, setActive] = useState(false);
  const [hover, setHover] = useState(false);

  // Cargar preferencia inicial
  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved === '1') {
        setActive(true);
        document.body.setAttribute('data-colorblind', 'true');
      }
    } catch (e) {
      // localStorage puede fallar en algunos navegadores · ignorar
    }
  }, []);

  const toggle = () => {
    const next = !active;
    setActive(next);
    if (next) {
      document.body.setAttribute('data-colorblind', 'true');
      try { localStorage.setItem(STORAGE_KEY, '1'); } catch (e) { /* ignore */ }
    } else {
      document.body.removeAttribute('data-colorblind');
      try { localStorage.removeItem(STORAGE_KEY); } catch (e) { /* ignore */ }
    }
  };

  return (
    <>
      {hover && (
        <div style={labelStyle}>
          {active ? 'Paleta colorblind ACTIVA · click para desactivar' : 'Activar paleta colorblind-safe (Viridis)'}
        </div>
      )}
      <button
        type="button"
        style={triggerStyle(active)}
        onClick={toggle}
        onMouseEnter={() => setHover(true)}
        onMouseLeave={() => setHover(false)}
        aria-label={active ? 'Desactivar paleta colorblind' : 'Activar paleta colorblind-safe'}
        aria-pressed={active}
        title="Toggle paleta colorblind-safe"
      >
        {active ? '◉' : '◎'}
      </button>
    </>
  );
}
