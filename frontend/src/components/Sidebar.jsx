import { NavLink, useLocation } from 'react-router-dom';

const NAV_GROUPS = [
  {
    label: 'Visión general',
    items: [
      { id: 'panorama',      to: '/',             label: 'Panorama Nacional',    initial: 'PG', num: '01' },
    ],
  },
  {
    label: 'Datos',
    items: [
      { id: 'pueblos',      to: '/pueblos',       label: 'Pueblos Indígenas',    initial: 'PI', num: '02' },
      { id: 'territorios',  to: '/territorios',   label: 'Territorios',          initial: 'TE', num: '03' },
      { id: 'conflicto',    to: '/conflicto',     label: 'Conflicto Armado',     initial: 'CA', num: '04' },
      { id: 'proyecciones', to: '/proyecciones',  label: 'Proyecciones',         initial: 'PR', num: '05' },
    ],
  },
  {
    label: 'Monitoreo',
    items: [
      { id: 'voz-propia',   to: '/voz-propia',   label: 'Voz Propia — SMT',     initial: 'VP', num: '06' },
      { id: 'indicadores',  to: '/indicadores',  label: 'Indicadores',           initial: 'IN', num: '07' },
    ],
  },
  {
    label: 'Producción',
    items: [
      { id: 'informes',     to: '/informes',     label: 'Informes',              initial: 'IF', num: '08' },
      { id: 'formulario',   to: '/formulario',   label: 'Formulario',            initial: 'FR', num: '09' },
    ],
  },
];

export default function Sidebar({ collapsed, onToggle }) {
  const location = useLocation();

  return (
    <aside className={'sidebar' + (collapsed ? ' col' : '')}>
      <div className="sb-head">
        <div className="sb-module-tag">Módulo</div>
        <div className="sb-module-name">Capacidades<br />Diversas</div>
      </div>

      <nav className="sb-nav">
        {NAV_GROUPS.map((g) => (
          <div key={g.label}>
            <div className="sb-group-label">{g.label}</div>
            {g.items.map((it) => {
              const isActive = it.to === '/'
                ? location.pathname === '/'
                : location.pathname.startsWith(it.to);
              return (
                <NavLink
                  key={it.id}
                  to={it.to}
                  className={'sb-item' + (isActive ? ' active' : '')}
                  title={it.label}
                  data-initial={it.initial}
                  end={it.to === '/'}
                >
                  <span className="sb-num">{it.num}</span>
                  <span className="sb-label">{it.label}</span>
                </NavLink>
              );
            })}
          </div>
        ))}
      </nav>

      <div className="sb-foot">
        <span className="sb-foot-text">SMT v2.0</span>
        <button className="sb-toggle" onClick={onToggle} title={collapsed ? 'Expandir' : 'Colapsar'}>
          {collapsed ? '›' : '‹'}
        </button>
      </div>
    </aside>
  );
}
