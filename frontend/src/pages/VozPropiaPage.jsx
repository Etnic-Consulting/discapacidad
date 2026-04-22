/* ============================================
   SMT-ONIC v2.0 — Voz Propia (SMT-ONIC data)
   ============================================ */

import { useMemo } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell,
} from 'recharts';
import KPICard from '../components/KPICard';
import DidYouKnow from '../components/DidYouKnow';
import { useSmtResumen } from '../hooks/useApi';

function fmt(n) {
  return new Intl.NumberFormat('es-CO').format(n);
}

/* ---- Fallback data (used when API is unavailable) ---- */
const FALLBACK_REGION = [
  { categoria: 'Occidente', valor: 669, pct: 64.1 },
  { categoria: 'Amazonia', valor: 141, pct: 13.5 },
  { categoria: 'Norte', valor: 98, pct: 9.4 },
  { categoria: 'Centro Oriente', valor: 85, pct: 8.1 },
  { categoria: 'Orinoquia', valor: 51, pct: 4.9 },
];

const FALLBACK_TIPO = [
  { categoria: 'Fisica', valor: 275, pct: 26.3 },
  { categoria: 'Visual', valor: 190, pct: 18.2 },
  { categoria: 'Mental / Psicosocial', valor: 132, pct: 12.6 },
  { categoria: 'Multiple', valor: 96, pct: 9.2 },
  { categoria: 'Auditiva', valor: 70, pct: 6.7 },
  { categoria: 'Desarmonia espiritual', valor: 10, pct: 1.0 },
];

const FALLBACK_CALIDAD = [
  { categoria: 'Tipo de capacidad diversa', valor: 62, pct: 62 },
  { categoria: 'Causa / origen', valor: 35, pct: 35 },
  { categoria: 'Servicios de salud', valor: 28, pct: 28 },
  { categoria: 'Ayudas tecnicas', valor: 22, pct: 22 },
  { categoria: 'Pueblo indigena especifico', valor: 89, pct: 89 },
  { categoria: 'Ubicacion geografica', valor: 91, pct: 91 },
  { categoria: 'Sexo / genero', valor: 95, pct: 95 },
  { categoria: 'Edad', valor: 93, pct: 93 },
];

const REGION_COLORS = ['#02432D', '#02AB44', '#C4920A', '#E8262A', '#6B6B6B'];
const TIPO_COLORS = ['#02432D', '#02AB44', '#C4920A', '#E8262A', '#6B6B6B', '#8B5CF6'];

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

