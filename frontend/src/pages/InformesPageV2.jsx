import { useEffect, useMemo, useState } from 'react';

const NIVELES = [
  { key: 'macro', label: 'Macrorregiones' },
  { key: 'dpto', label: 'Departamentos' },
  { key: 'mpio', label: 'Municipios' },
  { key: 'pueblo', label: 'Pueblos' },
  { key: 'resguardo', label: 'Resguardos' },
];

const API_BASE = import.meta.env.VITE_API_URL || '';

function tieneCascadaGeo(nivel) {
  return nivel === 'mpio' || nivel === 'resguardo';
}

export default function InformesPageV2() {
  const [nivelSel, setNivelSel] = useState('macro');
  const [catalog, setCatalog] = useState({ macro: [], dpto: [], mpio: [], pueblo: [], resguardo: [] });
  const [filtroTexto, setFiltroTexto] = useState('');
  const [filtroMacro, setFiltroMacro] = useState('');
  const [filtroDpto, setFiltroDpto] = useState('');
  const [filtroMpio, setFiltroMpio] = useState('');
  const [seleccionado, setSeleccionado] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetch(`${API_BASE}/api/v1/informes/_catalog`)
      .then(r => r.ok ? r.json() : Promise.reject(`HTTP ${r.status}`))
      .then(d => {
        setCatalog(d || {});
        setLoading(false);
      })
      .catch(err => {
        setError(`No se pudo cargar el catálogo: ${err}`);
        setLoading(false);
      });
  }, []);

  // Reset filtros geo al cambiar de nivel
  useEffect(() => {
    setFiltroMacro('');
    setFiltroDpto('');
    setFiltroMpio('');
    setFiltroTexto('');
    setSeleccionado(null);
  }, [nivelSel]);

  // Reset descendente cuando cambia un nivel padre
  useEffect(() => { setFiltroDpto(''); setFiltroMpio(''); }, [filtroMacro]);
  useEffect(() => { setFiltroMpio(''); }, [filtroDpto]);

  const macros = catalog.macro || [];
  const dptos = catalog.dpto || [];
  const mpios = catalog.mpio || [];

  // Dptos visibles según macro elegido (los dptos no tienen cod_macro directo,
  // pero los resguardos sí; derivamos qué dptos pertenecen a cada macro)
  const dptosPorMacro = useMemo(() => {
    if (!filtroMacro) return null;
    const macroNombre = macros.find(m => m.id === filtroMacro)?.nombre;
    if (!macroNombre) return null;
    const setDptos = new Set();
    (catalog.resguardo || []).forEach(r => {
      if (r.macro === macroNombre && r.cod_dpto) setDptos.add(r.cod_dpto);
    });
    return setDptos;
  }, [filtroMacro, macros, catalog.resguardo]);

  const dptosVisibles = useMemo(() => {
    if (!dptosPorMacro) return dptos;
    return dptos.filter(d => dptosPorMacro.has(d.id));
  }, [dptos, dptosPorMacro]);

  const mpiosVisibles = useMemo(() => {
    if (!filtroDpto) return mpios;
    return mpios.filter(m => m.cod_dpto === filtroDpto);
  }, [mpios, filtroDpto]);

  // Lista final del panel derecho según nivel + filtros
  const itemsListados = useMemo(() => {
    const fuente = catalog[nivelSel] || [];
    let lista = fuente;

    if (nivelSel === 'mpio' && filtroDpto) {
      lista = lista.filter(it => it.cod_dpto === filtroDpto);
    }
    if (nivelSel === 'resguardo') {
      if (filtroMpio) {
        lista = lista.filter(it => it.cod_mpio === filtroMpio);
      } else if (filtroDpto) {
        lista = lista.filter(it => it.cod_dpto === filtroDpto);
      } else if (filtroMacro) {
        const macroNombre = macros.find(m => m.id === filtroMacro)?.nombre;
        if (macroNombre) lista = lista.filter(it => it.macro === macroNombre);
      }
    }
    if (filtroTexto) {
      const t = filtroTexto.toLowerCase();
      lista = lista.filter(it =>
        (it.nombre || '').toLowerCase().includes(t) || (it.id || '').toLowerCase().includes(t)
      );
    }
    return lista;
  }, [catalog, nivelSel, filtroDpto, filtroMpio, filtroMacro, filtroTexto, macros]);

  const mostrarCascada = tieneCascadaGeo(nivelSel);
  const mostrarSelectorMacro = mostrarCascada;
  const mostrarSelectorDpto = mostrarCascada;
  const mostrarSelectorMpio = nivelSel === 'resguardo';

  return (
    <div style={{ padding: '24px', fontFamily: 'Georgia, serif', maxWidth: 1400, margin: '0 auto' }}>
      <h1 style={{ color: '#014a30', marginBottom: 8 }}>Informes territoriales · SMT-ONIC</h1>
      <p style={{ color: '#555', fontSize: 14, marginTop: 0 }}>
        Pre-renderizados con datos canónicos CNPV 2018 · cifras trazadas a fuente. Filtrá por nivel y geografía.
      </p>

      <div style={{ display: 'flex', gap: 8, marginTop: 20, flexWrap: 'wrap' }}>
        {NIVELES.map(n => {
          const cargados = (catalog[n.key] || []).length;
          const activo = nivelSel === n.key;
          return (
            <button
              key={n.key}
              onClick={() => setNivelSel(n.key)}
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
              <span style={{ marginLeft: 8, fontSize: 12, opacity: 0.85 }}>{cargados}</span>
            </button>
          );
        })}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '340px 1fr', gap: 16, marginTop: 20 }}>
        <aside style={{ background: '#fafaf7', borderRadius: 6, padding: 12, height: 'calc(100vh - 250px)', overflowY: 'auto' }}>
          {mostrarCascada && (
            <div style={{ marginBottom: 12, paddingBottom: 12, borderBottom: '1px dashed #d4d1c8' }}>
              <div style={{ fontSize: 12, color: '#666', marginBottom: 6, fontWeight: 600 }}>Cascada geográfica</div>

              {mostrarSelectorMacro && (
                <select
                  value={filtroMacro}
                  onChange={e => setFiltroMacro(e.target.value)}
                  style={{ width: '100%', padding: 7, marginBottom: 6, border: '1px solid #ccc', borderRadius: 4, fontSize: 13 }}
                >
                  <option value="">Todas las macrorregiones</option>
                  {macros.map(m => (
                    <option key={m.id} value={m.id}>{m.nombre}</option>
                  ))}
                </select>
              )}

              {mostrarSelectorDpto && (
                <select
                  value={filtroDpto}
                  onChange={e => setFiltroDpto(e.target.value)}
                  style={{ width: '100%', padding: 7, marginBottom: 6, border: '1px solid #ccc', borderRadius: 4, fontSize: 13 }}
                  disabled={dptosVisibles.length === 0}
                >
                  <option value="">{dptosVisibles.length === 0 ? 'Sin dptos en esta macro' : 'Todos los departamentos'}</option>
                  {dptosVisibles.map(d => (
                    <option key={d.id} value={d.id}>{d.nombre}</option>
                  ))}
                </select>
              )}

              {mostrarSelectorMpio && (
                <select
                  value={filtroMpio}
                  onChange={e => setFiltroMpio(e.target.value)}
                  style={{ width: '100%', padding: 7, marginBottom: 6, border: '1px solid #ccc', borderRadius: 4, fontSize: 13 }}
                  disabled={!filtroDpto}
                >
                  <option value="">{filtroDpto ? `Todos los mpios del dpto (${mpiosVisibles.length})` : 'Elegí un dpto primero'}</option>
                  {mpiosVisibles.map(m => (
                    <option key={m.id} value={m.id}>{m.nombre}</option>
                  ))}
                </select>
              )}
            </div>
          )}

          <input
            type="text"
            placeholder={`Buscar por nombre o código…`}
            value={filtroTexto}
            onChange={e => setFiltroTexto(e.target.value)}
            style={{ width: '100%', padding: 8, marginBottom: 12, border: '1px solid #ccc', borderRadius: 4 }}
          />

          {loading && <div style={{ color: '#888' }}>Cargando catálogo…</div>}
          {error && <div style={{ color: '#c33', fontSize: 13 }}>{error}</div>}
          {!loading && !error && (
            <div style={{ fontSize: 11, color: '#888', marginBottom: 8 }}>
              Mostrando {itemsListados.length} de {(catalog[nivelSel] || []).length}
            </div>
          )}
          {!loading && !error && itemsListados.length === 0 && (
            <div style={{ color: '#888', fontSize: 13 }}>Sin resultados con los filtros activos.</div>
          )}

          <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
            {itemsListados.map(it => (
              <li
                key={`${nivelSel}-${it.id}`}
                onClick={() => setSeleccionado({ ...it, tipo: nivelSel })}
                style={{
                  padding: '8px 10px',
                  marginBottom: 4,
                  cursor: 'pointer',
                  background: seleccionado?.id === it.id && seleccionado?.tipo === nivelSel ? '#e7f3eb' : '#fff',
                  borderLeft: seleccionado?.id === it.id && seleccionado?.tipo === nivelSel ? '4px solid #014a30' : '4px solid transparent',
                  fontSize: 13,
                }}
              >
                <div style={{ fontWeight: 600 }}>{it.nombre || it.id}</div>
                <div style={{ fontSize: 11, color: '#888' }}>
                  {it.id}
                  {it.dpto && <> · {it.dpto}</>}
                  {it.mpio && <> · {it.mpio}</>}
                </div>
              </li>
            ))}
          </ul>
        </aside>

        <main style={{ background: '#fff', borderRadius: 6, minHeight: 'calc(100vh - 250px)' }}>
          {seleccionado ? (
            <>
              <div style={{ padding: '12px 16px', borderBottom: '1px solid #e0ddd6', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <strong>
                  {NIVELES.find(n => n.key === seleccionado.tipo)?.label} · {seleccionado.nombre || seleccionado.id}
                </strong>
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
              Seleccioná un informe del listado para visualizarlo.
              {mostrarCascada && (
                <div style={{ marginTop: 12, fontSize: 13 }}>
                  Tip: usá los selectores de macrorregión y departamento para acotar la lista.
                </div>
              )}
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
