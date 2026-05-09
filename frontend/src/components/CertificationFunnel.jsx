/* ============================================
   SMT-ONIC v2.0 — Certification Gap Funnel
   Visual funnel showing the gap between census
   data and certification for indigenous peoples.
   ============================================ */

function formatNumber(n) {
  if (n == null || Number.isNaN(n)) return '—';
  return new Intl.NumberFormat('es-CO').format(n);
}

function pct(value, base) {
  if (value == null || base == null || base === 0) return null;
  return ((value / base) * 100).toFixed(1);
}

/* Plantilla estructural · sin cifras hardcoded. Si el backend no responde,
 * el componente renderiza un placeholder honesto (Sin datos).
 */
const PLACEHOLDER_STEPS = [
  { label: 'Poblacion indigena total',             value: null, color: '#02AB44', gapText: null, source: '(Fuente: CNPV 2018)' },
  { label: 'Con capacidades diversas (CNPV 2018)', value: null, color: '#C4920A', gapText: null, source: '(Fuente: CNPV 2018)' },
  { label: 'Registrados RLCPD',                    value: null, color: '#E8862A', gapText: null, source: '(Fuente: MinSalud RLCPD)' },
  { label: 'Caracterizados SMT-ONIC',              value: null, color: '#E8262A', gapText: null, source: '(Fuente: SMT-ONIC)' },
  { label: 'Con certificado oficial',              value: null, color: '#8B1A1A', gapText: null, source: '(Fuente: SMT-ONIC, calculado)' },
];

const styles = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '0',
    padding: '20px 0',
  },
  stepWrapper: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    width: '100%',
  },
  bar: (widthPct, color) => ({
    width: `${widthPct}%`,
    minWidth: '120px',
    background: color,
    borderRadius: '6px',
    padding: '16px 20px',
    color: '#fff',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: '12px',
    transition: 'width 0.8s ease, opacity 0.5s ease',
    position: 'relative',
    flexWrap: 'wrap',
  }),
  label: {
    fontSize: '0.88rem',
    fontWeight: 600,
    lineHeight: 1.3,
    flex: '1 1 auto',
    minWidth: '160px',
  },
  stats: {
    display: 'flex',
    gap: '16px',
    alignItems: 'center',
    flexShrink: 0,
    flexWrap: 'wrap',
  },
  mainValue: {
    fontFamily: 'var(--font-heading)',
    fontSize: '1.5rem',
    fontWeight: 700,
    lineHeight: 1,
  },
  pctBadge: {
    fontSize: '0.75rem',
    fontWeight: 600,
    background: 'rgba(255,255,255,0.2)',
    borderRadius: '12px',
    padding: '3px 10px',
    whiteSpace: 'nowrap',
  },
  connector: {
    width: '2px',
    height: '8px',
    background: 'var(--color-gray-300)',
  },
  gapBox: {
    background: 'var(--color-gold-light)',
    border: '1px dashed var(--color-gold)',
    borderRadius: 'var(--radius-sm)',
    padding: '8px 16px',
    fontSize: '0.82rem',
    color: '#7a5a00',
    fontStyle: 'italic',
    textAlign: 'center',
    maxWidth: '80%',
    margin: '4px 0',
  },
};

/** Map API brecha response (pasos array) to funnel steps */
function mapBrechaToSteps(brecha) {
  if (!brecha || !brecha.pasos || brecha.pasos.length === 0) return null;
  const COLORS = ['#02AB44', '#C4920A', '#E8862A', '#E8262A', '#8B1A1A'];
  return brecha.pasos.map((paso, i) => ({
    label: paso.label,
    value: paso.valor,
    color: COLORS[i] || '#6B6B6B',
    gapText: i >= 2 ? generateGapText(brecha.pasos, i) : null,
    source: `(Fuente: ${paso.fuente})`,
  }));
}

function generateGapText(pasos, index) {
  if (index < 1) return null;
  const prev = pasos[index - 1]?.valor || 0;
  const curr = pasos[index]?.valor || 0;
  const gap = prev - curr;
  if (gap <= 0) return null;
  return `~${new Intl.NumberFormat('es-CO').format(gap)} personas del paso anterior no llegan a este nivel`;
}

