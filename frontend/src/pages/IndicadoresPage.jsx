/* ============================================
   SMT-ONIC v2.0 — Sistema de Indicadores
   ============================================ */

import { useState } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer,
} from 'recharts';
import GlobalSelector from '../components/GlobalSelector';
import FilterBreadcrumb from '../components/FilterBreadcrumb';
import DidYouKnow from '../components/DidYouKnow';
import { useFilters } from '../context/FilterContext';
import { useIndicadores, useIndicadorSerie, useIndicadorValores } from '../hooks/useApi';

const MOCK_INDICADORES = [
  {
    id: 'COB-01',
    dimension: 'Cobertura',
    nombre: 'Tasa de prevalencia de capacidades diversas en pueblos indigenas',
    formula: '(Personas indigenas con cap. diversas / Poblacion indigena total) x 1000',
    meta: '> 65\u2030 (cierre de brecha con promedio nacional)',
    valor: '60.0\u2030',
    estado: 'alerta',
  },
  {
    id: 'COB-02',
    dimension: 'Cobertura',
    nombre: 'Cobertura del RLCPD en poblacion indigena',
    formula: '(Indigenas en RLCPD / Indigenas con cap. diversas CNPV) x 100',
    meta: '> 50%',
    valor: '32.4%',
    estado: 'critico',
  },
  {
    id: 'COB-03',
    dimension: 'Cobertura',
    nombre: 'Brecha de certificacion',
    formula: '(Sin certificado / Total con cap. diversas) x 100',
    meta: '< 40%',
    valor: '71.3%',
    estado: 'critico',
  },
  {
    id: 'EPI-01',
    dimension: 'Epidemiologico',
    nombre: 'Distribucion por tipo de dificultad funcional',
    formula: '% por cada dominio Washington Group',
    meta: 'Seguimiento',
    valor: 'Ver: 37.2%',
    estado: 'seguimiento',
  },
  {
    id: 'EPI-02',
    dimension: 'Epidemiologico',
    nombre: 'Indice de envejecimiento con cap. diversas',
    formula: '(>=60 anos con cap. div / Total con cap. div) x 100',
    meta: 'Seguimiento',
    valor: '32.1%',
    estado: 'seguimiento',
  },
  {
    id: 'DER-01',
    dimension: 'Derechos',
    nombre: 'Victimas del conflicto con cap. diversas sobre total indigena',
    formula: '(Victimas indig. con cap. div / Total indig. con cap. div) x 100',
    meta: '< 10%',
    valor: '16.8%',
    estado: 'alerta',
  },
  {
    id: 'DER-02',
    dimension: 'Derechos',
    nombre: 'Afiliacion a salud',
    formula: '% de personas con cap. diversas afiliadas al SGSSS',
    meta: '> 95%',
    valor: '89.2%',
    estado: 'alerta',
  },
  {
    id: 'DER-03',
    dimension: 'Derechos',
    nombre: 'Acceso a tratamiento',
    formula: '% que busco y recibio tratamiento en ultimos 12 meses',
    meta: '> 70%',
    valor: '55.0%',
    estado: 'critico',
  },
  {
    id: 'CAL-01',
    dimension: 'Calidad',
    nombre: 'Completitud de datos SMT-ONIC',
    formula: '% de campos criticos completos en registro propio',
    meta: '> 80%',
    valor: '52.0%',
    estado: 'critico',
  },
  {
    id: 'CAL-02',
    dimension: 'Calidad',
    nombre: 'Consistencia intercensal',
    formula: 'Variacion de prevalencia 2005-2018 explicable por modelo',
    meta: 'R2 > 0.85',
    valor: 'R2 = 0.78',
    estado: 'alerta',
  },
  {
    id: 'TER-01',
    dimension: 'Territorial',
    nombre: 'Cobertura georreferenciada',
    formula: '(Resguardos georreferenciados / Total resguardos) x 100',
    meta: '> 90%',
    valor: '92.0%',
    estado: 'cumplido',
  },
  {
    id: 'TER-02',
    dimension: 'Territorial',
    nombre: 'Indice de concentracion territorial',
    formula: 'Gini de distribucion de cap. diversas por municipio',
    meta: 'Seguimiento',
    valor: '0.72',
    estado: 'seguimiento',
  },
  {
    id: 'TER-03',
    dimension: 'Territorial',
    nombre: 'Municipios prioritarios',
    formula: 'Municipios con prevalencia > 100\u2030 y bajo acceso a salud',
    meta: 'Identificados',
    valor: '47 municipios',
    estado: 'seguimiento',
  },
];

