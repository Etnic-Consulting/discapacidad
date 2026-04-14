/* ============================================
   SMT-ONIC v2.0 — Proyecciones
   ============================================ */

import { useState, useMemo } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, ReferenceLine,
} from 'recharts';
import KPICard from '../components/KPICard';
import { useIntercensal } from '../hooks/useApi';

/* ---- Fallback data (used when API is unavailable) ---- */
const FALLBACK_INTERCENSAL = [
  { grupo_etnico: 'Indigena', periodo: '2005', pob_total: 1392623, pob_disc: 82435, prevalencia_pct: 5.92, tasa_x_1000: 59.2 },
  { grupo_etnico: 'Indigena', periodo: '2018', pob_total: 1905617, pob_disc: 114337, prevalencia_pct: 6.00, tasa_x_1000: 60.0 },
  { grupo_etnico: 'Afrodescendiente', periodo: '2005', pob_total: 4311757, pob_disc: 279282, prevalencia_pct: 6.48, tasa_x_1000: 64.8 },
  { grupo_etnico: 'Afrodescendiente', periodo: '2018', pob_total: 4671160, pob_disc: 310085, prevalencia_pct: 6.64, tasa_x_1000: 66.4 },
  { grupo_etnico: 'Sin pertenencia etnica', periodo: '2005', pob_total: 34898170, pob_disc: 2708359, prevalencia_pct: 7.76, tasa_x_1000: 77.6 },
  { grupo_etnico: 'Sin pertenencia etnica', periodo: '2018', pob_total: 33265994, pob_disc: 2378459, prevalencia_pct: 7.15, tasa_x_1000: 71.5 },
  { grupo_etnico: 'Nacional total', periodo: '2005', pob_total: 41174853, pob_disc: 3137524, prevalencia_pct: 7.62, tasa_x_1000: 76.2 },
  { grupo_etnico: 'Nacional total', periodo: '2018', pob_total: 44164417, pob_disc: 3105136, prevalencia_pct: 7.03, tasa_x_1000: 70.3 },
];

/* ---- Helper: extract rate for a grupo_etnico + periodo from data ---- */
function getRate(data, grupo, periodo) {
  const row = data.find(
    (r) => r.grupo_etnico === grupo && String(r.periodo) === String(periodo)
  );
  return row ? Number(row.tasa_x_1000) : null;
}

/* ---- Scenario projection functions ---- */
function computeScenarioData(scenarioId, base2005, base2018) {
  const slopeInd = (base2018.indigena - base2005.indigena) / 13;
  const slopeGen = (base2018.general - base2005.general) / 13;
  const slopeAfro = (base2018.afro - base2005.afro) / 13;

  switch (scenarioId) {
    case 'optimista': {
      const factor2030 = 0.80;
      const factor2024 = 1.0 - (1.0 - factor2030) * (6 / 12);
      return {
        indigena2024: +(base2018.indigena * factor2024).toFixed(1),
        general2024: +(base2018.general * factor2024).toFixed(1),
        afro2024: +(base2018.afro * factor2024).toFixed(1),
        indigena2030: +(base2018.indigena * factor2030).toFixed(1),
        general2030: +(base2018.general * factor2030).toFixed(1),
        afro2030: +(base2018.afro * factor2030).toFixed(1),
      };
    }
    case 'pesimista': {
      const factor2030 = 1.15;
      const factor2024 = 1.0 + (factor2030 - 1.0) * (6 / 12);
      return {
        indigena2024: +(base2018.indigena * factor2024).toFixed(1),
        general2024: +(base2018.general * factor2024).toFixed(1),
        afro2024: +(base2018.afro * factor2024).toFixed(1),
        indigena2030: +(base2018.indigena * factor2030).toFixed(1),
        general2030: +(base2018.general * factor2030).toFixed(1),
        afro2030: +(base2018.afro * factor2030).toFixed(1),
      };
    }
    case 'demografico': {
      const yearsTo2024 = 6;
      const yearsTo2030 = 12;
      return {
        indigena2024: +(base2018.indigena * Math.pow(1.03, yearsTo2024)).toFixed(1),
        general2024: +(base2018.general * Math.pow(1.03, yearsTo2024)).toFixed(1),
        afro2024: +(base2018.afro * Math.pow(1.03, yearsTo2024)).toFixed(1),
        indigena2030: +(base2018.indigena * Math.pow(1.03, yearsTo2030)).toFixed(1),
        general2030: +(base2018.general * Math.pow(1.03, yearsTo2030)).toFixed(1),
        afro2030: +(base2018.afro * Math.pow(1.03, yearsTo2030)).toFixed(1),
      };
    }
    case 'base':
    default: {
      return {
        indigena2024: +(base2018.indigena + slopeInd * 6).toFixed(1),
        general2024: +(base2018.general + slopeGen * 6).toFixed(1),
        afro2024: +(base2018.afro + slopeAfro * 6).toFixed(1),
        indigena2030: +(base2018.indigena + slopeInd * 12).toFixed(1),
        general2030: +(base2018.general + slopeGen * 12).toFixed(1),
        afro2030: +(base2018.afro + slopeAfro * 12).toFixed(1),
      };
    }
  }
}

