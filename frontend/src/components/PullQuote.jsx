export default function PullQuote({ children, attr }) {
  return (
    <div className="pull-quote">
      <div className="pull-quote-text">{children}</div>
      {attr && <div className="pull-quote-attr">— {attr}</div>}
    </div>
  );
}
