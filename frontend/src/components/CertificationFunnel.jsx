/* ============================================
   SMT-ONIC v2.0 — Certification Gap Funnel
   Visual funnel showing the gap between census
   data and certification for indigenous peoples.
   ============================================ */

function formatNumber(n) {
  return new Intl.NumberFormat('es-CO').format(n);
}

function pct(value, base) {
  if (!base || base === 0) return 0;
  return ((value / base) * 100).toFixed(1);
}

const DEFAULT_STEPS = [
  {
    label: 'Poblacion indigena total',
    value: 1905617,
    color: '#02AB44',
    gapText: null,
    source: '(Fuente: CNPV 2018)',
  },
  {
    label: 'Con capacidades diversas (CNPV 2018)',
    value: 225174,
    color: '#C4920A',
    gapText: null,
    source: '(Fuente: CNPV 2018)',
  },
  {
    label: 'Registrados RLCPD',
    value: 39374,
    color: '#E8862A',
    gapText: '185.800 personas no estan registradas en el RLCPD',
    source: '(Fuente: MinSalud RLCPD)',
  },
  {
    label: 'Caracterizados SMT-ONIC',
    value: 1044,
    color: '#E8262A',
    gapText: '~38.330 personas registradas en RLCPD no han sido caracterizadas por el SMT',
    source: '(Fuente: SMT-ONIC 2026)',
  },
  {
    label: 'Con certificado oficial',
    value: 428,
    color: '#8B1A1A',
    gapText: '616 personas caracterizadas aun no tienen certificado oficial',
    source: '(Fuente: SMT-ONIC 2026, calculado)',
  },
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
  const steps = brechaSteps || (data && data.length > 0 ? data : DEFAULT_STEPS);
  const totalBase = steps[0]?.value || 1;

  // Width percentages: first is 100%, rest scale proportionally but with a visual minimum
  const widthMap = [100, 85, 40, 15, 5];

  return (
    <div style={styles.container}>
      {steps.map((step, i) => {
        const prevValue = i > 0 ? steps[i - 1].value : null;
        const pctOfPrev = prevValue ? pct(step.value, prevValue) : null;
        const pctOfTotal = pct(step.value, totalBase);
        const barWidth = widthMap[i] ?? Math.max(5, (step.value / totalBase) * 100);

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
            <div style={styles.bar(barWidth, step.color)}>
              <div style={styles.label}>
                {step.label}
                {step.source && (
                  <div style={{ fontSize: '0.7rem', fontWeight: 400, opacity: 0.75, marginTop: '2px' }}>
                    {step.source}
                  </div>
                )}
              </div>
              <div style={styles.stats}>
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
              </div>
            </div>
          </div>
        );
      })}

      {/* Summary text */}
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
        <strong>Brecha critica:</strong> De las {formatNumber(steps[1]?.value || 225174)} personas
        indigenas con capacidades diversas identificadas en el CNPV 2018, solo{' '}
        {formatNumber(steps[steps.length - 1]?.value || 428)} ({pct(steps[steps.length - 1]?.value || 428, steps[1]?.value || 225174)}%)
        cuentan con certificado oficial. Esto significa que el{' '}
        {(100 - parseFloat(pct(steps[steps.length - 1]?.value || 428, steps[1]?.value || 225174))).toFixed(1)}%
        no puede acceder a los programas y derechos que requieren certificacion.
      </div>
    </div>
  );
}
