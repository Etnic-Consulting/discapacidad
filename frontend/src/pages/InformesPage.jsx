/* ============================================
   SMT-ONIC v2.0 — Informes (Professional Report Generator)
   Produces institutional-quality printable documents
   ============================================ */

import { useState, useCallback, useRef, useMemo } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ReferenceLine,
  ResponsiveContainer,
} from 'recharts';
import KPICard from '../components/KPICard';
import {
  usePerfilPueblo, usePrevalenciaDpto, useResguardosList,
  usePiramideDemografica, usePueblos, useNbiPueblos,
  useViviendaPueblo, useLenguaPueblos, useTerritoriosPueblo,
  usePiramideCapDiversas,
} from '../hooks/useApi';
import { DEPARTAMENTOS, PUEBLOS_LIST } from '../components/GlobalSelector';

function fmt(n) {
  return new Intl.NumberFormat('es-CO').format(n);
}

const REPORT_TYPES = [
  { id: 'pueblo', label: 'Por pueblo' },
  { id: 'departamento', label: 'Por departamento' },
  { id: 'resguardo', label: 'Por resguardo' },
];

/* National reference values (indigenous average, not general population) */
const NACIONAL = {
  prevalencia: 60.0,
  totalPersonas: 225174,
  pueblos: 121,
};

const fechaHoy = () => new Date().toLocaleDateString('es-CO', { year: 'numeric', month: 'long', day: 'numeric' });

/* ============================================
   REPORT COVER PAGE
   ============================================ */
function ReportCover({ titulo, subtitulo }) {
  return (
    <div className="report-cover">
      {/* Green institutional bar */}
      <div className="report-cover__bar" />

      <div className="report-cover__body">
        <div className="report-cover__org">
          <div className="report-cover__org-name">
            ORGANIZACION NACIONAL INDIGENA<br />DE COLOMBIA — ONIC
          </div>
          <div className="report-cover__system">
            Sistema de Monitoreo Territorial<br />
            Modulo de Capacidades Diversas
          </div>
        </div>

        <div className="report-cover__divider" />

        <h1 className="report-cover__title">{titulo}</h1>
        {subtitulo && <p className="report-cover__subtitle">{subtitulo}</p>}

        <div className="report-cover__meta">
          <p>Censo Nacional de Poblacion y Vivienda 2018</p>
          <p>Generado: {fechaHoy()}</p>
          <p>Convenio ONIC-AISO</p>
          <p>Ministerio de Igualdad y Equidad</p>
        </div>

        <div className="report-cover__footer">
          <p>NIT 860.521.808-1</p>
          <p>Calle 12B No. 4-38, Bogota D.C.</p>
          <p>poblacion@onic.org.co</p>
        </div>
      </div>
    </div>
  );
}

/* ============================================
   REPORT PAGE FOOTER (printed on each page via CSS)
   ============================================ */
function ReportSourceFooter() {
  return (
    <div className="report-footer">
      <p>Fuente: CNPV 2018 (DANE) procesado por SMT-ONIC</p>
      <p>Este informe fue generado automaticamente. Los datos corresponden al Censo 2018.</p>
      <p>ONIC — Sistema de Monitoreo Territorial — {new Date().getFullYear()}</p>
    </div>
  );
}

/* ============================================
   REPORT TABLE STYLES (shared)
   ============================================ */
const tblCell = { padding: '6px 10px', fontSize: '0.8rem', borderBottom: '1px solid #ddd' };
const tblHead = {
  ...tblCell,
  fontWeight: 600,
  fontSize: '0.72rem',
  textTransform: 'uppercase',
  color: '#555',
  background: '#f5f5f5',
  borderBottom: '2px solid #ccc',
};

/* ============================================
   PUEBLO REPORT — Professional multi-page layout
   ============================================ */
