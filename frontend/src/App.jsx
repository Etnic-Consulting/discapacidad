import { useState, useEffect } from 'react';
import { Routes, Route, useLocation } from 'react-router-dom';
import { FilterProvider } from './context/FilterContext';
import { AuthProvider } from './context/AuthContext';
import RequireAuth from './components/RequireAuth';
import SiteChrome from './components/SiteChrome';
import SiteFooter from './components/SiteFooter';
import ModuleBanner from './components/ModuleBanner';
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
import LoginPage from './pages/LoginPage';

export default function App() {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();

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
    <AuthProvider>
    <FilterProvider>
      <SiteChrome />
      <ModuleBanner />
      <div className="app">
        <Sidebar collapsed={collapsed} onToggle={() => setCollapsed((c) => !c)} />
        <main className={'main' + (collapsed ? ' sb-col' : '')}>
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
            <Route path="/login" element={<LoginPage />} />
            <Route path="/formulario" element={<RequireAuth><FormularioPage /></RequireAuth>} />
            <Route path="*" element={
              <div className="page-inner" style={{ textAlign: 'center', paddingTop: 80 }}>
                <div style={{ fontFamily: 'var(--serif)', fontSize: '4rem', fontWeight: 300, color: 'var(--ink-faint)', marginBottom: 16 }}>404</div>
                <p style={{ color: 'var(--ink-muted)', marginBottom: 24 }}>Página no encontrada</p>
                <a href="/" className="btn btn-primary">Volver al inicio</a>
              </div>
            } />
          </Routes>
        </main>
      </div>
      <SiteFooter />
    </FilterProvider>
    </AuthProvider>
  );
}
