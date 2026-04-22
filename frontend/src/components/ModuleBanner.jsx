import { Link, useLocation } from 'react-router-dom';

const LABELS = {
  '/':             'Panorama',
  '/pueblos':      'Pueblos',
  '/territorios':  'Territorios',
  '/conflicto':    'Conflicto',
  '/proyecciones': 'Proyecciones',
  '/voz-propia':   'Voz Propia',
  '/indicadores':  'Indicadores',
  '/informes':     'Informes',
  '/formulario':   'Formulario',
};

export default function ModuleBanner() {
  const { pathname } = useLocation();
  const base = '/' + (pathname.split('/')[1] || '');
  const label = LABELS[base] || 'Módulo';
  const isPuebloDetalle = pathname.startsWith('/pueblos/') && pathname !== '/pueblos';

  return (
    <div className="module-banner">
      <span className="mb-crumb">
        <a href="/">smt-onic.co</a>
        <span className="sep">›</span>
        <a href="/">Módulos</a>
        <span className="sep">›</span>
        {isPuebloDetalle
          ? <><Link to="/pueblos">Pueblos</Link><span className="sep">›</span><strong>Perfil pueblo</strong></>
          : <strong>{label}</strong>
        }
      </span>
      <span className="mb-spacer" />
      <Link to="/" className="mb-back">← Inicio</Link>
    </div>
  );
}
