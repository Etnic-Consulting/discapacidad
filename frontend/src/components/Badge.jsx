const ICONS = {
  alta: '★',
  media: '◐',
  baja: '○',
  ok: '✓',
  warn: '⚠',
  error: '✖',
  info: 'ℹ',
};

export default function Badge({ kind = 'line', icon, children, ariaLabel }) {
  const ico = icon ?? ICONS[kind];
  return (
    <span
      className={'badge badge-' + kind}
      aria-label={ariaLabel || (typeof children === 'string' ? children : undefined)}
    >
      {ico && <span aria-hidden="true" style={{ marginRight: 4 }}>{ico}</span>}
      {children}
    </span>
  );
}