const SAMPLE_SERIE = [
  { anio: 2010, valor: 42.0 },
  { anio: 2012, valor: 48.5 },
  { anio: 2014, valor: 52.1 },
  { anio: 2016, valor: 55.8 },
  { anio: 2018, valor: 60.0 },
  { anio: 2020, valor: 60.8 },
  { anio: 2022, valor: 61.5 },
];

const DIMENSION_COLORS = {
  Cobertura: 'var(--color-green-mid)',
  'Epidemiologico': 'var(--color-primary)',
  Derechos: 'var(--color-red)',
  Calidad: 'var(--color-gold)',
  Territorial: '#6366F1',
};

const ESTADO_BADGES = {
  cumplido: { bg: 'var(--color-green-light)', color: 'var(--color-green-mid)', label: 'Cumplido' },
  alerta: { bg: 'var(--color-gold-light)', color: 'var(--color-gold)', label: 'Alerta' },
  critico: { bg: '#fde8e8', color: 'var(--color-red)', label: 'Critico' },
  seguimiento: { bg: '#e8e8e8', color: 'var(--color-gray-600)', label: 'Seguimiento' },
  calculable: { bg: '#e0e7ff', color: '#6366F1', label: 'Calculable' },
  requiere_cruce: { bg: '#fff3cd', color: '#b8860b', label: 'Requiere cruce' },
  sin_valor: { bg: '#f0f0f0', color: '#999', label: 'Sin valor' },
};

/* Semaphore circle colors by status */
const SEMAPHORE_COLORS = {
  cumplido: '#22c55e',     // green
  calculable: '#22c55e',   // green
  alerta: '#22c55e',       // green (has a value)
  seguimiento: '#22c55e',  // green (has a value)
  requiere_cruce: '#eab308', // yellow
  critico: '#ef4444',      // red
  sin_valor: '#9ca3af',    // gray
};

const cardStyle = {
  background: '#fff',
  borderRadius: 'var(--radius-md)',
  boxShadow: 'var(--shadow-md)',
  padding: '20px 24px',
};