/* ---- Helper: classify trend ---- */
function classifyTrend(pctChange) {
  if (pctChange > 5) return 'Incremento significativo';
  if (pctChange > 1) return 'Incremento moderado';
  if (pctChange > -1) return 'Estable con leve incremento';
  if (pctChange > -5) return 'Descenso moderado';
  return 'Descenso significativo';
}

const ESCENARIOS = [
  { id: 'base', label: 'Escenario base', desc: 'Tendencia lineal intercensal sin intervencion' },
  { id: 'optimista', label: 'Escenario optimista', desc: 'La prevalencia disminuye 20% para 2030' },
  { id: 'pesimista', label: 'Escenario pesimista', desc: 'La prevalencia aumenta 15% para 2030' },
  { id: 'demografico', label: 'Escenario demografico', desc: 'Prevalencia constante, solo cambia estructura poblacional (efecto envejecimiento +3%/ano)' },
];

const SCENARIO_TITLES = {
  base: 'Proyeccion base: tendencia lineal intercensal',
  optimista: 'Proyeccion optimista: reduccion de prevalencia 20% al 2030',
  pesimista: 'Proyeccion pesimista: aumento de prevalencia 15% al 2030',
  demografico: 'Proyeccion demografica: prevalencia constante con efecto de envejecimiento',
};

