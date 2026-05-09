/* ============================================================
   RangoEdadTipoDisc — pirámide apilada por TIPO de capacidad
   diversa, sexo y edad · con soporte de granularidad fallback.

   Campos esperados en `data` (respuesta de /piramide-disc-tipo/{cod}?fallback=true):
     granularidad   : "pueblo" | "dpto" | "macro" | "sin_datos"
     entidad_origen : { tipo, id, nombre }
     total          : number
     tipos          : string[]
     resumen_tipos  : { tipo, hombres, mujeres, total, pct }[]
     piramide       : row[]
   ============================================================ */

import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ReferenceLine, ResponsiveContainer,
} from 'recharts';

/* Colorblind-safe qualitative palette (ColorBrewer) */
const TIPO_COLORS = {
  'Ver':               '#e41a1c',
  'Caminar':           '#377eb8',
  'Oir':               '#4daf4a',
  'Aprender':          '#984ea3',
  'Hablar':            '#ff7f00',
  'Actividades diarias': '#a65628',
  'Autocuidado':       '#f781bf',
  'Agarrar':           '#999999',
  'Relacionarse':      '#dede00',
};

/* ---- Banners de granularidad ---- */
function BannerDpto({ entidadOrigen }) {
  const id = entidadOrigen?.id ?? '';
  return (
    <div style={{
      display: 'flex',
      alignItems: 'flex-start',
      gap: '10px',
      background: '#fffbeb',
      border: '1px solid #f59e0b',
      borderRadius: '6px',
      padding: '10px 14px',
      marginBottom: '14px',
      fontSize: '0.82rem',
      color: '#92400e',
      lineHeight: 1.5,
    }}>
      <span style={{ fontSize: '1rem', flexShrink: 0 }}>&#9888;&#65039;</span>
      <span>
        <strong>Datos agregados a nivel departamento{id ? ` (${id})` : ''}</strong> por
        k-anonimato (k&ge;200 a nivel pueblo no alcanzado). Los datos mostrados corresponden
        al departamento de referencia, no exclusivamente a este pueblo.
      </span>
    </div>
  );
}

function BannerMacro({ entidadOrigen }) {
  const nombre = entidadOrigen?.nombre ?? '';
  return (
    <div style={{
      display: 'flex',
      alignItems: 'flex-start',
      gap: '10px',
      background: '#fff7ed',
      border: '1px solid #ea580c',
      borderRadius: '6px',
      padding: '10px 14px',
      marginBottom: '14px',
      fontSize: '0.82rem',
      color: '#7c2d12',
      lineHeight: 1.5,
    }}>
      <span style={{ fontSize: '1rem', flexShrink: 0 }}>&#128681;</span>
      <span>
        <strong>Datos agregados a nivel macrorregión{nombre ? ` (${nombre})` : ''}</strong>.
        Pueblo y departamento sin desagregación segura (k&lt;200). Los valores representan
        el agregado macrorregional.
      </span>
    </div>
  );
}

function BannerSinDatos() {
  return (
    <div style={{
      textAlign: 'center',
      padding: '40px 24px',
      background: '#f9fafb',
      borderRadius: '8px',
      border: '1px dashed #d1d5db',
    }}>
      <div style={{ fontSize: '2rem', marginBottom: '12px' }}>&#128683;</div>
      <p style={{ fontWeight: 700, color: '#374151', marginBottom: '6px', fontSize: '0.95rem' }}>
        Datos no disponibles con desagregación segura para este pueblo
      </p>
      <p style={{ fontSize: '0.82rem', color: '#6b7280', maxWidth: '480px', margin: '0 auto' }}>
        El umbral k&ge;30 de privacidad estadística no pudo alcanzarse ni a nivel de pueblo,
        departamento ni macrorregión. No se muestran datos para proteger la privacidad
        de los individuos.
      </p>
    </div>
  );
}

