export default function SiteFooter() {
  return (
    <footer className="site-footer">
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: 16,
        padding: '24px 32px',
        background: 'var(--bg-elev,#0F1B14)',
        color: 'var(--ink-soft,#D8D4CC)',
        fontSize: '0.82rem',
        marginTop: '48px',
        borderTop: '1px solid var(--line,#2a2a2a)'
      }}>
        <div>
          <div style={{ fontWeight: 600, marginBottom: 4 }}>SMT — ONIC</div>
          <div>Sistema de Monitoreo Territorial</div>
          <div>Organizacion Nacional Indigena de Colombia</div>
        </div>
        <div>
          <div>poblacion@onic.org.co</div>
          <div>Bogota, Colombia</div>
        </div>
        <div>
          <div>© 2026 ONIC. Datos abiertos bajo CC BY 4.0.</div>
          <div><a href="/login" style={{ color: 'var(--ink-soft,#D8D4CC)', textDecoration: 'underline' }}>Acceso restringido</a></div>
        </div>
      </div>
    </footer>
  );
}
