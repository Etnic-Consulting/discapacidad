/* ============================================
   3 piramides nacionales — Panorama
   1. Poblacion indigena total por edad/sexo
   2. Poblacion con capacidades diversas
   3. Apilada por tipo de capacidad diversa
   ============================================ */
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, ReferenceLine,
} from 'recharts';
import {
  usePiramideNacional, usePiramideDiscNacional, usePiramideDiscTipoNacional,
} from '../hooks/useApi';
import { useFilters } from '../context/FilterContext';

const fmt = (n) => new Intl.NumberFormat('es-CO').format(Math.round(n || 0));

const TIPO_COLORS = {
  'Ver': '#e41a1c', 'Caminar': '#377eb8', 'Oir': '#4daf4a',
  'Aprender': '#984ea3', 'Hablar': '#ff7f00',
  'Actividades diarias': '#a65628', 'Autocuidado': '#f781bf',
  'Agarrar': '#999999', 'Relacionarse': '#dede00',
};

const cardStyle = {
  background: '#fff',
  borderRadius: 10,
  boxShadow: '0 2px 10px rgba(14,31,26,0.06)',
  border: '1px solid var(--line, #E4DFD6)',
  padding: '18px 22px',
  marginBottom: 20,
};

const cardTitle = {
  fontFamily: 'var(--serif, Georgia)',
  fontSize: '1rem',
  fontWeight: 700,
  color: 'var(--primary, #02432D)',
  marginBottom: 4,
};

const cardSubtitle = {
  fontSize: '0.8rem',
  color: 'var(--ink-muted, #5B6B66)',
  marginBottom: 14,
};

function niceBound(maxAbs) {
  if (!maxAbs || maxAbs <= 0) return 1;
  const magnitude = Math.pow(10, Math.floor(Math.log10(maxAbs)));
  return Math.ceil(maxAbs / magnitude) * magnitude;
}

function fmtAxis(v) {
  const abs = Math.abs(v);
  if (abs >= 1000) return (abs / 1000).toFixed(abs >= 10000 ? 0 : 1) + 'K';
  return abs.toString();
}

/* ---- Pyramid 1 & 2 ---- */
function SimplePyramid({ data, title, subtitle, loading, isError }) {
  if (loading) return <div style={cardStyle}><div style={cardTitle}>{title}</div><div style={{ color: 'var(--ink-muted)' }}>Cargando...</div></div>;
  if (isError || !data || !data.piramide) {
    return <div style={cardStyle}><div style={cardTitle}>{title}</div><div style={{ color: 'var(--alert)' }}>Sin datos disponibles</div></div>;
  }
  const { piramide, total, total_hombres, total_mujeres, razon_masculinidad } = data;

  const chartData = piramide.map((r) => {
    const h = r.hombres_abs ?? Math.abs(r.hombres || 0);
    const m = r.mujeres_abs ?? Math.abs(r.mujeres || 0);
    return {
      grupo_edad: r.grupo_edad,
      h_signed: -h,
      m_signed: m,
      h_abs: h,
      m_abs: m,
      pct_h: r.pct_hombres || 0,
      pct_m: r.pct_mujeres || 0,
    };
  }).slice().reverse();

  const maxAbs = Math.max(...chartData.map((r) => Math.max(Math.abs(r.h_signed), r.m_signed)));
  const axisBound = niceBound(maxAbs);
  const pctH = total > 0 ? ((total_hombres / total) * 100).toFixed(1) : '0.0';
  const pctM = total > 0 ? ((total_mujeres / total) * 100).toFixed(1) : '0.0';

  return (
    <div style={cardStyle}>
      <div style={cardTitle}>{title}</div>
      <div style={cardSubtitle}>{subtitle}</div>
      <ResponsiveContainer width="100%" height={380}>
        <BarChart layout="vertical" data={chartData} margin={{ top: 5, right: 20, bottom: 20, left: 10 }} barCategoryGap="6%" barGap={0} barSize={14}>
          <CartesianGrid horizontal={false} strokeDasharray="3 3" stroke="#e5e5e5" />
          <XAxis type="number" domain={[-axisBound, axisBound]} tickFormatter={fmtAxis} tick={{ fontSize: 11 }} />
          <YAxis type="category" dataKey="grupo_edad" width={50} tick={{ fontSize: 10, fontWeight: 600 }} axisLine={false} tickLine={false} />
          <ReferenceLine x={0} stroke="#333" strokeWidth={1.5} />
          <Tooltip content={({ active, payload, label }) => {
            if (!active || !payload?.length) return null;
            const row = payload[0]?.payload;
            if (!row) return null;
            return (
              <div style={{ background: '#fff', border: '1px solid #ddd', borderRadius: 6, padding: '8px 12px', fontSize: '0.82rem' }}>
                <div style={{ fontWeight: 700, marginBottom: 4 }}>Grupo: {label}</div>
                <div><span style={{ color: '#4A90D9', fontWeight: 600 }}>Hombres:</span> {fmt(row.h_abs)} ({row.pct_h.toFixed(2)}%)</div>
                <div><span style={{ color: '#E74C3C', fontWeight: 600 }}>Mujeres:</span> {fmt(row.m_abs)} ({row.pct_m.toFixed(2)}%)</div>
              </div>
            );
          }} />
          <Legend formatter={(v) => v === 'h_signed' ? 'Hombres' : v === 'm_signed' ? 'Mujeres' : v} />
          <Bar dataKey="h_signed" name="Hombres" fill="#4A90D9" />
          <Bar dataKey="m_signed" name="Mujeres" fill="#E74C3C" />
        </BarChart>
      </ResponsiveContainer>
      <div style={{ textAlign: 'center', marginTop: 8, fontSize: '0.82rem', color: 'var(--ink-muted, #5B6B66)' }}>
        Total: <strong>{fmt(total)}</strong> · <span style={{ color: '#4A90D9' }}>Hombres {fmt(total_hombres)} ({pctH}%)</span> · <span style={{ color: '#E74C3C' }}>Mujeres {fmt(total_mujeres)} ({pctM}%)</span> · Razon masc. <strong>{razon_masculinidad?.toFixed ? razon_masculinidad.toFixed(1) : razon_masculinidad}</strong>
      </div>
    </div>
  );
}

