/* ============================================
   SMT-ONIC v2.0 — App Shell
   ============================================ */

import { useState, useEffect } from 'react';
import { Routes, Route, Link, useLocation } from 'react-router-dom';
import { FilterProvider } from './context/FilterContext';
import Sidebar from './components/Sidebar';
import PanoramaPage from './pages/PanoramaPage';
import PueblosPage from './pages/PueblosPage';
import PuebloDetallePage from './pages/PuebloDetallePage';
import TerritoriosPage from './pages/TerritoriosPage';
import ConflictoPage from './pages/ConflictoPage';
import ProyeccionesPage from './pages/ProyeccionesPage';
import VozPropiaPage from './pages/VozPropiaPage';
import IndicadoresPage from './pages/IndicadoresPage';
import InformesPage from './pages/InformesPage';
import FormularioPage from './pages/FormularioPage';

export default function App() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const location = useLocation();

  /* Presentation mode: ?present=true adds larger fonts for projector use */
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    if (params.get('present') === 'true') {
      document.body.classList.add('presentation-mode');
    } else {
      document.body.classList.remove('presentation-mode');
    }
    return () => document.body.classList.remove('presentation-mode');
  }, [location.search]);

  return (
    <FilterProvider>
      <div className="app-layout">
        <Sidebar
          collapsed={sidebarCollapsed}
          onToggle={() => setSidebarCollapsed((c) => !c)}
        />
        <main className={`main-content ${sidebarCollapsed ? 'sidebar-collapsed' : ''}`}>
          <Routes>
            <Route path="/" element={<PanoramaPage />} />
            <Route path="/pueblos" element={<PueblosPage />} />
            <Route path="/pueblos/:codPueblo" element={<PuebloDetallePage />} />
            <Route path="/territorios" element={<TerritoriosPage />} />
            <Route path="/conflicto" element={<ConflictoPage />} />
            <Route path="/proyecciones" element={<ProyeccionesPage />} />
            <Route path="/voz-propia" element={<VozPropiaPage />} />
            <Route path="/indicadores" element={<IndicadoresPage />} />
            <Route path="/informes" element={<InformesPage />} />
            <Route path="/formulario" element={<FormularioPage />} />
            <Route path="*" element={
              <div style={{ textAlign: 'center', padding: '80px 20px' }}>
                <h1 style={{ fontSize: '3rem', color: 'var(--color-gray-400)', marginBottom: '12px' }}>404</h1>
                <p style={{ fontSize: '1.1rem', color: 'var(--color-gray-500)', marginBottom: '24px' }}>
                  Pagina no encontrada
                </p>
                <Link
                  to="/"
                  style={{
                    display: 'inline-block',
                    padding: '10px 24px',
                    background: 'var(--color-primary)',
                    color: '#fff',
                    borderRadius: 'var(--radius-sm)',
                    textDecoration: 'none',
                    fontWeight: 600,
                    fontSize: '0.9rem',
                  }}
                >
                  Volver al inicio
                </Link>
              </div>
            } />
          </Routes>
        </main>
      </div>
    </FilterProvider>
  );
}
