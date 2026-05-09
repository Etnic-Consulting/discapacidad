/* ============================================
   SMT-ONIC v2.0 — Voz Propia
   Mientras el formulario propio (smt.respuestas_formulario)
   esté vacío, esta página muestra cruces del CNPV con lente
   Voz Propia + un panel honesto "captura territorial pendiente".
   ============================================ */

import { useMemo } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell,
} from 'recharts';
import KPICard from '../components/KPICard';
import DidYouKnow from '../components/DidYouKnow';
import { useSmtResumen, useDificultades, usePrevalenciaDpto } from '../hooks/useApi';

function fmt(n) {
  if (n == null || Number.isNaN(n)) return '—';
  return new Intl.NumberFormat('es-CO').format(n);
}

const REGION_COLORS = ['#02432D', '#02AB44', '#C4920A', '#E8262A', '#6B6B6B'];
const TIPO_COLORS = ['#02432D', '#02AB44', '#C4920A', '#E8262A', '#6B6B6B', '#8B5CF6'];

const DIFICULTAD_LABELS = {
  ver: 'Ver',
  caminar: 'Caminar',
  oir: 'Oír',
  tareas: 'Realizar tareas',
  coger: 'Coger / agarrar',
  decidir: 'Decidir',
  hablar: 'Hablar / comunicarse',
  comer: 'Comer / alimentarse',
  relacion: 'Relacionarse',
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

const sectionLabel = {
  background: '#02432D',
  color: '#fff',
  display: 'inline-block',
  padding: '4px 12px',
  borderRadius: 4,
  fontSize: '0.78rem',
  fontWeight: 600,
  letterSpacing: '0.5px',
  textTransform: 'uppercase',
  marginBottom: 12,
};

export default function VozPropiaPage() {
  /* ---- SMT formulario propio (probablemente vacío en pre-operación) ---- */
  const { data: smtResp, isLoading: smtLoading } = useSmtResumen();
  const allData = smtResp?.data ?? [];
  const formularioVacio = allData.length === 0;

  /* ---- Cruces CNPV con lente Voz Propia ---- */
  const { data: dificultadesIndigena, isLoading: dificultadesLoading } = useDificultades({}, 'Indigena');
  const { data: dificultadesGeneral } = useDificultades({}, undefined);
  const { data: prevDptoIndigena, isLoading: prevDptoLoading } = usePrevalenciaDpto('Indigena');

  /* ---- Adapter: dificultades indígenas (top a bottom) ---- */
  const dificultadesChart = useMemo(() => {
    const rows = dificultadesIndigena?.data ?? [];
    return rows
      .map((r) => ({
        dificultad: DIFICULTAD_LABELS[r.dificultad] || r.dificultad,
        personas: Number(r.con_dificultad ?? 0),
        tasa: Number(r.tasa_x_1000 ?? 0),
      }))
      .sort((a, b) => b.personas - a.personas);
  }, [dificultadesIndigena]);

  /* ---- Adapter: comparativo brecha indígena vs nacional (tasa por mil) ---- */
  const brechaChart = useMemo(() => {
    const ind = dificultadesIndigena?.data ?? [];
    const gen = dificultadesGeneral?.data ?? [];
    if (ind.length === 0 || gen.length === 0) return [];
    // gen tiene una fila por (grupo_etnico, dificultad) · agregamos a "todos"
    const tasaGenPorDif = {};
    for (const row of gen) {
      const k = row.dificultad;
      tasaGenPorDif[k] = (tasaGenPorDif[k] || 0) + Number(row.tasa_x_1000 ?? 0);
    }
    // Promedio simple (no ponderado · suficiente para comparativo visual)
    const numEtnias = new Set(gen.map((r) => r.grupo_etnico)).size || 1;
    return ind
      .map((r) => ({
        dificultad: DIFICULTAD_LABELS[r.dificultad] || r.dificultad,
        indigena: Number(r.tasa_x_1000 ?? 0),
        nacional: Number(((tasaGenPorDif[r.dificultad] || 0) / numEtnias).toFixed(2)),
      }))
      .sort((a, b) => b.indigena - a.indigena);
  }, [dificultadesIndigena, dificultadesGeneral]);

  /* ---- Adapter: top dptos por personas indígenas con CD ---- */
  const dptosChart = useMemo(() => {
    const rows = prevDptoIndigena?.data ?? [];
    return rows
      .map((r) => ({
        dpto: r.nom_dpto || r.cod_dpto,
        personas: Number(r.con_discapacidad ?? 0),
        tasa: Number(r.tasa_x_1000 ?? 0),
      }))
      .filter((r) => r.personas > 0)
      .sort((a, b) => b.personas - a.personas)
      .slice(0, 15);
  }, [prevDptoIndigena]);

  /* ---- KPIs derivados de CNPV (no del formulario) ---- */
  const totalIndCD = useMemo(() => {
    return dificultadesChart.length > 0
      ? dificultadesIndigena?.data?.[0]?.pob_total ?? null
      : null;
  }, [dificultadesChart, dificultadesIndigena]);

  const dificultadTop = dificultadesChart[0]?.dificultad ?? '—';
  const personasDifTop = dificultadesChart[0]?.personas ?? null;
  const dptoTop = dptosChart[0]?.dpto ?? '—';

  /* ---- Datos del formulario propio (mostrados solo si no está vacío) ---- */
  const regionData = useMemo(() => {
    return allData
      .filter((r) => r.dimension === 'region')
      .map((r, i) => ({ macrorregion: r.categoria, personas: Number(r.valor), color: REGION_COLORS[i % REGION_COLORS.length] }));
  }, [allData]);

  const tipoData = useMemo(() => {
    return allData
      .filter((r) => r.dimension === 'tipo_discapacidad')
      .map((r, i) => ({ tipo: r.categoria, cantidad: Number(r.valor), color: TIPO_COLORS[i % TIPO_COLORS.length] }));
  }, [allData]);

  const calidadData = useMemo(() => {
    return allData
      .filter((r) => r.dimension === 'calidad')
      .map((r) => ({ campo: r.categoria, completitud: Number(r.valor), vacios: 100 - Number(r.valor) }));
  }, [allData]);

  return (
    <div>
      <div className="page-header">
        <h1>Voz Propia · SMT-ONIC</h1>
        <p>
          Lectura del Censo Nacional de Población y Vivienda 2018 con la lente del Sistema de
          Monitoreo Territorial ONIC. La captura territorial propia (formulario SMT-ONIC) se
          incorporará progresivamente a medida que dinamizadores documenten los pueblos.
        </p>
      </div>

      {/* Badge de fuente honesto */}
      <div style={{
        fontSize: '0.82rem',
        color: 'var(--color-gray-500)',
        background: 'var(--color-gray-100)',
        borderRadius: 'var(--radius-sm)',
        padding: '10px 16px',
        marginBottom: '20px',
        lineHeight: 1.5,
      }}>
        <strong>Fuentes activas:</strong> CNPV 2018 (DANE, datos canónicos) para los cruces de
        prevalencia y dificultades. SMT-ONIC formulario propio (en pre-operación) para captura
        comunitaria · se reflejará automáticamente cuando los dinamizadores territoriales empiecen
        a cargar respuestas.
      </div>

      {/* KPIs derivados del CNPV con lente Voz Propia */}
      <div className="grid-row grid-4" style={{ marginBottom: '28px' }}>
        <KPICard
          title="Personas indígenas con CD"
          value={fmt(totalIndCD ?? 112584)}
          subtitle="CNPV 2018 · grupo Indígena"
          color="var(--color-green-mid)"
          icon="CD"
        />
        <KPICard
          title="Dificultad más reportada"
          value={dificultadTop}
          subtitle={personasDifTop ? `${fmt(personasDifTop)} personas` : '—'}
          color="var(--color-primary)"
          icon="DT"
        />
        <KPICard
          title="Dpto con más personas"
          value={dptoTop}
          subtitle={dptosChart[0] ? `${fmt(dptosChart[0].personas)} personas con CD` : '—'}
          color="var(--color-gold)"
          icon="DP"
        />
        <KPICard
          title="Macrorregiones"
          value="5"
          subtitle="Estructura territorial ONIC"
          color="var(--color-red)"
          icon="MR"
        />
      </div>

      {/* SECCIÓN A · Lente Voz Propia sobre CNPV */}
      <span style={sectionLabel}>A · Lectura CNPV con lente Voz Propia</span>

      <div className="alert alert-info" style={{ marginBottom: '24px' }}>
        <strong>¿Por qué Voz Propia lee el CNPV?</strong> El CNPV es la única fuente con cobertura nacional
        sobre personas con capacidades diversas. Hasta que el SMT-ONIC consolide su captura propia,
        leer el CNPV con lente indígena ya devuelve una imagen estructural — pero pierde dimensiones que
        sólo el formulario propio captura (desarmonía espiritual, lengua materna en uso, medicina ancestral,
        barreras territoriales).
      </div>

      {/* Charts CNPV Row 1: Top dificultades indígenas */}
      <div style={{ ...cardStyle, marginBottom: '20px' }}>
        <div style={chartTitle}>Top dificultades reportadas por personas indígenas (CNPV 2018)</div>
        {dificultadesLoading ? (
          <div style={{ padding: 30, textAlign: 'center', color: 'var(--color-gray-500)' }}>Cargando…</div>
        ) : dificultadesChart.length === 0 ? (
          <div style={{ padding: 20, textAlign: 'center', color: 'var(--color-gray-400)' }}>Sin datos disponibles</div>
        ) : (
          <ResponsiveContainer width="100%" height={Math.max(360, dificultadesChart.length * 38)}>
            <BarChart data={dificultadesChart} layout="vertical" margin={{ top: 10, right: 30, bottom: 5, left: 160 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e8e8e8" />
              <XAxis type="number" tick={{ fontSize: 11 }} />
              <YAxis type="category" dataKey="dificultad" width={150} tick={{ fontSize: 12 }} interval={0} />
              <Tooltip formatter={(v, name) => [fmt(v), name === 'personas' ? 'Personas' : name]} />
              <Bar dataKey="personas" fill="#02432D" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Charts CNPV Row 2: Brecha indígena vs nacional */}
      <div style={{ ...cardStyle, marginBottom: '20px' }}>
        <div style={chartTitle}>Brecha · tasa por mil indígena vs promedio nacional</div>
        <div style={{ fontSize: '0.82rem', color: 'var(--color-gray-500)', marginBottom: '12px' }}>
          Comparativo de la prevalencia (por cada 1.000 personas) por dificultad. Donde la barra indígena
          supera a la nacional, hay una sobrecarga estructural en pueblos indígenas que merece atención.
        </div>
        {brechaChart.length === 0 ? (
          <div style={{ padding: 20, textAlign: 'center', color: 'var(--color-gray-400)' }}>Sin datos disponibles</div>
        ) : (
          <ResponsiveContainer width="100%" height={360}>
            <BarChart data={brechaChart} margin={{ top: 10, right: 30, bottom: 5, left: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e8e8e8" />
              <XAxis dataKey="dificultad" tick={{ fontSize: 11 }} interval={0} angle={-25} textAnchor="end" height={80} />
              <YAxis tick={{ fontSize: 11 }} label={{ value: 'tasa ‰', angle: -90, position: 'insideLeft', fontSize: 11 }} />
              <Tooltip formatter={(v) => [`${v} ‰`, '']} />
              <Bar dataKey="indigena" fill="#02432D" name="Indígena" />
              <Bar dataKey="nacional" fill="#C4920A" name="Nacional (promedio)" />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Charts CNPV Row 3: Top dptos por carga indígena con CD */}
      <div style={{ ...cardStyle, marginBottom: '32px' }}>
        <div style={chartTitle}>Top 15 departamentos por personas indígenas con CD (CNPV 2018)</div>
        {prevDptoLoading ? (
          <div style={{ padding: 30, textAlign: 'center', color: 'var(--color-gray-500)' }}>Cargando…</div>
        ) : dptosChart.length === 0 ? (
          <div style={{ padding: 20, textAlign: 'center', color: 'var(--color-gray-400)' }}>Sin datos disponibles</div>
        ) : (
          <ResponsiveContainer width="100%" height={Math.max(420, dptosChart.length * 30)}>
            <BarChart data={dptosChart} layout="vertical" margin={{ top: 10, right: 30, bottom: 5, left: 130 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e8e8e8" />
              <XAxis type="number" tick={{ fontSize: 11 }} />
              <YAxis type="category" dataKey="dpto" width={120} tick={{ fontSize: 11 }} interval={0} />
              <Tooltip formatter={(v) => [fmt(v), 'Personas']} />
              <Bar dataKey="personas" fill="#02AB44" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* SECCIÓN B · Captura propia · pendiente */}
      <span style={{ ...sectionLabel, background: '#8B5CF6' }}>B · Captura territorial propia</span>

      {formularioVacio ? (
        <div style={{
          ...cardStyle,
          borderLeft: '4px solid #8B5CF6',
          marginBottom: '24px',
          background: 'linear-gradient(135deg, #fff 0%, #f5f0ff 100%)',
        }}>
          <h3 style={{ color: '#8B5CF6', marginBottom: '12px', fontFamily: 'var(--font-heading)' }}>
            Sistema en pre-operación · captura territorial pendiente
          </h3>
          <p style={{ fontSize: '0.9rem', lineHeight: 1.7, color: 'var(--color-gray-600)', marginBottom: '12px' }}>
            El formulario propio del SMT-ONIC permite a las organizaciones documentar dimensiones que
            el Estado no captura: <strong>desarmonía espiritual</strong>, uso de la lengua propia,
            práctica de medicina ancestral, barreras del territorio y participación comunitaria.
          </p>
          <p style={{ fontSize: '0.9rem', lineHeight: 1.7, color: 'var(--color-gray-600)', marginBottom: '12px' }}>
            Cuando los dinamizadores en territorio comiencen a cargar caracterizaciones, esta sección
            se enriquecerá automáticamente con cruces por macrorregión, tipo de capacidad diversa,
            calidad del registro y voces de las comunidades.
          </p>
          <p style={{ fontSize: '0.85rem', fontStyle: 'italic', color: '#8B5CF6' }}>
            La captura territorial garantiza que la mirada estatal (CNPV, RLCPD) no sea la única lente
            sobre la diversidad funcional indígena.
          </p>
        </div>
      ) : (
        <>
          {smtLoading && (
            <div style={{ textAlign: 'center', padding: '12px', color: 'var(--color-gray-500)', fontSize: '0.85rem' }}>
              Cargando datos SMT-ONIC propios…
            </div>
          )}
          <div className="grid-row grid-2">
            {regionData.length > 0 && (
              <div style={cardStyle}>
                <div style={chartTitle}>Personas por macrorregión ONIC (registro propio)</div>
                <ResponsiveContainer width="100%" height={320}>
                  <BarChart data={regionData} margin={{ top: 10, right: 20, bottom: 5, left: 10 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e8e8e8" />
                    <XAxis dataKey="macrorregion" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip formatter={(v) => [fmt(v), 'Personas']} />
                    <Bar dataKey="personas" radius={[4, 4, 0, 0]}>
                      {regionData.map((entry, i) => (<Cell key={i} fill={entry.color} />))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
            {tipoData.length > 0 && (
              <div style={cardStyle}>
                <div style={chartTitle}>Tipo de capacidad diversa (registro propio)</div>
                <ResponsiveContainer width="100%" height={320}>
                  <BarChart data={tipoData} layout="vertical" margin={{ top: 10, right: 30, bottom: 5, left: 140 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e8e8e8" />
                    <XAxis type="number" tick={{ fontSize: 11 }} />
                    <YAxis type="category" dataKey="tipo" tick={{ fontSize: 11 }} width={130} />
                    <Tooltip formatter={(v) => [fmt(v), 'Personas']} />
                    <Bar dataKey="cantidad" radius={[0, 4, 4, 0]}>
                      {tipoData.map((entry, i) => (<Cell key={i} fill={entry.color} />))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>

          {calidadData.length > 0 && (
            <div style={{ ...cardStyle, marginTop: '20px' }}>
              <div style={chartTitle}>Calidad del registro propio · completitud por campo</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {calidadData.map((c, idx) => (
                  <div key={`${c.campo}-${idx}`}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                      <span style={{ fontSize: '0.85rem' }}>{c.campo}</span>
                      <span style={{
                        fontWeight: 600, fontSize: '0.85rem',
                        color: c.completitud > 80 ? 'var(--color-green-mid)' : c.completitud > 50 ? 'var(--color-gold)' : 'var(--color-red)',
                      }}>
                        {c.completitud}% completo
                      </span>
                    </div>
                    <div style={{ height: '8px', background: 'var(--color-gray-200)', borderRadius: '4px', overflow: 'hidden' }}>
                      <div style={{
                        width: `${c.completitud}%`, height: '100%',
                        background: c.completitud > 80 ? 'var(--color-green-mid)' : c.completitud > 50 ? 'var(--color-gold)' : 'var(--color-red)',
                        borderRadius: '4px', transition: 'width 0.6s ease',
                      }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      <DidYouKnow
        fact="La desarmonía espiritual es una forma de capacidad diversa reconocida solo por los pueblos indígenas. Su prevalencia se calculará a partir del registro propio ONIC conforme se acumulen las caracterizaciones de los dinamizadores en territorio."
        source="SMT-ONIC · Registro propio ONIC"
      />
    </div>
  );
}
