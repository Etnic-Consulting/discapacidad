import { NavLink } from 'react-router-dom';

const LINKS = [
  { to: '/',             label: 'Panorama' },
  { to: '/pueblos',      label: 'Pueblos' },
  { to: '/territorios',  label: 'Territorios' },
  { to: '/conflicto',    label: 'Conflicto' },
  { to: '/proyecciones', label: 'Proyecciones' },
  { to: '/indicadores',  label: 'Indicadores' },
];

export default function SiteChrome() {
  return (
    <div className="site-chrome">
      <NavLink to="/" className="site-logo">
        <div className="site-logo-mark">s</div>
        <span>SMT—ONIC</span>
      </NavLink>
      <nav className="site-nav">
        {LINKS.map((l) => (
          <NavLink
            key={l.to}
            to={l.to}
            className={({ isActive }) => isActive ? 'active' : ''}
            end={l.to === '/'}
          >
            {l.label}
          </NavLink>
        ))}
      </nav>
      <div className="site-user">
        <span>Wilson Herrera</span>
        <div className="site-avatar">WH</div>
      </div>
    </div>
  );
}