/* ---- Pyramid 3 — stacked by type ---- */
function StackedPyramid({ data, title, subtitle, loading, isError }) {
  if (loading) return <div style={cardStyle}><div style={cardTitle}>{title}</div><div style={{ color: 'var(--ink-muted)' }}>Cargando...</div></div>;
  if (isError || !data || !data.piramide) {
    return <div style={cardStyle}><div style={cardTitle}>{title}</div><div style={{ color: 'var(--alert)' }}>Sin datos disponibles</div></div>;
  }
  const { resumen_tipos, piramide, total } = data;
  const tiposOrd = [...resumen_tipos].sort((a, b) => b.total - a.total).map((t) => t.tipo);

  const chartData = [...piramide].reverse().map((row) => {
    const entry = { grupo_edad: row.grupo_edad };
    tiposOrd.forEach((tipo) => {
      const hAbs = Math.abs(row[`h_${tipo}`] || 0);
      const mAbs = row[`m_${tipo}`] || 0;
      entry[`h_${tipo}`] = -hAbs;
      entry[`m_${tipo}`] = mAbs;
      entry[`abs_h_${tipo}`] = hAbs;
      entry[`abs_m_${tipo}`] = mAbs;
    });
    entry.total_h = Math.abs(row.total_h || 0);
    entry.total_m = row.total_m || 0;
    return entry;
  });

  const maxAbs = Math.max(
    ...chartData.map((r) => tiposOrd.reduce((s, t) => s + Math.abs(r[`h_${t}`] || 0), 0)),
    ...chartData.map((r) => tiposOrd.reduce((s, t) => s + (r[`m_${t}`] || 0), 0)),
  );
  const axisBound = niceBound(maxAbs);

  return (
    <div style={cardStyle}>
      <div style={cardTitle}>{title}</div>
      <div style={cardSubtitle}>{subtitle}</div>

      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10, justifyContent: 'center', marginBottom: 12 }}>
        {tiposOrd.map((tipo) => {
          const t = resumen_tipos.find((r) => r.tipo === tipo);
          return (
            <div key={tipo} style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: '0.74rem' }}>
              <div style={{ width: 12, height: 12, borderRadius: 2, background: TIPO_COLORS[tipo] || '#999' }} />
              <span style={{ fontWeight: 600 }}>{tipo}</span>
              <span style={{ color: 'var(--ink-muted, #5B6B66)' }}>({t?.pct || 0}%)</span>
            </div>
          );
        })}
      </div>

      <ResponsiveContainer width="100%" height={460}>
        <BarChart layout="vertical" data={chartData} margin={{ top: 5, right: 20, bottom: 20, left: 10 }} stackOffset="sign" barCategoryGap="6%" barGap={0} barSize={16}>
          <CartesianGrid horizontal={false} strokeDasharray="3 3" stroke="#e5e5e5" />
          <XAxis type="number" domain={[-axisBound, axisBound]} tickFormatter={fmtAxis} tick={{ fontSize: 11 }} />
          <YAxis type="category" dataKey="grupo_edad" width={50} tick={{ fontSize: 10, fontWeight: 600 }} axisLine={false} tickLine={false} />
          <ReferenceLine x={0} stroke="#333" strokeWidth={1.5} />
          <Tooltip content={({ active, payload, label }) => {
            if (!active || !payload?.length) return null;
            const row = chartData.find((r) => r.grupo_edad === label) || {};
            const items = tiposOrd.map((tipo) => ({
              tipo,
              h: row[`abs_h_${tipo}`] || 0,
              m: row[`abs_m_${tipo}`] || 0,
              total: (row[`abs_h_${tipo}`] || 0) + (row[`abs_m_${tipo}`] || 0),
            })).filter((x) => x.total > 0).sort((a, b) => b.total - a.total);
            return (
              <div style={{ background: '#fff', border: '1px solid #ddd', borderRadius: 6, padding: '8px 12px', fontSize: '0.78rem', maxWidth: 300 }}>
                <div style={{ fontWeight: 700, marginBottom: 4 }}>{label} anos</div>
                {items.map(({ tipo, h, m, total: t }) => (
                  <div key={tipo} style={{ display: 'flex', gap: 6, marginBottom: 2 }}>
                    <div style={{ width: 10, height: 10, borderRadius: 2, background: TIPO_COLORS[tipo] || '#999', flexShrink: 0, marginTop: 3 }} />
                    <span style={{ flex: 1 }}>{tipo}</span>
                    <span style={{ color: '#4A90D9' }}>H:{fmt(h)}</span>
                    <span style={{ color: '#E74C3C' }}>M:{fmt(m)}</span>
                  </div>
                ))}
              </div>
            );
          }} />
          {tiposOrd.map((tipo) => (
            <Bar key={`h_${tipo}`} dataKey={`h_${tipo}`} name={`H-${tipo}`} fill={TIPO_COLORS[tipo] || '#999'} stackId="hombres" />
          ))}
          {tiposOrd.map((tipo) => (
            <Bar key={`m_${tipo}`} dataKey={`m_${tipo}`} name={`M-${tipo}`} fill={TIPO_COLORS[tipo] || '#999'} stackId="mujeres" />
          ))}
        </BarChart>
      </ResponsiveContainer>

      <div style={{ textAlign: 'center', marginTop: 8, fontSize: '0.82rem', color: 'var(--ink-muted, #5B6B66)' }}>
        Total con capacidad diversa apilada: <strong>{fmt(total)}</strong> personas. Cada bloque muestra el peso del tipo en ese grupo de edad.
      </div>
    </div>
  );
}

