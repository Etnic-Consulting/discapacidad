/* ============================================================
   RangoEdadDiscBar — barras horizontales por rango de edad
   Uso: personas CON capacidades diversas (CNPV 2018)

   DIFERENCIA CLAVE vs PiramidePoblacional:
   - SIN .reverse() → orden cronológico ascendente:
     0-4 arriba, 85+ abajo (Recharts layout="vertical"
     pinta [0] en la parte superior del eje Y de categorías).
   - Barras positivas para Hombres y Mujeres (stacked o side-by-side),
     sin eje negativo. Lectura de magnitud, no de mariposa.
   ============================================================ */

import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer,
} from 'recharts';

function fmt(n) {
  return new Intl.NumberFormat('es-CO').format(n);
}

function ErrorTab({ message }) {
  return (
    <div style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--color-gray-400)' }}>
      <p>{message || 'Sin datos de capacidades diversas para este pueblo.'}</p>
    </div>
  );
}

/**
 * @param {object} piramideData  - respuesta de /api/piramide-cap-diversas/<codPueblo>
 * @param {string} nombrePueblo  - nombre visible del pueblo
 * @param {boolean} compact      - modo compacto (omite tabla de índices)
 */
export default function RangoEdadDiscBar({ piramideData, nombrePueblo, compact = false }) {
  if (!piramideData || !piramideData.piramide || piramideData.piramide.length === 0) {
    return <ErrorTab message="No hay datos de capacidades diversas por rango de edad disponibles." />;
  }

  const { piramide, total, total_hombres, total_mujeres, pueblo } = piramideData;
  const displayName = nombrePueblo || pueblo || '';
  const pctH = total > 0 ? ((total_hombres / total) * 100).toFixed(1) : '0.0';
  const pctM = total > 0 ? ((total_mujeres / total) * 100).toFixed(1) : '0.0';

  // SIN reverse(): mantener el orden original del API (ascendente 0-4 → 85+).
  // Recharts layout="vertical" pinta [0] primero desde arriba, de modo que
  // 0-4 queda arriba y 85+ queda abajo — orden cronológico de lectura natural.
  const barData = piramide.map((row) => {
    const hAbs = row.hombres_abs || Math.abs(row.hombres || 0);
    const mAbs = row.mujeres_abs || Math.abs(row.mujeres || 0);
    const pH = row.pct_hombres || (total > 0 ? (hAbs / total) * 100 : 0);
    const pM = row.pct_mujeres || (total > 0 ? (mAbs / total) * 100 : 0);
    return {
      grupo_edad: row.grupo_edad,
      hombres: hAbs,
      mujeres: mAbs,
      hombres_abs: hAbs,
      mujeres_abs: mAbs,
      pct_hombres_raw: pH,
      pct_mujeres_raw: pM,
    };
  });
  // No se aplica .reverse() — orden cronológico preservado.

  const chartHeight = compact ? 400 : Math.max(350, barData.length * 28 + 60);

  return (
    <div>
      {/* Title */}
      {!compact && (
        <div style={{
          textAlign: 'center',
          marginBottom: '8px',
          fontSize: '1rem',
          fontWeight: 700,
          color: 'var(--color-primary)',
          fontFamily: 'var(--font-heading)',
        }}>
          {`Capacidades diversas por rango de edad — ${displayName}`}
          <span style={{ fontWeight: 400, fontSize: '0.82rem', color: 'var(--color-gray-500)' }}>
            {' '}-- CNPV 2018
          </span>
        </div>
      )}

      {/* Chart */}
      <ResponsiveContainer width="100%" height={chartHeight}>
        <BarChart
          layout="vertical"
          data={barData}
          margin={{ top: 5, right: 40, bottom: 20, left: 10 }}
          barCategoryGap="10%"
          barGap={2}
          barSize={11}
        >
          <CartesianGrid horizontal={false} strokeDasharray="3 3" stroke="#ddd" />
          <XAxis
            type="number"
            tickFormatter={(v) => {
              if (v >= 1000) return (v / 1000).toFixed(v >= 10000 ? 0 : 1) + 'K';
              return v.toString();
            }}
            tick={{ fontSize: 11 }}
            axisLine={{ stroke: '#999' }}
          />
          <YAxis
            type="category"
            dataKey="grupo_edad"
            width={65}
            tick={{ fontSize: 11, fontWeight: 600 }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            content={({ active, payload, label }) => {
              if (!active || !payload || payload.length === 0) return null;
              const row = payload[0]?.payload;
              if (!row) return null;
              return (
                <div style={{
                  background: '#fff',
                  border: '1px solid #e5e7eb',
                  borderRadius: '6px',
                  padding: '10px 14px',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.12)',
                  fontSize: '0.82rem',
                  lineHeight: 1.6,
                }}>
                  <div style={{ fontWeight: 700, marginBottom: '4px', color: '#374151' }}>
                    Grupo: {label}
                  </div>
                  <div>
                    <span style={{ color: '#4A90D9', fontWeight: 600 }}>Hombres:</span>{' '}
                    {fmt(row.hombres_abs)} ({row.pct_hombres_raw.toFixed(2)}%)
                  </div>
                  <div>
                    <span style={{ color: '#E74C3C', fontWeight: 600 }}>Mujeres:</span>{' '}
                    {fmt(row.mujeres_abs)} ({row.pct_mujeres_raw.toFixed(2)}%)
                  </div>
                  <div style={{ marginTop: '4px', borderTop: '1px solid #e5e7eb', paddingTop: '4px', fontWeight: 600 }}>
                    Total: {fmt(row.hombres_abs + row.mujeres_abs)}
                  </div>
                </div>
              );
            }}
          />
          <Legend
            formatter={(value) => {
              if (value === 'hombres') return 'Hombres';
              if (value === 'mujeres') return 'Mujeres';
              return value;
            }}
          />
          <Bar dataKey="hombres" name="Hombres" fill="#4A90D9" />
          <Bar dataKey="mujeres" name="Mujeres" fill="#E74C3C" />
        </BarChart>
      </ResponsiveContainer>

      {/* Summary */}
      <div style={{
        textAlign: 'center',
        marginTop: '16px',
        padding: '12px 20px',
        background: '#f9fafb',
        borderRadius: 'var(--radius-sm)',
        fontSize: '0.88rem',
        color: 'var(--color-gray-600)',
        lineHeight: 1.7,
      }}>
        Personas con capacidades diversas en <strong>{displayName}</strong>:{' '}
        <span style={{ color: '#4A90D9', fontWeight: 700 }}>{fmt(total_hombres)}</span> hombres ({pctH}%) y{' '}
        <span style={{ color: '#E74C3C', fontWeight: 700 }}>{fmt(total_mujeres)}</span> mujeres ({pctM}%).
        {' '}Total: <strong>{fmt(total)}</strong> personas.
      </div>
    </div>
  );
}
