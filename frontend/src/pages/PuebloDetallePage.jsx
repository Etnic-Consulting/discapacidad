/* ============================================
   SMT-ONIC v2.0 — Pueblo Detalle Page (Ficha)
   Datos reales desde API para todos los tabs.
   ============================================ */

import { useState, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ReferenceLine,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  PieChart, Pie, Cell, ResponsiveContainer,
} from 'recharts';
import KPICard from '../components/KPICard';
import { usePerfilPueblo, useTerritoriosPueblo, useVictimasPueblo, usePerfilDemografico, usePiramideDemografica, usePiramideCapDiversas, usePiramideTipoDisc, useResguardosPorPueblo } from '../hooks/useApi';

const NACIONAL_PREVALENCIA = 60.0;

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

const actionBtnStyle = {
  padding: '7px 18px',
  border: 'none',
  borderRadius: 'var(--radius-sm)',
  fontSize: '0.82rem',
  fontWeight: 600,
  fontFamily: 'var(--font-body)',
  cursor: 'pointer',
  transition: 'background 0.15s',
};

function fmt(n) {
  return new Intl.NumberFormat('es-CO').format(n);
}

function ConfiabilidadBadge({ nivel }) {
  const config = {
    ALTA: { bg: '#dcfce7', color: '#166534', label: 'Alta' },
    MEDIA: { bg: '#fef9c3', color: '#854d0e', label: 'Media' },
    BAJA: { bg: '#fee2e2', color: '#991b1b', label: 'Baja' },
  };
  const c = config[nivel] || config.MEDIA;
  return (
    <span style={{
      display: 'inline-block',
      padding: '3px 12px',
      borderRadius: '12px',
      fontSize: '0.75rem',
      fontWeight: 600,
      background: c.bg,
      color: c.color,
    }}>
      Confiabilidad: {c.label}
    </span>
  );
}

function LoadingTab() {
  return (
    <div className="loading-container" style={{ padding: '40px 20px' }}>
      <div className="spinner" />
      <span>Cargando datos...</span>
    </div>
  );
}

function ErrorTab({ message }) {
  return (
    <div style={{ ...cardStyle, textAlign: 'center', padding: '40px 20px', color: 'var(--color-gray-400)' }}>
      <p>{message || 'Error cargando datos para esta seccion.'}</p>
    </div>
  );
}

