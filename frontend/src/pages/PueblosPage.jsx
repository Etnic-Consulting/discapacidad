/* ============================================
   SMT-ONIC v2.0 — Pueblos Indigenas
   Datos reales desde /api/v1/pueblos/
   ============================================ */

import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import DataTable from '../components/DataTable';
import KPICard from '../components/KPICard';
import GlobalSelector from '../components/GlobalSelector';
import FilterBreadcrumb from '../components/FilterBreadcrumb';
import { useFilters } from '../context/FilterContext';
import DidYouKnow from '../components/DidYouKnow';
import { usePueblos, usePueblosMunicipio } from '../hooks/useApi';

/* Confiabilidad badge component */
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
      padding: '2px 10px',
      borderRadius: '12px',
      fontSize: '0.72rem',
      fontWeight: 600,
      background: c.bg,
      color: c.color,
      letterSpacing: '0.3px',
    }}>
      {c.label}
    </span>
  );
}

const columns = [
  { key: 'ranking', label: '#', sortable: true },
  { key: 'nombre', label: 'Pueblo', sortable: true },
  {
    key: 'poblacion',
    label: 'Poblacion total',
    sortable: true,
    render: (val) => new Intl.NumberFormat('es-CO').format(val),
  },
  {
    key: 'conCapDiv',
    label: 'Con capacidades diversas',
    sortable: true,
    render: (val) => new Intl.NumberFormat('es-CO').format(val),
  },
  {
    key: 'prevalencia',
    label: 'Prevalencia (\u2030)',
    sortable: true,
    render: (val) => (
      <span style={{
        fontWeight: 600,
        color: val > 100 ? 'var(--color-red)' : val > 60 ? 'var(--color-gold)' : 'var(--color-green-mid)',
      }}>
        {typeof val === 'number' ? val.toFixed(1) : '--'}
      </span>
    ),
  },
  {
    key: 'confiabilidad',
    label: 'Confiabilidad',
    sortable: true,
    render: (val) => <ConfiabilidadBadge nivel={val} />,
  },
];

function formatNumber(n) {
  return new Intl.NumberFormat('es-CO').format(n);
}

