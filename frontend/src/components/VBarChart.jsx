import { fmtK } from '../lib/fmt';

export default function VBarChart({ data, keyX, keyY, yFmt = fmtK, barColor = 'var(--primary)', maxWidth = 52 }) {
  const max = Math.max(...data.map((d) => d[keyY]));
  return (
    <>
      <div className="vbar-chart">
        {data.map((d, i) => (
          <div key={i} className="vbar-col">
            <span className="vbar-val">{yFmt(d[keyY])}</span>
            <div
              className="vbar-fill"
              style={{
                height: ((d[keyY] / max) * 90) + '%',
                background: d.color || barColor,
                maxWidth,
              }}
            />
          </div>
        ))}
      </div>
      <div className="vbar-labels">
        {data.map((d, i) => (
          <div key={i} className="vbar-label">{d[keyX]}</div>
        ))}
      </div>
    </>
  );
}