export default function VozPropiaPage() {
  /* ---- Fetch all SMT resumen data (no dimension filter = get all) ---- */
  const { data: smtResp, isLoading, isError } = useSmtResumen();
  const allData = smtResp?.data ?? [];

  /* ---- Derive per-dimension data with fallbacks ---- */
  const regionData = useMemo(() => {
    const filtered = allData.filter((r) => r.dimension === 'region');
    if (filtered.length === 0) return FALLBACK_REGION;
    return filtered.map((r) => ({
      macrorregion: r.categoria,
      personas: Number(r.valor),
      pct: r.pct,
    }));
  }, [allData]);

  const tipoData = useMemo(() => {
    const filtered = allData.filter((r) => r.dimension === 'tipo_discapacidad');
    if (filtered.length === 0) return FALLBACK_TIPO;
    return filtered.map((r) => ({
      tipo: r.categoria,
      cantidad: Number(r.valor),
      pct: r.pct,
    }));
  }, [allData]);

  const calidadData = useMemo(() => {
    const filtered = allData.filter((r) => r.dimension === 'calidad');
    if (filtered.length === 0) return FALLBACK_CALIDAD;
    return filtered.map((r) => ({
      campo: r.categoria,
      completitud: Number(r.valor),
      vacios: 100 - Number(r.valor),
    }));
  }, [allData]);

  /* ---- KPIs derived from data ---- */
  const totalPersonas = useMemo(() => {
    // Sum of region values = total registered
    if (regionData.length > 0 && regionData[0].personas != null) {
      return regionData.reduce((sum, r) => sum + (r.personas || 0), 0);
    }
    return 1044;
  }, [regionData]);

  const numMacrorregiones = regionData.length || 5;

  // Pueblos and orgs come from specific dimensions if available
  const pueblosCount = useMemo(() => {
    const pueblosRows = allData.filter((r) => r.dimension === 'pueblo');
    return pueblosRows.length > 0 ? pueblosRows.length : 28;
  }, [allData]);

  const orgsCount = useMemo(() => {
    const orgRows = allData.filter((r) => r.dimension === 'organizacion');
    return orgRows.length > 0 ? orgRows.length : 38;
  }, [allData]);

  /* ---- Desarmonia espiritual count ---- */
  const desarmoniaCount = useMemo(() => {
    const found = tipoData.find(
      (r) => (r.tipo || r.categoria || '').toLowerCase().includes('desarmonia')
    );
    return found ? (found.cantidad || found.valor || 10) : 10;
  }, [tipoData]);

  /* ---- Chart data adapters ---- */
  const macrorregionChart = useMemo(() =>
    regionData.map((r, i) => ({
      macrorregion: r.macrorregion || r.categoria,
      personas: r.personas || r.valor,
      color: REGION_COLORS[i % REGION_COLORS.length],
    })),
    [regionData],
  );

  const tipoChart = useMemo(() =>
    tipoData.map((r, i) => ({
      tipo: r.tipo || r.categoria,
      cantidad: r.cantidad || r.valor,
      color: TIPO_COLORS[i % TIPO_COLORS.length],
    })),
    [tipoData],
  );

  return (
    <div>
      <div className="page-header">
        <h1>Voz Propia — Datos SMT-ONIC</h1>
        <p>
          Datos del Sistema de Monitoreo Territorial de la ONIC {'\u2014'} Registro propio de
          organizaciones indigenas
        </p>
      </div>

      {/* Data source label */}
      <div style={{
        fontSize: '0.82rem',
        color: 'var(--color-gray-500)',
        background: 'var(--color-gray-100)',
        borderRadius: 'var(--radius-sm)',
        padding: '10px 16px',
        marginBottom: '20px',
        lineHeight: 1.5,
      }}>
        <strong>Fuente:</strong> Datos del instrumento SMT-ONIC 2026 ({fmt(totalPersonas)} registros).
        Estos datos provienen del proceso de caracterizacion propio de la ONIC. Se actualizaran con cada nueva fase de recoleccion.
        {isError && ' (usando datos de respaldo — API no disponible)'}
      </div>

      {/* Loading indicator */}
      {isLoading && (
        <div style={{ textAlign: 'center', padding: '12px', color: 'var(--color-gray-500)', fontSize: '0.85rem' }}>
          Cargando datos SMT-ONIC...
        </div>
      )}

      {/* KPIs */}
      <div className="grid-row grid-4" style={{ marginBottom: '28px' }}>
        <KPICard
          title="Personas registradas"
          value={fmt(totalPersonas)}
          subtitle="Registro SMT-ONIC"
          color="var(--color-green-mid)"
          icon="PE"
        />
        <KPICard
          title="Pueblos"
          value={String(pueblosCount)}
          subtitle="Con datos propios"
          color="var(--color-primary)"
          icon="PU"
        />
        <KPICard
          title="Organizaciones"
          value={String(orgsCount)}
          subtitle="Reportando"
          color="var(--color-gold)"
          icon="OR"
        />
        <KPICard
          title="Macrorregiones"
          value={String(numMacrorregiones)}
          subtitle="Cobertura territorial"
          color="var(--color-red)"
          icon="MR"
        />
      </div>

      {/* Alert */}
      <div className="alert alert-info" style={{ marginBottom: '24px' }}>
        <strong>Datos de voz propia:</strong> A diferencia de las fuentes estatales (DANE, RUV),
        estos datos provienen directamente de las organizaciones indigenas afiliadas a la ONIC.
        Incluyen la categoria culturalmente significativa de <em>desarmonia espiritual</em>,
        una dimension que el Estado no contempla en sus instrumentos de medicion.
      </div>

      {/* Charts Row 1: Macrorregion + Tipo */}
      <div className="grid-row grid-2">
        <div style={cardStyle}>
          <div style={chartTitle}>Personas por macrorregion ONIC</div>
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={macrorregionChart} margin={{ top: 10, right: 20, bottom: 5, left: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e8e8e8" />
              <XAxis dataKey="macrorregion" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip formatter={(v) => [fmt(v), 'Personas']} />
              <Bar dataKey="personas" radius={[4, 4, 0, 0]}>
                {macrorregionChart.map((entry, i) => (
                  <Cell key={i} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div style={cardStyle}>
          <div style={chartTitle}>Tipo de capacidad diversa (registro propio)</div>
          <ResponsiveContainer width="100%" height={320}>
            <BarChart
              data={tipoChart}
              layout="vertical"
              margin={{ top: 10, right: 30, bottom: 5, left: 140 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#e8e8e8" />
              <XAxis type="number" tick={{ fontSize: 11 }} />
              <YAxis type="category" dataKey="tipo" tick={{ fontSize: 11 }} width={130} />
              <Tooltip formatter={(v) => [fmt(v), 'Personas']} />
              <Bar dataKey="cantidad" radius={[0, 4, 4, 0]}>
                {tipoChart.map((entry, i) => (
                  <Cell key={i} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Data Quality */}
      <div style={{ ...cardStyle, marginBottom: '24px' }}>
        <div style={chartTitle}>Calidad de datos -- Completitud de campos criticos</div>
        <div className="alert alert-warning" style={{ marginBottom: '16px' }}>
          <strong>Alerta de calidad:</strong> Varios campos criticos presentan mas del
          60% de valores vacios. Se recomienda fortalecer los procesos de recoleccion,
          especialmente en servicios de salud, ayudas tecnicas y causa/origen de la
          condicion.
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {calidadData.map((campo, idx) => (
            <div key={`${campo.campo ?? 'sin-campo'}-${idx}`}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                <span style={{ fontSize: '0.85rem' }}>{campo.campo}</span>
                <span style={{
                  fontWeight: 600,
                  fontSize: '0.85rem',
                  color: campo.completitud > 80 ? 'var(--color-green-mid)'
                    : campo.completitud > 50 ? 'var(--color-gold)'
                    : 'var(--color-red)',
                }}>
                  {campo.completitud}% completo
                </span>
              </div>
              <div style={{
                height: '8px',
                background: 'var(--color-gray-200)',
                borderRadius: '4px',
                overflow: 'hidden',
              }}>
                <div
                  style={{
                    width: `${campo.completitud}%`,
                    height: '100%',
                    background: campo.completitud > 80 ? 'var(--color-green-mid)'
                      : campo.completitud > 50 ? 'var(--color-gold)'
                      : 'var(--color-red)',
                    borderRadius: '4px',
                    transition: 'width 0.6s ease',
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* DidYouKnow callout */}
      <DidYouKnow
        fact="La desarmonia espiritual, una forma de capacidad diversa reconocida solo por los pueblos indigenas, fue identificada en 10 de las 1,044 personas caracterizadas por el SMT-ONIC."
        source="SMT-ONIC 2026 - Registro propio ONIC"
      />

      {/* Desarmonia Espiritual section */}
      <div style={{
        ...cardStyle,
        borderLeft: '4px solid #8B5CF6',
        background: 'linear-gradient(135deg, #fff 0%, #f5f0ff 100%)',
      }}>
        <h3 style={{ color: '#8B5CF6', marginBottom: '12px', fontFamily: 'var(--font-heading)' }}>
          Desarmonia espiritual: lo que el Estado no mide
        </h3>
        <p style={{ fontSize: '0.9rem', lineHeight: 1.7, color: 'var(--color-gray-600)', marginBottom: '12px' }}>
          El registro del SMT-ONIC incluye {desarmoniaCount} personas catalogadas bajo la categoria de
          <strong> desarmonia espiritual</strong>. Esta dimension, ausente en las herramientas
          de medicion del Estado colombiano (CNPV, RLCPD), refleja una comprension
          cosmogonica indigena de la salud y el bienestar que va mas alla del
          modelo biomedico occidental.
        </p>
        <p style={{ fontSize: '0.9rem', lineHeight: 1.7, color: 'var(--color-gray-600)', marginBottom: '12px' }}>
          Para muchos pueblos indigenas, la salud es un equilibrio entre el cuerpo, el espiritu,
          el territorio y la comunidad. La desarmonia espiritual puede manifestarse como resultado
          del desplazamiento forzado, la perdida del territorio ancestral, la ruptura de practicas
          rituales o la imposicion de sistemas externos de salud.
        </p>
        <p style={{ fontSize: '0.85rem', fontStyle: 'italic', color: '#8B5CF6' }}>
          Esta categoria representa la brecha epistemica entre el sistema de clasificacion
          estatal y las formas propias de comprension de la diversidad funcional en los pueblos
          indigenas de Colombia.
        </p>
      </div>
    </div>
  );
}
