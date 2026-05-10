/* ============================================
   SMT-ONIC v1.2 — Observatorio (datos formulario propio)
   ============================================ */

import { useQuery } from '@tanstack/react-query';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  LineChart, Line, ResponsiveContainer, Cell,
} from 'recharts';
import {
  fetchObservatorioKpis,
  fetchObservatorioTerritorial,
  fetchObservatorioTipos,
  fetchObservatorioAyudas,
  fetchObservatorioTimeline,
  fetchObservatorioUltimas,
} from '../lib/api';

const COLORS = ['#02432D', '#0e7c52', '#3a9d6e', '#73b88c', '#a8d3b3', '#c8e0c1', '#d6e9d0'];

const cardStyle = {
  background: '#fff',
  borderRadius: '8px',
  boxShadow: '0 1px 4px rgba(0,0,0,0.08)',
  padding: '1rem',
  marginBottom: '1rem',
};
const kpiStyle = {
  ...cardStyle,
  flex: 1,
  minWidth: '180px',
  textAlign: 'center',
};

function KpiBox({ label, value, suffix = '' }) {
  return (
    <div style={kpiStyle}>
      <div style={{ fontSize: '0.78rem', color: '#666', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
        {label}
      </div>
      <div style={{ fontSize: '2rem', fontWeight: 700, color: '#02432D', margin: '0.5rem 0' }}>
        {value === undefined || value === null ? '—' : value}
        {value !== undefined && value !== null && suffix}
      </div>
    </div>
  );
}

export default function ObservatorioPage() {
  const { data: kpis } = useQuery({ queryKey: ['obs-kpis'], queryFn: fetchObservatorioKpis, staleTime: 60_000 });
  const { data: territorial } = useQuery({ queryKey: ['obs-territorial'], queryFn: fetchObservatorioTerritorial, staleTime: 60_000 });
  const { data: tipos } = useQuery({ queryKey: ['obs-tipos'], queryFn: fetchObservatorioTipos, staleTime: 60_000 });
  const { data: ayudas } = useQuery({ queryKey: ['obs-ayudas'], queryFn: fetchObservatorioAyudas, staleTime: 60_000 });
  const { data: timeline } = useQuery({ queryKey: ['obs-timeline', 'week'], queryFn: () => fetchObservatorioTimeline('week'), staleTime: 60_000 });
  const { data: ultimas } = useQuery({ queryKey: ['obs-ultimas', 20], queryFn: () => fetchObservatorioUltimas(20), staleTime: 60_000 });

  const totalRespuestas = kpis?.total_respuestas ?? 0;
  const sinDatos = totalRespuestas === 0;

  return (
    <div style={{ padding: '1.5rem', maxWidth: '1280px', margin: '0 auto' }}>
      <h1 style={{ color: '#02432D', borderBottom: '3px solid #02432D', paddingBottom: '0.5rem' }}>
        Observatorio · Datos formulario SMT
      </h1>
      <p style={{ color: '#666', marginTop: '0.25rem' }}>
        Captura territorial propia · sistema CPLI · cifras agregadas con k-anonimato (k≥5).
      </p>

      <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', marginTop: '1.5rem' }}>
        <KpiBox label="Total respuestas" value={kpis?.total_respuestas?.toLocaleString('es-CO')} />
        <KpiBox label="Macros cubiertos" value={kpis?.macros_cubiertos} suffix="/5" />
        <KpiBox label="Dptos cubiertos" value={kpis?.dptos_cubiertos} />
        <KpiBox label="Completitud" value={kpis?.completitud_pct} suffix="%" />
      </div>

      {sinDatos ? (
        <div style={{ ...cardStyle, marginTop: '1rem', textAlign: 'center', padding: '3rem 1rem' }}>
          <h3 style={{ color: '#666' }}>Sin respuestas todavía</h3>
          <p style={{ color: '#999' }}>Esperando captura territorial · los dinamizadores cargan respuestas en <code>/formulario</code>.</p>
        </div>
      ) : (
        <>
          <h2 style={{ color: '#02432D', marginTop: '2rem' }}>Distribución territorial</h2>
          <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
            <div style={{ ...cardStyle, flex: 1, minWidth: '320px' }}>
              <h3 style={{ fontSize: '0.95rem', marginTop: 0 }}>Por macrorregión</h3>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={territorial?.por_macro || []}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e8e8e8" />
                  <XAxis dataKey="macro" tick={{ fontSize: 10 }} />
                  <YAxis tick={{ fontSize: 10 }} />
                  <Tooltip />
                  <Bar dataKey="n" fill="#02432D" />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div style={{ ...cardStyle, flex: 1, minWidth: '320px' }}>
              <h3 style={{ fontSize: '0.95rem', marginTop: 0 }}>Top departamentos</h3>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={(territorial?.por_dpto || []).slice(0, 10)} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#e8e8e8" />
                  <XAxis type="number" tick={{ fontSize: 10 }} />
                  <YAxis dataKey="nom_dpto" type="category" tick={{ fontSize: 9 }} width={100} />
                  <Tooltip />
                  <Bar dataKey="n" fill="#0e7c52" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', marginTop: '1rem' }}>
            <div style={{ ...cardStyle, flex: 1, minWidth: '320px' }}>
              <h3 style={{ fontSize: '0.95rem', marginTop: 0 }}>Tipos de dificultad reportados</h3>
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={tipos?.tipos || []} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#e8e8e8" />
                  <XAxis type="number" tick={{ fontSize: 10 }} />
                  <YAxis dataKey="tipo" type="category" tick={{ fontSize: 10 }} width={100} />
                  <Tooltip />
                  <Bar dataKey="n">
                    {(tipos?.tipos || []).map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div style={{ ...cardStyle, flex: 1, minWidth: '320px' }}>
              <h3 style={{ fontSize: '0.95rem', marginTop: 0 }}>Ayudas técnicas</h3>
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={ayudas?.ayudas || []} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#e8e8e8" />
                  <XAxis type="number" tick={{ fontSize: 10 }} />
                  <YAxis dataKey="ayuda" type="category" tick={{ fontSize: 10 }} width={120} />
                  <Tooltip />
                  <Bar dataKey="n">
                    {(ayudas?.ayudas || []).map((_, i) => <Cell key={i} fill={COLORS[(i + 2) % COLORS.length]} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <h2 style={{ color: '#02432D', marginTop: '2rem' }}>Línea de tiempo</h2>
          <div style={cardStyle}>
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={timeline?.data || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e8e8e8" />
                <XAxis dataKey="periodo" tick={{ fontSize: 10 }} />
                <YAxis tick={{ fontSize: 10 }} />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="n" stroke="#02432D" strokeWidth={2} name="Respuestas/semana" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <h2 style={{ color: '#02432D', marginTop: '2rem' }}>Últimas respuestas (anonimizadas)</h2>
          <div style={cardStyle}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ background: '#02432D', color: '#fff' }}>
                  <th style={{ padding: '0.5rem', textAlign: 'left' }}>ID</th>
                  <th style={{ padding: '0.5rem', textAlign: 'left' }}>Fecha</th>
                  <th style={{ padding: '0.5rem', textAlign: 'left' }}>Macro</th>
                  <th style={{ padding: '0.5rem', textAlign: 'left' }}>Dpto</th>
                  <th style={{ padding: '0.5rem', textAlign: 'right' }}>Dificultades</th>
                  <th style={{ padding: '0.5rem', textAlign: 'right' }}>Ayudas</th>
                  <th style={{ padding: '0.5rem', textAlign: 'right' }}>Compl. %</th>
                </tr>
              </thead>
              <tbody>
                {(ultimas || []).map((r) => (
                  <tr key={r.id} style={{ borderBottom: '1px solid #eee' }}>
                    <td style={{ padding: '0.4rem' }}>{r.id}</td>
                    <td style={{ padding: '0.4rem' }}>{r.fecha_envio?.slice(0, 10)}</td>
                    <td style={{ padding: '0.4rem' }}>{r.macrorregion}</td>
                    <td style={{ padding: '0.4rem' }}>{r.cod_dpto}</td>
                    <td style={{ padding: '0.4rem', textAlign: 'right' }}>{r.n_dificultades}</td>
                    <td style={{ padding: '0.4rem', textAlign: 'right' }}>{r.n_ayudas}</td>
                    <td style={{ padding: '0.4rem', textAlign: 'right' }}>{r.completitud_pct}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
