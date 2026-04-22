import { useState, useMemo } from 'react';

export default function DataTable({ columns = [], data = [], onRow }) {
  const [sort, setSort] = useState({ key: null, dir: 'desc' });

  const sorted = useMemo(() => {
    if (!sort.key) return data;
    return [...data].sort((a, b) => {
      const av = a[sort.key], bv = b[sort.key];
      if (typeof av === 'number' && typeof bv === 'number') {
        return sort.dir === 'asc' ? av - bv : bv - av;
      }
      return sort.dir === 'asc'
        ? String(av).localeCompare(String(bv), 'es')
        : String(bv).localeCompare(String(av), 'es');
    });
  }, [data, sort]);

  const doSort = (col) => {
    if (!col.sortable) return;
    setSort((s) => ({
      key: col.key,
      dir: s.key === col.key && s.dir === 'desc' ? 'asc' : 'desc',
    }));
  };

  return (
    <div className="table-wrap">
      <table className="data">
        <thead>
          <tr>
            {columns.map((c) => (
              <th
                key={c.key}
                className={[
                  c.sortable ? 'sortable' : '',
                  sort.key === c.key ? 'active' : '',
                ].join(' ')}
                onClick={() => doSort(c)}
              >
                {c.label}
                {c.sortable && (
                  <span className="sort">
                    {sort.key === c.key ? (sort.dir === 'asc' ? '▲' : '▼') : '↕'}
                  </span>
                )}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.length === 0 ? (
            <tr>
              <td colSpan={columns.length} style={{ padding: '32px', textAlign: 'center', color: 'var(--ink-muted)' }}>
                Sin registros
              </td>
            </tr>
          ) : sorted.map((row, i) => (
            <tr key={row.id || i} onClick={() => onRow && onRow(row)}>
              {columns.map((c) => (
                <td key={c.key} className={c.cls || ''}>
                  {c.render ? c.render(row[c.key], row) : row[c.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
