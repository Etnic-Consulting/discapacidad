import { fmt2, fmtDec } from '../lib/fmt';

export default function Donut({ data, totalLabel = 'Total' }) {
  const total = data.reduce((s, d) => s + d.value, 0);
  let acc = 0;
  const stops = data.map((d) => {
    const from = (acc / total) * 100;
    acc += d.value;
    const to = (acc / total) * 100;
    return `${d.color} ${from}% ${to}%`;
  }).join(', ');

  return (
    <div className="donut-wrap">
      <div className="donut" style={{ background: `conic-gradient(${stops})` }}>
        <div className="donut-center">
          <div className="donut-big">{fmt2(total)}</div>
          <div className="donut-lbl">{totalLabel}</div>
        </div>
      </div>
      <div className="donut-legend">
        {data.map((d, i) => (
          <div key={i} className="donut-li">
            <span className="dot" style={{ background: d.color }} />
            <span>{d.name}</span>
            <span className="v">{fmtDec(d.value)}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}