export default function PueblosPage() {
  const navigate = useNavigate();
  const { dpto, mpio, dptoNombre, mpioNombre, pueblos: filteredPueblosFromContext } = useFilters();
  const { data: apiPueblos, isLoading, isError } = usePueblos();
  const { data: apiPueblosMpio } = usePueblosMunicipio(mpio || undefined);

  // API returns { periodo, total, data: [{ cod_pueblo, pueblo, con_discapacidad, sin_discapacidad, total, prevalencia_pct, tasa_x_1000, confiabilidad }] }
  const allPueblos = useMemo(() => {
    const pueblosRaw = apiPueblos?.data;
    if (!pueblosRaw || pueblosRaw.length === 0) return [];
    return pueblosRaw
      .map((p, i) => ({
        id: i,
        codPueblo: p.cod_pueblo,
        nombre: p.pueblo,
        poblacion: p.total ?? 0,
        conCapDiv: p.con_discapacidad ?? 0,
        sinCapDiv: p.sin_discapacidad ?? 0,
        prevalencia: p.tasa_x_1000 ?? 0,
        prevalenciaPct: p.prevalencia_pct ?? 0,
        confiabilidad: p.confiabilidad || 'MEDIA',
        ranking: i + 1,
      }));
  }, [apiPueblos]);

  // Filter pueblos based on current geographic selection
  const pueblos = useMemo(() => {
    if (allPueblos.length === 0) return [];

    // When municipio is selected, use the municipio-specific endpoint data
    if (mpio && apiPueblosMpio?.data) {
      const mpioPueblosCodes = new Set(apiPueblosMpio.data.map((p) => p.cod_pueblo));
      return allPueblos
        .filter((p) => mpioPueblosCodes.has(p.codPueblo))
        .sort((a, b) => b.poblacion - a.poblacion)
        .map((p, i) => ({ ...p, ranking: i + 1 }));
    }

    // When departamento is selected, use the cascading filter data
    if (dpto && filteredPueblosFromContext.length > 0) {
      const dptoPueblosCodes = new Set(filteredPueblosFromContext.map((p) => p.cod_pueblo));
      return allPueblos
        .filter((p) => dptoPueblosCodes.has(p.codPueblo))
        .sort((a, b) => b.poblacion - a.poblacion)
        .map((p, i) => ({ ...p, ranking: i + 1 }));
    }

    // Default: sorted by population descending
    return [...allPueblos]
      .sort((a, b) => b.poblacion - a.poblacion)
      .map((p, i) => ({ ...p, ranking: i + 1 }));
  }, [allPueblos, dpto, mpio, apiPueblosMpio, filteredPueblosFromContext]);

  // KPI: total personas con capacidades diversas
  const totalConCapDiv = useMemo(
    () => pueblos.reduce((sum, p) => sum + (p.conCapDiv || 0), 0),
    [pueblos]
  );

  // KPI: prevalencia promedio ponderada (sum con_disc / sum total * 1000)
  const avgPrevalencia = useMemo(() => {
    const totalPob = pueblos.reduce((sum, p) => sum + (p.poblacion || 0), 0);
    if (totalPob === 0) return '0.0';
    return ((totalConCapDiv / totalPob) * 1000).toFixed(1);
  }, [pueblos, totalConCapDiv]);

  // KPI: pueblo con mayor prevalencia (solo ALTA confiabilidad)
  const maxPueblo = useMemo(() => {
    const altaConfianza = pueblos.filter((p) => p.confiabilidad === 'ALTA');
    if (altaConfianza.length === 0) {
      // Fallback: all pueblos if none have ALTA
      return pueblos.reduce(
        (max, p) => (p.prevalencia > (max?.prevalencia || 0) ? p : max),
        pueblos[0]
      );
    }
    return altaConfianza.reduce(
      (max, p) => (p.prevalencia > (max?.prevalencia || 0) ? p : max),
      altaConfianza[0]
    );
  }, [pueblos]);

  if (isLoading) return <div className="loading-container"><div className="spinner" /><p>Cargando pueblos...</p></div>;
  if (isError) return <div className="error-container"><p>Error cargando datos de pueblos</p></div>;

  // Build title based on filters
  let pageTitle = 'Pueblos Indigenas';
  let subtitle = `${pueblos.length} pueblos indigenas identificados con personas con capacidades diversas`;
  if (mpioNombre) {
    pageTitle = `Pueblos en ${mpioNombre}`;
    subtitle = `${pueblos.length} pueblos presentes en el municipio de ${mpioNombre}`;
  } else if (dptoNombre) {
    pageTitle = `Pueblos en ${dptoNombre}`;
    subtitle = `${pueblos.length} pueblos presentes en el departamento de ${dptoNombre}`;
  }

  return (
    <div>
      <div className="page-header">
        <h1>{pageTitle}</h1>
        <p>{subtitle}</p>
      </div>

      {/* Global Selector */}
      <GlobalSelector />

      {/* Breadcrumb */}
      <FilterBreadcrumb />

      {/* KPIs */}
      <div className="grid-row grid-4" style={{ marginBottom: '24px' }}>
        <KPICard
          title="Pueblos registrados"
          value={pueblos.length}
          subtitle="Con datos censales"
          color="var(--color-primary)"
          icon="PR"
        />
        <KPICard
          title="Total con capacidades diversas"
          value={formatNumber(totalConCapDiv)}
          subtitle="En pueblos listados"
          color="var(--color-green-mid)"
          icon="CD"
        />
        <KPICard
          title="Prevalencia ponderada"
          value={`${avgPrevalencia}\u2030`}
          subtitle="Ponderada por poblacion"
          color="var(--color-gold)"
          icon="PV"
        />
        <KPICard
          title="Mayor prevalencia"
          value={`${maxPueblo?.prevalencia?.toFixed(1) || '--'}\u2030`}
          subtitle={maxPueblo ? `${maxPueblo.nombre}${maxPueblo.confiabilidad === 'ALTA' ? ' (conf. alta)' : ''}` : '--'}
          color="var(--color-red)"
          icon="MP"
        />
      </div>

      {/* Table */}
      <DataTable
        title={`Pueblos Indigenas con Capacidades Diversas${dptoNombre ? ` - ${dptoNombre}` : ''}${mpioNombre ? ` > ${mpioNombre}` : ''}`}
        columns={columns}
        data={pueblos}
        onRowClick={(row) => navigate(`/pueblos/${row.codPueblo}`)}
      />

      {/* DidYouKnow callout */}
      <DidYouKnow
        fact="El pueblo Wayuu tiene la prevalencia mas baja (12.7 por mil) y el Kamentsa la mas alta (133.5 por mil) — una diferencia de 10 veces entre pueblos indigenas de Colombia."
        source="CNPV 2018 - DANE, analisis por pueblo indigena"
      />

      <div style={{
        textAlign: 'center',
        color: 'var(--color-gray-400)',
        fontSize: '0.78rem',
        marginTop: '16px',
      }}>
        Haga clic en un pueblo para ver su perfil detallado. Datos: CNPV 2018 (DANE).
      </div>
    </div>
  );
}
