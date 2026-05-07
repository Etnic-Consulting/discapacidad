import { useEffect, useMemo, useState } from 'react';

const NIVELES = [
  { key: 'macro', label: 'Macrorregiones', n_total: 5 },
  { key: 'dpto', label: 'Departamentos', n_total: 33 },
  { key: 'mpio', label: 'Municipios', n_total: 1122 },
  { key: 'pueblo', label: 'Pueblos', n_total: 124 },
  { key: 'resguardo', label: 'Resguardos', n_total: 830 },
];

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8095';

export default function InformesPageV2() {
  const [nivelSel, setNivelSel] = useState('macro');
  const [items, setItems] = useState([]);
  const [filtro, setFiltro] = useState('');
  const [seleccionado, setSeleccionado] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetch(`${API_BASE}/api/v1/informes/_index`)
      .then(r => r.ok ? r.json() : Promise.reject(`HTTP ${r.status}`))
      .then(d => {
        setItems(d.items || []);
        setLoading(false);
      })
      .catch(err => {
        setError(`No se pudo cargar índice: ${err}`);
        setLoading(false);
      });
  }, []);

  const itemsFiltrados = useMemo(() => {
    return items
      .filter(it => it.tipo === nivelSel)
      .filter(it => !filtro || it.id.toLowerCase().includes(filtro.toLowerCase()));
  }, [items, nivelSel, filtro]);

  const totalNivel = items.filter(it => it.tipo === nivelSel).length;

  return (
    <div style={{ padding: '24px', fontFamily: 'Georgia, serif', maxWidth: 1400, margin: '0 auto' }}>
      <h1 style={{ color: '#014a30', marginBottom: 8 }}>Informes territoriales · SMT-ONIC</h1>
      <p style={{ color: '#555', fontSize: 14, marginTop: 0 }}>
        Pre-renderizados con análisis de Gemini 2.5 Pro · datos canónicos CNPV 2018 · cifras trazadas a fuente.
      </p>

      <div style={{ display: 'flex', gap: 8, marginTop: 20, flexWrap: 'wrap' }}>
        {NIVELES.map(n => {
          const cargados = items.filter(it => it.tipo === n.key).length;
          const activo = nivelSel === n.key;
          return (
            <button
              key={n.key}
              onClick={() => { setNivelSel(n.key); setSeleccionado(null); }}
              style={{
                padding: '10px 16px',
                background: activo ? '#014a30' : '#fff',
                color: activo ? '#fff' : '#014a30',
                border: '2px solid #014a30',
                borderRadius: 6,
                cursor: 'pointer',
                fontWeight: 600,
              }}
            >
              {n.label}
              <span style={{ marginLeft: 8, fontSize: 12, opacity: 0.85 }}>
                {cargados}/{n.n_total}
              </span>
            </button>
          );
        })}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: 16, marginTop: 20 }}>
        <aside style={{ background: '#fafaf7', borderRadius: 6, padding: 12, height: 'calc(100vh - 250px)', overflowY: 'auto' }}>
          <input
            type="text"
            placeholder={`Buscar entre ${totalNivel} ${NIVELES.find(n => n.key === nivelSel)?.label.toLowerCase()}...`}
            value={filtro}
            onChange={e => setFiltro(e.target.value)}
            style={{ width: '100%', padding: 8, marginBottom: 12, border: '1px solid #ccc', borderRadius: 4 }}
          />

          {loading && <div style={{ color: '#888' }}>Cargando…</div>}
          {error && <div style={{ color: '#c33', fontSize: 13 }}>{error}</div>}
          {!loading && itemsFiltrados.length === 0 && (
            <div style={{ color: '#888', fontSize: 13 }}>
              {totalNivel === 0
                ? `Aún no hay informes pre-renderizados de este nivel. Ejecutar L12 batch para generarlos.`
                : 'Sin resultados para el filtro.'}
            </div>
          )}

          <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
            {itemsFiltrados.map(it => (
              <li
                key={`${it.tipo}-${it.id}`}
                onClick={() => setSeleccionado(it)}
                style={{
                  padding: '8px 10px',
                  marginBottom: 4,
                  cursor: 'pointer',
                  background: seleccionado?.id === it.id ? '#e7f3eb' : '#fff',
                  borderLeft: seleccionado?.id === it.id ? '4px solid #014a30' : '4px solid transparent',
                  fontSize: 13,
                }}
              >
                <div style={{ fontWeight: 600 }}>{it.id}</div>
                <div style={{ fontSize: 11, color: '#888' }}>{it.size_kb} KB</div>
              </li>
            ))}
          </ul>
        </aside>

        <main style={{ background: '#fff', borderRadius: 6, minHeight: 'calc(100vh - 250px)' }}>
          {seleccionado ? (
            <>
              <div style={{ padding: '12px 16px', borderBottom: '1px solid #e0ddd6', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <strong>{NIVELES.find(n => n.key === seleccionado.tipo)?.label} · {seleccionado.id}</strong>
                <div style={{ display: 'flex', gap: 8 }}>
                  <a
                    href={`${API_BASE}/api/v1/informes/${seleccionado.tipo}/${seleccionado.id}/pdf`}
                    target="_blank"
                    rel="noopener"
                    style={{ padding: '6px 12px', background: '#014a30', color: '#fff', borderRadius: 4, textDecoration: 'none', fontSize: 13 }}
                  >
                    Descargar PDF
                  </a>
                  <a
                    href={`${API_BASE}/api/v1/informes/${seleccionado.tipo}/${seleccionado.id}/docx`}
                    target="_blank"
                    rel="noopener"
                    style={{ padding: '6px 12px', background: '#2e7d4f', color: '#fff', borderRadius: 4, textDecoration: 'none', fontSize: 13 }}
                  >
                    Descargar Word
                  </a>
                </div>
              </div>
              <iframe
                src={`${API_BASE}/api/v1/informes/${seleccionado.tipo}/${seleccionado.id}`}
                title={`Informe ${seleccionado.tipo} ${seleccionado.id}`}
                style={{ width: '100%', height: 'calc(100vh - 320px)', border: 'none' }}
              />
            </>
          ) : (
            <div style={{ padding: 40, color: '#888', textAlign: 'center' }}>
              Selecciona un informe del listado para visualizarlo.
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
