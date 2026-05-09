/* ============================================================
   PiramidePoblacional — pirámide vertical DANE-style
   Uso: población total del pueblo (CNPV 2018)
   Mantiene .reverse() para que 85+ quede ARRIBA en Recharts
   layout="vertical" (el eje de categorías es Y, [0] → top).
   ============================================================ */

import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ReferenceLine, ResponsiveContainer,
} from 'recharts';

function fmt(n) {
  return new Intl.NumberFormat('es-CO').format(n);
}

function ErrorTab({ message }) {
  return (
    <div style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--color-gray-400)' }}>
      <p>{message || 'Error cargando datos.'}</p>
    </div>
  );
}

const gruposInfantil = ['0-4', '5-9', '10-14'];
const gruposAdulto = ['15-19', '20-24', '25-29', '30-34', '35-39', '40-44', '45-49', '50-54', '55-59', '60-64'];
const gruposMayor = ['65-69', '70-74', '75-79', '80-84', '85 y mas', '85+'];

export default function PiramidePoblacional({ piramideData, nombrePueblo, compact = false }) {
  if (!piramideData || !piramideData.piramide || piramideData.piramide.length === 0) {
    return <ErrorTab message="No hay datos de piramide poblacional disponibles." />;
  }

  const {
    piramide, total, total_hombres, total_mujeres,
    razon_masculinidad, indice_dependencia, indice_envejecimiento, pueblo,
  } = piramideData;

  const displayName = nombrePueblo || pueblo || '';
  const pctH = total > 0 ? ((total_hombres / total) * 100).toFixed(1) : '0.0';
  const pctM = total > 0 ? ((total_mujeres / total) * 100).toFixed(1) : '0.0';

  // REVERSE: Recharts layout="vertical" pinta [0] arriba.
  // 85+ debe estar arriba, 0-4 abajo → necesita reverse.
  const pctData = piramide.map((row) => {
    const hAbs = row.hombres_abs || Math.abs(row.hombres || 0);
    const mAbs = row.mujeres_abs || Math.abs(row.mujeres || 0);
    const pH = row.pct_hombres || (total > 0 ? (hAbs / total) * 100 : 0);
    const pM = row.pct_mujeres || (total > 0 ? (mAbs / total) * 100 : 0);
    return {
      grupo_edad: row.grupo_edad,
      hombres_pct: -hAbs,   // negativo → izquierda
      mujeres_pct: mAbs,
      hombres_abs: hAbs,
      mujeres_abs: mAbs,
      pct_hombres_raw: pH,
      pct_mujeres_raw: pM,
    };
  }).slice().reverse(); // <-- REVERSE intencional para pirámide vertical

  const maxAbs = Math.max(
    ...pctData.map((r) => Math.max(Math.abs(r.hombres_pct), Math.abs(r.mujeres_pct)))
  );
  const magnitude = Math.pow(10, Math.floor(Math.log10(maxAbs)));
  const axisBound = Math.ceil(maxAbs / magnitude) * magnitude;

  const sumGrupo = (grupos) => {
    let h = 0, m = 0;
    piramide.forEach((row) => {
      if (grupos.includes(row.grupo_edad)) {
        h += row.hombres_abs || Math.abs(row.hombres || 0);
        m += row.mujeres_abs || Math.abs(row.mujeres || 0);
      }
    });
    return { h, m };
  };

  const gInfantil = sumGrupo(gruposInfantil);
  const gAdulto = sumGrupo(gruposAdulto);
  const gMayor = sumGrupo(gruposMayor);
  const pctOfGroup = (val, groupTotal) => groupTotal > 0 ? ((val / groupTotal) * 100).toFixed(1) : '0.0';

  const pyramidHeight = compact ? 450 : 550;

  const tblCell = {
    padding: '6px 12px',
    fontSize: '0.82rem',
    borderBottom: '1px solid var(--color-gray-200)',
  };
  const tblHead = {
    ...tblCell,
    fontWeight: 600,
    fontSize: '0.75rem',
    textTransform: 'uppercase',
    color: 'var(--color-gray-500)',
    background: 'var(--color-gray-100)',
    borderBottom: '2px solid var(--color-gray-200)',
  };

  return (
    <div>
      {/* Title */}
      <div style={{
        textAlign: 'center',
        marginBottom: '8px',
        fontSize: '1rem',
        fontWeight: 700,
        color: 'var(--color-primary)',
        fontFamily: 'var(--font-heading)',
      }}>
        {compact ? '' : `Piramide poblacional ${displayName}`}
        {!compact && (
          <span style={{ fontWeight: 400, fontSize: '0.82rem', color: 'var(--color-gray-500)' }}>
            {' '}-- CNPV 2018
          </span>
        )}
      </div>

      {/* Chart */}
      <ResponsiveContainer width="100%" height={pyramidHeight}>
        <BarChart
          layout="vertical"
          data={pctData}
          margin={{ top: 5, right: 30, bottom: 20, left: 10 }}
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
            width={65}
            tick={{ fontSize: 11, fontWeight: 600 }}
            axisLine={false}
            tickLine={false}
          />
          <ReferenceLine x={0} stroke="#333" strokeWidth={2} />
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
                </div>
              );
            }}
          />
          <Legend
            formatter={(value) => {
              if (value === 'hombres_pct') return 'Hombres';
              if (value === 'mujeres_pct') return 'Mujeres';
              return value;
            }}
          />
          <Bar dataKey="hombres_pct" name="Hombres" fill="#4A90D9" />
          <Bar dataKey="mujeres_pct" name="Mujeres" fill="#E74C3C" />
        </BarChart>
      </ResponsiveContainer>

      {/* Summary text */}
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
        La poblacion del pueblo <strong>{displayName}</strong> se distribuye asi:{' '}
        <span style={{ color: '#4A90D9', fontWeight: 700 }}>{fmt(total_hombres)}</span> son hombres ({pctH}%) y{' '}
        <span style={{ color: '#E74C3C', fontWeight: 700 }}>{fmt(total_mujeres)}</span> son mujeres ({pctM}%).
        {' '}Total: <strong>{fmt(total)}</strong> personas.
      </div>

      {/* Grandes grupos de edad */}
      {!compact && (
        <div style={{ marginTop: '16px' }}>
          <div style={{
            fontSize: '0.82rem',
            fontWeight: 600,
            textTransform: 'uppercase',
            letterSpacing: '0.4px',
            color: 'var(--color-gray-500)',
            marginBottom: '8px',
          }}>
            Grandes grupos de edad
          </div>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <th style={tblHead}>Grupo</th>
                <th style={{ ...tblHead, textAlign: 'right' }}>Hombres</th>
                <th style={{ ...tblHead, textAlign: 'right' }}>Mujeres</th>
                <th style={{ ...tblHead, textAlign: 'right' }}>% Hombres</th>
                <th style={{ ...tblHead, textAlign: 'right' }}>% Mujeres</th>
                <th style={{ ...tblHead, textAlign: 'right' }}>Total</th>
              </tr>
            </thead>
            <tbody>
              {[
                { label: '0-14 anos', data: gInfantil },
                { label: '15-64 anos', data: gAdulto },
                { label: '65+ anos', data: gMayor },
              ].map((g, i) => {
                const groupTotal = g.data.h + g.data.m;
                return (
                  <tr key={i} style={{ background: i % 2 === 0 ? '#fff' : '#f9fafb' }}>
                    <td style={{ ...tblCell, fontWeight: 600 }}>{g.label}</td>
                    <td style={{ ...tblCell, textAlign: 'right', color: '#4A90D9', fontWeight: 600 }}>{fmt(g.data.h)}</td>
                    <td style={{ ...tblCell, textAlign: 'right', color: '#E74C3C', fontWeight: 600 }}>{fmt(g.data.m)}</td>
                    <td style={{ ...tblCell, textAlign: 'right' }}>{pctOfGroup(g.data.h, groupTotal)}%</td>
                    <td style={{ ...tblCell, textAlign: 'right' }}>{pctOfGroup(g.data.m, groupTotal)}%</td>
                    <td style={{ ...tblCell, textAlign: 'right', fontWeight: 600 }}>{fmt(groupTotal)}</td>
                  </tr>
                );
              })}
              <tr style={{ background: '#f0f9ff', fontWeight: 700 }}>
                <td style={tblCell}>Total</td>
                <td style={{ ...tblCell, textAlign: 'right', color: '#4A90D9' }}>{fmt(total_hombres)}</td>
                <td style={{ ...tblCell, textAlign: 'right', color: '#E74C3C' }}>{fmt(total_mujeres)}</td>
                <td style={{ ...tblCell, textAlign: 'right' }}>{pctH}%</td>
                <td style={{ ...tblCell, textAlign: 'right' }}>{pctM}%</td>
                <td style={{ ...tblCell, textAlign: 'right' }}>{fmt(total)}</td>
              </tr>
            </tbody>
          </table>
        </div>
      )}

      {/* Demographic indices */}
      {!compact && (
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          gap: '32px',
          flexWrap: 'wrap',
          marginTop: '16px',
          padding: '12px 20px',
          background: '#f0f9ff',
          borderRadius: 'var(--radius-sm)',
          fontSize: '0.82rem',
          color: 'var(--color-gray-600)',
        }}>
          <span>
            <strong>Razon de masculinidad:</strong>{' '}
            <span style={{ fontWeight: 700, color: 'var(--color-primary)' }}>
              {razon_masculinidad != null ? razon_masculinidad.toFixed(1) : 'N/D'}
            </span>
          </span>
          <span>
            <strong>Indice de dependencia:</strong>{' '}
            <span style={{ fontWeight: 700, color: 'var(--color-gold)' }}>
              {indice_dependencia != null ? indice_dependencia.toFixed(1) : 'N/D'}
            </span>
          </span>
          <span>
            <strong>Indice de envejecimiento:</strong>{' '}
            <span style={{ fontWeight: 700, color: '#991b1b' }}>
              {indice_envejecimiento != null ? indice_envejecimiento.toFixed(1) : 'N/D'}
            </span>
          </span>
        </div>
      )}
    </div>
  );
}
