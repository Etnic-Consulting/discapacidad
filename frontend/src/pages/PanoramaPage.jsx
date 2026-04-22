/* ============================================
   SMT-ONIC v2.0 — Panorama General (Dashboard)
   ============================================ */

import { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  PieChart, Pie, Cell, ResponsiveContainer,
} from 'recharts';
import KPICard from '../components/KPICard';
import GlobalSelector from '../components/GlobalSelector';
import FilterBreadcrumb from '../components/FilterBreadcrumb';
import CertificationFunnel from '../components/CertificationFunnel';
import DidYouKnow from '../components/DidYouKnow';
import NationalPyramids from '../components/NationalPyramids';
import Term from '../components/Term';
import { useFilters } from '../context/FilterContext';
import { useResumenNacional, usePrevalenciaDpto, usePerfilPueblo, usePueblos, useBrecha, usePerfilResguardo, useDificultades, usePiramideDiscNacional, usePanoramaKpis } from '../hooks/useApi';
import { sortAndMergeAgeGroups } from '../lib/ageGroups';

/* ---- Mock Data (real numbers from CNPV 2018 / RUV analysis) ---- */
const MOCK_KPI = {
  totalPersonas: 225174,
  pueblos: 121,
  prevalencia: '60.0',
  coberturaRegistro: '32.4',
  brechaCertificacion: '71.3',
  victimasConflicto: 37797,
};

const PREVALENCIA_ETNICA = [
  { grupo: 'Indigena 2005', prevalencia: 59.2, fill: '#02432D' },
  { grupo: 'Indigena 2018', prevalencia: 60.0, fill: '#02AB44' },
  { grupo: 'Afro 2005', prevalencia: 64.8, fill: '#C4920A' },
  { grupo: 'Afro 2018', prevalencia: 66.4, fill: '#E8B84B' },
  { grupo: 'Ninguno 2005', prevalencia: 77.6, fill: '#6B6B6B' },
  { grupo: 'Ninguno 2018', prevalencia: 71.5, fill: '#A0A0A0' },
];

const DIFICULTADES_WG = [
  { dificultad: 'Ver', value: 37.2, fullMark: 50 },
  { dificultad: 'Oir', value: 15.8, fullMark: 50 },
  { dificultad: 'Caminar', value: 30.1, fullMark: 50 },
  { dificultad: 'Agarrar', value: 12.4, fullMark: 50 },
  { dificultad: 'Autocuidado', value: 11.6, fullMark: 50 },
  { dificultad: 'Comunicarse', value: 9.8, fullMark: 50 },
  { dificultad: 'Aprender', value: 10.5, fullMark: 50 },
  { dificultad: 'Relacionarse', value: 7.3, fullMark: 50 },
  { dificultad: 'Act. diarias', value: 14.2, fullMark: 50 },
];

const SEXO_DATA = [
  { name: 'Hombres', value: 53.2, color: '#02432D' },
  { name: 'Mujeres', value: 46.8, color: '#C4920A' },
];

const EDAD_DATA = [
  { rango: '0-4', personas: 5420 },
  { rango: '5-14', personas: 18340 },
  { rango: '15-24', personas: 22150 },
  { rango: '25-34', personas: 24800 },
  { rango: '35-44', personas: 28600 },
  { rango: '45-54', personas: 35400 },
  { rango: '55-64', personas: 38200 },
  { rango: '65-74', personas: 32100 },
  { rango: '75+', personas: 20164 },
];

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

function formatNumber(n) {
  return new Intl.NumberFormat('es-CO').format(n);
}

