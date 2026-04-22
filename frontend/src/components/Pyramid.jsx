export default function Pyramid({ data }) {
  const max = Math.max(...data.flatMap((d) => [d.h, d.m]));

  return (
    <>
      <div className="pyr">
        {[...data].reverse().map((r, i) => (
          <div key={i} className="pyr-row">
            <div className="pyr-l">
              <div
                className="pyr-l-fill"
                style={{ width: ((r.h / max) * 100) + '%' }}
                title={`Hombres ${r.h}`}
              />
            </div>
            <div className="pyr-grp">{r.grupo}</div>
            <div>
              <div
                className="pyr-r-fill"
                style={{ width: ((r.m / max) * 100) + '%' }}
                title={`Mujeres ${r.m}`}
              />
            </div>
          </div>
        ))}
      </div>
      <div className="pyr-legend">
        <span className="lg">
          <span className="lg-dot" style={{ background: 'var(--primary)' }} />
          Hombres
        </span>
        <span>Grupo edad</span>
        <span className="lg">
          Mujeres
          <span className="lg-dot" style={{ background: 'var(--gold)' }} />
        </span>
      </div>
    </>
  );
}
