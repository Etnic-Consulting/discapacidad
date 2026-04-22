export default function DYK({ fact, source }) {
  return (
    <div className="dyk">
      <div className="dyk-mark">¶</div>
      <div>
        <div className="dyk-label">¿Sabías que…?</div>
        <div className="dyk-text">{fact}</div>
        {source && <div className="dyk-source">Fuente · {source}</div>}
      </div>
    </div>
  );
}
