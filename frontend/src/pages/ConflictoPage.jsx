/* ============================================
   SMT-ONIC v2.0 — Conflicto Armado
   Datos reales desde victimas.universo
   ============================================ */

import { useMemo } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell,
} from 'recharts';
import KPICard from '../components/KPICard';
import GlobalSelector from '../components/GlobalSelector';
import FilterBreadcrumb from '../components/FilterBreadcrumb';
import DidYouKnow from '../components/DidYouKnow';
import { useFilters } from '../context/FilterContext';
import {
  useVictimasPorPueblo,
  useVictimasPorHecho,
  useVictimasPorTipo,
  useVictimasPueblo,
} from '../hooks/useApi';

function fmt(n) {
  return new Intl.NumberFormat('es-CO').format(n);
}

/* Color palette for tipo de capacidad diversa */
const TIPO_COLORS = {
  FISICA: '#02432D',
  VISUAL: '#02AB44',
  AUDITIVA: '#C4920A',
  INTELECTUAL: '#E8B84B',
  PSICOSOCIAL: '#E8262A',
  SIN_INFORMACION: '#6B6B6B',
  MULTIPLE: '#8B5CF6',
};

/* Human-readable labels for tipo */
const TIPO_LABELS = {
  FISICA: 'Fisica',
  VISUAL: 'Visual',
  AUDITIVA: 'Auditiva',
  INTELECTUAL: 'Intelectual / Cognitiva',
  PSICOSOCIAL: 'Psicosocial / Mental',
  SIN_INFORMACION: 'Sin informacion',
  MULTIPLE: 'Multiple',
};

const cardStyle = {
  background: '#fff',
  borderRadius: 'var(--radius-md)',
  boxShadow: 'var(--shadow-md)',
  padding: '20px 24px',
};

const chartTitle = {
  fontFamily: 'var(--font-body)',
  fontSize: '0.85rem',
  fontWeight: 600,
  textTransform: 'uppercase',
  letterSpacing: '0.5px',
  color: 'var(--color-gray-500)',
  marginBottom: '16px',
};

const spinnerSmall = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  height: '320px',
  color: 'var(--color-gray-400)',
  fontSize: '0.9rem',
};

