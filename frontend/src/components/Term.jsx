import { lookup } from '../lib/glossary';

export default function Term({ term, children }) {
  const def = lookup(term);
  if (!def) return <>{children}</>;
  return (
    <abbr
      title={def}
      style={{
        textDecoration: 'underline dotted',
        textUnderlineOffset: 3,
        cursor: 'help',
      }}
      aria-label={`${term}: ${def}`}
    >
      {children}
    </abbr>
  );
}