export default function IndicadoresPage() {
  const { dpto, pueblo, dptoNombre, puebloNombre } = useFilters();
  const [selectedIndicador, setSelectedIndicador] = useState(null);
  const { data: apiIndicadores, isLoading, isError } = useIndicadores();
  const { data: apiValores } = useIndicadorValores('2018', 'nacional');
  const { data: apiSerie } = useIndicadorSerie(selectedIndicador || undefined);

  // Build a map of cod_indicador -> valor from the valores endpoint
  const valoresMap = {};
  if (apiValores?.data) {
    for (const v of apiValores.data) {
      if (v.cod_indicador && v.valor != null) {
        // Keep the first (or nacional-level) value per indicator
        if (!valoresMap[v.cod_indicador]) {
          valoresMap[v.cod_indicador] = v;
        }
      }
    }
  }

  // Build time series data from API, fallback to SAMPLE_SERIE
  const serieData = (apiSerie?.serie && apiSerie.serie.length > 0)
    ? apiSerie.serie.map((s) => ({ anio: s.periodo, valor: s.valor }))
    : SAMPLE_SERIE;
  const serieIsReal = apiSerie?.serie && apiSerie.serie.length > 0;

  // API returns { total, data: [{ id, codigo, nombre, grupo, formula, meta, fuente_primaria, fuente_cruce, unidad, descripcion }] }
  const indicadoresRaw = apiIndicadores?.data;
  const indicadores = indicadoresRaw
    ? indicadoresRaw.map((i) => {
        const codigo = i.codigo || i.id;
        const valorInfo = valoresMap[codigo];
        const unitSuffix = i.unidad === 'tasa_x_1000' ? '\u2030' : i.unidad === 'porcentaje' ? '%' : '';
        let valorStr = valorInfo ? `${valorInfo.valor}${unitSuffix}` : undefined;

        // Determine estado based on available data
        let estado;
        if (valorInfo && valorInfo.valor != null) {
          // Has a computed value
          estado = 'calculable';
        } else if (i.fuente_cruce) {
          // Needs cross-reference data from another source
          estado = 'requiere_cruce';
        } else {
          // No value calculated yet
          estado = 'sin_valor';
        }

        return {
          ...i,
          id: codigo,
          dimension: i.grupo,
          meta: i.meta || '--',
          valor: valorStr,
          estado,
        };
      })
    : MOCK_INDICADORES;

  const dimensiones = [...new Set(indicadores.map((ind) => ind.dimension))];

  // Build page title
  let pageTitle = 'Sistema de Indicadores';
  if (puebloNombre) {
    pageTitle = `Indicadores: ${puebloNombre}`;
  } else if (dptoNombre) {
    pageTitle = `Indicadores: ${dptoNombre}`;
  }

  if (isLoading) return <div className="loading-container"><div className="spinner" /><p>Cargando...</p></div>;
  if (isError) return <div className="error-container"><p>Error cargando datos</p></div>;

  return (
    <div>
      <div className="page-header">
        <h1>{pageTitle}</h1>
        <p>{indicadores.length} indicadores agrupados por dimension para el monitoreo de capacidades diversas en pueblos indigenas</p>
      </div>

      {/* Global Selector */}
      <GlobalSelector />

      {/* Breadcrumb */}
      <FilterBreadcrumb />

      {/* Introductory explanation */}
      <div style={{
        ...cardStyle,
        marginBottom: '24px',
        borderLeft: '4px solid var(--color-green-mid)',
        lineHeight: 1.7,
      }}>
        <p style={{ fontSize: '0.92rem', color: 'var(--color-gray-600)', marginBottom: '12px' }}>
          El Sistema de Indicadores monitorea 13 metricas clave sobre la situacion de personas
          con capacidades diversas en pueblos indigenas de Colombia. Cada indicador tiene una
          formula, una meta y un valor actual calculado automaticamente. Los indicadores se
          agrupan en 5 dimensiones: Cobertura del Registro, Perfil Epidemiologico, Acceso a
          Derechos, Calidad del Instrumento y Analisis Territorial.
        </p>
        <p style={{ fontSize: '0.85rem', color: 'var(--color-gray-500)', fontStyle: 'italic' }}>
          Los valores se actualizan cada vez que se incorporan nuevos datos al sistema.
        </p>
      </div>

      {/* Filter active note */}
      {(dpto || pueblo) && (
        <div className="alert alert-info" style={{ marginBottom: '16px' }}>
          <strong>Alcance:</strong>{' '}
          {puebloNombre && `Pueblo: ${puebloNombre}`}
          {!puebloNombre && dptoNombre && `Departamento: ${dptoNombre}`}
          {'. '}Los valores de indicadores se ajustaran al nivel territorial seleccionado cuando los datos esten disponibles.
        </div>
      )}

      {/* Dimension summary */}
      <div className="grid-row" style={{ gridTemplateColumns: `repeat(${dimensiones.length}, 1fr)`, marginBottom: '24px' }}>
        {dimensiones.map((dim) => {
          const dimInds = indicadores.filter((ind) => ind.dimension === dim);
          const count = dimInds.length;
          const criticos = dimInds.filter((ind) => ind.estado === 'critico').length;
          const alertas = dimInds.filter((ind) => ind.estado === 'alerta').length;
          const cumplidos = dimInds.filter((ind) => ind.estado === 'cumplido').length;
          const calculables = dimInds.filter((ind) => ind.estado === 'calculable').length;
          const reqCruce = dimInds.filter((ind) => ind.estado === 'requiere_cruce').length;
          const sinValor = dimInds.filter((ind) => ind.estado === 'sin_valor').length;

          const statusParts = [];
          if (cumplidos > 0) statusParts.push(`${cumplidos} cumplidos`);
          if (calculables > 0) statusParts.push(`${calculables} calculables`);
          if (alertas > 0) statusParts.push(`${alertas} en alerta`);
          if (criticos > 0) statusParts.push(`${criticos} criticos`);
          if (reqCruce > 0) statusParts.push(`${reqCruce} requieren cruce`);
          if (sinValor > 0) statusParts.push(`${sinValor} sin valor`);

          return (
            <div
              key={dim}
              style={{
                ...cardStyle,
                borderLeft: `4px solid ${DIMENSION_COLORS[dim] || '#999'}`,
                padding: '14px 18px',
              }}
            >
              <div style={{ fontSize: '0.78rem', fontWeight: 600, textTransform: 'uppercase', color: 'var(--color-gray-500)' }}>
                {dim}
              </div>
              <div style={{ fontSize: '1.5rem', fontWeight: 700, fontFamily: 'var(--font-heading)', color: 'var(--color-primary)' }}>
                {count}
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--color-gray-400)', lineHeight: 1.4 }}>
                {statusParts.length > 0 ? statusParts.join(', ') : 'Sin alertas criticas'}
              </div>
            </div>
          );
        })}
      </div>

      {/* Indicators table */}
      <div style={{ ...cardStyle, marginBottom: '24px' }}>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
            <thead>
              <tr>
                {['', 'Codigo', 'Dimension', 'Indicador', 'Formula', 'Meta', 'Valor actual', 'Estado'].map(
                  (h) => (
                    <th
                      key={h}
                      style={{
                        padding: '10px 14px',
                        textAlign: 'left',
                        fontWeight: 600,
                        fontSize: '0.75rem',
                        textTransform: 'uppercase',
                        color: 'var(--color-gray-500)',
                        background: 'var(--color-gray-100)',
                        borderBottom: '2px solid var(--color-gray-200)',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {h}
                    </th>
                  )
                )}
              </tr>
            </thead>
            <tbody>
              {indicadores.map((ind, i) => {
                const badge = ESTADO_BADGES[ind.estado] || ESTADO_BADGES.seguimiento;
                return (
                  <tr
                    key={ind.id}
                    style={{
                      background: i % 2 === 0 ? '#fff' : 'var(--color-gray-100)',
                      cursor: 'pointer',
                      transition: 'background 0.1s',
                    }}
                    onClick={() =>
                      setSelectedIndicador(selectedIndicador === ind.id ? null : ind.id)
                    }
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = 'var(--color-green-light)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background =
                        i % 2 === 0 ? '#fff' : 'var(--color-gray-100)';
                    }}
                  >
                    <td style={{ padding: '10px 14px', borderBottom: '1px solid var(--color-gray-200)', textAlign: 'center', width: '36px' }}>
                      <span
                        style={{
                          display: 'inline-block',
                          width: '14px',
                          height: '14px',
                          borderRadius: '50%',
                          background: SEMAPHORE_COLORS[ind.estado] || SEMAPHORE_COLORS.sin_valor,
                          boxShadow: '0 0 3px rgba(0,0,0,0.15)',
                        }}
                        title={
                          ind.estado === 'calculable' || ind.valor ? 'Tiene valor calculado'
                          : ind.estado === 'requiere_cruce' ? 'Requiere cruce con otra fuente'
                          : ind.estado === 'critico' ? 'Problema critico de calidad'
                          : 'Sin valor calculado aun'
                        }
                      />
                    </td>
                    <td style={{ padding: '10px 14px', borderBottom: '1px solid var(--color-gray-200)', fontWeight: 600, fontFamily: 'monospace', fontSize: '0.82rem' }}>
                      {ind.id}
                    </td>
                    <td style={{ padding: '10px 14px', borderBottom: '1px solid var(--color-gray-200)' }}>
                      <span style={{
                        display: 'inline-block',
                        padding: '2px 8px',
                        borderRadius: '10px',
                        fontSize: '0.72rem',
                        fontWeight: 600,
                        background: `${DIMENSION_COLORS[ind.dimension] || '#999'}22`,
                        color: DIMENSION_COLORS[ind.dimension] || '#999',
                      }}>
                        {ind.dimension}
                      </span>
                    </td>
                    <td style={{ padding: '10px 14px', borderBottom: '1px solid var(--color-gray-200)', maxWidth: '280px' }}>
                      {ind.nombre}
                    </td>
                    <td style={{ padding: '10px 14px', borderBottom: '1px solid var(--color-gray-200)', fontSize: '0.8rem', color: 'var(--color-gray-500)', maxWidth: '240px' }}>
                      {ind.formula}
                    </td>
                    <td style={{ padding: '10px 14px', borderBottom: '1px solid var(--color-gray-200)', fontSize: '0.82rem', whiteSpace: 'nowrap' }}>
                      {ind.meta}
                    </td>
                    <td style={{ padding: '10px 14px', borderBottom: '1px solid var(--color-gray-200)', fontWeight: 600, whiteSpace: 'nowrap' }}>
                      {ind.valor}
                    </td>
                    <td style={{ padding: '10px 14px', borderBottom: '1px solid var(--color-gray-200)' }}>
                      <span
                        style={{
                          display: 'inline-block',
                          padding: '2px 10px',
                          borderRadius: '12px',
                          fontSize: '0.72rem',
                          fontWeight: 600,
                          background: badge.bg,
                          color: badge.color,
                        }}
                      >
                        {badge.label}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Time series chart (shown when indicator selected) */}
      {selectedIndicador && (
        <div style={cardStyle}>
          <div style={{
            fontFamily: 'var(--font-body)',
            fontSize: '0.85rem',
            fontWeight: 600,
            textTransform: 'uppercase',
            letterSpacing: '0.5px',
            color: 'var(--color-gray-500)',
            marginBottom: '16px',
          }}>
            Serie de tiempo \u2014 {selectedIndicador}
            {dptoNombre && ` (${dptoNombre})`}
            {puebloNombre && ` - ${puebloNombre}`}
          </div>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={serieData} margin={{ top: 10, right: 30, bottom: 10, left: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e8e8e8" />
              <XAxis dataKey="anio" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip formatter={(v) => [v, 'Valor']} />
              <Line
                type="monotone"
                dataKey="valor"
                stroke="#02432D"
                strokeWidth={2}
                dot={{ r: 4 }}
                activeDot={{ r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
          {!serieIsReal && (
            <div style={{ textAlign: 'center', fontSize: '0.78rem', color: 'var(--color-gray-400)', marginTop: '8px' }}>
              Datos ilustrativos. No se encontraron datos de serie de tiempo para este indicador.
            </div>
          )}
        </div>
      )}

      {/* DidYouKnow callout */}
      <DidYouKnow
        fact="Solo el 0.46% de las personas indigenas con capacidades diversas ha sido caracterizado por el SMT-ONIC."
        source="SMT-ONIC 2026 vs CNPV 2018"
      />
    </div>
  );
}