/* ---- Reusable: Population Pyramid — DANE Visor style (percentages) ---- */
function PopulationPyramid({ piramideData, nombrePueblo, compact = false }) {
  if (!piramideData || !piramideData.piramide || piramideData.piramide.length === 0) {
    return <ErrorTab message="No hay datos de piramide poblacional disponibles." />;
  }

  const { piramide, total, total_hombres, total_mujeres, razon_masculinidad, indice_dependencia, indice_envejecimiento, pueblo } = piramideData;
  const displayName = nombrePueblo || pueblo || '';
  const pctH = total > 0 ? ((total_hombres / total) * 100).toFixed(1) : '0.0';
  const pctM = total > 0 ? ((total_mujeres / total) * 100).toFixed(1) : '0.0';

  // Build data using absolute counts (Recharts v3 domain calc works better this way)
  // REVERSE: Recharts layout=vertical pinta [0] arriba. 85+ debe estar arriba, 0-4 abajo.
  const pctData = piramide.map((row) => {
    const hAbs = row.hombres_abs || Math.abs(row.hombres || 0);
    const mAbs = row.mujeres_abs || Math.abs(row.mujeres || 0);
    const pctH = row.pct_hombres || (total > 0 ? (hAbs / total) * 100 : 0);
    const pctM = row.pct_mujeres || (total > 0 ? (mAbs / total) * 100 : 0);
    return {
      grupo_edad: row.grupo_edad,
      hombres_pct: -hAbs,
      mujeres_pct: mAbs,
      hombres_abs: hAbs,
      mujeres_abs: mAbs,
      pct_hombres_raw: pctH,
      pct_mujeres_raw: pctM,
    };
  }).slice().reverse();

  // Symmetric axis based on max absolute value
  const maxAbs = Math.max(
    ...pctData.map((r) => Math.max(Math.abs(r.hombres_pct), Math.abs(r.mujeres_pct)))
  );
  // Round up to a nice number
  const magnitude = Math.pow(10, Math.floor(Math.log10(maxAbs)));
  const axisBound = Math.ceil(maxAbs / magnitude) * magnitude;

  // Grandes grupos de edad
  const gruposInfantil = ['0-4', '5-9', '10-14'];
  const gruposAdulto = ['15-19', '20-24', '25-29', '30-34', '35-39', '40-44', '45-49', '50-54', '55-59', '60-64'];
  const gruposMayor = ['65-69', '70-74', '75-79', '80-84', '85 y mas', '85+'];

  const sumGrupo = (gruposEdad) => {
    let h = 0, m = 0;
    piramide.forEach((row) => {
      if (gruposEdad.includes(row.grupo_edad)) {
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
        {!compact && <span style={{ fontWeight: 400, fontSize: '0.82rem', color: 'var(--color-gray-500)' }}> -- CNPV 2018</span>}
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
              if (abs >= 1000) return (abs/1000).toFixed(abs >= 10000 ? 0 : 1) + 'K';
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
                  <div style={{ fontWeight: 700, marginBottom: '4px', color: '#374151' }}>Grupo: {label}</div>
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

      {/* Summary text — DANE style */}
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

      {/* Grandes grupos de edad — DANE style table */}
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

      {/* Demographic indices — DANE style */}
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

/* ---- Tab: Perfil ---- */
function TabPerfil({ perfil, codPueblo, nombrePueblo }) {
  const { data: piramideData, isLoading: pirLoading } = usePiramideDemografica(codPueblo);
  const { data: piramideDiscData, isLoading: pirDiscLoading } = usePiramideCapDiversas(codPueblo);
  const hasPyramidDisc = !pirDiscLoading && piramideDiscData && piramideDiscData.piramide && piramideDiscData.piramide.length > 0;
  const { data: piramideTipoData, isLoading: pirTipoLoading } = usePiramideTipoDisc(codPueblo);
  const hasPyramidTipo = !pirTipoLoading && piramideTipoData && piramideTipoData.piramide && piramideTipoData.piramide.length > 0;

  const dificultades = perfil.limitaciones
    ? perfil.limitaciones.map((l) => ({ dificultad: l.limitacion, value: l.valor }))
    : [];

  const sexoData = perfil.sexo
    ? [
        { name: 'Hombres', value: perfil.sexo.hombres, color: '#02432D' },
        { name: 'Mujeres', value: perfil.sexo.mujeres, color: '#C4920A' },
      ]
    : [];

  const hasPyramid = !pirLoading && piramideData && piramideData.piramide && piramideData.piramide.length > 0;

  if (dificultades.length === 0 && sexoData.length === 0 && !hasPyramid && !pirLoading) {
    return <ErrorTab message="No hay datos de perfil disponibles para este pueblo." />;
  }

  return (
    <div>
      <div className="grid-row grid-2">
        {/* Radar: Limitaciones funcionales */}
        {dificultades.length > 0 && (
          <div style={cardStyle}>
            <div style={chartTitle}>Limitaciones funcionales (Washington Group)</div>
            <ResponsiveContainer width="100%" height={300}>
              <RadarChart data={dificultades} cx="50%" cy="50%" outerRadius="70%">
                <PolarGrid stroke="#e8e8e8" />
                <PolarAngleAxis dataKey="dificultad" tick={{ fontSize: 11 }} />
                <PolarRadiusAxis tick={{ fontSize: 10 }} />
                <Radar
                  name="Personas"
                  dataKey="value"
                  stroke="#02432D"
                  fill="#02AB44"
                  fillOpacity={0.3}
                />
                <Tooltip formatter={(v) => [fmt(v), 'Personas']} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Pie: Sexo (capacidades diversas) */}
        {sexoData.length > 0 && (
          <div style={cardStyle}>
            <div style={chartTitle}>Distribucion por sexo (capacidades diversas)</div>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={sexoData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  innerRadius={40}
                  outerRadius={85}
                  label={({ name, value }) => `${name}: ${fmt(value)}`}
                >
                  {sexoData.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip formatter={(v) => [fmt(v), 'Personas']} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Professional Population Pyramid */}
      <div style={{ ...cardStyle, marginTop: '20px' }}>
        <div style={chartTitle}>Piramide poblacional por sexo y grupo quinquenal de edad</div>
        {pirLoading ? (
          <div className="loading-container" style={{ padding: '40px 20px' }}>
            <div className="spinner" />
            <span>Cargando piramide poblacional...</span>
          </div>
        ) : hasPyramid ? (
          <PopulationPyramid piramideData={piramideData} nombrePueblo={nombrePueblo} />
        ) : (
          <div style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--color-gray-400)' }}>
            No se encontraron datos de piramide poblacional para este pueblo.
          </div>
        )}
      </div>

      {/* SECOND PYRAMID: Persons WITH capacidades diversas only */}
      <div style={{ ...cardStyle, marginTop: '20px' }}>
        <div style={chartTitle}>Piramide de personas CON capacidades diversas por sexo y edad</div>
        <div style={{ fontSize: '0.78rem', color: 'var(--color-gray-500)', marginBottom: '12px' }}>
          Solo incluye personas que reportaron alguna dificultad en su vida diaria (CNPV 2018)
        </div>
        {pirDiscLoading ? (
          <div className="loading-container" style={{ padding: '40px 20px' }}>
            <div className="spinner" />
            <span>Cargando piramide de capacidades diversas...</span>
          </div>
        ) : hasPyramidDisc ? (
          <PopulationPyramid piramideData={piramideDiscData} nombrePueblo={`${nombrePueblo} (cap. diversas)`} />
        ) : (
          <div style={{ textAlign: 'center', padding: '30px 20px', color: 'var(--color-gray-400)', fontSize: '0.85rem' }}>
            Datos de piramide de capacidades diversas en proceso de extraccion desde REDATAM.
          </div>
        )}
      </div>

      {/* THIRD PYRAMID: Stacked by disability type */}
      <div style={{ ...cardStyle, marginTop: '20px' }}>
        <div style={chartTitle}>Piramide por TIPO de capacidad diversa, sexo y edad</div>
        <div style={{ fontSize: '0.78rem', color: 'var(--color-gray-500)', marginBottom: '12px' }}>
          Cada barra muestra la proporcion de cada tipo de limitacion. Hombres a la izquierda, mujeres a la derecha.
        </div>
        {pirTipoLoading ? (
          <div className="loading-container" style={{ padding: '40px 20px' }}>
            <div className="spinner" />
            <span>Cargando datos por tipo de limitacion...</span>
          </div>
        ) : hasPyramidTipo ? (
          <StackedTypePyramid data={piramideTipoData} nombrePueblo={nombrePueblo} />
        ) : (
          <div style={{ textAlign: 'center', padding: '30px 20px', color: 'var(--color-gray-400)', fontSize: '0.85rem' }}>
            Datos por tipo de limitacion disponibles para los 30 pueblos mas grandes.
          </div>
        )}
      </div>
    </div>
  );
}

/* ---- Stacked Type Pyramid Component ---- */
/* Colorblind-safe qualitative palette (ColorBrewer) */
const TIPO_COLORS = {
  'Ver': '#e41a1c',
  'Caminar': '#377eb8',
  'Oir': '#4daf4a',
  'Aprender': '#984ea3',
  'Hablar': '#ff7f00',
  'Actividades diarias': '#a65628',
  'Autocuidado': '#f781bf',
  'Agarrar': '#999999',
  'Relacionarse': '#dede00',
};

function StackedTypePyramid({ data, nombrePueblo }) {
  const { resumen_tipos, piramide, total } = data;

  // Sort tipos by total descending (most frequent first) - ALWAYS same order
  const tiposOrdenados = [...resumen_tipos].sort((a, b) => b.total - a.total).map(t => t.tipo);

  // Build chart data using absolute counts (Recharts v3 handles absolutes better than %)
  const chartData = [...piramide].reverse().map(row => {
    const entry = { grupo_edad: row.grupo_edad };
    tiposOrdenados.forEach(tipo => {
      const hAbs = Math.abs(row[`h_${tipo}`] || 0);
      const mAbs = row[`m_${tipo}`] || row[`abs_m_${tipo}`] || 0;
      entry[`h_${tipo}`] = -hAbs;
      entry[`m_${tipo}`] = mAbs;
      entry[`abs_h_${tipo}`] = hAbs;
      entry[`abs_m_${tipo}`] = mAbs;
    });
    entry['total_h'] = Math.abs(row.total_h || 0);
    entry['total_m'] = row.total_m || 0;
    return entry;
  });

  // Find max total (summed over tipos) per side for symmetric axis
  const maxAbs = Math.max(
    ...chartData.map(r => tiposOrdenados.reduce((s, t) => s + Math.abs(r[`h_${t}`] || 0), 0)),
    ...chartData.map(r => tiposOrdenados.reduce((s, t) => s + (r[`m_${t}`] || 0), 0)),
  );
  const magnitude = Math.pow(10, Math.floor(Math.log10(Math.max(maxAbs, 1))));
  const axisBound = Math.ceil(maxAbs / magnitude) * magnitude;

  return (
    <div>
      {/* Legend: ordered by frequency (most frequent first) */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px', justifyContent: 'center', marginBottom: '16px' }}>
        {tiposOrdenados.map(tipo => {
          const t = resumen_tipos.find(r => r.tipo === tipo);
          return (
            <div key={tipo} style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '0.78rem' }}>
              <div style={{ width: '14px', height: '14px', borderRadius: '2px', background: TIPO_COLORS[tipo] || '#999' }} />
              <span style={{ fontWeight: 600 }}>{tipo}</span>
              <span style={{ color: 'var(--color-gray-500)' }}>({t?.pct || 0}%)</span>
            </div>
          );
        })}
      </div>

      {/* Header: same style as other pyramids */}
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
              if (abs >= 1000) return (abs/1000).toFixed(abs >= 10000 ? 0 : 1) + 'K';
              return abs.toString();
            }}
            tick={{ fontSize: 11 }}
            axisLine={{ stroke: '#999' }}
          />
          <YAxis type="category" dataKey="grupo_edad" width={50} tick={{ fontSize: 11, fontWeight: 600 }} axisLine={false} tickLine={false} />
          <ReferenceLine x={0} stroke="#333" strokeWidth={2} />
          <Tooltip
            content={({ active, payload, label }) => {
              if (!active || !payload || !payload.length) return null;
              const row = chartData.find(r => r.grupo_edad === label) || {};
              // Build tooltip items sorted by total (h+m) descending
              const items = tiposOrdenados.map(tipo => ({
                tipo,
                h: row[`abs_h_${tipo}`] || 0,
                m: row[`abs_m_${tipo}`] || 0,
                total: (row[`abs_h_${tipo}`] || 0) + (row[`abs_m_${tipo}`] || 0),
              })).filter(x => x.total > 0).sort((a, b) => b.total - a.total);

              return (
                <div style={{ background: '#fff', border: '1px solid #ddd', borderRadius: '6px', padding: '10px 14px', fontSize: '0.8rem', maxWidth: '320px', boxShadow: '0 2px 8px rgba(0,0,0,0.15)' }}>
                  <div style={{ fontWeight: 700, marginBottom: '6px', borderBottom: '1px solid #eee', paddingBottom: '4px' }}>{label} anos</div>
                  {items.map(({ tipo, h, m, total: t }) => (
                    <div key={tipo} style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '3px' }}>
                      <div style={{ width: '10px', height: '10px', borderRadius: '2px', background: TIPO_COLORS[tipo] || '#999', flexShrink: 0 }} />
                      <span style={{ flex: 1, fontWeight: 500 }}>{tipo}</span>
                      <span style={{ color: '#4A90D9' }}>H:{h.toLocaleString()}</span>
                      <span style={{ color: '#E74C3C' }}>M:{m.toLocaleString()}</span>
                      <span style={{ fontWeight: 700 }}>{t.toLocaleString()}</span>
                    </div>
                  ))}
                  <div style={{ borderTop: '1px solid #eee', marginTop: '4px', paddingTop: '4px', fontWeight: 600, display: 'flex', justifyContent: 'space-between' }}>
                    <span>Total:</span>
                    <span style={{ color: '#4A90D9' }}>H:{(row.total_h||0).toLocaleString()}</span>
                    <span style={{ color: '#E74C3C' }}>M:{(row.total_m||0).toLocaleString()}</span>
                    <span>{((row.total_h||0)+(row.total_m||0)).toLocaleString()}</span>
                  </div>
                </div>
              );
            }}
          />
          {/* Stacked bars: hombres (negative/left) - ordered by frequency */}
          {tiposOrdenados.map(tipo => (
            <Bar key={`h_${tipo}`} dataKey={`h_${tipo}`} name={`H-${tipo}`} fill={TIPO_COLORS[tipo] || '#999'} stackId="hombres" />
          ))}
          {/* Stacked bars: mujeres (positive/right) - same order */}
          {tiposOrdenados.map(tipo => (
            <Bar key={`m_${tipo}`} dataKey={`m_${tipo}`} name={`M-${tipo}`} fill={TIPO_COLORS[tipo] || '#999'} stackId="mujeres" />
          ))}
        </BarChart>
      </ResponsiveContainer>

      {/* Summary table */}
      <div style={{ marginTop: '16px' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
          <thead>
            <tr style={{ background: 'var(--color-gray-100)' }}>
              <th style={{ padding: '6px 10px', textAlign: 'left', borderBottom: '2px solid var(--color-gray-200)' }}>Tipo de limitacion</th>
              <th style={{ padding: '6px 10px', textAlign: 'right', borderBottom: '2px solid var(--color-gray-200)' }}>Hombres</th>
              <th style={{ padding: '6px 10px', textAlign: 'right', borderBottom: '2px solid var(--color-gray-200)' }}>Mujeres</th>
              <th style={{ padding: '6px 10px', textAlign: 'right', borderBottom: '2px solid var(--color-gray-200)' }}>Total</th>
              <th style={{ padding: '6px 10px', textAlign: 'right', borderBottom: '2px solid var(--color-gray-200)' }}>%</th>
            </tr>
          </thead>
          <tbody>
            {resumen_tipos.map(t => (
              <tr key={t.tipo} style={{ borderBottom: '1px solid var(--color-gray-200)' }}>
                <td style={{ padding: '5px 10px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <div style={{ width: '12px', height: '12px', borderRadius: '2px', background: TIPO_COLORS[t.tipo] || '#999' }} />
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

      <div style={{ textAlign: 'center', marginTop: '12px', fontSize: '0.78rem', color: 'var(--color-gray-500)' }}>
        Total personas con capacidades diversas: {total.toLocaleString()} | Fuente: CNPV 2018 via REDATAM
      </div>
    </div>
  );
}

/* ---- Tab: Territorios ---- */
function TabTerritorios({ codPueblo, nombrePueblo }) {
  const { data: terData, isLoading, isError } = useTerritoriosPueblo(codPueblo);
  const { data: resgData, isLoading: loadingResg } = useResguardosPorPueblo(codPueblo);

  if (isLoading) return <LoadingTab />;
  if (isError) return <ErrorTab message="Error cargando datos territoriales." />;

  const departamentos = terData?.data || [];
  const resguardosList = resgData?.data || [];
  if (departamentos.length === 0) {
    return <ErrorTab message="No se encontraron datos territoriales para este pueblo." />;
  }

  return (
    <>
    <div className="grid-row grid-2">
      <div style={cardStyle}>
        <div style={chartTitle}>Departamentos donde habita el pueblo {nombrePueblo}</div>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.88rem' }}>
          <thead>
            <tr>
              {['Departamento', 'Poblacion', 'Con cap. diversas', 'Prevalencia', 'Confiabilidad'].map(
                (h) => (
                  <th
                    key={h}
                    style={{
                      padding: '10px 16px',
                      textAlign: 'left',
                      fontWeight: 600,
                      fontSize: '0.78rem',
                      textTransform: 'uppercase',
                      color: 'var(--color-gray-500)',
                      background: 'var(--color-gray-100)',
                      borderBottom: '2px solid var(--color-gray-200)',
                    }}
                  >
                    {h}
                  </th>
                )
              )}
            </tr>
          </thead>
          <tbody>
            {departamentos.map((d, i) => (
              <tr
                key={i}
                style={{ background: i % 2 === 0 ? '#fff' : 'var(--color-gray-100)' }}
              >
                <td style={{ padding: '10px 16px', borderBottom: '1px solid var(--color-gray-200)' }}>
                  {d.nom_dpto || d.cod_dpto}
                </td>
                <td style={{ padding: '10px 16px', borderBottom: '1px solid var(--color-gray-200)' }}>
                  {fmt(d.total || 0)}
                </td>
                <td style={{ padding: '10px 16px', borderBottom: '1px solid var(--color-gray-200)' }}>
                  {fmt(d.con_discapacidad || 0)}
                </td>
                <td style={{ padding: '10px 16px', borderBottom: '1px solid var(--color-gray-200)' }}>
                  {d.tasa_x_1000 != null ? (
                    <span
                      style={{
                        fontWeight: 600,
                        color:
                          d.tasa_x_1000 > 100
                            ? 'var(--color-red)'
                            : d.tasa_x_1000 > 60
                            ? 'var(--color-gold)'
                            : 'var(--color-green-mid)',
                      }}
                    >
                      {Number(d.tasa_x_1000).toFixed(1)}{'\u2030'}
                    </span>
                  ) : (
                    <span style={{ color: 'var(--color-gray-400)', fontSize: '0.82rem' }}>N/D (n&lt;30)</span>
                  )}
                </td>
                <td style={{ padding: '10px 16px', borderBottom: '1px solid var(--color-gray-200)' }}>
                  <span style={{
                    display: 'inline-block',
                    padding: '2px 10px',
                    borderRadius: '12px',
                    fontSize: '0.72rem',
                    fontWeight: 600,
                    background: d.confiabilidad === 'CONFIABLE' ? '#dcfce7' : '#fee2e2',
                    color: d.confiabilidad === 'CONFIABLE' ? '#166534' : '#991b1b',
                  }}>
                    {d.confiabilidad === 'CONFIABLE' ? 'Confiable' : 'No confiable'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Presence summary panel */}
      <div style={{
        ...cardStyle,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '300px',
      }}>
        <div style={chartTitle}>Presencia territorial</div>
        <div style={{
          width: '100%',
          flex: 1,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'var(--color-gray-100)',
          borderRadius: 'var(--radius-sm)',
          border: '2px dashed var(--color-gray-300)',
          padding: '20px',
          textAlign: 'center',
        }}>
          <div>
            <div style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--color-primary)', fontFamily: 'var(--font-heading)' }}>
              {departamentos.length}
            </div>
            <div style={{ fontSize: '0.9rem', color: 'var(--color-gray-500)', marginBottom: '12px' }}>
              departamento{departamentos.length !== 1 ? 's' : ''} con presencia del pueblo {nombrePueblo}
            </div>
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', justifyContent: 'center', marginTop: '12px' }}>
              {departamentos.map((d, i) => (
                <span key={i} style={{
                  padding: '4px 12px',
                  borderRadius: '12px',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  background: 'var(--color-green-light)',
                  color: 'var(--color-green-mid)',
                }}>
                  {d.nom_dpto || d.cod_dpto}
                </span>
              ))}
            </div>
            <Link
              to={`/territorios?pueblo=${codPueblo}`}
              style={{
                display: 'inline-block',
                marginTop: '16px',
                padding: '6px 16px',
                background: 'var(--color-green-mid)',
                color: '#fff',
                borderRadius: 'var(--radius-sm)',
                fontSize: '0.82rem',
                fontWeight: 600,
              }}
            >
              Ver en mapa interactivo
            </Link>
          </div>
        </div>
      </div>
    </div>

      {/* Resguardos where this pueblo is present */}
      {loadingResg && (
        <div style={{ ...cardStyle, marginTop: '20px', padding: '20px', textAlign: 'center' }}>
          <div className="spinner" style={{ display: 'inline-block', marginRight: '8px' }} />
          Cargando resguardos...
        </div>
      )}
      {!loadingResg && resguardosList.length > 0 && (
        <div style={{ ...cardStyle, marginTop: '20px' }}>
          <div style={chartTitle}>Resguardos donde habita el pueblo {nombrePueblo} ({resguardosList.length})</div>
          <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
              <thead>
                <tr>
                  {['Resguardo', 'Departamento', 'Municipio', 'Poblacion', 'Organizacion'].map((h) => (
                    <th
                      key={h}
                      style={{
                        padding: '8px 12px',
                        textAlign: h === 'Poblacion' ? 'right' : 'left',
                        fontWeight: 600,
                        fontSize: '0.75rem',
                        textTransform: 'uppercase',
                        color: 'var(--color-gray-500)',
                        background: 'var(--color-gray-100)',
                        borderBottom: '2px solid var(--color-gray-200)',
                        position: 'sticky',
                        top: 0,
                      }}
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {resguardosList.map((r, i) => (
                  <tr key={r.cod_resguardo || i} style={{ background: i % 2 === 0 ? '#fff' : 'var(--color-gray-100)' }}>
                    <td style={{ padding: '8px 12px', borderBottom: '1px solid var(--color-gray-200)', fontWeight: 500 }}>
                      {r.territorio || r.nombre_resguardo || '--'}
                    </td>
                    <td style={{ padding: '8px 12px', borderBottom: '1px solid var(--color-gray-200)' }}>
                      {r.departamento || '--'}
                    </td>
                    <td style={{ padding: '8px 12px', borderBottom: '1px solid var(--color-gray-200)' }}>
                      {r.municipio || '--'}
                    </td>
                    <td style={{ padding: '8px 12px', borderBottom: '1px solid var(--color-gray-200)', textAlign: 'right' }}>
                      {fmt(r.poblacion || 0)}
                    </td>
                    <td style={{ padding: '8px 12px', borderBottom: '1px solid var(--color-gray-200)' }}>
                      {r.organizacion || '--'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </>
  );
}

/* ---- Tab: Salud ---- */
function TabSalud({ perfil }) {
  const tratamientoData = perfil.tratamiento
    ? perfil.tratamiento.map((t) => ({ categoria: t.tratamiento, valor: t.valor }))
    : [];

  const causasData = perfil.causas
    ? perfil.causas.map((c) => ({ causa: c.causa, valor: c.valor }))
    : [];

  const enfermedad = perfil.enfermedad;

  // Enfermedad pie chart data
  const enfermedadPieData = enfermedad
    ? [
        { name: 'Reportaron enfermedad', value: enfermedad.enfermo_si || 0, color: '#E8262A' },
        { name: 'Sin enfermedad', value: enfermedad.enfermo_no || 0, color: '#02AB44' },
        ...(enfermedad.no_informa > 0
          ? [{ name: 'No informa', value: enfermedad.no_informa, color: '#9ca3af' }]
          : []),
      ].filter((d) => d.value > 0)
    : [];

  if (tratamientoData.length === 0 && causasData.length === 0 && !enfermedad) {
    return <ErrorTab message="No hay datos de salud disponibles para este pueblo." />;
  }

  return (
    <div>
      <div className="grid-row grid-2">
        {/* Tratamiento buscado - bar chart */}
        {tratamientoData.length > 0 && (
          <div style={cardStyle}>
            <div style={chartTitle}>Tratamiento buscado</div>
            <ResponsiveContainer width="100%" height={Math.max(250, tratamientoData.length * 40)}>
              <BarChart
                data={tratamientoData}
                layout="vertical"
                margin={{ top: 10, right: 30, bottom: 5, left: 140 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#e8e8e8" />
                <XAxis type="number" tick={{ fontSize: 11 }} />
                <YAxis type="category" dataKey="categoria" tick={{ fontSize: 11 }} width={130} />
                <Tooltip formatter={(v) => [fmt(v), 'Personas']} />
                <Bar dataKey="valor" fill="#02AB44" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Enfermedad reciente - pie chart */}
        {enfermedadPieData.length > 0 && (
          <div style={cardStyle}>
            <div style={chartTitle}>Enfermedad reciente</div>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={enfermedadPieData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  innerRadius={45}
                  outerRadius={85}
                  label={({ name, value }) => `${name}: ${fmt(value)}`}
                >
                  {enfermedadPieData.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip formatter={(v) => [fmt(v), 'Personas']} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
            {enfermedad && (
              <div style={{ textAlign: 'center', fontSize: '0.82rem', color: 'var(--color-gray-500)', marginTop: '8px' }}>
                Total: {fmt(enfermedad.total || 0)} personas con capacidades diversas
              </div>
            )}
          </div>
        )}
      </div>

      {/* Enfermedad summary cards */}
      {enfermedad && (
        <div style={{ ...cardStyle, marginTop: '20px' }}>
          <div style={chartTitle}>Detalle de enfermedad reciente</div>
          <div className="grid-row grid-3">
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--color-red)', fontFamily: 'var(--font-heading)' }}>
                {fmt(enfermedad.enfermo_si || 0)}
              </div>
              <div style={{ fontSize: '0.82rem', color: 'var(--color-gray-500)' }}>Reportaron enfermedad</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--color-green-mid)', fontFamily: 'var(--font-heading)' }}>
                {fmt(enfermedad.enfermo_no || 0)}
              </div>
              <div style={{ fontSize: '0.82rem', color: 'var(--color-gray-500)' }}>Sin enfermedad</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--color-gray-400)', fontFamily: 'var(--font-heading)' }}>
                {fmt(enfermedad.no_informa || 0)}
              </div>
              <div style={{ fontSize: '0.82rem', color: 'var(--color-gray-500)' }}>No informa</div>
            </div>
          </div>
        </div>
      )}

      {/* Causas de capacidades diversas - bar chart */}
      {causasData.length > 0 && (
        <div style={{ ...cardStyle, marginTop: '20px' }}>
          <div style={chartTitle}>Causas de capacidades diversas</div>
          <ResponsiveContainer width="100%" height={Math.max(200, causasData.length * 35)}>
            <BarChart
              data={causasData}
              layout="vertical"
              margin={{ top: 10, right: 30, bottom: 5, left: 160 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#e8e8e8" />
              <XAxis type="number" tick={{ fontSize: 11 }} />
              <YAxis type="category" dataKey="causa" tick={{ fontSize: 11 }} width={150} />
              <Tooltip formatter={(v) => [fmt(v), 'Personas']} />
              <Bar dataKey="valor" fill="#C4920A" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

/* ---- Tab: Conflicto ---- */
function TabConflicto({ codPueblo, nombrePueblo }) {
  const { data: vicData, isLoading, isError } = useVictimasPueblo(codPueblo);

  if (isLoading) return <LoadingTab />;
  if (isError) return <ErrorTab message="Error cargando datos de conflicto. Es posible que no existan datos de victimas para este pueblo." />;

  const rows = vicData?.data || [];
  if (rows.length === 0) {
    return <ErrorTab message={`No se encontraron datos de victimas para el pueblo ${nombrePueblo}.`} />;
  }

  // Aggregate by hecho (type of victimizing event)
  const hechoAgg = {};
  rows.forEach((r) => {
    const hecho = r.hecho || 'Sin clasificar';
    const cantidad = r.cantidad || r.eventos || 0;
    hechoAgg[hecho] = (hechoAgg[hecho] || 0) + cantidad;
  });

  const hechoData = Object.entries(hechoAgg)
    .map(([hecho, cantidad]) => ({ hecho, cantidad }))
    .sort((a, b) => b.cantidad - a.cantidad);

  const totalVictimas = hechoData.reduce((sum, h) => sum + h.cantidad, 0);

  // Aggregate by tipo_disc_limpia if available
  const tipoDiscAgg = {};
  rows.forEach((r) => {
    const tipo = r.tipo_disc_limpia || r.discapacidad;
    if (tipo) {
      const cantidad = r.cantidad || r.eventos || 0;
      tipoDiscAgg[tipo] = (tipoDiscAgg[tipo] || 0) + cantidad;
    }
  });
  const tipoDiscData = Object.entries(tipoDiscAgg)
    .map(([tipo, cantidad]) => ({ tipo, cantidad }))
    .sort((a, b) => b.cantidad - a.cantidad);

  return (
    <div>
      {/* Summary */}
      <div className="alert alert-info" style={{ marginBottom: '20px' }}>
        <strong>Fuente:</strong> {vicData?.fuente || 'RUV'} |{' '}
        <strong>Total registros:</strong> {fmt(totalVictimas)} eventos victimizantes para el pueblo {nombrePueblo}
      </div>

      <div className="grid-row grid-2">
        {/* Main chart: por hecho */}
        <div style={cardStyle}>
          <div style={chartTitle}>Victimas por hecho victimizante -- {nombrePueblo}</div>
          <ResponsiveContainer width="100%" height={Math.max(300, hechoData.length * 35)}>
            <BarChart
              data={hechoData}
              layout="vertical"
              margin={{ top: 10, right: 30, bottom: 5, left: 140 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#e8e8e8" />
              <XAxis type="number" tick={{ fontSize: 11 }} />
              <YAxis type="category" dataKey="hecho" tick={{ fontSize: 12 }} width={130} />
              <Tooltip formatter={(v) => [fmt(v), 'Victimas']} />
              <Bar dataKey="cantidad" fill="#E8262A" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* By tipo_disc if available */}
        {tipoDiscData.length > 0 ? (
          <div style={cardStyle}>
            <div style={chartTitle}>Por tipo de capacidad diversa</div>
            <ResponsiveContainer width="100%" height={Math.max(300, tipoDiscData.length * 40)}>
              <BarChart
                data={tipoDiscData}
                layout="vertical"
                margin={{ top: 10, right: 30, bottom: 5, left: 140 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#e8e8e8" />
                <XAxis type="number" tick={{ fontSize: 11 }} />
                <YAxis type="category" dataKey="tipo" tick={{ fontSize: 11 }} width={130} />
                <Tooltip formatter={(v) => [fmt(v), 'Victimas']} />
                <Bar dataKey="cantidad" fill="#C4920A" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div style={cardStyle}>
            <div style={chartTitle}>Detalle por hecho</div>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.88rem' }}>
                <thead>
                  <tr>
                    {['Hecho victimizante', 'Cantidad'].map((h) => (
                      <th key={h} style={{
                        padding: '10px 16px',
                        textAlign: 'left',
                        fontWeight: 600,
                        fontSize: '0.78rem',
                        textTransform: 'uppercase',
                        color: 'var(--color-gray-500)',
                        background: 'var(--color-gray-100)',
                        borderBottom: '2px solid var(--color-gray-200)',
                      }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {hechoData.map((d, i) => (
                    <tr key={i} style={{ background: i % 2 === 0 ? '#fff' : 'var(--color-gray-100)' }}>
                      <td style={{ padding: '10px 16px', borderBottom: '1px solid var(--color-gray-200)' }}>{d.hecho}</td>
                      <td style={{ padding: '10px 16px', borderBottom: '1px solid var(--color-gray-200)', fontWeight: 600 }}>{fmt(d.cantidad)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/* ---- Tab: Demografia (Visor DANE) ---- */
function nbiColor(val) {
  if (val == null) return 'var(--color-gray-400)';
  if (val < 30) return '#166534';
  if (val <= 60) return '#854d0e';
  return '#991b1b';
}

function nbiBg(val) {
  if (val == null) return '#f3f4f6';
  if (val < 30) return '#dcfce7';
  if (val <= 60) return '#fef9c3';
  return '#fee2e2';
}

function IndicatorCard({ label, value, suffix = '%', subtitle }) {
  const numVal = typeof value === 'number' ? value : parseFloat(value);
  return (
    <div style={{
      ...cardStyle,
      borderLeft: `4px solid ${nbiColor(numVal)}`,
      background: nbiBg(numVal),
      textAlign: 'center',
    }}>
      <div style={{ fontSize: '0.78rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.4px', color: 'var(--color-gray-500)', marginBottom: '6px' }}>
        {label}
      </div>
      <div style={{ fontSize: '1.6rem', fontWeight: 700, fontFamily: 'var(--font-heading)', color: nbiColor(numVal) }}>
        {value != null ? `${Number(value).toFixed(1)}${suffix}` : 'N/D'}
      </div>
      {subtitle && <div style={{ fontSize: '0.78rem', color: 'var(--color-gray-400)', marginTop: '4px' }}>{subtitle}</div>}
    </div>
  );
}

function LenguaBar({ pctHabla, pctNoHabla }) {
  const pctOtro = Math.max(0, 100 - (pctHabla || 0) - (pctNoHabla || 0));
  return (
    <div>
      <div style={{ display: 'flex', height: '28px', borderRadius: '6px', overflow: 'hidden', fontSize: '0.72rem', fontWeight: 600, color: '#fff' }}>
        {pctHabla > 0 && (
          <div style={{ width: `${pctHabla}%`, background: '#02AB44', display: 'flex', alignItems: 'center', justifyContent: 'center', minWidth: pctHabla > 5 ? 'auto' : '0' }}>
            {pctHabla > 8 ? `${Number(pctHabla).toFixed(0)}%` : ''}
          </div>
        )}
        {pctOtro > 0 && (
          <div style={{ width: `${pctOtro}%`, background: '#C4920A', display: 'flex', alignItems: 'center', justifyContent: 'center', minWidth: pctOtro > 5 ? 'auto' : '0' }}>
            {pctOtro > 8 ? `${Number(pctOtro).toFixed(0)}%` : ''}
          </div>
        )}
        {pctNoHabla > 0 && (
          <div style={{ width: `${pctNoHabla}%`, background: '#E8262A', display: 'flex', alignItems: 'center', justifyContent: 'center', minWidth: pctNoHabla > 5 ? 'auto' : '0' }}>
            {pctNoHabla > 8 ? `${Number(pctNoHabla).toFixed(0)}%` : ''}
          </div>
        )}
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '8px', fontSize: '0.78rem', color: 'var(--color-gray-500)' }}>
        <span><span style={{ display: 'inline-block', width: 10, height: 10, borderRadius: 2, background: '#02AB44', marginRight: 4 }} />Habla la lengua</span>
        <span><span style={{ display: 'inline-block', width: 10, height: 10, borderRadius: 2, background: '#C4920A', marginRight: 4 }} />Solo entiende / otro</span>
        <span><span style={{ display: 'inline-block', width: 10, height: 10, borderRadius: 2, background: '#E8262A', marginRight: 4 }} />No habla ni entiende</span>
      </div>
    </div>
  );
}

function TabDemografia({ codPueblo, nombrePueblo }) {
  const { data: demo, isLoading, isError } = usePerfilDemografico(codPueblo);
  const { data: piramideData, isLoading: pirLoading } = usePiramideDemografica(codPueblo);

  if (isLoading) return <LoadingTab />;
  if (isError) return <ErrorTab message="Error cargando datos demograficos. Es posible que no existan datos del Visor DANE para este pueblo." />;
  if (!demo) return <ErrorTab message="No hay datos demograficos disponibles." />;

  const pob = demo.poblacion || {};
  const nbi = demo.nbi || {};
  const lengua = demo.lengua || {};
  const edu = demo.educacion || {};
  const viv = demo.vivienda || {};
  const demog = demo.demografia || {};
  const capDiv = demo.capacidades_diversas || {};

  const hasPyramid = !pirLoading && piramideData && piramideData.piramide && piramideData.piramide.length > 0;

  return (
    <div>
      {/* Row 1: KPI indicators with color coding */}
      <div style={{ ...cardStyle, marginBottom: '20px' }}>
        <div style={chartTitle}>Indicadores clave</div>
        <div className="grid-row grid-4">
          <IndicatorCard label="NBI" value={nbi.pct_nbi} subtitle="% poblacion con NBI" />
          <IndicatorCard label="IPM" value={nbi.ipm} subtitle="Incidencia pobreza" />
          <IndicatorCard
            label="Alfabetismo"
            value={edu.tasa_alfabetismo}
            subtitle="Tasa de alfabetismo"
          />
          <IndicatorCard
            label="Lengua nativa"
            value={lengua.pct_habla}
            subtitle="% que habla la lengua"
          />
        </div>
      </div>

      {/* Row 2: Population comparison 2005 vs 2018 */}
      <div style={{ ...cardStyle, marginBottom: '20px' }}>
        <div style={chartTitle}>Poblacion intercensal</div>
        <div className="grid-row grid-3">
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '1.5rem', fontWeight: 700, fontFamily: 'var(--font-heading)', color: 'var(--color-gray-500)' }}>
              {pob.poblacion_2005 != null ? fmt(pob.poblacion_2005) : 'N/D'}
            </div>
            <div style={{ fontSize: '0.82rem', color: 'var(--color-gray-500)' }}>Censo 2005</div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '1.5rem', fontWeight: 700, fontFamily: 'var(--font-heading)', color: 'var(--color-primary)' }}>
              {pob.poblacion_2018 != null ? fmt(pob.poblacion_2018) : 'N/D'}
            </div>
            <div style={{ fontSize: '0.82rem', color: 'var(--color-gray-500)' }}>Censo 2018</div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '1.5rem', fontWeight: 700, fontFamily: 'var(--font-heading)', color: pob.tasa_crecimiento_pct >= 0 ? '#166534' : '#991b1b' }}>
              {pob.tasa_crecimiento_pct != null ? `${pob.tasa_crecimiento_pct >= 0 ? '+' : ''}${Number(pob.tasa_crecimiento_pct).toFixed(1)}%` : 'N/D'}
            </div>
            <div style={{ fontSize: '0.82rem', color: 'var(--color-gray-500)' }}>Crecimiento intercensal</div>
          </div>
        </div>
      </div>

      {/* Row 3: Professional Population Pyramid */}
      <div style={{ ...cardStyle, marginBottom: '20px' }}>
        <div style={chartTitle}>Piramide poblacional por sexo y grupo quinquenal de edad</div>
        {pirLoading ? (
          <div className="loading-container" style={{ padding: '40px 20px' }}>
            <div className="spinner" />
            <span>Cargando piramide poblacional...</span>
          </div>
        ) : hasPyramid ? (
          <PopulationPyramid piramideData={piramideData} nombrePueblo={nombrePueblo} />
        ) : (
          <div style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--color-gray-400)' }}>
            No se encontraron datos de piramide poblacional para este pueblo.
          </div>
        )}
      </div>

      <div className="grid-row grid-2">
        {/* Lengua */}
        <div style={cardStyle}>
          <div style={chartTitle}>Vitalidad linguistica</div>
          <LenguaBar pctHabla={lengua.pct_habla} pctNoHabla={lengua.pct_no_habla} />
          <div style={{ marginTop: '12px', fontSize: '0.85rem', color: 'var(--color-gray-500)' }}>
            <strong>{fmt(lengua.pob_habla || 0)}</strong> personas hablan la lengua propia
            {lengua.pct_habla != null && ` (${Number(lengua.pct_habla).toFixed(1)}%)`}
          </div>
        </div>

        {/* Educacion */}
        <div style={cardStyle}>
          <div style={chartTitle}>Educacion</div>
          <div style={{ textAlign: 'center', marginBottom: '12px' }}>
            <div style={{ fontSize: '2rem', fontWeight: 700, fontFamily: 'var(--font-heading)', color: nbiColor(edu.tasa_alfabetismo != null ? 100 - edu.tasa_alfabetismo : null) }}>
              {edu.tasa_alfabetismo != null ? `${Number(edu.tasa_alfabetismo).toFixed(1)}%` : 'N/D'}
            </div>
            <div style={{ fontSize: '0.82rem', color: 'var(--color-gray-500)' }}>Tasa de alfabetismo</div>
          </div>
          <div style={{ textAlign: 'center', fontSize: '0.82rem', color: 'var(--color-gray-400)' }}>
            {nbi.pct_miseria != null && (
              <span>Miseria: <strong style={{ color: nbiColor(nbi.pct_miseria) }}>{Number(nbi.pct_miseria).toFixed(1)}%</strong></span>
            )}
          </div>
        </div>
      </div>

      <div className="grid-row grid-2" style={{ marginTop: '20px' }}>
        {/* Vivienda */}
        <div style={cardStyle}>
          <div style={chartTitle}>Condiciones de vivienda</div>
          <div className="grid-row grid-2">
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '1.5rem', fontWeight: 700, fontFamily: 'var(--font-heading)', color: 'var(--color-primary)' }}>
                {viv.pct_vivienda_tradicional != null ? `${Number(viv.pct_vivienda_tradicional).toFixed(1)}%` : 'N/D'}
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--color-gray-500)' }}>Vivienda tradicional indigena</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '1.5rem', fontWeight: 700, fontFamily: 'var(--font-heading)', color: nbiColor(viv.pct_sin_acueducto) }}>
                {viv.pct_sin_acueducto != null ? `${Number(viv.pct_sin_acueducto).toFixed(1)}%` : 'N/D'}
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--color-gray-500)' }}>Sin acceso a acueducto</div>
            </div>
          </div>
        </div>

        {/* Indices demograficos */}
        <div style={cardStyle}>
          <div style={chartTitle}>Indices demograficos</div>
          <div className="grid-row grid-3">
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '1.3rem', fontWeight: 700, fontFamily: 'var(--font-heading)', color: 'var(--color-primary)' }}>
                {demog.indice_dependencia != null ? `${Number(demog.indice_dependencia).toFixed(1)}` : 'N/D'}
              </div>
              <div style={{ fontSize: '0.72rem', color: 'var(--color-gray-500)' }}>Indice de dependencia</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '1.3rem', fontWeight: 700, fontFamily: 'var(--font-heading)', color: 'var(--color-gold)' }}>
                {demog.indice_envejecimiento != null ? `${Number(demog.indice_envejecimiento).toFixed(1)}` : 'N/D'}
              </div>
              <div style={{ fontSize: '0.72rem', color: 'var(--color-gray-500)' }}>Indice de envejecimiento</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '1.3rem', fontWeight: 700, fontFamily: 'var(--font-heading)', color: 'var(--color-green-mid)' }}>
                {demog.indice_urbanizacion != null ? `${Number(demog.indice_urbanizacion).toFixed(1)}%` : 'N/D'}
              </div>
              <div style={{ fontSize: '0.72rem', color: 'var(--color-gray-500)' }}>Urbanizacion</div>
            </div>
          </div>
        </div>
      </div>

      {/* Capacidades diversas */}
      <div style={{ ...cardStyle, marginTop: '20px' }}>
        <div style={chartTitle}>Capacidades diversas (Visor DANE)</div>
        <div className="grid-row grid-3">
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '1.5rem', fontWeight: 700, fontFamily: 'var(--font-heading)', color: 'var(--color-gold)' }}>
              {capDiv.tasa_x_1000 != null ? `${Number(capDiv.tasa_x_1000).toFixed(1)}\u2030` : 'N/D'}
            </div>
            <div style={{ fontSize: '0.78rem', color: 'var(--color-gray-500)' }}>Tasa por mil hab.</div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '1.5rem', fontWeight: 700, fontFamily: 'var(--font-heading)', color: 'var(--color-green-mid)' }}>
              {capDiv.con_cap_diversas != null ? fmt(capDiv.con_cap_diversas) : 'N/D'}
            </div>
            <div style={{ fontSize: '0.78rem', color: 'var(--color-gray-500)' }}>Personas con cap. diversas</div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '1.5rem', fontWeight: 700, fontFamily: 'var(--font-heading)', color: 'var(--color-gray-500)' }}>
              {capDiv.total_evaluados != null ? fmt(capDiv.total_evaluados) : 'N/D'}
            </div>
            <div style={{ fontSize: '0.78rem', color: 'var(--color-gray-500)' }}>Total evaluados</div>
          </div>
        </div>
      </div>

      {/* ICV components */}
      {demo.icv_componentes && (
        <div style={{ ...cardStyle, marginTop: '20px' }}>
          <div style={chartTitle}>Indice Compuesto de Vulnerabilidad (ICV)</div>
          <div className="alert alert-info" style={{ marginBottom: '12px', fontSize: '0.82rem' }}>
            ICV = (tasa_cap_diversas_norm x 0.3) + (NBI_norm x 0.3) + (IPM_norm x 0.2) + (tasa_victimas_norm x 0.2).
            Consulte el ranking completo en el modulo de indicadores.
          </div>
          <div className="grid-row grid-3">
            <IndicatorCard label="NBI (componente)" value={demo.icv_componentes.pct_nbi} subtitle="Peso: 30%" />
            <IndicatorCard label="IPM (componente)" value={demo.icv_componentes.pct_ipm} subtitle="Peso: 20%" />
            <IndicatorCard
              label="Cap. diversas"
              value={demo.icv_componentes.tasa_cap_diversas}
              suffix={'\u2030'}
              subtitle="Peso: 30%"
            />
          </div>
        </div>
      )}
    </div>
  );
}

/* ============ MAIN COMPONENT ============ */
export default function PuebloDetallePage() {
  const { codPueblo } = useParams();
  const [activeTab, setActiveTab] = useState('perfil');
  const { data: apiPerfil, isLoading: perfilLoading, isError: perfilError } = usePerfilPueblo(codPueblo);

  // Derived perfil values from API
  const nombre = apiPerfil?.prevalencia?.pueblo ?? codPueblo ?? 'Pueblo';
  const poblacion = apiPerfil?.prevalencia?.total ?? 0;
  const conCapDiv = apiPerfil?.prevalencia?.con_discapacidad ?? 0;
  const prevalenciaNum = apiPerfil?.prevalencia?.tasa_x_1000 ?? 0;
  const confiabilidad = apiPerfil?.confiabilidad ?? 'MEDIA';

  const handlePrintPDF = useCallback(() => {
    window.print();
  }, []);

  const handleDownloadCSV = useCallback(() => {
    const lines = [
      'Campo,Valor',
      `Pueblo,${nombre}`,
      `Poblacion total,${poblacion}`,
      `Con capacidades diversas,${conCapDiv}`,
      `Prevalencia (x1000),${prevalenciaNum}`,
      `Confiabilidad,${confiabilidad}`,
    ];
    if (apiPerfil?.limitaciones) {
      lines.push('');
      lines.push('Limitacion,Personas');
      apiPerfil.limitaciones.forEach((l) => {
        lines.push(`${l.limitacion},${l.valor}`);
      });
    }
    if (apiPerfil?.piramide_edad) {
      lines.push('');
      lines.push('Grupo edad,Personas');
      apiPerfil.piramide_edad.forEach((e) => {
        lines.push(`${e.grupo_edad},${e.valor}`);
      });
    }
    if (apiPerfil?.causas) {
      lines.push('');
      lines.push('Causa,Personas');
      apiPerfil.causas.forEach((c) => {
        lines.push(`${c.causa},${c.valor}`);
      });
    }
    const csv = lines.join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ficha-${codPueblo}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }, [codPueblo, nombre, poblacion, conCapDiv, prevalenciaNum, confiabilidad, apiPerfil]);

  if (perfilError) return <div className="error-container"><p>Error cargando datos del pueblo</p></div>;

  const TABS = [
    { key: 'perfil', label: 'Perfil' },
    { key: 'demografia', label: 'Demografia' },
    { key: 'territorios', label: 'Territorios' },
    { key: 'salud', label: 'Salud' },
    { key: 'conflicto', label: 'Conflicto' },
  ];

  const prevNum = typeof prevalenciaNum === 'number' ? prevalenciaNum : parseFloat(prevalenciaNum) || 0;

  return (
    <div>
      {/* Breadcrumb */}
      <div style={{ fontSize: '0.85rem', marginBottom: '12px', color: 'var(--color-gray-500)' }}>
        <Link to="/pueblos" style={{ color: 'var(--color-green-mid)' }}>
          Pueblos Indigenas
        </Link>
        {' > '}{perfilLoading ? '...' : nombre}
      </div>

      {/* Header with action buttons */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px' }}>
        <div className="page-header" style={{ marginBottom: '12px' }}>
          <h1>{perfilLoading ? 'Cargando...' : nombre}</h1>
          <p style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
            Ficha de capacidades diversas
            {!perfilLoading && <ConfiabilidadBadge nivel={confiabilidad} />}
          </p>
        </div>
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          <button
            onClick={handlePrintPDF}
            style={{
              ...actionBtnStyle,
              background: 'var(--color-primary)',
              color: '#fff',
            }}
            onMouseEnter={(e) => { e.currentTarget.style.background = '#013d28'; }}
            onMouseLeave={(e) => { e.currentTarget.style.background = 'var(--color-primary)'; }}
          >
            Generar informe PDF
          </button>
          <button
            onClick={handleDownloadCSV}
            style={{
              ...actionBtnStyle,
              background: '#fff',
              color: 'var(--color-primary)',
              border: '2px solid var(--color-primary)',
            }}
            onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--color-green-light)'; }}
            onMouseLeave={(e) => { e.currentTarget.style.background = '#fff'; }}
          >
            Descargar datos CSV
          </button>
        </div>
      </div>

      {/* Prevalencia comparison banner */}
      {!perfilLoading && (
        <div className="alert alert-info" style={{ marginBottom: '20px' }}>
          <strong>Prevalencia de {nombre}:</strong> {prevNum.toFixed(1)}{'\u2030'}
          {' '}vs <strong>Promedio indigena nacional:</strong> {NACIONAL_PREVALENCIA.toFixed(1)}{'\u2030'}
          {prevNum < NACIONAL_PREVALENCIA
            ? ' -- Inferior al promedio indigena nacional. Posible sub-registro en territorio.'
            : prevNum > NACIONAL_PREVALENCIA
            ? ' -- Superior al promedio indigena nacional.'
            : ' -- Similar al promedio indigena nacional.'}
        </div>
      )}

      {/* KPIs */}
      {perfilLoading ? (
        <div className="loading-container" style={{ padding: '20px' }}>
          <div className="spinner" />
          <span>Cargando perfil...</span>
        </div>
      ) : (
        <div className="grid-row grid-4" style={{ marginBottom: '24px' }}>
          <KPICard
            title="Poblacion total"
            value={fmt(poblacion)}
            subtitle="CNPV 2018"
            color="var(--color-primary)"
          />
          <KPICard
            title="Con capacidades diversas"
            value={fmt(conCapDiv)}
            subtitle="Personas"
            color="var(--color-green-mid)"
          />
          <KPICard
            title="Prevalencia pueblo"
            value={`${prevNum.toFixed(1)}\u2030`}
            subtitle="Tasa por mil hab."
            color="var(--color-gold)"
          />
          <KPICard
            title="Promedio indigena nacional"
            value={`${NACIONAL_PREVALENCIA.toFixed(1)}\u2030`}
            subtitle="Referencia (pob. indigena)"
            color="var(--color-gray-500)"
          />
        </div>
      )}

      {/* Tabs */}
      <div className="tabs">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            className={`tab-btn ${activeTab === tab.key ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.key)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* TAB: Perfil */}
      {activeTab === 'perfil' && (
        perfilLoading
          ? <LoadingTab />
          : apiPerfil
            ? <TabPerfil perfil={apiPerfil} codPueblo={codPueblo} nombrePueblo={nombre} />
            : <ErrorTab message="No se pudieron cargar los datos del perfil." />
      )}

      {/* TAB: Demografia */}
      {activeTab === 'demografia' && (
        <TabDemografia codPueblo={codPueblo} nombrePueblo={nombre} />
      )}

      {/* TAB: Territorios */}
      {activeTab === 'territorios' && (
        <TabTerritorios codPueblo={codPueblo} nombrePueblo={nombre} />
      )}

      {/* TAB: Salud */}
      {activeTab === 'salud' && (
        perfilLoading
          ? <LoadingTab />
          : apiPerfil
            ? <TabSalud perfil={apiPerfil} />
            : <ErrorTab message="No se pudieron cargar los datos de salud." />
      )}

      {/* TAB: Conflicto */}
      {activeTab === 'conflicto' && (
        <TabConflicto codPueblo={codPueblo} nombrePueblo={nombre} />
      )}
    </div>
  );
}
