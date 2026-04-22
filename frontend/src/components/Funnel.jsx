import { fmt2, fmtDec } from '../lib/fmt';
import { FUNNEL_STEPS } from '../lib/data';

export default function Funnel({ steps = FUNNEL_STEPS }) {
  const total = steps[0]?.value || 1;

  return (
    <div className="funnel">
      {steps.map((s, i) => {
        const prev = i > 0 ? steps[i - 1].value : null;
        const pctPrev = prev ? ((s.value / prev) * 100).toFixed(1) : null;
        const pctTotal = ((s.value / total) * 100).toFixed(1);

        return (
          <div key={i}>
            {s.gap && <div className="funnel-gap">{s.gap}</div>}
            <div className="funnel-step" style={{ '--s-color': s.color }}>
              <div className="funnel-idx">{String(i + 1).padStart(2, '0')}</div>
              <div>
                <div className="funnel-label">{s.label}</div>
                <div className="funnel-source">Fuente · {s.source}</div>
              </div>
              <div className="funnel-nums">
                <div className="funnel-big">{fmt2(s.value)}</div>
                <div className="funnel-pct">
                  {pctPrev !== null && <>{pctPrev}% del anterior · </>}
                  {pctTotal}% del total
                </div>
              </div>
            </div>
          </div>
        );
      })}

      <div className="funnel-summary">
        <div className="funnel-summary-label">Lectura crítica</div>
        <div className="funnel-summary-text">
          De <b>{fmt2(steps[1]?.value ?? 225174)}</b> personas indígenas con capacidades diversas
          identificadas en el CNPV 2018, solo{' '}
          <b>{fmt2(steps[steps.length - 1]?.value ?? 428)}</b> cuentan con certificado oficial. El{' '}
          <b>{(100 - ((steps[steps.length - 1]?.value ?? 428) / (steps[1]?.value ?? 225174) * 100)).toFixed(1)}%</b>{' '}
          enfrenta barreras para acceder a programas y derechos que requieren certificación.
        </div>
      </div>
    </div>
  );
}
