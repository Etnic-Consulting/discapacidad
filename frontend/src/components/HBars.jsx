import { fmtDec } from '../lib/fmt';

export default function HBars({ data, keyX, keyY, suffix = '', color = '' }) {
  const max = Math.max(...data.map((d) => d[keyY]));
  return (
    <div className="hbars">
      {data.map((d, i) => (
        <div key={i} className="hbar">
          <div className="hbar-label">{d[keyX]}</div>
          <div className="hbar-track">
            <div
              className={'hbar-fill ' + color}
              style={{ width: ((d[keyY] / max) * 100) + '%' }}
            />
          </div>
          <div className="hbar-val">{fmtDec(d[keyY])}{suffix}</div>
        </div>
      ))}
    </div>
  );
}