export default function CertificationFunnel({ data, brecha }) {
  const brechaSteps = brecha ? mapBrechaToSteps(brecha) : null;
  const steps = brechaSteps || (data && data.length > 0 ? data : PLACEHOLDER_STEPS);
  const totalBase = steps[0]?.value || null;
  const sinDatos = !totalBase;

  // Width percentages: first is 100%, rest scale proportionally but with a visual minimum
  const widthMap = [100, 85, 40, 15, 5];

  return (
    <div style={styles.container}>
      {!sinDatos && steps.map((step, i) => {
        const prevValue = i > 0 ? steps[i - 1].value : null;
        const pctOfPrev = prevValue ? pct(step.value, prevValue) : null;
        const pctOfTotal = pct(step.value, totalBase);
        const barWidth = widthMap[i] ?? Math.max(5, (step.value / totalBase) * 100);
        // Paso pendiente · sistema en pre-operación: la captura territorial vía
        // formulario propio aún no ha comenzado. Renderizar muted en lugar de "0".
        const esPasoPendienteCaptura =
          step.value === 0 &&
          typeof step.source === 'string' &&
          step.source.includes('SMT-ONIC');

        return (
          <div key={i} style={styles.stepWrapper}>
            {/* Connector line */}
            {i > 0 && <div style={styles.connector} />}

            {/* Gap explanation */}
            {step.gapText && (
              <>
                <div style={styles.gapBox}>
                  {step.gapText}
                </div>
                <div style={styles.connector} />
              </>
            )}

            {/* Funnel bar */}
            <div
              style={{
                ...styles.bar(barWidth, step.color),
                ...(esPasoPendienteCaptura ? { opacity: 0.55, background: 'var(--color-gray-400)' } : {}),
              }}
            >
              <div style={styles.label}>
                {step.label}
                {step.source && (
                  <div style={{ fontSize: '0.7rem', fontWeight: 400, opacity: 0.75, marginTop: '2px' }}>
                    {step.source}
                  </div>
                )}
              </div>
              <div style={styles.stats}>
                {esPasoPendienteCaptura ? (
                  <span style={{ ...styles.mainValue, fontSize: '0.95rem', fontStyle: 'italic', fontWeight: 600 }}>
                    Pendiente · captura territorial
                  </span>
                ) : (
                  <>
                    <span style={styles.mainValue}>{formatNumber(step.value)}</span>
                    {pctOfPrev !== null && (
                      <span style={styles.pctBadge}>
                        {pctOfPrev}% del anterior
                      </span>
                    )}
                    {i > 0 && (
                      <span style={styles.pctBadge}>
                        {pctOfTotal}% del total
                      </span>
                    )}
                  </>
                )}
              </div>
            </div>
          </div>
        );
      })}

      {/* Summary text · solo se renderiza si hay datos reales (incluido el cierre RLCPD/SMT) */}
      {!sinDatos && steps[1]?.value != null && steps[steps.length - 1]?.value != null && steps[steps.length - 1].value > 0 && (() => {
        const conCD = steps[1].value;
        const conCert = steps[steps.length - 1].value;
        const pctCert = pct(conCert, conCD);
        const pctSin = pctCert != null ? (100 - parseFloat(pctCert)).toFixed(1) : null;
        return (
          <div style={{
            marginTop: '20px',
            padding: '16px 24px',
            background: '#fde8e8',
            borderRadius: 'var(--radius-sm)',
            borderLeft: '4px solid var(--color-red)',
            fontSize: '0.88rem',
            color: '#6B1A1A',
            lineHeight: 1.6,
            maxWidth: '90%',
            textAlign: 'center',
          }}>
            <strong>Brecha critica:</strong> De las {formatNumber(conCD)} personas
            indigenas con capacidades diversas identificadas en el CNPV 2018, solo{' '}
            {formatNumber(conCert)} ({pctCert}%) cuentan con certificado oficial.
            Esto significa que el {pctSin}% no puede acceder a los programas y
            derechos que requieren certificacion.
          </div>
        );
      })()}
      {sinDatos && (
        <div style={{
          marginTop: '20px',
          padding: '16px 24px',
          background: 'var(--color-gray-100)',
          borderRadius: 'var(--radius-sm)',
          borderLeft: '4px solid var(--color-gray-500)',
          fontSize: '0.88rem',
          color: 'var(--color-gray-500)',
          fontStyle: 'italic',
          textAlign: 'center',
          maxWidth: '90%',
        }}>
          Embudo en construcción · esperando datos del backend.
        </div>
      )}
    </div>
  );
}
