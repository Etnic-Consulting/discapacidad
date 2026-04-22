export default function ChartSkeleton({ height = 280, label = 'Cargando grafico' }) {
  return (
    <div
      role="status"
      aria-busy="true"
      aria-label={label}
      style={{
        height,
        width: '100%',
        background: 'linear-gradient(90deg,#f3f1ec 25%,#ebe7df 50%,#f3f1ec 75%)',
        backgroundSize: '200% 100%',
        animation: 'chartSkeleton 1.4s ease-in-out infinite',
        borderRadius: 6,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: 'var(--ink-muted,#5B6B66)',
        fontSize: '0.85rem',
      }}
    >
      {label}
      <style>{`@keyframes chartSkeleton{0%{background-position:200% 0}100%{background-position:-200% 0}}`}</style>
    </div>
  );
}