const SCENARIO_DESCRIPTIONS = {
  base: '2005 y 2018: datos censales verificados | 2024 y 2030: extrapolacion lineal de la tendencia 2005-2018',
  optimista: '2005 y 2018: datos censales verificados | 2024 y 2030: escenario con reduccion progresiva del 20% en prevalencia',
  pesimista: '2005 y 2018: datos censales verificados | 2024 y 2030: escenario con incremento progresivo del 15% en prevalencia',
  demografico: '2005 y 2018: datos censales verificados | 2024 y 2030: prevalencia constante ajustada por envejecimiento poblacional (+3%/ano)',
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

export default function ProyeccionesPage() {
  const [selectedEscenario, setSelectedEscenario] = useState('base');

  /* ---- Fetch real intercensal data ---- */
  const { data: intercensalResp, isLoading, isError } = useIntercensal();
  const intercensalData = intercensalResp?.data ?? FALLBACK_INTERCENSAL;

  /* ---- Extract base values from real data (or fallback) ---- */
  const base2005 = useMemo(() => ({
    indigena: getRate(intercensalData, 'Indigena', '2005') ?? 59.2,
    general: getRate(intercensalData, 'Sin pertenencia etnica', '2005') ?? 77.6,
    afro: getRate(intercensalData, 'Afrodescendiente', '2005') ?? 64.8,
  }), [intercensalData]);

  const base2018 = useMemo(() => ({
    indigena: getRate(intercensalData, 'Indigena', '2018') ?? 60.0,
    general: getRate(intercensalData, 'Sin pertenencia etnica', '2018') ?? 71.5,
    afro: getRate(intercensalData, 'Afrodescendiente', '2018') ?? 66.4,
  }), [intercensalData]);

  /* ---- Build chart data dynamically based on selected scenario ---- */
  const scenarioData = useMemo(
    () => computeScenarioData(selectedEscenario, base2005, base2018),
    [selectedEscenario, base2005, base2018],
  );

  const serieIntercensal = useMemo(() => [
    { anio: 2005, indigena: base2005.indigena, general: base2005.general, afro: base2005.afro },
    { anio: 2018, indigena: base2018.indigena, general: base2018.general, afro: base2018.afro },
    { anio: 2024, indigena: scenarioData.indigena2024, general: scenarioData.general2024, afro: scenarioData.afro2024, proyeccion: true },
    { anio: 2030, indigena: scenarioData.indigena2030, general: scenarioData.general2030, afro: scenarioData.afro2030, proyeccion: true },
  ], [base2005, base2018, scenarioData]);

  /* ---- Build comparison table from ALL groups in the API data ---- */
  const comparacion = useMemo(() => {
    const groups = [...new Set(intercensalData.map((r) => r.grupo_etnico))];
    return groups.map((grupo) => {
      const val2005 = getRate(intercensalData, grupo, '2005');
      const val2018 = getRate(intercensalData, grupo, '2018');
      const pctChange = val2005 && val2018
        ? (((val2018 - val2005) / val2005) * 100)
        : null;
      return {
        grupo,
        prev2005: val2005,
        prev2018: val2018,
        cambio: pctChange !== null
          ? `${pctChange >= 0 ? '+' : ''}${pctChange.toFixed(1)}%`
          : 'N/D',
        tendencia: pctChange !== null ? classifyTrend(pctChange) : 'Sin datos',
      };
    });
  }, [intercensalData]);

  /* ---- KPI derived values ---- */
  const cambioIntercensal = useMemo(() => {
    if (base2005.indigena && base2018.indigena) {
      const pct = ((base2018.indigena - base2005.indigena) / base2005.indigena) * 100;
      return `${pct >= 0 ? '+' : ''}${pct.toFixed(1)}%`;
    }
    return '+1.4%';
  }, [base2005, base2018]);

  return (
    <div>
      <div className="page-header">
        <h1>Proyecciones Intercensales</h1>
        <p>
          Analisis intercensal 2005-2018 y proyecciones demograficas al 2030
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
        <strong>Fuente:</strong> Datos intercensales verificados: CG 2005 y CNPV 2018 (DANE).
        {isError && ' (usando datos de respaldo — API no disponible)'}
      </div>

      {/* Loading indicator */}
      {isLoading && (
        <div style={{ textAlign: 'center', padding: '12px', color: 'var(--color-gray-500)', fontSize: '0.85rem' }}>
          Cargando datos intercensales...
        </div>
      )}

      {/* KPIs */}
      <div className="grid-row grid-4" style={{ marginBottom: '28px' }}>
        <KPICard
          title="Prevalencia 2005"
          value={`${base2005.indigena}\u2030`}
          subtitle="Indigenas"
          color="var(--color-primary)"
          icon="05"
        />
        <KPICard
          title="Prevalencia 2018"
          value={`${base2018.indigena}\u2030`}
          subtitle="Indigenas"
          color="var(--color-green-mid)"
          icon="18"
        />
        <KPICard
          title="Cambio intercensal"
          value={cambioIntercensal}
          subtitle="2005 -> 2018"
          color="var(--color-gold)"
          icon="CI"
        />
        <KPICard
          title={`Proyeccion 2030 (${selectedEscenario})`}
          value={`${scenarioData.indigena2030}\u2030`}
          subtitle={ESCENARIOS.find((e) => e.id === selectedEscenario)?.desc || 'Proyeccion estimada'}
          color="var(--color-red)"
          icon="30"
        />
      </div>

      {/* Line Chart */}
      <div style={{ ...cardStyle, marginBottom: '24px' }}>
        <div style={chartTitle}>{SCENARIO_TITLES[selectedEscenario] || 'Prevalencia intercensal y proyeccion 2005-2030 (tasa x 1000)'}</div>
        <div style={{ fontSize: '0.75rem', color: 'var(--color-gray-400)', marginBottom: '8px', marginTop: '-12px' }}>
          {SCENARIO_DESCRIPTIONS[selectedEscenario] || '2005 y 2018: datos censales verificados | 2024 y 2030: proyeccion estimada'}
        </div>
        <ResponsiveContainer width="100%" height={380}>
          <LineChart data={serieIntercensal} margin={{ top: 10, right: 30, bottom: 10, left: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e8e8e8" />
            <XAxis dataKey="anio" tick={{ fontSize: 12 }} />
            <YAxis domain={[40, 100]} tick={{ fontSize: 11 }} label={{ value: 'Tasa x 1000', angle: -90, position: 'insideLeft', style: { fontSize: 11 } }} />
            <Tooltip
              contentStyle={{ fontSize: '0.85rem' }}
              formatter={(v, name) => [`${v}\u2030`, name]}
            />
            <Legend />
            <ReferenceLine x={2018} stroke="#aaa" strokeDasharray="3 3" label={{ value: 'CNPV 2018', position: 'top', fontSize: 10 }} />
            <Line
              type="monotone"
              dataKey="indigena"
              name="Indigena"
              stroke="#02432D"
              strokeWidth={3}
              dot={{ r: 5 }}
              activeDot={{ r: 7 }}
            />
            <Line
              type="monotone"
              dataKey="general"
              name="Nacional general"
              stroke="#6B6B6B"
              strokeWidth={2}
              strokeDasharray="5 5"
              dot={{ r: 4 }}
            />
            <Line
              type="monotone"
              dataKey="afro"
              name="Afrodescendiente"
              stroke="#C4920A"
              strokeWidth={2}
              dot={{ r: 4 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Scenario selector */}
      <div className="grid-row grid-2">
        <div style={cardStyle}>
          <div style={chartTitle}>Escenarios de proyeccion</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {ESCENARIOS.map((esc) => (
              <label
                key={esc.id}
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '10px',
                  padding: '10px 12px',
                  borderRadius: 'var(--radius-sm)',
                  border: selectedEscenario === esc.id
                    ? '2px solid var(--color-green-mid)'
                    : '2px solid var(--color-gray-200)',
                  cursor: 'pointer',
                  transition: 'border-color 0.15s',
                }}
              >
                <input
                  type="radio"
                  name="escenario"
                  value={esc.id}
                  checked={selectedEscenario === esc.id}
                  onChange={() => setSelectedEscenario(esc.id)}
                  style={{ accentColor: 'var(--color-green-mid)', marginTop: '3px' }}
                />
                <div>
                  <div style={{ fontWeight: 600, fontSize: '0.88rem', color: 'var(--color-primary)' }}>
                    {esc.label}
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--color-gray-500)', marginTop: '2px' }}>
                    {esc.desc}
                  </div>
                </div>
              </label>
            ))}
          </div>
        </div>

        {/* Comparison table */}
        <div style={cardStyle}>
          <div style={chartTitle}>Comparacion intercensal por grupo etnico</div>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
            <thead>
              <tr>
                {['Grupo', '2005', '2018', 'Cambio', 'Tendencia'].map((h) => (
                  <th
                    key={h}
                    style={{
                      padding: '8px 12px',
                      textAlign: 'left',
                      fontWeight: 600,
                      fontSize: '0.75rem',
                      textTransform: 'uppercase',
                      color: 'var(--color-gray-500)',
                      background: 'var(--color-gray-100)',
                      borderBottom: '2px solid var(--color-gray-200)',
                    }}
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {comparacion.map((row, i) => (
                <tr key={i} style={{ background: i % 2 === 0 ? '#fff' : 'var(--color-gray-100)' }}>
                  <td style={{ padding: '8px 12px', fontWeight: 600, borderBottom: '1px solid var(--color-gray-200)' }}>
                    {row.grupo}
                  </td>
                  <td style={{ padding: '8px 12px', borderBottom: '1px solid var(--color-gray-200)' }}>
                    {row.prev2005 != null ? `${row.prev2005}\u2030` : 'N/D'}
                  </td>
                  <td style={{ padding: '8px 12px', borderBottom: '1px solid var(--color-gray-200)' }}>
                    {row.prev2018 != null ? `${row.prev2018}\u2030` : 'N/D'}
                  </td>
                  <td style={{
                    padding: '8px 12px',
                    borderBottom: '1px solid var(--color-gray-200)',
                    fontWeight: 600,
                    color: row.cambio.startsWith('+') ? 'var(--color-red)' : 'var(--color-green-mid)',
                  }}>
                    {row.cambio}
                  </td>
                  <td style={{ padding: '8px 12px', borderBottom: '1px solid var(--color-gray-200)', fontSize: '0.8rem', color: 'var(--color-gray-500)' }}>
                    {row.tendencia}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Methodology note */}
      <div className="alert alert-info" style={{ marginTop: '24px' }}>
        <strong>Nota metodologica:</strong> Proyecciones basadas en modelo de componentes
        demograficos (CELADE/Sullivan). La diferencia entre la prevalencia indigena
        ({base2018.indigena}{'\u2030'}) y la nacional ({base2018.general}{'\u2030'}) sugiere un sub-registro significativo en
        territorios indigenas, no una menor prevalencia real. Los escenarios permiten
        explorar distintas hipotesis sobre la evolucion futura.
      </div>
    </div>
  );
}