export default function NationalPyramids() {
  const { dpto, mpio, pueblo, dptoNombre, mpioNombre, puebloNombre } = useFilters();
  const filters = {
    cod_dpto: dpto || undefined,
    cod_mpio: mpio || undefined,
    cod_pueblo: pueblo || undefined,
  };
  const p1 = usePiramideNacional(filters);
  const p2 = usePiramideDiscNacional(filters);
  const p3 = usePiramideDiscTipoNacional(filters);

  let scopeLabel = 'NACIONAL';
  let scopeNote = 'agregadas sobre todos los pueblos indigenas del pais';
  if (puebloNombre) {
    scopeLabel = `PUEBLO ${puebloNombre.toUpperCase()}`;
    scopeNote = `datos directos del pueblo ${puebloNombre}`;
  } else if (mpioNombre) {
    scopeLabel = `MUNICIPIO ${mpioNombre.toUpperCase()}`;
    scopeNote = `estimacion: piramide nacional de cada pueblo escalada por su presencia en el municipio`;
  } else if (dptoNombre) {
    scopeLabel = `DEPARTAMENTO ${dptoNombre.toUpperCase()}`;
    scopeNote = `estimacion: piramide nacional de cada pueblo escalada por su presencia en el departamento`;
  }

  return (
    <div>
      <div style={{
        padding: '14px 20px',
        background: 'var(--paper, #FAF6EC)',
        borderLeft: '4px solid var(--primary, #02432D)',
        borderRadius: 8,
        marginBottom: 20,
      }}>
        <div style={{ fontFamily: 'var(--mono, monospace)', fontSize: '0.7rem', color: 'var(--primary, #02432D)', letterSpacing: '0.1em', marginBottom: 4 }}>
          ANALISIS {scopeLabel} · CNPV 2018
        </div>
        <div style={{ fontSize: '0.88rem', color: 'var(--ink-soft, #2D3A36)', lineHeight: 1.5 }}>
          Tres piramides poblacionales ({scopeNote}): la primera muestra la estructura general, la segunda solo quienes tienen capacidades diversas, y la tercera desglosa por tipo de limitacion.
        </div>
      </div>

      <SimplePyramid
        title="1. Estructura poblacional indigena"
        subtitle={`Poblacion total por grupo de edad y sexo (CNPV 2018, ${scopeLabel.toLowerCase()})`}
        data={p1.data}
        loading={p1.isLoading}
        isError={p1.isError}
      />

      <SimplePyramid
        title="2. Poblacion con capacidades diversas"
        subtitle={`Personas con limitacion identificada por grupo de edad y sexo. n=${fmt(p2.data?.total)} de ${fmt(225174)} reportados por CNPV (la diferencia corresponde a registros sin clasificacion pueblo-especifica).`}
        data={p2.data}
        loading={p2.isLoading}
        isError={p2.isError}
      />

      <StackedPyramid
        title="3. Poblacion con capacidades diversas — apilada por tipo"
        subtitle="Cada barra muestra el volumen por tipo de limitacion en el grupo de edad"
        data={p3.data}
        loading={p3.isLoading}
        isError={p3.isError}
      />
    </div>
  );
}