/* ---- Componente principal de la pirámide apilada ---- */
function StackedTypePyramid({ data, nombrePueblo }) {
  const { resumen_tipos, piramide, total } = data;

  /* Sort tipos by total descending (most frequent first) - ALWAYS same order */
  const tiposOrdenados = [...resumen_tipos]
    .sort((a, b) => b.total - a.total)
    .map((t) => t.tipo);

  /* Build chart data using absolute counts */
  const chartData = [...piramide].reverse().map((row) => {
    const entry = { grupo_edad: row.grupo_edad };
    tiposOrdenados.forEach((tipo) => {
      const hAbs = Math.abs(row[`h_${tipo}`] || 0);
      const mAbs = row[`m_${tipo}`] || row[`abs_m_${tipo}`] || 0;
      entry[`h_${tipo}`]     = -hAbs;
      entry[`m_${tipo}`]     = mAbs;
      entry[`abs_h_${tipo}`] = hAbs;
      entry[`abs_m_${tipo}`] = mAbs;
    });
    entry['total_h'] = Math.abs(row.total_h || 0);
    entry['total_m'] = row.total_m || 0;
    return entry;
  });

  /* Symmetric axis bound */
  const maxAbs = Math.max(
    ...chartData.map((r) => tiposOrdenados.reduce((s, t) => s + Math.abs(r[`h_${t}`] || 0), 0)),
    ...chartData.map((r) => tiposOrdenados.reduce((s, t) => s + (r[`m_${t}`] || 0), 0)),
    1,
  );
  const magnitude  = Math.pow(10, Math.floor(Math.log10(maxAbs)));
  const axisBound  = Math.ceil(maxAbs / magnitude) * magnitude;

  return (
    <div>
      {/* Legend */}
      <div style={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: '12px',
        justifyContent: 'center',
        marginBottom: '16px',
      }}>
        {tiposOrdenados.map((tipo) => {
          const t = resumen_tipos.find((r) => r.tipo === tipo);
          return (
            <div
              key={tipo}
              style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '0.78rem' }}
            >
              <div style={{
                width: '14px', height: '14px', borderRadius: '2px',
                background: TIPO_COLORS[tipo] || '#999',
              }} />
              <span style={{ fontWeight: 600 }}>{tipo}</span>
              <span style={{ color: 'var(--color-gray-500)' }}>({t?.pct || 0}%)</span>
            </div>
          );
        })}
      </div>

      {/* Sexo header */}
      <div style={{ display: 'flex', justifyContent: 'center', gap: '4px', marginBottom: '8px' }}>
        <span style={{ color: '#4A90D9', fontWeight: 700, fontSize: '0.85rem' }}>Hombres</span>
        <span style={{ color: 'var(--color-gray-400)' }}>|</span>
        <span style={{ color: '#E74C3C', fontWeight: 700, fontSize: '0.85rem' }}>Mujeres</span>
      </div>

      <ResponsiveContainer width="100%" height={600}>
        <BarChart
          layout="vertical"
          data={chartData}
          margin={{ top: 5, right: 30, bottom: 20, left: 10 }}
          stackOffset="sign"
          barCategoryGap="6%"
          barGap={0}
          barSize={20}
        >
          <CartesianGrid horizontal={false} strokeDasharray="3 3" stroke="#ddd" />
          <XAxis
            type="number"
            domain={[-axisBound, axisBound]}
            tickFormatter={(v) => {
              const abs = Math.abs(v);
              if (abs >= 1000) return (abs / 1000).toFixed(abs >= 10000 ? 0 : 1) + 'K';
              return abs.toString();
            }}
            tick={{ fontSize: 11 }}
            axisLine={{ stroke: '#999' }}
          />
          <YAxis
            type="category"
            dataKey="grupo_edad"
            width={50}
            tick={{ fontSize: 11, fontWeight: 600 }}
            axisLine={false}
            tickLine={false}
          />
          <ReferenceLine x={0} stroke="#333" strokeWidth={2} />
          <Tooltip
            content={({ active, payload, label }) => {
              if (!active || !payload || !payload.length) return null;
              const row = chartData.find((r) => r.grupo_edad === label) || {};
              const items = tiposOrdenados
                .map((tipo) => ({
                  tipo,
                  h: row[`abs_h_${tipo}`] || 0,
                  m: row[`abs_m_${tipo}`] || 0,
                  total: (row[`abs_h_${tipo}`] || 0) + (row[`abs_m_${tipo}`] || 0),
                }))
                .filter((x) => x.total > 0)
                .sort((a, b) => b.total - a.total);

              return (
                <div style={{
                  background: '#fff',
                  border: '1px solid #ddd',
                  borderRadius: '6px',
                  padding: '10px 14px',
                  fontSize: '0.8rem',
                  maxWidth: '320px',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
                }}>
                  <div style={{
                    fontWeight: 700,
                    marginBottom: '6px',
                    borderBottom: '1px solid #eee',
                    paddingBottom: '4px',
                  }}>
                    {label} años
                  </div>
                  {items.map(({ tipo, h, m, total: t }) => (
                    <div
                      key={tipo}
                      style={{
                        display: 'flex',
                        gap: '8px',
                        alignItems: 'center',
                        marginBottom: '3px',
                      }}
                    >
                      <div style={{
                        width: '10px', height: '10px', borderRadius: '2px',
                        background: TIPO_COLORS[tipo] || '#999', flexShrink: 0,
                      }} />
                      <span style={{ flex: 1, fontWeight: 500 }}>{tipo}</span>
                      <span style={{ color: '#4A90D9' }}>H:{h.toLocaleString()}</span>
                      <span style={{ color: '#E74C3C' }}>M:{m.toLocaleString()}</span>
                      <span style={{ fontWeight: 700 }}>{t.toLocaleString()}</span>
                    </div>
                  ))}
                  <div style={{
                    borderTop: '1px solid #eee',
                    marginTop: '4px',
                    paddingTop: '4px',
                    fontWeight: 600,
                    display: 'flex',
                    justifyContent: 'space-between',
                  }}>
                    <span>Total:</span>
                    <span style={{ color: '#4A90D9' }}>H:{(row.total_h || 0).toLocaleString()}</span>
                    <span style={{ color: '#E74C3C' }}>M:{(row.total_m || 0).toLocaleString()}</span>
                    <span>{((row.total_h || 0) + (row.total_m || 0)).toLocaleString()}</span>
                  </div>
                </div>
              );
            }}
          />
          {/* Stacked bars: hombres (negative/left) */}
          {tiposOrdenados.map((tipo) => (
            <Bar
              key={`h_${tipo}`}
              dataKey={`h_${tipo}`}
              name={`H-${tipo}`}
              fill={TIPO_COLORS[tipo] || '#999'}
              stackId="hombres"
            />
          ))}
          {/* Stacked bars: mujeres (positive/right) */}
          {tiposOrdenados.map((tipo) => (
            <Bar
              key={`m_${tipo}`}
              dataKey={`m_${tipo}`}
              name={`M-${tipo}`}
              fill={TIPO_COLORS[tipo] || '#999'}
              stackId="mujeres"
            />
          ))}
        </BarChart>
      </ResponsiveContainer>

      {/* Summary table */}
      <div style={{ marginTop: '16px' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
          <thead>
            <tr style={{ background: 'var(--color-gray-100)' }}>
              {['Tipo de limitación', 'Hombres', 'Mujeres', 'Total', '%'].map((h) => (
                <th
                  key={h}
                  style={{
                    padding: '6px 10px',
                    textAlign: h === 'Tipo de limitación' ? 'left' : 'right',
                    borderBottom: '2px solid var(--color-gray-200)',
                  }}
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {resumen_tipos.map((t) => (
              <tr key={t.tipo} style={{ borderBottom: '1px solid var(--color-gray-200)' }}>
                <td style={{ padding: '5px 10px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <div style={{
                    width: '12px', height: '12px', borderRadius: '2px',
                    background: TIPO_COLORS[t.tipo] || '#999',
                  }} />
                  {t.tipo}
                </td>
                <td style={{ padding: '5px 10px', textAlign: 'right' }}>{t.hombres.toLocaleString()}</td>
                <td style={{ padding: '5px 10px', textAlign: 'right' }}>{t.mujeres.toLocaleString()}</td>
                <td style={{ padding: '5px 10px', textAlign: 'right', fontWeight: 600 }}>{t.total.toLocaleString()}</td>
                <td style={{ padding: '5px 10px', textAlign: 'right', fontWeight: 600 }}>{t.pct}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div style={{
        textAlign: 'center',
        marginTop: '12px',
        fontSize: '0.78rem',
        color: 'var(--color-gray-500)',
      }}>
        Total personas con capacidades diversas: {total.toLocaleString()} | Fuente: CNPV 2018 via REDATAM
      </div>
    </div>
  );
}

/* ============================================================
   Exportación principal · envuelve StackedTypePyramid con
   lógica de granularidad (pueblo / dpto / macro / sin_datos).

   Props:
     data        {object}  respuesta completa del endpoint fallback
     nombrePueblo {string} nombre visible del pueblo
   ============================================================ */
export default function RangoEdadTipoDisc({ data, nombrePueblo }) {
  /* Guardia: datos ausentes o estructura inválida */
  if (!data) {
    return (
      <div style={{ textAlign: 'center', padding: '30px', color: 'var(--color-gray-400)', fontSize: '0.85rem' }}>
        Sin datos de tipo de capacidad diversa para este pueblo.
      </div>
    );
  }

  const granularidad   = data.granularidad   ?? 'pueblo';
  const entidadOrigen  = data.entidad_origen ?? null;
  const tienePiramide  = Array.isArray(data.piramide) && data.piramide.length > 0;

  /* sin_datos: mensaje honesto, sin gráfico */
  if (granularidad === 'sin_datos' || !tienePiramide) {
    return <BannerSinDatos />;
  }

  return (
    <div>
      {/* Banners condicionales por granularidad */}
      {granularidad === 'dpto'  && <BannerDpto  entidadOrigen={entidadOrigen} />}
      {granularidad === 'macro' && <BannerMacro entidadOrigen={entidadOrigen} />}
      {/* granularidad === "pueblo" → render normal sin banner */}

      <StackedTypePyramid data={data} nombrePueblo={nombrePueblo} />
    </div>
  );
}