function PuebloReport({ codPueblo, puebloNombre }) {
  const { data: apiPerfil, isLoading, isError } = usePerfilPueblo(codPueblo);
  const { data: piramideData } = usePiramideDemografica(codPueblo);
  const { data: nbiData } = useNbiPueblos(codPueblo);
  const { data: viviendaData } = useViviendaPueblo(codPueblo);
  const { data: lenguaData } = useLenguaPueblos(codPueblo);
  const { data: territoriosData } = useTerritoriosPueblo(codPueblo);
  const { data: piramideCapDiv } = usePiramideCapDiversas(codPueblo);

  if (isLoading) return <div className="loading-container"><div className="spinner" /><p>Cargando perfil...</p></div>;
  if (isError) return <div className="error-container"><p>Error cargando datos del pueblo</p></div>;

  const prevalencia = apiPerfil?.prevalencia || {};
  const nombre = prevalencia.pueblo || puebloNombre || codPueblo;
  const poblacion = prevalencia.total || 0;
  const conCapDiv = prevalencia.con_discapacidad || 0;
  const tasa = prevalencia.tasa_x_1000 || 0;

  const limitaciones = apiPerfil?.limitaciones
    ? apiPerfil.limitaciones.map((l) => ({ dificultad: l.limitacion, value: l.valor }))
    : [];
  const sortedLimitaciones = [...limitaciones].sort((a, b) => (b.value || 0) - (a.value || 0));

  const causas = apiPerfil?.causas || [];
  const tratamiento = apiPerfil?.tratamiento || [];
  const enfermedad = apiPerfil?.enfermedad || null;

  const sexoData = apiPerfil?.sexo || {};
  const hombres = sexoData.hombres || 0;
  const mujeres = sexoData.mujeres || 0;

  // Territories data
  const territorios = territoriosData?.data || [];

  // NBI
  const nbiValue = nbiData?.nbi ?? nbiData?.pct_nbi ?? null;

  // Vivienda services
  const viviendaRows = viviendaData?.data || (Array.isArray(viviendaData) ? viviendaData : []);
  const sinAcueducto = viviendaData?.sin_acueducto ?? (() => {
    const r = viviendaRows.find((v) => (v.servicio || v.variable || '').toLowerCase().includes('acueducto'));
    return r ? (r.sin_servicio_pct || r.pct_sin || r.valor || null) : null;
  })();
  const sinEnergia = viviendaData?.sin_energia ?? (() => {
    const r = viviendaRows.find((v) => (v.servicio || v.variable || '').toLowerCase().includes('energia') || (v.servicio || v.variable || '').toLowerCase().includes('electr'));
    return r ? (r.sin_servicio_pct || r.pct_sin || r.valor || null) : null;
  })();

  // Lengua
  const hablaLengua = lenguaData?.habla_lengua_pct ?? (() => {
    const rows = lenguaData?.data || (Array.isArray(lenguaData) ? lenguaData : []);
    const r = rows.find((v) => (v.categoria || v.variable || '').toLowerCase().includes('habla'));
    return r ? (r.pct || r.valor || null) : null;
  })();

  // Enfermedad funnel
  const enfTotal = enfermedad ? (enfermedad.enfermo_si || 0) + (enfermedad.enfermo_no || 0) + (enfermedad.no_informa || 0) : 0;
  const enfSi = enfermedad?.enfermo_si || 0;
  const enfPctSi = enfTotal > 0 ? ((enfSi / enfTotal) * 100).toFixed(1) : null;

  // Treatment analysis
  const tratTotal = tratamiento.reduce((s, t) => s + (t.valor || 0), 0);
  const formalKeys = ['Medico', 'Hospital', 'EPS', 'IPS', 'Centro de salud'];
  const ancestralKeys = ['Curandero', 'Medico tradicional', 'Partera', 'Plantas medicinales', 'Medicina ancestral'];
  const formalVal = tratamiento.filter((t) =>
    formalKeys.some((k) => (t.tratamiento || t.nombre || '').toLowerCase().includes(k.toLowerCase()))
  ).reduce((s, t) => s + (t.valor || 0), 0);
  const ancestralVal = tratamiento.filter((t) =>
    ancestralKeys.some((k) => (t.tratamiento || t.nombre || '').toLowerCase().includes(k.toLowerCase()))
  ).reduce((s, t) => s + (t.valor || 0), 0);
  const formalPct = tratTotal > 0 ? ((formalVal / tratTotal) * 100).toFixed(1) : null;
  const ancestralPct = tratTotal > 0 ? ((ancestralVal / tratTotal) * 100).toFixed(1) : null;

  // ======== PAGE 1: COVER ========
  // ======== PAGE 2: EXECUTIVE SUMMARY ========
  // ======== PAGE 3: DEMOGRAPHIC PROFILE ========
  // ======== PAGE 4: CAPABILITIES ========
  // ======== PAGE 5: CAUSES & HEALTH ========
  // ======== PAGE 6: TERRITORIAL CONTEXT ========
  // ======== PAGE 7: FINDINGS & RECOMMENDATIONS ========

  return (
    <div className="report-document">
      {/* ═══════════════ PAGE 1: COVER ═══════════════ */}
      <ReportCover
        titulo={`INFORME: PUEBLO ${nombre.toUpperCase()}`}
        subtitulo="Capacidades Diversas en Pueblos Indigenas"
      />

      {/* ═══════════════ PAGE 2: RESUMEN EJECUTIVO ═══════════════ */}
      <div className="report-section">
        <h2 className="report-section__title">1. Resumen Ejecutivo</h2>

        <div className="report-kpi-grid">
          <div className="report-kpi">
            <div className="report-kpi__label">Poblacion Total</div>
            <div className="report-kpi__value">{fmt(poblacion)}</div>
            <div className="report-kpi__sub">CNPV 2018</div>
          </div>
          <div className="report-kpi">
            <div className="report-kpi__label">Con Capacidades Diversas</div>
            <div className="report-kpi__value">{fmt(conCapDiv)}</div>
            <div className="report-kpi__sub">Personas</div>
          </div>
          <div className="report-kpi">
            <div className="report-kpi__label">Prevalencia</div>
            <div className="report-kpi__value">{tasa.toFixed ? tasa.toFixed(1) : tasa}{'\u2030'}</div>
            <div className="report-kpi__sub">Tasa por mil hab.</div>
          </div>
          <div className="report-kpi">
            <div className="report-kpi__label">Promedio Indigena Nacional</div>
            <div className="report-kpi__value">{NACIONAL.prevalencia}{'\u2030'}</div>
            <div className="report-kpi__sub">Referencia</div>
          </div>
        </div>

        <div className="report-comparison">
          <strong>Comparacion:</strong> La prevalencia de capacidades diversas del pueblo {nombre} es
          de {tasa.toFixed ? tasa.toFixed(1) : tasa}{'\u2030'}, <strong>{tasa < NACIONAL.prevalencia ? 'inferior' : 'superior'}</strong> al
          promedio indigena nacional de {NACIONAL.prevalencia}{'\u2030'}.
          {tasa < NACIONAL.prevalencia && ' Esto puede indicar sub-registro en los territorios de este pueblo.'}
          {tasa > NACIONAL.prevalencia * 1.5 && ` Esto indica una situacion critica que requiere atencion prioritaria.`}
        </div>

        <div className="report-findings-summary">
          <h3>Hallazgos principales</h3>
          <ol>
            <li>
              {tasa >= NACIONAL.prevalencia
                ? `La prevalencia es ${((tasa / NACIONAL.prevalencia) * 100 - 100).toFixed(0)}% superior al promedio indigena nacional.`
                : `La prevalencia es ${((1 - tasa / NACIONAL.prevalencia) * 100).toFixed(0)}% inferior al promedio indigena nacional.`
              }
            </li>
            {sortedLimitaciones.length > 0 && (
              <li>
                Las principales dificultades funcionales son: {sortedLimitaciones.slice(0, 3).map((l) => l.dificultad).join(', ')}.
              </li>
            )}
            {causas.length > 0 && (
              <li>
                La principal causa de capacidades diversas es {(causas.sort((a, b) => (b.valor || 0) - (a.valor || 0))[0]?.causa || causas[0]?.nombre || 'no identificada')} ({causas[0]?.valor || 0}%).
              </li>
            )}
          </ol>
        </div>

        <ReportSourceFooter />
      </div>

      {/* ═══════════════ PAGE 3: PERFIL DEMOGRAFICO ═══════════════ */}
      <div className="report-section">
        <h2 className="report-section__title">2. Perfil Demografico</h2>

        {piramideData && piramideData.piramide && piramideData.piramide.length > 0 && (() => {
          const { piramide, total, total_hombres, total_mujeres, razon_masculinidad, indice_dependencia, indice_envejecimiento } = piramideData;
          const pctH = total > 0 ? ((total_hombres / total) * 100).toFixed(1) : '0.0';
          const pctM = total > 0 ? ((total_mujeres / total) * 100).toFixed(1) : '0.0';

          const pctData = piramide.map((row) => ({
            grupo_edad: row.grupo_edad,
            hombres_pct: -(row.pct_hombres || (total > 0 ? (Math.abs(row.hombres_abs || row.hombres || 0) / total) * 100 : 0)),
            mujeres_pct: row.pct_mujeres || (total > 0 ? (Math.abs(row.mujeres_abs || row.mujeres || 0) / total) * 100 : 0),
            hombres_abs: row.hombres_abs || Math.abs(row.hombres || 0),
            mujeres_abs: row.mujeres_abs || Math.abs(row.mujeres || 0),
            pct_hombres_raw: row.pct_hombres || (total > 0 ? (Math.abs(row.hombres_abs || row.hombres || 0) / total) * 100 : 0),
            pct_mujeres_raw: row.pct_mujeres || (total > 0 ? (Math.abs(row.mujeres_abs || row.mujeres || 0) / total) * 100 : 0),
          })).slice().reverse();
          const maxPct = Math.max(...pctData.map((r) => Math.max(Math.abs(r.hombres_pct), Math.abs(r.mujeres_pct))));
          const axisBound = Math.ceil(maxPct + 1);

          // Grandes grupos
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
          const pctOfTotal = (val) => total > 0 ? ((val / total) * 100).toFixed(1) : '0.0';

          return (
            <>
              <p className="report-text">
                El pueblo {nombre} cuenta con <strong>{fmt(total)}</strong> personas segun el CNPV 2018.
                De estas, <strong style={{ color: '#4A90D9' }}>{fmt(total_hombres)}</strong> son hombres ({pctH}%) y{' '}
                <strong style={{ color: '#E74C3C' }}>{fmt(total_mujeres)}</strong> son mujeres ({pctM}%).
              </p>

              <div className="report-chart-title">Piramide Poblacional — CNPV 2018</div>
              <div className="report-chart-container">
                <ResponsiveContainer width="100%" height={480}>
                  <BarChart layout="vertical" data={pctData} margin={{ top: 5, right: 20, bottom: 20, left: 10 }} stackOffset="sign" barCategoryGap="6%" barGap={0} barSize={16}>
                    <CartesianGrid horizontal={false} strokeDasharray="3 3" stroke="#ddd" />
                    <XAxis
                      type="number"
                      domain={[-axisBound, axisBound]}
                      ticks={Array.from({ length: Math.floor(axisBound) * 2 + 1 }, (_, i) => i - Math.floor(axisBound))}
                      tickFormatter={(v) => `${Math.abs(v)}`}
                      tick={{ fontSize: 9 }}
                      axisLine={{ stroke: '#999' }}
                      label={{ value: '% de la poblacion total', position: 'insideBottom', offset: -12, fontSize: 9, fill: '#666' }}
                    />
                    <YAxis type="category" dataKey="grupo_edad" width={50} tick={{ fontSize: 9, fontWeight: 600 }} axisLine={false} tickLine={false} />
                    <ReferenceLine x={0} stroke="#333" strokeWidth={2} />
                    <Tooltip
                      content={({ active, payload, label }) => {
                        if (!active || !payload || payload.length === 0) return null;
                        const row = payload[0]?.payload;
                        if (!row) return null;
                        return (
                          <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: '6px', padding: '8px 12px', boxShadow: '0 2px 8px rgba(0,0,0,0.12)', fontSize: '0.78rem', lineHeight: 1.6 }}>
                            <div style={{ fontWeight: 700, marginBottom: '3px', color: '#374151' }}>Grupo: {label}</div>
                            <div><span style={{ color: '#4A90D9', fontWeight: 600 }}>Hombres:</span> {fmt(row.hombres_abs)} ({row.pct_hombres_raw.toFixed(2)}%)</div>
                            <div><span style={{ color: '#E74C3C', fontWeight: 600 }}>Mujeres:</span> {fmt(row.mujeres_abs)} ({row.pct_mujeres_raw.toFixed(2)}%)</div>
                          </div>
                        );
                      }}
                    />
                    <Legend formatter={(value) => value === 'hombres_pct' ? 'Hombres' : value === 'mujeres_pct' ? 'Mujeres' : value} />
                    <Bar dataKey="hombres_pct" name="Hombres" fill="#4A90D9" stackId="pyramid" />
                    <Bar dataKey="mujeres_pct" name="Mujeres" fill="#E74C3C" stackId="pyramid" />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Grandes grupos table */}
              <div className="report-chart-title" style={{ marginTop: '16px' }}>Grandes Grupos de Edad</div>
              <table className="report-table">
                <thead>
                  <tr>
                    <th style={tblHead}>Grupo</th>
                    <th style={{ ...tblHead, textAlign: 'right' }}>Hombres</th>
                    <th style={{ ...tblHead, textAlign: 'right' }}>Mujeres</th>
                    <th style={{ ...tblHead, textAlign: 'right' }}>Total</th>
                    <th style={{ ...tblHead, textAlign: 'right' }}>% Pob.</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    { label: '0-14 (Infantil)', data: gInfantil },
                    { label: '15-64 (Productiva)', data: gAdulto },
                    { label: '65+ (Mayor)', data: gMayor },
                  ].map((g, i) => {
                    const gt = g.data.h + g.data.m;
                    return (
                      <tr key={i}>
                        <td style={{ ...tblCell, fontWeight: 600 }}>{g.label}</td>
                        <td style={{ ...tblCell, textAlign: 'right', color: '#4A90D9' }}>{fmt(g.data.h)}</td>
                        <td style={{ ...tblCell, textAlign: 'right', color: '#E74C3C' }}>{fmt(g.data.m)}</td>
                        <td style={{ ...tblCell, textAlign: 'right', fontWeight: 600 }}>{fmt(gt)}</td>
                        <td style={{ ...tblCell, textAlign: 'right' }}>{pctOfTotal(gt)}%</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>

              {/* Demographic indices */}
              <div className="report-indices">
                <div className="report-index-item">
                  <span className="report-index-label">Razon de masculinidad</span>
                  <span className="report-index-value">{razon_masculinidad != null ? razon_masculinidad.toFixed(1) : 'N/D'}</span>
                </div>
                <div className="report-index-item">
                  <span className="report-index-label">Indice de dependencia</span>
                  <span className="report-index-value">{indice_dependencia != null ? indice_dependencia.toFixed(1) : 'N/D'}</span>
                </div>
                <div className="report-index-item">
                  <span className="report-index-label">Indice de envejecimiento</span>
                  <span className="report-index-value">{indice_envejecimiento != null ? indice_envejecimiento.toFixed(1) : 'N/D'}</span>
                </div>
              </div>
            </>
          );
        })()}

        {(!piramideData || !piramideData.piramide || piramideData.piramide.length === 0) && (
          <p className="report-text" style={{ fontStyle: 'italic', color: '#888' }}>
            Datos de piramide poblacional no disponibles para este pueblo.
          </p>
        )}

        <ReportSourceFooter />
      </div>

      {/* ═══════════════ PAGE 4: CAPACIDADES DIVERSAS ═══════════════ */}
      <div className="report-section">
        <h2 className="report-section__title">3. Capacidades Diversas</h2>

        <p className="report-text">
          Del total de <strong>{fmt(poblacion)}</strong> personas del pueblo {nombre},
          <strong> {fmt(conCapDiv)}</strong> presentan al menos una capacidad diversa,
          equivalente a una tasa de <strong>{tasa.toFixed ? tasa.toFixed(1) : tasa} por mil</strong> habitantes.
        </p>

        {/* Pyramid of persons WITH cap diversas */}
        {piramideCapDiv && piramideCapDiv.piramide && piramideCapDiv.piramide.length > 0 && (() => {
          const { piramide, total } = piramideCapDiv;
          const pctData = piramide.map((row) => ({
            grupo_edad: row.grupo_edad,
            hombres_pct: -(total > 0 ? (Math.abs(row.hombres_abs || row.hombres || 0) / total) * 100 : 0),
            mujeres_pct: total > 0 ? (Math.abs(row.mujeres_abs || row.mujeres || 0) / total) * 100 : 0,
            hombres_abs: row.hombres_abs || Math.abs(row.hombres || 0),
            mujeres_abs: row.mujeres_abs || Math.abs(row.mujeres || 0),
          })).slice().reverse();
          const maxPct = Math.max(...pctData.map((r) => Math.max(Math.abs(r.hombres_pct), Math.abs(r.mujeres_pct))), 1);
          const axisBound = Math.ceil(maxPct + 1);

          return (
            <>
              <div className="report-chart-title">Piramide de Personas con Capacidades Diversas</div>
              <div className="report-chart-container">
                <ResponsiveContainer width="100%" height={400}>
                  <BarChart layout="vertical" data={pctData} margin={{ top: 5, right: 20, bottom: 20, left: 10 }} stackOffset="sign" barCategoryGap="6%" barGap={0} barSize={14}>
                    <CartesianGrid horizontal={false} strokeDasharray="3 3" stroke="#ddd" />
                    <XAxis type="number" domain={[-axisBound, axisBound]} tickFormatter={(v) => `${Math.abs(v).toFixed(0)}`} tick={{ fontSize: 9 }} label={{ value: '% del total con cap. diversas', position: 'insideBottom', offset: -12, fontSize: 9, fill: '#666' }} />
                    <YAxis type="category" dataKey="grupo_edad" width={50} tick={{ fontSize: 9, fontWeight: 600 }} axisLine={false} tickLine={false} />
                    <ReferenceLine x={0} stroke="#333" strokeWidth={2} />
                    <Legend formatter={(value) => value === 'hombres_pct' ? 'Hombres' : 'Mujeres'} />
                    <Bar dataKey="hombres_pct" name="Hombres" fill="#4A90D9" stackId="pyramid" />
                    <Bar dataKey="mujeres_pct" name="Mujeres" fill="#E74C3C" stackId="pyramid" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </>
          );
        })()}

        {/* Horizontal bar chart: 9 types of limitation sorted */}
        {sortedLimitaciones.length > 0 && (
          <>
            <div className="report-chart-title" style={{ marginTop: '20px' }}>Tipos de Dificultad Funcional (Washington Group)</div>
            <div className="report-chart-container">
              <ResponsiveContainer width="100%" height={Math.max(280, sortedLimitaciones.length * 36)}>
                <BarChart layout="vertical" data={sortedLimitaciones} margin={{ top: 5, right: 30, bottom: 5, left: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#eee" horizontal={false} />
                  <XAxis type="number" tick={{ fontSize: 9 }} label={{ value: '% de personas con cap. diversas', position: 'insideBottom', offset: -4, fontSize: 9, fill: '#666' }} />
                  <YAxis type="category" dataKey="dificultad" width={140} tick={{ fontSize: 9 }} axisLine={false} tickLine={false} />
                  <Tooltip formatter={(v) => [`${v}%`, 'Prevalencia']} />
                  <Bar dataKey="value" fill="#02432D" radius={[0, 3, 3, 0]} barSize={20} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Table with counts and percentages */}
            <table className="report-table" style={{ marginTop: '12px' }}>
              <thead>
                <tr>
                  <th style={tblHead}>Dificultad funcional</th>
                  <th style={{ ...tblHead, textAlign: 'right' }}>Porcentaje</th>
                </tr>
              </thead>
              <tbody>
                {sortedLimitaciones.map((l, i) => (
                  <tr key={i}>
                    <td style={tblCell}>{l.dificultad}</td>
                    <td style={{ ...tblCell, textAlign: 'right', fontWeight: 600 }}>{l.value}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        )}

        <ReportSourceFooter />
      </div>

      {/* ═══════════════ PAGE 5: CAUSAS Y ACCESO A SALUD ═══════════════ */}
      <div className="report-section">
        <h2 className="report-section__title">4. Causas y Acceso a Salud</h2>

        {/* Causes bar chart */}
        {causas.length > 0 && (() => {
          const sortedCausas = [...causas].sort((a, b) => (b.valor || 0) - (a.valor || 0));
          const causasChart = sortedCausas.map((c) => ({
            nombre: c.causa || c.nombre || 'Desconocida',
            valor: c.valor || 0,
          }));
          return (
            <>
              <div className="report-chart-title">Causa Principal de Capacidades Diversas</div>
              <div className="report-chart-container">
                <ResponsiveContainer width="100%" height={Math.max(250, causasChart.length * 34)}>
                  <BarChart layout="vertical" data={causasChart} margin={{ top: 5, right: 30, bottom: 5, left: 10 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#eee" horizontal={false} />
                    <XAxis type="number" tick={{ fontSize: 9 }} label={{ value: '%', position: 'insideBottom', offset: -4, fontSize: 9, fill: '#666' }} />
                    <YAxis type="category" dataKey="nombre" width={160} tick={{ fontSize: 9 }} axisLine={false} tickLine={false} />
                    <Tooltip formatter={(v) => [`${v}%`, 'Porcentaje']} />
                    <Bar dataKey="valor" fill="#C4920A" radius={[0, 3, 3, 0]} barSize={18} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </>
          );
        })()}

        {/* Treatment bar chart */}
        {tratamiento.length > 0 && (() => {
          const sortedTrat = [...tratamiento].sort((a, b) => (b.valor || 0) - (a.valor || 0));
          const tratChart = sortedTrat.map((t) => ({
            nombre: t.tratamiento || t.nombre || 'Otro',
            valor: t.valor || 0,
          }));
          return (
            <>
              <div className="report-chart-title" style={{ marginTop: '20px' }}>Tratamiento Buscado</div>
              <div className="report-chart-container">
                <ResponsiveContainer width="100%" height={Math.max(200, tratChart.length * 32)}>
                  <BarChart layout="vertical" data={tratChart} margin={{ top: 5, right: 30, bottom: 5, left: 10 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#eee" horizontal={false} />
                    <XAxis type="number" tick={{ fontSize: 9 }} label={{ value: '%', position: 'insideBottom', offset: -4, fontSize: 9, fill: '#666' }} />
                    <YAxis type="category" dataKey="nombre" width={160} tick={{ fontSize: 9 }} axisLine={false} tickLine={false} />
                    <Tooltip formatter={(v) => [`${v}%`, 'Porcentaje']} />
                    <Bar dataKey="valor" fill="#02AB44" radius={[0, 3, 3, 0]} barSize={18} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </>
          );
        })()}

        {/* Health funnel */}
        {enfermedad && (
          <div style={{ marginTop: '20px' }}>
            <div className="report-chart-title">Enfermedad Reciente y Acceso a Salud</div>
            <div className="report-funnel">
              <div className="report-funnel-step">
                <div className="report-funnel-bar" style={{ width: '100%', background: '#02432D' }} />
                <span>Total evaluados: {fmt(enfTotal)}</span>
              </div>
              <div className="report-funnel-step">
                <div className="report-funnel-bar" style={{ width: enfTotal > 0 ? `${(enfSi / enfTotal) * 100}%` : '0%', background: '#C4920A' }} />
                <span>Estuvo enfermo: {fmt(enfSi)} ({enfPctSi}%)</span>
              </div>
              {formalPct && (
                <div className="report-funnel-step">
                  <div className="report-funnel-bar" style={{ width: `${formalPct}%`, background: '#02AB44' }} />
                  <span>Busco atencion formal: {formalPct}%</span>
                </div>
              )}
              {ancestralPct && parseFloat(ancestralPct) > 0 && (
                <div className="report-funnel-step">
                  <div className="report-funnel-bar" style={{ width: `${Math.min(parseFloat(ancestralPct), 100)}%`, background: '#E8262A' }} />
                  <span>Medicina ancestral: {ancestralPct}%</span>
                </div>
              )}
            </div>
          </div>
        )}

        <ReportSourceFooter />
      </div>

      {/* ═══════════════ PAGE 6: CONTEXTO TERRITORIAL ═══════════════ */}
      <div className="report-section">
        <h2 className="report-section__title">5. Contexto Territorial</h2>

        {/* Departments table */}
        {territorios.length > 0 && (
          <>
            <div className="report-chart-title">Departamentos con Presencia del Pueblo {nombre}</div>
            <table className="report-table">
              <thead>
                <tr>
                  <th style={tblHead}>Departamento</th>
                  <th style={{ ...tblHead, textAlign: 'right' }}>Poblacion</th>
                  <th style={{ ...tblHead, textAlign: 'right' }}>Con cap. diversas</th>
                  <th style={{ ...tblHead, textAlign: 'right' }}>Tasa (x1000)</th>
                  <th style={{ ...tblHead, textAlign: 'center' }}>Confiabilidad</th>
                </tr>
              </thead>
              <tbody>
                {territorios.map((t, i) => (
                  <tr key={i}>
                    <td style={{ ...tblCell, fontWeight: 600 }}>{t.nom_dpto || t.departamento || t.cod_dpto}</td>
                    <td style={{ ...tblCell, textAlign: 'right' }}>{fmt(t.total || 0)}</td>
                    <td style={{ ...tblCell, textAlign: 'right' }}>{fmt(t.con_discapacidad || 0)}</td>
                    <td style={{ ...tblCell, textAlign: 'right', fontWeight: 600 }}>
                      {t.tasa_x_1000 != null ? (typeof t.tasa_x_1000 === 'number' ? t.tasa_x_1000.toFixed(1) : t.tasa_x_1000) : 'N/C'}
                    </td>
                    <td style={{ ...tblCell, textAlign: 'center', fontSize: '0.72rem' }}>
                      <span style={{
                        padding: '2px 8px',
                        borderRadius: '8px',
                        background: t.confiabilidad === 'CONFIABLE' ? '#e6f7ed' : '#fde8e8',
                        color: t.confiabilidad === 'CONFIABLE' ? '#02AB44' : '#E8262A',
                        fontWeight: 600,
                      }}>
                        {t.confiabilidad || '--'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        )}

        {/* NBI, IPM, Services, Language */}
        <div className="report-chart-title" style={{ marginTop: '20px' }}>Indicadores de Condiciones de Vida</div>
        <table className="report-table">
          <thead>
            <tr>
              <th style={tblHead}>Indicador</th>
              <th style={{ ...tblHead, textAlign: 'right' }}>Valor</th>
              <th style={tblHead}>Observacion</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td style={tblCell}>NBI (Necesidades Basicas Insatisfechas)</td>
              <td style={{ ...tblCell, textAlign: 'right', fontWeight: 600 }}>
                {nbiValue != null ? `${typeof nbiValue === 'number' ? nbiValue.toFixed(1) : nbiValue}%` : 'N/D'}
              </td>
              <td style={{ ...tblCell, fontSize: '0.75rem', color: '#666' }}>
                {nbiValue != null && nbiValue > 70 ? 'Critico' : nbiValue != null && nbiValue > 50 ? 'Alto' : nbiValue != null ? 'Moderado' : '--'}
              </td>
            </tr>
            <tr>
              <td style={tblCell}>Sin servicio de acueducto</td>
              <td style={{ ...tblCell, textAlign: 'right', fontWeight: 600 }}>
                {sinAcueducto != null ? `${typeof sinAcueducto === 'number' ? sinAcueducto.toFixed(1) : sinAcueducto}%` : 'N/D'}
              </td>
              <td style={{ ...tblCell, fontSize: '0.75rem', color: '#666' }}>
                {sinAcueducto != null && sinAcueducto > 50 ? 'Deficit critico' : sinAcueducto != null ? '--' : '--'}
              </td>
            </tr>
            <tr>
              <td style={tblCell}>Sin servicio de energia electrica</td>
              <td style={{ ...tblCell, textAlign: 'right', fontWeight: 600 }}>
                {sinEnergia != null ? `${typeof sinEnergia === 'number' ? sinEnergia.toFixed(1) : sinEnergia}%` : 'N/D'}
              </td>
              <td style={{ ...tblCell, fontSize: '0.75rem', color: '#666' }}>
                {sinEnergia != null && sinEnergia > 50 ? 'Deficit critico' : sinEnergia != null ? '--' : '--'}
              </td>
            </tr>
            <tr>
              <td style={tblCell}>Habla lengua nativa</td>
              <td style={{ ...tblCell, textAlign: 'right', fontWeight: 600 }}>
                {hablaLengua != null ? `${typeof hablaLengua === 'number' ? hablaLengua.toFixed(1) : hablaLengua}%` : 'N/D'}
              </td>
              <td style={{ ...tblCell, fontSize: '0.75rem', color: '#666' }}>
                {hablaLengua != null && hablaLengua < 30 ? 'Riesgo de extincion linguistica' : hablaLengua != null ? '--' : '--'}
              </td>
            </tr>
          </tbody>
        </table>

        <ReportSourceFooter />
      </div>

      {/* ═══════════════ PAGE 7: HALLAZGOS Y RECOMENDACIONES ═══════════════ */}
      <div className="report-section">
        <h2 className="report-section__title">6. Hallazgos y Recomendaciones</h2>

        {/* Hallazgos clave */}
        <div className="report-findings">
          <h3>6.1 Hallazgos Clave</h3>
          <ol>
            {/* 1. Prevalence */}
            <li>
              {tasa >= NACIONAL.prevalencia
                ? `El pueblo ${nombre} presenta una prevalencia de ${tasa.toFixed ? tasa.toFixed(1) : tasa} por mil, que es ${((tasa / NACIONAL.prevalencia) * 100 - 100).toFixed(0)}% superior al promedio indigena nacional (${NACIONAL.prevalencia} por mil). Esto posiciona a este pueblo entre los de mayor afectacion.`
                : `El pueblo ${nombre} presenta una prevalencia de ${tasa.toFixed ? tasa.toFixed(1) : tasa} por mil, que es ${((1 - tasa / NACIONAL.prevalencia) * 100).toFixed(0)}% inferior al promedio indigena nacional (${NACIONAL.prevalencia} por mil). Es posible que exista sub-registro.`
              }
            </li>

            {/* 2. Top limitations */}
            {sortedLimitaciones.length > 0 && (
              <li>
                Las dificultades funcionales mas prevalentes son:{' '}
                {sortedLimitaciones.slice(0, 3).map((l, i) => (
                  <span key={i}>{i > 0 ? (i === Math.min(2, sortedLimitaciones.length - 1) ? ' y ' : ', ') : ''}<strong>{l.dificultad}</strong> ({l.value}%)</span>
                ))}.
              </li>
            )}

            {/* 3. Health access */}
            {formalPct && (
              <li>
                Del total de tratamientos buscados, el <strong>{formalPct}%</strong> corresponde a atencion formal
                {ancestralPct && parseFloat(ancestralPct) > 0 ? ` y el ${ancestralPct}% a medicina ancestral` : ''}.
                {parseFloat(formalPct) < 50 ? ' Se evidencia una barrera significativa de acceso al sistema de salud formal.' : ''}
              </li>
            )}

            {/* 4. Top cause */}
            {causas.length > 0 && (() => {
              const sorted = [...causas].sort((a, b) => (b.valor || 0) - (a.valor || 0));
              const top = sorted[0];
              return (
                <li>
                  La causa principal de capacidades diversas es <strong>{top.causa || top.nombre || 'Desconocida'}</strong> ({top.valor || 0}%).
                  {(top.causa || top.nombre || '').toLowerCase().includes('conflicto') && ' Esto se vincula directamente con el conflicto armado y exige articulacion con rutas de reparacion.'}
                  {(top.causa || top.nombre || '').toLowerCase().includes('nacimiento') && ' Esto sugiere factores geneticos o condiciones prenatales que requieren atencion en salud materno-infantil.'}
                </li>
              );
            })()}

            {/* 5. Enfermedad */}
            {enfPctSi && (
              <li>
                El <strong>{enfPctSi}%</strong> de las personas con capacidades diversas reporto haber estado enfermo recientemente,
                lo que indica {parseFloat(enfPctSi) > 50 ? 'una alta carga de morbilidad asociada' : 'condiciones de salud que requieren seguimiento'}.
              </li>
            )}

            {/* 6. Territorial */}
            {territorios.length > 0 && (
              <li>
                El pueblo {nombre} tiene presencia en <strong>{territorios.length}</strong> departamento{territorios.length > 1 ? 's' : ''}.
                {territorios.length > 1 ? ` El mayor asentamiento esta en ${territorios[0]?.nom_dpto || territorios[0]?.departamento || '--'} con ${fmt(territorios[0]?.total || 0)} personas.` : ''}
              </li>
            )}

            {/* 7. NBI */}
            {nbiValue != null && nbiValue > 50 && (
              <li>
                El NBI del pueblo es de <strong>{typeof nbiValue === 'number' ? nbiValue.toFixed(1) : nbiValue}%</strong>,
                lo que indica un nivel {nbiValue > 70 ? 'critico' : 'alto'} de necesidades basicas insatisfechas.
              </li>
            )}

            {/* 8. Language */}
            {hablaLengua != null && hablaLengua < 30 && (
              <li>
                Solo el <strong>{typeof hablaLengua === 'number' ? hablaLengua.toFixed(1) : hablaLengua}%</strong> de la poblacion habla lengua nativa propia,
                lo que representa un riesgo de extincion linguistica.
              </li>
            )}
          </ol>
        </div>

        {/* Recomendaciones de politica publica */}
        <div className="report-recommendations">
          <h3>6.2 Recomendaciones de Politica Publica</h3>
          <ol>
            {/* High prevalence */}
            {tasa > 80 && (
              <li>
                <strong>Prevalencia critica:</strong> Priorizar jornadas de certificacion de capacidades diversas
                en territorios del pueblo {nombre}. Coordinar con EPS-I y Secretarias de Salud departamentales.
              </li>
            )}

            {/* Health alert */}
            {tasa > 100 && (
              <li>
                <strong>Alerta de salud publica:</strong> Con una tasa de {tasa.toFixed ? tasa.toFixed(1) : tasa} por mil,
                se recomienda declarar alerta de salud publica diferencial para el pueblo {nombre}.
              </li>
            )}

            {/* Conflict */}
            {causas.length > 0 && (() => {
              const sorted = [...causas].sort((a, b) => (b.valor || 0) - (a.valor || 0));
              return (sorted[0]?.causa || sorted[0]?.nombre || '').toLowerCase().includes('conflicto');
            })() && (
              <li>
                <strong>Conflicto armado como causa principal:</strong> Articular con rutas de reparacion integral
                de la UARIV y programas de atencion psicosocial del Ministerio de Salud.
              </li>
            )}

            {/* Mobility */}
            {sortedLimitaciones.length > 0 && (() => {
              const topLim = (sortedLimitaciones[0]?.dificultad || '').toLowerCase();
              return topLim.includes('caminar') || topLim.includes('moverse') || topLim.includes('desplaz');
            })() && (
              <li>
                <strong>Movilidad como principal dificultad:</strong> Gestionar ayudas tecnicas de movilidad
                (sillas de ruedas, bastones, muletas) con EPS-I y Secretaria de Salud.
              </li>
            )}

            {/* Poverty */}
            {nbiValue != null && nbiValue > 70 && (
              <li>
                <strong>Pobreza multidimensional critica (NBI: {typeof nbiValue === 'number' ? nbiValue.toFixed(1) : nbiValue}%):</strong>{' '}
                Priorizar inclusion en programas de superacion de pobreza (Mas Familias en Accion, Colombia Mayor).
              </li>
            )}

            {/* Water */}
            {sinAcueducto != null && sinAcueducto > 50 && (
              <li>
                <strong>Deficit de acueducto ({typeof sinAcueducto === 'number' ? sinAcueducto.toFixed(1) : sinAcueducto}% sin servicio):</strong>{' '}
                Incluir en planes departamentales de agua y saneamiento basico.
              </li>
            )}

            {/* Language */}
            {hablaLengua != null && hablaLengua < 30 && (
              <li>
                <strong>Riesgo de extincion linguistica ({typeof hablaLengua === 'number' ? hablaLengua.toFixed(1) : hablaLengua}%):</strong>{' '}
                Activar protocolos de salvaguarda linguistica (Ley 1381 de 2010).
              </li>
            )}

            {/* Traditional medicine */}
            {ancestralPct && parseFloat(ancestralPct) > 10 && (
              <li>
                <strong>Medicina ancestral relevante ({ancestralPct}%):</strong>{' '}
                Fortalecer la articulacion entre medicina ancestral y sistema formal (SISPI).
              </li>
            )}

            {/* Placeholder */}
            <li style={{ color: '#999', fontStyle: 'italic' }}>
              [Completar] Acciones priorizadas por el equipo tecnico para este pueblo.
            </li>
            <li style={{ color: '#999', fontStyle: 'italic' }}>
              [Completar] Fecha estimada de implementacion.
            </li>
            <li style={{ color: '#999', fontStyle: 'italic' }}>
              [Completar] Responsable.
            </li>
          </ol>
        </div>

        {/* Data quality note */}
        <div className="report-note">
          <strong>Nota sobre calidad de datos:</strong> Los datos provienen del Censo Nacional de
          Poblacion y Vivienda (CNPV) 2018. La medicion de capacidades diversas en pueblos indigenas
          puede presentar sub-registro debido a barreras linguisticas, culturales y de acceso
          geografico. El SMT-ONIC trabaja en complementar estos datos con registros propios de las
          organizaciones indigenas.
        </div>

        <ReportSourceFooter />
      </div>
    </div>
  );
}

/* ============================================
   DEPARTAMENTO REPORT — Professional multi-page layout
   ============================================ */
function DepartamentoReport({ codDpto, dptoNombre }) {
  const { data: apiData, isLoading, isError } = usePrevalenciaDpto('Indigena');
  const { data: allPueblosData } = usePueblos();

  if (isLoading) return <div className="loading-container"><div className="spinner" /><p>Cargando datos departamentales...</p></div>;
  if (isError) return <div className="error-container"><p>Error cargando datos</p></div>;

  const allDptoData = Array.isArray(apiData?.data) ? apiData.data : [];
  const dptoRows = allDptoData.filter((d) => String(d.cod_dpto) === String(codDpto));
  const row = dptoRows[0] || {};
  const nombre = dptoNombre || row.nom_dpto || row.departamento || 'Departamento';
  const poblacion = row.pob_total || row.total || 0;
  const conCapDiv = row.pob_disc || row.con_discapacidad || 0;
  const tasa = row.tasa_x_1000 || 0;

  // Try to find pueblos in this department from all department data
  // The prevalencia/departamento endpoint returns per-department stats
  // We'll also look for a list of pueblos if available
  const pueblosEnDpto = useMemo(() => {
    if (!allPueblosData?.data) return [];
    // We don't have per-department pueblos data from this endpoint,
    // but we can show all pueblos as reference.
    return [];
  }, [allPueblosData]);

  // Top/bottom departments for comparison
  const sortedDptos = useMemo(() => {
    return [...allDptoData]
      .filter((d) => d.tasa_x_1000 != null && d.tasa_x_1000 > 0)
      .sort((a, b) => (b.tasa_x_1000 || 0) - (a.tasa_x_1000 || 0));
  }, [allDptoData]);

  const dptoRank = sortedDptos.findIndex((d) => String(d.cod_dpto) === String(codDpto)) + 1;

  // Chart data: all departments sorted by prevalence for horizontal bar
  const dptoChartData = useMemo(() => {
    return sortedDptos.slice(0, 15).map((d) => ({
      nombre: d.nom_dpto || d.departamento || d.cod_dpto,
      tasa: d.tasa_x_1000 || 0,
      esActual: String(d.cod_dpto) === String(codDpto),
    }));
  }, [sortedDptos, codDpto]);

  return (
    <div className="report-document">
      {/* ═══════════════ PAGE 1: COVER ═══════════════ */}
      <ReportCover
        titulo={`INFORME DEPARTAMENTAL: ${nombre.toUpperCase()}`}
        subtitulo="Capacidades Diversas en Poblacion Indigena"
      />

      {/* ═══════════════ PAGE 2: RESUMEN EJECUTIVO ═══════════════ */}
      <div className="report-section">
        <h2 className="report-section__title">1. Resumen Ejecutivo</h2>

        <div className="report-kpi-grid">
          <div className="report-kpi">
            <div className="report-kpi__label">Poblacion Indigena</div>
            <div className="report-kpi__value">{fmt(poblacion)}</div>
            <div className="report-kpi__sub">CNPV 2018</div>
          </div>
          <div className="report-kpi">
            <div className="report-kpi__label">Con Capacidades Diversas</div>
            <div className="report-kpi__value">{fmt(conCapDiv)}</div>
            <div className="report-kpi__sub">Personas</div>
          </div>
          <div className="report-kpi">
            <div className="report-kpi__label">Prevalencia</div>
            <div className="report-kpi__value">{tasa.toFixed ? tasa.toFixed(1) : tasa}{'\u2030'}</div>
            <div className="report-kpi__sub">Tasa por mil hab.</div>
          </div>
          <div className="report-kpi">
            <div className="report-kpi__label">Ranking Departamental</div>
            <div className="report-kpi__value">{dptoRank > 0 ? `#${dptoRank}` : 'N/D'}</div>
            <div className="report-kpi__sub">de {sortedDptos.length} departamentos</div>
          </div>
        </div>

        <div className="report-comparison">
          <strong>Comparacion:</strong> La prevalencia de capacidades diversas en la poblacion
          indigena de {nombre} es de {tasa.toFixed ? tasa.toFixed(1) : tasa}{'\u2030'},
          <strong>{tasa < NACIONAL.prevalencia ? ' inferior' : ' superior'}</strong> al promedio
          indigena nacional de {NACIONAL.prevalencia}{'\u2030'}.
          {dptoRank > 0 && dptoRank <= 5 && ` Este departamento se encuentra entre los 5 con mayor prevalencia a nivel nacional.`}
        </div>

        <ReportSourceFooter />
      </div>

      {/* ═══════════════ PAGE 3: COMPARACION DEPARTAMENTAL ═══════════════ */}
      <div className="report-section">
        <h2 className="report-section__title">2. Comparacion Departamental</h2>

        <p className="report-text">
          A continuacion se presenta la comparacion de prevalencia de capacidades diversas
          en la poblacion indigena entre los departamentos con mayor afectacion.
          {nombre && ` ${nombre} se resalta en la grafica.`}
        </p>

        {dptoChartData.length > 0 && (
          <div className="report-chart-container">
            <ResponsiveContainer width="100%" height={Math.max(350, dptoChartData.length * 28)}>
              <BarChart layout="vertical" data={dptoChartData} margin={{ top: 5, right: 30, bottom: 5, left: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#eee" horizontal={false} />
                <XAxis type="number" tick={{ fontSize: 9 }} label={{ value: 'Tasa por mil', position: 'insideBottom', offset: -4, fontSize: 9, fill: '#666' }} />
                <YAxis type="category" dataKey="nombre" width={120} tick={{ fontSize: 9 }} axisLine={false} tickLine={false} />
                <ReferenceLine x={NACIONAL.prevalencia} stroke="#E8262A" strokeDasharray="4 4" label={{ value: `Promedio: ${NACIONAL.prevalencia}`, position: 'top', fontSize: 9, fill: '#E8262A' }} />
                <Tooltip formatter={(v) => [`${v.toFixed(1)}\u2030`, 'Prevalencia']} />
                <Bar
                  dataKey="tasa"
                  radius={[0, 3, 3, 0]}
                  barSize={18}
                  fill="#02432D"
                  // eslint-disable-next-line react/no-unstable-nested-components
                  shape={(props) => {
                    const { x, y, width, height, payload } = props;
                    return (
                      <rect
                        x={x}
                        y={y}
                        width={width}
                        height={height}
                        fill={payload.esActual ? '#C4920A' : '#02432D'}
                        rx={3}
                        ry={3}
                      />
                    );
                  }}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Full table of all departments */}
        <div className="report-chart-title" style={{ marginTop: '20px' }}>Tabla Completa por Departamento</div>
        <table className="report-table">
          <thead>
            <tr>
              <th style={tblHead}>#</th>
              <th style={tblHead}>Departamento</th>
              <th style={{ ...tblHead, textAlign: 'right' }}>Pob. Indigena</th>
              <th style={{ ...tblHead, textAlign: 'right' }}>Con cap. diversas</th>
              <th style={{ ...tblHead, textAlign: 'right' }}>Tasa (x1000)</th>
            </tr>
          </thead>
          <tbody>
            {sortedDptos.map((d, i) => {
              const isThis = String(d.cod_dpto) === String(codDpto);
              return (
                <tr key={i} style={isThis ? { background: '#fdf3dc', fontWeight: 600 } : {}}>
                  <td style={tblCell}>{i + 1}</td>
                  <td style={{ ...tblCell, fontWeight: isThis ? 700 : 400 }}>
                    {d.nom_dpto || d.departamento || d.cod_dpto}
                    {isThis ? ' *' : ''}
                  </td>
                  <td style={{ ...tblCell, textAlign: 'right' }}>{fmt(d.pob_total || d.total || 0)}</td>
                  <td style={{ ...tblCell, textAlign: 'right' }}>{fmt(d.pob_disc || d.con_discapacidad || 0)}</td>
                  <td style={{ ...tblCell, textAlign: 'right', fontWeight: 600 }}>
                    {(d.tasa_x_1000 || 0).toFixed(1)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>

        <ReportSourceFooter />
      </div>

      {/* ═══════════════ PAGE 4: HALLAZGOS Y RECOMENDACIONES ═══════════════ */}
      <div className="report-section">
        <h2 className="report-section__title">3. Hallazgos y Recomendaciones</h2>

        <div className="report-findings">
          <h3>3.1 Hallazgos</h3>
          <ol>
            <li>
              {nombre} tiene una poblacion indigena de <strong>{fmt(poblacion)}</strong> personas,
              de las cuales <strong>{fmt(conCapDiv)}</strong> ({poblacion > 0 ? ((conCapDiv / poblacion) * 100).toFixed(1) : 0}%)
              presentan al menos una capacidad diversa.
            </li>
            <li>
              La tasa de {tasa.toFixed ? tasa.toFixed(1) : tasa} por mil es{' '}
              {tasa < NACIONAL.prevalencia ? 'inferior' : 'superior'} al promedio indigena nacional ({NACIONAL.prevalencia} por mil).
              {dptoRank > 0 && ` Ocupa el puesto ${dptoRank} de ${sortedDptos.length} departamentos.`}
            </li>
            {tasa < NACIONAL.prevalencia * 0.5 && (
              <li>
                La tasa significativamente baja puede indicar sub-registro censal en la poblacion
                indigena de este departamento, o barreras de acceso que impiden la identificacion.
              </li>
            )}
            {tasa > NACIONAL.prevalencia * 1.5 && (
              <li>
                La prevalencia es significativamente alta, lo que puede reflejar condiciones
                socioeconomicas criticas, exposicion al conflicto armado, o factores ambientales.
              </li>
            )}
          </ol>
        </div>

        <div className="report-recommendations">
          <h3>3.2 Recomendaciones</h3>
          <ol>
            {tasa > 80 && (
              <li>Priorizar jornadas de certificacion de capacidades diversas en municipios con presencia indigena.</li>
            )}
            {tasa < NACIONAL.prevalencia * 0.5 && (
              <li>Realizar jornadas de busqueda activa para reducir el sub-registro en poblacion indigena.</li>
            )}
            <li>
              Articular con la Secretaria de Salud departamental para garantizar rutas de atencion
              diferencial en los municipios con mayor concentracion de poblacion indigena.
            </li>
            <li style={{ color: '#999', fontStyle: 'italic' }}>
              [Completar] Acciones priorizadas por el equipo tecnico para este departamento.
            </li>
            <li style={{ color: '#999', fontStyle: 'italic' }}>
              [Completar] Fecha y responsable.
            </li>
          </ol>
        </div>

        {/* Data quality note */}
        <div className="report-note">
          <strong>Nota sobre calidad de datos:</strong> Las estadisticas departamentales agregan la
          informacion de todos los municipios con presencia indigena. La distribucion intra-departamental
          puede variar significativamente entre municipios urbanos y rurales.
        </div>

        <ReportSourceFooter />
      </div>
    </div>
  );
}

/* ============================================
   RESGUARDO REPORT (kept simple — data limited)
   ============================================ */
function ResguardoReport({ resguardoData }) {
  if (!resguardoData) return null;

  const nombre = resguardoData.nombre || resguardoData.territorio || 'Resguardo';
  const pueblo = resguardoData.pueblo || '--';
  const departamento = resguardoData.departamento || resguardoData.nom_dpto || '--';
  const municipio = resguardoData.municipio || resguardoData.nom_mpio || '--';
  const area = resguardoData.area_ha || resguardoData.area || null;

  return (
    <div className="report-document">
      <ReportCover
        titulo={`INFORME: RESGUARDO ${nombre.toUpperCase()}`}
        subtitulo="Informacion Territorial"
      />

      <div className="report-section">
        <h2 className="report-section__title">1. Informacion del Resguardo</h2>

        <table className="report-table">
          <tbody>
            <tr>
              <td style={{ ...tblCell, fontWeight: 600, width: '200px' }}>Territorio</td>
              <td style={tblCell}>{nombre}</td>
            </tr>
            <tr>
              <td style={{ ...tblCell, fontWeight: 600 }}>Pueblo</td>
              <td style={tblCell}>{pueblo}</td>
            </tr>
            <tr>
              <td style={{ ...tblCell, fontWeight: 600 }}>Departamento</td>
              <td style={tblCell}>{departamento}</td>
            </tr>
            <tr>
              <td style={{ ...tblCell, fontWeight: 600 }}>Municipio</td>
              <td style={tblCell}>{municipio}</td>
            </tr>
            {area != null && (
              <tr>
                <td style={{ ...tblCell, fontWeight: 600 }}>Area</td>
                <td style={tblCell}>{fmt(area)} ha</td>
              </tr>
            )}
          </tbody>
        </table>

        <div className="report-note" style={{ marginTop: '20px' }}>
          <strong>Nota:</strong> Los datos detallados de capacidades diversas a nivel de resguardo
          requieren cruce con microdatos censales. Este informe muestra la informacion territorial
          basica disponible.
        </div>

        <ReportSourceFooter />
      </div>
    </div>
  );
}

/* ============================================
   MAIN PAGE COMPONENT
   ============================================ */
export default function InformesPage() {
  const [reportType, setReportType] = useState('pueblo');
  const [selectedEntity, setSelectedEntity] = useState('');
  const [showReport, setShowReport] = useState(false);
  const reportRef = useRef(null);

  const { data: apiPueblosData } = usePueblos();
  const allPueblosList = useMemo(() => {
    const pueblosRaw = apiPueblosData?.data;
    if (!pueblosRaw || pueblosRaw.length === 0) return PUEBLOS_LIST;
    return pueblosRaw.map((p) => ({
      cod: p.cod_pueblo,
      nombre: p.pueblo,
    }));
  }, [apiPueblosData]);

  const { data: resguardosApiData } = useResguardosList();
  const resguardosList = useMemo(() => {
    if (!resguardosApiData) return [];
    const raw = Array.isArray(resguardosApiData) ? resguardosApiData : (resguardosApiData?.data || resguardosApiData?.features || []);
    return raw.map((r, i) => ({
      cod: r.cod_resguardo || r.id || String(i),
      nombre: r.nombre || r.territorio || r.nom_resguardo || `Resguardo ${i + 1}`,
      _raw: r,
    }));
  }, [resguardosApiData]);

  const entities = reportType === 'pueblo'
    ? allPueblosList
    : reportType === 'departamento'
    ? DEPARTAMENTOS.map((d) => ({ cod: d.cod, nombre: d.nombre }))
    : resguardosList;

  const { data: perfilForCSV } = usePerfilPueblo(
    reportType === 'pueblo' && showReport ? selectedEntity : undefined
  );

  const handleGenerate = useCallback(() => {
    if (!selectedEntity) return;
    setShowReport(true);
  }, [selectedEntity]);

  const handlePrint = useCallback(() => {
    window.print();
  }, []);

  const handleDownloadCSV = useCallback(() => {
    const entityObj = entities.find((e) => e.cod === selectedEntity);
    const name = entityObj?.nombre || selectedEntity;
    const rows = [];

    if (reportType === 'pueblo' && perfilForCSV) {
      const prev = perfilForCSV.prevalencia || {};
      const limitaciones = perfilForCSV.limitaciones || [];
      const causas = perfilForCSV.causas || [];

      rows.push(['Informe Pueblo Indigena', name]);
      rows.push(['Fecha', new Date().toISOString()]);
      rows.push(['Fuente', 'CNPV 2018 - SMT-ONIC']);
      rows.push([]);
      rows.push(['Indicador', 'Valor']);
      rows.push(['Pueblo', prev.pueblo || name]);
      rows.push(['Poblacion total', prev.total || 0]);
      rows.push(['Con capacidades diversas', prev.con_discapacidad || 0]);
      rows.push(['Prevalencia (tasa x 1000)', prev.tasa_x_1000 || 0]);
      rows.push(['Confiabilidad', prev.confiabilidad || '--']);
      rows.push([]);

      if (limitaciones.length > 0) {
        rows.push(['Limitacion', 'Valor (%)']);
        limitaciones.forEach((l) => {
          rows.push([l.limitacion || l.dificultad || '--', l.valor || 0]);
        });
        rows.push([]);
      }

      if (causas.length > 0) {
        rows.push(['Causa', 'Valor (%)']);
        causas.forEach((c) => {
          rows.push([c.causa || c.nombre || '--', c.valor || 0]);
        });
        rows.push([]);
      }
    } else {
      rows.push(['Tipo', 'Entidad', 'Fecha']);
      rows.push([reportType, name, new Date().toISOString()]);
    }

    const csv = rows.map((r) =>
      r.map((cell) => {
        const str = String(cell ?? '');
        return str.includes(',') || str.includes('"') ? `"${str.replace(/"/g, '""')}"` : str;
      }).join(',')
    ).join('\n');

    const bom = '\uFEFF';
    const blob = new Blob([bom + csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `informe-${reportType}-${selectedEntity}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }, [reportType, selectedEntity, entities, perfilForCSV]);

  const entityObj = entities.find((e) => e.cod === selectedEntity);

  const cardStyle = {
    background: '#fff',
    borderRadius: 'var(--radius-md)',
    boxShadow: 'var(--shadow-md)',
    padding: '20px 24px',
  };

  return (
    <div>
      <div className="page-header no-print">
        <h1>Generacion de Informes</h1>
        <p>
          Generacion de informes profesionales sobre capacidades diversas en pueblos indigenas
        </p>
      </div>

      {/* Report configuration — hidden in print */}
      <div className="no-print" style={{
        ...cardStyle,
        marginBottom: '24px',
        display: 'flex',
        alignItems: 'flex-end',
        gap: '20px',
        flexWrap: 'wrap',
      }}>
        {/* Report type */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <label style={{
            fontSize: '0.78rem',
            fontWeight: 600,
            textTransform: 'uppercase',
            color: 'var(--color-gray-500)',
          }}>
            Tipo de informe
          </label>
          <select
            value={reportType}
            onChange={(e) => {
              setReportType(e.target.value);
              setSelectedEntity('');
              setShowReport(false);
            }}
            style={{
              padding: '8px 14px',
              border: '1px solid var(--color-gray-300)',
              borderRadius: 'var(--radius-sm)',
              fontSize: '0.88rem',
              fontFamily: 'var(--font-body)',
              minWidth: '200px',
            }}
          >
            {REPORT_TYPES.map((t) => (
              <option key={t.id} value={t.id}>{t.label}</option>
            ))}
          </select>
        </div>

        {/* Entity selector */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <label style={{
            fontSize: '0.78rem',
            fontWeight: 600,
            textTransform: 'uppercase',
            color: 'var(--color-gray-500)',
          }}>
            {reportType === 'pueblo' ? 'Pueblo' : reportType === 'departamento' ? 'Departamento' : 'Resguardo'}
          </label>
          <select
            value={selectedEntity}
            onChange={(e) => {
              setSelectedEntity(e.target.value);
              setShowReport(false);
            }}
            style={{
              padding: '8px 14px',
              border: '1px solid var(--color-gray-300)',
              borderRadius: 'var(--radius-sm)',
              fontSize: '0.88rem',
              fontFamily: 'var(--font-body)',
              minWidth: '260px',
            }}
          >
            <option value="">
              {reportType === 'resguardo'
                ? (resguardosList.length > 0 ? `Seleccionar resguardo (${resguardosList.length})` : 'Cargando resguardos...')
                : `Seleccionar ${reportType === 'pueblo' ? 'pueblo' : 'departamento'}`}
            </option>
            {entities.map((e) => (
              <option key={e.cod} value={e.cod}>{e.nombre}</option>
            ))}
          </select>
        </div>

        {/* Action buttons */}
        <button
          onClick={handleGenerate}
          disabled={!selectedEntity}
          style={{
            padding: '8px 24px',
            background: selectedEntity ? 'var(--color-green-mid)' : 'var(--color-gray-300)',
            color: '#fff',
            border: 'none',
            borderRadius: 'var(--radius-sm)',
            fontSize: '0.88rem',
            fontWeight: 600,
            fontFamily: 'var(--font-body)',
            cursor: selectedEntity ? 'pointer' : 'not-allowed',
            transition: 'background 0.15s',
          }}
          onMouseEnter={(e) => {
            if (selectedEntity) e.currentTarget.style.background = 'var(--color-primary)';
          }}
          onMouseLeave={(e) => {
            if (selectedEntity) e.currentTarget.style.background = 'var(--color-green-mid)';
          }}
        >
          Generar informe
        </button>

        {showReport && (
          <>
            <button
              onClick={handlePrint}
              style={{
                padding: '8px 20px',
                background: 'var(--color-primary)',
                color: '#fff',
                border: 'none',
                borderRadius: 'var(--radius-sm)',
                fontSize: '0.88rem',
                fontWeight: 600,
                fontFamily: 'var(--font-body)',
                cursor: 'pointer',
                transition: 'background 0.15s',
              }}
              onMouseEnter={(e) => { e.currentTarget.style.background = '#013d28'; }}
              onMouseLeave={(e) => { e.currentTarget.style.background = 'var(--color-primary)'; }}
            >
              Descargar PDF
            </button>
            <button
              onClick={handleDownloadCSV}
              style={{
                padding: '8px 20px',
                background: '#fff',
                color: 'var(--color-primary)',
                border: '2px solid var(--color-primary)',
                borderRadius: 'var(--radius-sm)',
                fontSize: '0.88rem',
                fontWeight: 600,
                fontFamily: 'var(--font-body)',
                cursor: 'pointer',
                transition: 'all 0.15s',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = 'var(--color-green-light)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = '#fff';
              }}
            >
              Descargar CSV
            </button>
          </>
        )}
      </div>

      {/* Report preview */}
      {showReport && selectedEntity && (
        <div ref={reportRef}>
          {reportType === 'pueblo' && (
            <PuebloReport
              codPueblo={selectedEntity}
              puebloNombre={entityObj?.nombre}
            />
          )}
          {reportType === 'departamento' && (
            <DepartamentoReport
              codDpto={selectedEntity}
              dptoNombre={entityObj?.nombre}
            />
          )}
          {reportType === 'resguardo' && (
            <ResguardoReport resguardoData={entityObj?._raw || { nombre: entityObj?.nombre }} />
          )}
        </div>
      )}

      {!showReport && (
        <div className="no-print" style={{
          ...cardStyle,
          textAlign: 'center',
          padding: '60px 20px',
          color: 'var(--color-gray-400)',
        }}>
          <div style={{ fontSize: '2rem', marginBottom: '12px' }}>[ ]</div>
          <p style={{ fontSize: '0.95rem' }}>
            Seleccione un tipo de informe y una entidad, luego presione "Generar informe"
          </p>
          <p style={{ fontSize: '0.82rem', marginTop: '8px' }}>
            Los informes incluyen portada institucional, graficos, tablas comparativas y recomendaciones
          </p>
        </div>
      )}
    </div>
  );
}