export default function ConflictoPage() {
  const { dpto, pueblo, dptoNombre, puebloNombre } = useFilters();

  /* ---- API hooks — filter by dpto when selected ---- */
  const codDpto = dpto || undefined;
  const {
    data: pueblosData,
    isLoading: loadingPueblos,
    isError: errorPueblos,
  } = useVictimasPorPueblo(codDpto, 10);

  const {
    data: hechosData,
    isLoading: loadingHechos,
    isError: errorHechos,
  } = useVictimasPorHecho(codDpto);

  const {
    data: tipoData,
    isLoading: loadingTipo,
    isError: errorTipo,
  } = useVictimasPorTipo(codDpto);

  /* ---- Pueblo-specific data when a pueblo is selected ---- */
  const {
    data: puebloVictimasData,
    isLoading: loadingPuebloVictimas,
  } = useVictimasPueblo(pueblo || undefined);

  /* ---- Derived chart data ---- */
  const topPueblos = useMemo(() => {
    const raw = Array.isArray(pueblosData?.data) ? pueblosData.data : [];
    return raw.map((r) => ({
      pueblo: r.pueblo,
      victimas: Number(r.total_victimas) || 0,
    }));
  }, [pueblosData]);

  const hechosChart = useMemo(() => {
    // When pueblo is selected and we have pueblo-specific data, use it
    if (pueblo && puebloVictimasData?.hechos) {
      const raw = Array.isArray(puebloVictimasData.hechos) ? puebloVictimasData.hechos : [];
      return raw.map((r) => ({
        hecho: r.hecho,
        cantidad: Number(r.total_victimas || r.cantidad || r.victimas) || 0,
      }));
    }
    const raw = Array.isArray(hechosData?.data) ? hechosData.data : [];
    return raw.map((r) => ({
      hecho: r.hecho,
      cantidad: Number(r.total_victimas) || 0,
    }));
  }, [hechosData, pueblo, puebloVictimasData]);

  const tipoChart = useMemo(() => {
    // When pueblo is selected and we have pueblo-specific data, use it
    if (pueblo && puebloVictimasData?.tipos) {
      const raw = Array.isArray(puebloVictimasData.tipos) ? puebloVictimasData.tipos : [];
      return raw
        .filter((r) => r.tipo)
        .map((r) => ({
          tipo: TIPO_LABELS[r.tipo] || r.tipo,
          cantidad: Number(r.total_victimas || r.cantidad || r.victimas) || 0,
          color: TIPO_COLORS[r.tipo] || '#999',
        }));
    }
    const raw = Array.isArray(tipoData?.data) ? tipoData.data : [];
    return raw
      .filter((r) => r.tipo) // exclude null
      .map((r) => ({
        tipo: TIPO_LABELS[r.tipo] || r.tipo,
        cantidad: Number(r.total_victimas) || 0,
        color: TIPO_COLORS[r.tipo] || '#999',
      }));
  }, [tipoData, pueblo, puebloVictimasData]);

  /* ---- KPI computations from real data ---- */
  const totalVictimas = useMemo(() => {
    // When pueblo is selected, use pueblo-specific total
    if (pueblo && puebloVictimasData?.total_victimas != null) {
      return puebloVictimasData.total_victimas;
    }
    // Use por-tipo total as it covers all records
    if (tipoData?.total_victimas) return tipoData.total_victimas;
    return tipoChart.reduce((s, r) => s + r.cantidad, 0);
  }, [tipoData, tipoChart, pueblo, puebloVictimasData]);

  const pueblosAfectados = useMemo(() => {
    if (pueblo) return 1;
    // Total distinct pueblos from pueblosData (could be more than limit=10)
    if (pueblosData?.total) return pueblosData.total;
    return topPueblos.length;
  }, [pueblosData, topPueblos, pueblo]);

  const hechoPrincipal = useMemo(() => {
    if (hechosChart.length === 0) return { nombre: '---', porcentaje: '0%' };
    const top = hechosChart[0];
    const totalH = hechosChart.reduce((s, r) => s + r.cantidad, 0);
    const pct = totalH > 0 ? ((top.cantidad / totalH) * 100).toFixed(1) : '0';
    return { nombre: top.hecho, porcentaje: `${pct}%` };
  }, [hechosChart]);

  const tipoMasFrecuente = useMemo(() => {
    // Find the most frequent tipo excluding SIN_INFORMACION
    const filtered = tipoChart.filter((t) => t.tipo !== 'Sin informacion');
    if (filtered.length === 0) return { nombre: '---', cantidad: 0 };
    const top = filtered.reduce((a, b) => (a.cantidad >= b.cantidad ? a : b), filtered[0]);
    return { nombre: top.tipo, cantidad: top.cantidad };
  }, [tipoChart]);

  // Global loading: only if ALL are loading
  const allLoading = loadingPueblos && loadingHechos && loadingTipo && (!pueblo || loadingPuebloVictimas);
  const anyError = errorPueblos && errorHechos && errorTipo;

  // Build page title based on filters
  let pageTitle = 'Conflicto Armado';
  if (puebloNombre) {
    pageTitle = `Conflicto Armado: ${puebloNombre}`;
  } else if (dptoNombre) {
    pageTitle = `Conflicto Armado: ${dptoNombre}`;
  }

  if (allLoading) return <div className="loading-container"><div className="spinner" /><p>Cargando datos de conflicto armado...</p></div>;
  if (anyError) return <div className="error-container"><p>Error cargando datos de conflicto armado. Verifique la conexion con el servidor.</p></div>;

  return (
    <div>
      <div className="page-header">
        <h1>{pageTitle}</h1>
        <p>
          Victimas indigenas con capacidades diversas en el marco del conflicto armado
          colombiano — Registro Unico de Victimas (RUV)
        </p>
      </div>

      {/* Global Selector */}
      <GlobalSelector />

      {/* Breadcrumb */}
      <FilterBreadcrumb />

      {/* Filter active note */}
      {(dpto || pueblo) && (
        <div className="alert alert-info" style={{ marginBottom: '16px' }}>
          <strong>Filtro activo:</strong>{' '}
          {dptoNombre && `Departamento: ${dptoNombre}`}
          {dptoNombre && puebloNombre && ' | '}
          {puebloNombre && `Pueblo: ${puebloNombre}`}
          {'. '}Los datos se filtran automaticamente segun la seleccion.
        </div>
      )}

      {/* Pueblo-specific banner */}
      {pueblo && puebloNombre && (
        <div style={{
          background: 'var(--color-green-light)',
          borderLeft: '4px solid var(--color-green-mid)',
          padding: '12px 20px',
          borderRadius: 'var(--radius-sm)',
          marginBottom: '16px',
          fontSize: '0.88rem',
          color: 'var(--color-primary)',
        }}>
          <strong>Datos del pueblo {puebloNombre}:</strong>{' '}
          {puebloVictimasData
            ? `Se encontraron ${fmt(totalVictimas)} victimas con capacidades diversas registradas en el RUV para este pueblo.`
            : loadingPuebloVictimas
            ? 'Cargando datos especificos del pueblo...'
            : 'Los datos mostrados corresponden al nivel departamental/nacional.'}
        </div>
      )}

      {/* KPIs */}
      <div className="grid-row grid-4" style={{ marginBottom: '28px' }}>
        <KPICard
          title="Total victimas"
          value={loadingTipo ? '...' : fmt(totalVictimas)}
          subtitle="Indigenas con capacidades diversas"
          color="var(--color-red)"
          icon="TV"
        />
        <KPICard
          title="Pueblos afectados"
          value={loadingPueblos ? '...' : String(pueblosAfectados)}
          subtitle={dpto ? `En ${dptoNombre}` : 'A nivel nacional'}
          color="var(--color-gold)"
          icon="PA"
        />
        <KPICard
          title="Hecho principal"
          value={loadingHechos ? '...' : hechoPrincipal.porcentaje}
          subtitle={hechoPrincipal.nombre}
          color="var(--color-primary)"
          icon="HP"
        />
        <KPICard
          title="Cap. diversa mas frecuente"
          value={loadingTipo ? '...' : fmt(tipoMasFrecuente.cantidad)}
          subtitle={tipoMasFrecuente.nombre}
          color="var(--color-red)"
          icon="CD"
        />
      </div>

      {/* Alert */}
      <div className="alert alert-warning" style={{ marginBottom: '24px' }}>
        <strong>Nota:</strong> La relacion entre
        conflicto armado y capacidades diversas es bidireccional: el conflicto genera nuevas
        condiciones de diversidad funcional, y las personas con capacidades diversas son mas
        vulnerables a los impactos del conflicto.
        {hechoPrincipal.nombre !== '---' && (
          <> El {hechoPrincipal.porcentaje} de las victimas reporta <em>{hechoPrincipal.nombre.toLowerCase()}</em> como hecho victimizante principal.</>
        )}
      </div>

      {/* DidYouKnow callouts */}
      <DidYouKnow
        fact="Las capacidades diversas adquiridas por conflicto armado frecuentemente se deben a desplazamiento forzado. El desarraigo territorial genera condiciones de diversidad funcional que no se habrian producido sin el conflicto."
        source="Registro Unico de Victimas (RUV) - cruce con enfoque diferencial"
      />

      {/* Charts Row 1: Pueblos + Hechos */}
      <div className="grid-row grid-2">
        <div style={cardStyle}>
          <div style={chartTitle}>
            Top {topPueblos.length} pueblos por numero de victimas con capacidades diversas
          </div>
          {loadingPueblos ? (
            <div style={spinnerSmall}><div className="spinner" /></div>
          ) : errorPueblos ? (
            <div style={spinnerSmall}>Error cargando datos de pueblos</div>
          ) : topPueblos.length === 0 ? (
            <div style={spinnerSmall}>Sin datos disponibles</div>
          ) : (
            <ResponsiveContainer width="100%" height={380}>
              <BarChart
                data={topPueblos}
                layout="vertical"
                margin={{ top: 10, right: 30, bottom: 5, left: 120 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#e8e8e8" />
                <XAxis type="number" tick={{ fontSize: 11 }} />
                <YAxis type="category" dataKey="pueblo" tick={{ fontSize: 11 }} width={110} />
                <Tooltip formatter={(v) => [fmt(v), 'Victimas']} />
                <Bar dataKey="victimas" fill="#E8262A" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        <div style={cardStyle}>
          <div style={chartTitle}>Hechos victimizantes — victimas con capacidades diversas</div>
          {loadingHechos ? (
            <div style={spinnerSmall}><div className="spinner" /></div>
          ) : errorHechos ? (
            <div style={spinnerSmall}>Error cargando datos de hechos</div>
          ) : hechosChart.length === 0 ? (
            <div style={spinnerSmall}>Sin datos disponibles</div>
          ) : (
            <ResponsiveContainer width="100%" height={380}>
              <BarChart
                data={hechosChart}
                layout="vertical"
                margin={{ top: 10, right: 30, bottom: 5, left: 160 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#e8e8e8" />
                <XAxis type="number" tick={{ fontSize: 11 }} />
                <YAxis type="category" dataKey="hecho" tick={{ fontSize: 11 }} width={150} />
                <Tooltip formatter={(v) => [fmt(v), 'Victimas']} />
                <Bar dataKey="cantidad" fill="#02432D" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Chart Row 2: By tipo capacidad diversa */}
      <div className="grid-row" style={{ gridTemplateColumns: '1fr' }}>
        <div style={cardStyle}>
          <div style={chartTitle}>Victimas por tipo de capacidad diversa</div>
          {loadingTipo ? (
            <div style={spinnerSmall}><div className="spinner" /></div>
          ) : errorTipo ? (
            <div style={spinnerSmall}>Error cargando datos por tipo</div>
          ) : tipoChart.length === 0 ? (
            <div style={spinnerSmall}>Sin datos disponibles</div>
          ) : (
            <ResponsiveContainer width="100%" height={320}>
              <BarChart data={tipoChart} margin={{ top: 10, right: 30, bottom: 5, left: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e8e8e8" />
                <XAxis dataKey="tipo" tick={{ fontSize: 11 }} angle={-10} textAnchor="end" height={60} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip formatter={(v) => [fmt(v), 'Victimas']} />
                <Bar dataKey="cantidad" radius={[4, 4, 0, 0]}>
                  {tipoChart.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      <div style={{
        textAlign: 'center',
        color: 'var(--color-gray-400)',
        fontSize: '0.78rem',
        marginTop: '12px',
        marginBottom: '24px',
      }}>
        Fuente: Registro Unico de Victimas (RUV) — Unidad para las Victimas.
        Cruce con enfoque diferencial etnico y condicion de capacidades diversas.
      </div>
    </div>
  );
}