/* ---- Inline pueblo profile preview ---- */
function PuebloPreview({ codPueblo, puebloNombre }) {
  const { data: apiPerfil, isLoading } = usePerfilPueblo(codPueblo);

  if (isLoading) {
    return (
      <div style={{ ...cardStyle, marginBottom: '24px' }}>
        <div className="loading-container" style={{ padding: '20px' }}>
          <div className="spinner" />
          <span>Cargando perfil de {puebloNombre}...</span>
        </div>
      </div>
    );
  }

  if (!apiPerfil) return null;

  const prev = apiPerfil.prevalencia || {};
  const nombre = prev.pueblo || puebloNombre || codPueblo;
  const poblacion = prev.total || 0;
  const conCapDiv = prev.con_discapacidad || 0;
  const tasa = prev.tasa_x_1000 || 0;

  const limitaciones = apiPerfil.limitaciones
    ? apiPerfil.limitaciones.slice(0, 5).map((l) => ({ dificultad: l.limitacion, value: l.valor }))
    : [];

  const edades = apiPerfil.piramide_edad
    ? sortAndMergeAgeGroups(apiPerfil.piramide_edad, 'grupo_edad', 'valor')
        .map((e) => ({ rango: e.grupo_edad, personas: e.valor }))
    : [];

  return (
    <div style={{
      ...cardStyle,
      marginBottom: '24px',
      borderLeft: '4px solid var(--color-green-mid)',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
        <div>
          <h3 style={{ marginBottom: '4px' }}>Pueblo {nombre}</h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--color-gray-500)' }}>
            Prevalencia: {tasa.toFixed ? tasa.toFixed(1) : tasa}{'\u2030'} vs Promedio indigena nacional: {NACIONAL_PREVALENCIA}{'\u2030'}
          </p>
        </div>
        <Link
          to={`/pueblos/${codPueblo}`}
          style={{
            padding: '6px 16px',
            background: 'var(--color-green-mid)',
            color: '#fff',
            borderRadius: 'var(--radius-sm)',
            fontSize: '0.82rem',
            fontWeight: 600,
            textDecoration: 'none',
          }}
        >
          Ver perfil completo
        </Link>
      </div>

      <div className="grid-row grid-3" style={{ marginBottom: '16px' }}>
        <KPICard
          title="Poblacion total"
          value={formatNumber(poblacion)}
          subtitle="CNPV 2018"
          color="var(--color-primary)"
        />
        <KPICard
          title="Con capacidades diversas"
          value={formatNumber(conCapDiv)}
          subtitle="Personas"
          color="var(--color-green-mid)"
        />
        <KPICard
          title="Prevalencia"
          value={`${tasa.toFixed ? tasa.toFixed(1) : tasa}\u2030`}
          subtitle={tasa < NACIONAL_PREVALENCIA ? 'Inferior al promedio indigena nacional' : 'Superior al promedio indigena nacional'}
          color="var(--color-gold)"
        />
      </div>

      {limitaciones.length > 0 && (
        <div style={{ display: 'flex', gap: '20px', flexWrap: 'wrap' }}>
          <div style={{ flex: 1, minWidth: '250px' }}>
            <div style={{ ...chartTitle, fontSize: '0.78rem' }}>Top dificultades funcionales</div>
            {limitaciones.map((l) => (
              <div key={l.dificultad} style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                <span style={{ fontSize: '0.82rem', width: '100px' }}>{l.dificultad}</span>
                <div style={{ flex: 1, height: '6px', background: 'var(--color-gray-200)', borderRadius: '3px', overflow: 'hidden' }}>
                  <div style={{
                    width: `${Math.min(l.value * 2, 100)}%`,
                    height: '100%',
                    background: 'var(--color-green-mid)',
                    borderRadius: '3px',
                  }} />
                </div>
                <span style={{ fontSize: '0.78rem', fontWeight: 600, width: '50px', textAlign: 'right' }}>{formatNumber(l.value)}</span>
              </div>
            ))}
          </div>
          {edades.length > 0 && (
            <div style={{ flex: 1, minWidth: '300px' }}>
              <div style={{ ...chartTitle, fontSize: '0.78rem' }}>Piramide de edad</div>
              <ResponsiveContainer width="100%" height={160}>
                <BarChart data={edades} margin={{ top: 5, right: 10, bottom: 5, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e8e8e8" />
                  <XAxis dataKey="rango" tick={{ fontSize: 9 }} />
                  <YAxis tick={{ fontSize: 9 }} />
                  <Tooltip formatter={(v) => [formatNumber(v), 'Personas']} />
                  <Bar dataKey="personas" fill="#02432D" radius={[2, 2, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/* ---- Inline resguardo profile preview ---- */
function ResguardoPreview({ codResguardo, resguardoNombre }) {
  const { data: perfil, isLoading } = usePerfilResguardo(codResguardo);

  if (isLoading) {
    return (
      <div style={{ ...cardStyle, marginBottom: '24px' }}>
        <div className="loading-container" style={{ padding: '20px' }}>
          <div className="spinner" />
          <span>Cargando perfil de resguardo {resguardoNombre}...</span>
        </div>
      </div>
    );
  }

  if (!perfil) return null;

  const nombre = perfil.nombre || perfil.territorio || resguardoNombre;

  return (
    <div style={{
      ...cardStyle,
      marginBottom: '24px',
      borderLeft: '4px solid var(--color-gold)',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
        <div>
          <h3 style={{ marginBottom: '4px' }}>Resguardo: {nombre}</h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--color-gray-500)' }}>
            {perfil.departamento} &rsaquo; {perfil.municipio}
            {perfil.organizacion ? ` | Org: ${perfil.organizacion}` : ''}
          </p>
        </div>
      </div>

      <div className="grid-row grid-4" style={{ marginBottom: '16px' }}>
        <KPICard
          title="Poblacion total"
          value={formatNumber(perfil.poblacion_total)}
          subtitle="CNPV 2018"
          color="var(--color-primary)"
        />
        <KPICard
          title="Est. cap. diversas"
          value={formatNumber(perfil.est_cap_diversas)}
          subtitle="Estimacion ponderada"
          color="var(--color-green-mid)"
        />
        <KPICard
          title="Tasa estimada"
          value={`${perfil.est_tasa_x_1000}\u2030`}
          subtitle="Por mil hab."
          color="var(--color-gold)"
        />
        <KPICard
          title="Area"
          value={perfil.area_ha ? `${formatNumber(Math.round(perfil.area_ha))} ha` : '--'}
          subtitle="Hectareas"
          color="var(--color-gray-500)"
        />
      </div>

      {/* Pueblos in this resguardo */}
      {perfil.pueblos && perfil.pueblos.length > 0 && (
        <div>
          <div style={{ ...chartTitle, fontSize: '0.78rem' }}>Pueblos en este resguardo</div>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid var(--color-gray-200)' }}>
                <th style={{ textAlign: 'left', padding: '6px 8px', fontWeight: 600, fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--color-gray-500)' }}>Pueblo</th>
                <th style={{ textAlign: 'right', padding: '6px 8px', fontWeight: 600, fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--color-gray-500)' }}>Poblacion</th>
                <th style={{ textAlign: 'right', padding: '6px 8px', fontWeight: 600, fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--color-gray-500)' }}>%</th>
                <th style={{ textAlign: 'right', padding: '6px 8px', fontWeight: 600, fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--color-gray-500)' }}>Tasa pueblo</th>
              </tr>
            </thead>
            <tbody>
              {perfil.pueblos.map((p) => (
                <tr key={p.cod_pueblo} style={{ borderBottom: '1px solid var(--color-gray-100)' }}>
                  <td style={{ padding: '6px 8px' }}>
                    <Link to={`/pueblos/${p.cod_pueblo}`} style={{ color: 'var(--color-green-mid)', fontWeight: 600, textDecoration: 'none' }}>
                      {p.pueblo}
                    </Link>
                  </td>
                  <td style={{ padding: '6px 8px', textAlign: 'right' }}>{formatNumber(p.poblacion)}</td>
                  <td style={{ padding: '6px 8px', textAlign: 'right' }}>{p.pct}%</td>
                  <td style={{ padding: '6px 8px', textAlign: 'right' }}>{p.tasa_pueblo != null ? `${p.tasa_pueblo}\u2030` : '--'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default function PanoramaPage() {
  const { dpto, mpio, pueblo, resguardo, macro, dptoNombre, mpioNombre, puebloNombre, resguardoNombre } = useFilters();
  const [compareNacional, setCompareNacional] = useState(false);

  const { data: apiData, isLoading, isError } = useResumenNacional();
  const { data: dptoData } = usePrevalenciaDpto(dpto ? 'Indigena' : undefined);
  const { data: apiPueblos } = usePueblos();
  const { data: brechaData } = useBrecha(dpto || undefined);
  const { data: dificultadesData } = useDificultades(dpto || undefined, 'Indigena');
  const { data: piramideDiscData } = usePiramideDiscNacional({
    cod_dpto: dpto || undefined,
    cod_mpio: mpio || undefined,
    cod_pueblo: pueblo || undefined,
  });
  const { data: kpisData } = usePanoramaKpis({
    cod_dpto: dpto || undefined,
    cod_mpio: mpio || undefined,
    cod_pueblo: pueblo || undefined,
    cod_resguardo: resguardo || undefined,
    cod_macro: macro || undefined,
  });

  // API returns { periodo, data: [{ grupo_etnico, pob_total, pob_disc, prevalencia_pct, tasa_x_1000 }] }
  const resumen = apiData?.data || [];
  const indigena = resumen.find((r) => r.grupo_etnico === 'Indigena');

  // Department-level data from prevalencia endpoint
  const dptoRows = dptoData?.data || [];
  const selectedDptoRow = dpto
    ? dptoRows.find((d) => String(d.cod_dpto) === String(dpto))
    : null;

  const pueblosCount = apiPueblos?.total ?? MOCK_KPI.pueblos;

  const kpi = kpisData
    ? {
        totalPersonas: kpisData.total_personas,
        pueblos: kpisData.pueblos,
        prevalencia: kpisData.prevalencia?.toFixed(1) ?? MOCK_KPI.prevalencia,
        coberturaRegistro: kpisData.cobertura_smt != null ? kpisData.cobertura_smt.toFixed(2) : null,
        brechaCertificacion: kpisData.brecha_certificacion != null ? kpisData.brecha_certificacion.toFixed(1) : null,
        victimasConflicto: kpisData.victimas_conflicto,
        dptoNombre: dptoNombre,
      }
    : selectedDptoRow
    ? {
        totalPersonas: selectedDptoRow.pob_disc || selectedDptoRow.pob_total || 0,
        pueblos: pueblosCount,
        prevalencia: selectedDptoRow.tasa_x_1000?.toFixed(1) ?? MOCK_KPI.prevalencia,
        coberturaRegistro: MOCK_KPI.coberturaRegistro,
        brechaCertificacion: MOCK_KPI.brechaCertificacion,
        victimasConflicto: MOCK_KPI.victimasConflicto,
        dptoNombre: dptoNombre,
      }
    : indigena
    ? {
        totalPersonas: indigena.pob_disc,
        pueblos: pueblosCount,
        prevalencia: indigena.tasa_x_1000?.toFixed(1) ?? MOCK_KPI.prevalencia,
        coberturaRegistro: MOCK_KPI.coberturaRegistro,
        brechaCertificacion: MOCK_KPI.brechaCertificacion,
        victimasConflicto: MOCK_KPI.victimasConflicto,
      }
    : { ...MOCK_KPI, pueblos: pueblosCount };

  if (isLoading) return <div className="loading-container"><div className="spinner" /><p>Cargando...</p></div>;
  if (isError) return <div className="error-container"><p>Error cargando datos</p></div>;

  // Build dynamic title
  let pageTitle = 'Panorama Nacional de Capacidades Diversas';
  if (dptoNombre) pageTitle = `Panorama: ${dptoNombre}`;
  if (dptoNombre && mpioNombre) pageTitle = `Panorama: ${dptoNombre} > ${mpioNombre}`;

  const scopeLabel = dptoNombre
    ? (mpioNombre ? `Departamento: ${dptoNombre}, Municipio: ${mpioNombre}` : `Departamento: ${dptoNombre}`)
    : macro
    ? `Macrorregión ONIC: ${macro}`
    : 'Nacional';

  return (
    <div>
      <div className="page-header">
        <h1>{pageTitle}</h1>
        <p>
          Personas indigenas con capacidades diversas en Colombia -- CNPV 2018, RUV, SMT-ONIC
        </p>
      </div>

      {/* Global Selector */}
      <GlobalSelector />

      {/* Breadcrumb */}
      <FilterBreadcrumb />

      {/* Scope indicator and compare toggle */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '16px',
        flexWrap: 'wrap',
        gap: '10px',
      }}>
        <div style={{
          fontSize: '0.88rem',
          fontWeight: 600,
          color: 'var(--color-primary)',
        }}>
          Mostrando datos: {scopeLabel}
        </div>
        {dpto && (
          <label style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '0.82rem',
            color: 'var(--color-gray-600)',
            cursor: 'pointer',
          }}>
            <input
              type="checkbox"
              checked={compareNacional}
              onChange={(e) => setCompareNacional(e.target.checked)}
              style={{ accentColor: 'var(--color-green-mid)' }}
            />
            Comparar con nacional
          </label>
        )}
      </div>

      {/* Pueblo preview (when a pueblo is selected) */}
      {pueblo && (
        <PuebloPreview
          codPueblo={pueblo}
          puebloNombre={puebloNombre}
        />
      )}

      {/* Resguardo preview (when a resguardo is selected) */}
      {resguardo && (
        <ResguardoPreview
          codResguardo={resguardo}
          resguardoNombre={resguardoNombre}
        />
      )}

      {/* Compare with national banner */}
      {dpto && compareNacional && (
        <div className="alert alert-info" style={{ marginBottom: '20px' }}>
          <strong>Comparacion:</strong> Prevalencia en {dptoNombre || 'departamento seleccionado'}:
          {' '}{kpi.prevalencia}{'\u2030'} vs Promedio indigena nacional: {NACIONAL_PREVALENCIA}{'\u2030'}
          {' '}vs Nacional general: 71.5{'\u2030'}
        </div>
      )}

      {/* KPI Row */}
      <div className="grid-row grid-6" style={{ marginBottom: '28px' }}>
        <KPICard
          title="Total personas"
          value={formatNumber(kpi.totalPersonas || MOCK_KPI.totalPersonas)}
          subtitle={dptoNombre || 'CNPV 2018'}
          color="var(--color-green-mid)"
        />
        <KPICard
          title="Pueblos identificados"
          value={kpi.pueblos || MOCK_KPI.pueblos}
          subtitle="Con registro censal"
          color="var(--color-primary)"
        />
        <KPICard
          title="Prevalencia"
          value={`${kpi.prevalencia || MOCK_KPI.prevalencia}\u2030`}
          subtitle="Tasa por mil hab."
          color="var(--color-gold)"
        />
        <KPICard
          title="Cobertura SMT-ONIC"
          value={kpi.coberturaRegistro != null ? `${kpi.coberturaRegistro}%` : 'N/D'}
          subtitle={kpi.coberturaRegistro != null ? 'Caracterizados / censo 2018' : 'Solo nivel nacional'}
          color="var(--color-green-mid)"
        />
        <KPICard
          title="Brecha certificacion"
          value={kpi.brechaCertificacion != null ? `${kpi.brechaCertificacion}%` : 'N/D'}
          subtitle={kpi.brechaCertificacion != null ? 'Sin certificar' : 'Sin caracterizados en el filtro'}
          color="var(--color-red)"
        />
        <KPICard
          title="Victimas conflicto"
          value={formatNumber(kpi.victimasConflicto || MOCK_KPI.victimasConflicto)}
          subtitle="RUV - cap. diversas"
          color="var(--color-red)"
        />
      </div>

      {/* Certification Gap Funnel — top position for maximum impact */}
      <div style={{
        ...cardStyle,
        marginBottom: '24px',
      }}>
        <div style={chartTitle}>Brecha de certificacion</div>
        <p style={{
          fontSize: '0.88rem',
          color: 'var(--color-gray-500)',
          marginBottom: '16px',
          lineHeight: 1.5,
        }}>
          Embudo que muestra la reduccion progresiva desde la poblacion indigena total
          hasta quienes cuentan con certificacion oficial de capacidades diversas. Cada
          nivel representa una barrera adicional en el proceso de reconocimiento.
        </p>
        <CertificationFunnel brecha={brechaData} />
      </div>

      {/* Charts Row 1: Prevalencia + Radar */}
      <div className="grid-row grid-2">
        <div style={cardStyle}>
          <div style={chartTitle}>Prevalencia por grupo etnico (CNPV 2018)</div>
          {(() => {
            // Build chart data from API when available, fallback to hardcoded CNPV 2018 data
            const ETNICO_COLORS = {
              'Indigena': '#02AB44',
              'Afrodescendiente': '#C4920A',
              'Sin pertenencia etnica': '#A0A0A0',
              'Ninguno': '#A0A0A0',
              'Rom': '#8B5CF6',
              'Raizal': '#2196F3',
              'Palenquero': '#E8862A',
            };
            const apiChartData = resumen.length > 0
              ? resumen.map((r) => ({
                  grupo: r.grupo_etnico,
                  prevalencia: r.tasa_x_1000,
                  fill: ETNICO_COLORS[r.grupo_etnico] || '#6B6B6B',
                }))
              : PREVALENCIA_ETNICA;
            return (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={apiChartData} margin={{ top: 10, right: 20, bottom: 5, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e8e8e8" />
                  <XAxis
                    dataKey="grupo"
                    tick={{ fontSize: 11 }}
                    angle={-15}
                    textAnchor="end"
                    height={60}
                  />
                  <YAxis
                    tick={{ fontSize: 11 }}
                    label={{
                      value: 'Tasa x 1000',
                      angle: -90,
                      position: 'insideLeft',
                      style: { fontSize: 11 },
                    }}
                  />
                  <Tooltip
                    formatter={(v) => [`${v}\u2030`, 'Prevalencia']}
                    contentStyle={{ fontSize: '0.85rem' }}
                  />
                  <Bar dataKey="prevalencia" radius={[4, 4, 0, 0]}>
                    {apiChartData.map((entry, i) => (
                      <Cell key={i} fill={entry.fill} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            );
          })()}
          {resumen.length === 0 && (
            <div style={{ fontSize: '0.72rem', color: 'var(--color-gray-400)', textAlign: 'center', marginTop: '4px' }}>
              (Datos fijos CG 2005 y CNPV 2018)
            </div>
          )}
        </div>

        <div style={cardStyle}>
          <div style={chartTitle}>Dificultades funcionales (Washington Group)</div>
          {(() => {
            const rows = dificultadesData?.data || [];
            const indigenaRows = rows.filter((r) => r.grupo_etnico === 'Indigena');
            const radarData = indigenaRows.length > 0
              ? indigenaRows.map((r) => ({
                  dificultad: r.dificultad.charAt(0).toUpperCase() + r.dificultad.slice(1),
                  value: parseFloat(r.tasa_x_1000) || 0,
                  fullMark: 300,
                }))
              : DIFICULTADES_WG;
            return (
              <ResponsiveContainer width="100%" height={300}>
                <RadarChart data={radarData} cx="50%" cy="50%" outerRadius="70%">
                  <PolarGrid stroke="#e8e8e8" />
                  <PolarAngleAxis dataKey="dificultad" tick={{ fontSize: 11 }} />
                  <PolarRadiusAxis tick={{ fontSize: 10 }} />
                  <Radar
                    name="Tasa x 1000"
                    dataKey="value"
                    stroke="#02432D"
                    fill="#02AB44"
                    fillOpacity={0.3}
                  />
                  <Tooltip formatter={(v) => [`${v}‰`, 'Tasa']} />
                </RadarChart>
              </ResponsiveContainer>
            );
          })()}
          <div style={{ fontSize: '0.72rem', color: 'var(--color-gray-400)', textAlign: 'center', marginTop: '4px' }}>
            {dificultadesData?.data?.length > 0 ? `CNPV 2018 · ${scopeLabel}` : '(Datos nacionales CNPV 2018)'}
          </div>
        </div>
      </div>

      {/* Epidemiological paradox warning */}
      <div style={{
        border: '2px solid var(--color-gold)',
        background: 'var(--color-gold-light)',
        borderRadius: 'var(--radius-sm)',
        padding: '14px 18px',
        marginBottom: '20px',
      }}>
        <div style={{
          fontSize: '0.78rem',
          fontWeight: 700,
          textTransform: 'uppercase',
          letterSpacing: '0.5px',
          color: 'var(--color-gold)',
          marginBottom: '8px',
        }}>
          Nota metodologica
        </div>
        <p style={{
          fontSize: '0.88rem',
          color: '#7a5a00',
          lineHeight: 1.7,
          margin: 0,
        }}>
          La menor prevalencia observada en pueblos indigenas (60.0 por mil) frente a la
          poblacion general (71.5 por mil) NO significa que los pueblos indigenas tengan menos
          condiciones de capacidades diversas. Esta diferencia refleja: (1) sub-registro censal
          en territorios remotos, (2) barreras linguisticas en la autoidentificacion de
          dificultades, (3) diferencias culturales en la concepcion de &lsquo;dificultad&rsquo;,
          y (4) menor esperanza de vida que reduce la acumulacion de condiciones degenerativas.
        </p>
      </div>

      {/* Charts Row 2: Sex + Age (derivados de la piramide con capacidades diversas) */}
      {(() => {
        const piramide = piramideDiscData?.piramide || [];
        const totalH = piramideDiscData?.total_hombres || 0;
        const totalM = piramideDiscData?.total_mujeres || 0;
        const totalPD = totalH + totalM;
        const sexoData = totalPD > 0
          ? [
              { name: 'Hombres', value: Number(((totalH / totalPD) * 100).toFixed(1)), absoluto: totalH, color: '#4A90D9' },
              { name: 'Mujeres', value: Number(((totalM / totalPD) * 100).toFixed(1)), absoluto: totalM, color: '#E74C3C' },
            ]
          : SEXO_DATA;
        const edadData = piramide.length > 0
          ? piramide.map((r) => ({ rango: r.grupo_edad, personas: (r.hombres_abs || 0) + (r.mujeres_abs || 0) }))
          : EDAD_DATA;
        return (
          <div className="grid-row grid-2">
            <div style={cardStyle}>
              <div style={chartTitle}>Distribucion por sexo (con capacidades diversas)</div>
              <ResponsiveContainer width="100%" height={280}>
                <PieChart>
                  <Pie
                    data={sexoData}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={3}
                    label={({ name, value }) => `${name}: ${value}%`}
                  >
                    {sexoData.map((entry, i) => (
                      <Cell key={i} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(v, n, p) => [`${v}% (${formatNumber(p.payload.absoluto || 0)})`, p.payload.name]} />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
              <div style={{ fontSize: '0.72rem', color: 'var(--color-gray-400)', textAlign: 'center', marginTop: '4px' }}>
                {totalPD > 0 ? `Total: ${formatNumber(totalPD)} personas · ${scopeLabel}` : '(Datos nacionales CNPV 2018)'}
              </div>
            </div>

            <div style={cardStyle}>
              <div style={chartTitle}>Distribucion por grupo de edad (con capacidades diversas)</div>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={edadData} margin={{ top: 10, right: 20, bottom: 5, left: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e8e8e8" />
                  <XAxis dataKey="rango" tick={{ fontSize: 10 }} angle={-35} textAnchor="end" height={55} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip
                    formatter={(v) => [formatNumber(v), 'Personas']}
                    contentStyle={{ fontSize: '0.85rem' }}
                  />
                  <Bar dataKey="personas" fill="#02432D" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
              <div style={{ fontSize: '0.72rem', color: 'var(--color-gray-400)', textAlign: 'center', marginTop: '4px' }}>
                {piramide.length > 0 ? `CNPV 2018 · ${scopeLabel}` : '(Datos nacionales CNPV 2018)'}
              </div>
            </div>
          </div>
        );
      })()}

      {/* Piramides nacionales (3): poblacion total, con CD, apilada por tipo */}
      <NationalPyramids />

      {/* DidYouKnow callouts */}
      <DidYouKnow
        fact="La prevalencia varia 10 veces entre pueblos: desde 11.2 por mil (Uwa) hasta 133.5 por mil (Kamsa). Esto refleja no solo diferencias reales sino tambien brechas en el acceso a diagnostico."
        source="CNPV 2018 - DANE, analisis por pueblo indigena"
      />
      <DidYouKnow
        fact="Solo el 0.46% de la poblacion indigena con capacidades diversas ha sido caracterizada por el SMT-ONIC. Esto significa que el 99.5% permanece invisible para el sistema de monitoreo propio."
        source="SMT-ONIC 2024 vs CNPV 2018"
      />

      {/* Source note */}
      <div style={{
        textAlign: 'center',
        color: 'var(--color-gray-400)',
        fontSize: '0.78rem',
        marginTop: '12px',
        padding: '12px',
      }}>
        Fuentes: <Term term="CNPV">CNPV 2018</Term> (<Term term="DANE">DANE</Term>),
        Registro Unico de Victimas (<Term term="RUV">RUV</Term>),
        Registro de Localizacion y Caracterizacion de Personas con Capacidades Diversas (<Term term="RLCPD">RLCPD</Term>),
        Sistema de Monitoreo Territorial ONIC (<Term term="SMT">SMT-ONIC</Term>)
      </div>
    </div>
  );
}
