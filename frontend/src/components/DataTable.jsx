/* ============================================
   SMT-ONIC v2.0 — Sortable Data Table
   ============================================ */

import { useState, useMemo } from 'react';

const styles = {
  wrapper: {
    background: '#fff',
    borderRadius: 'var(--radius-md)',
    boxShadow: 'var(--shadow-md)',
    overflow: 'hidden',
  },
  toolbar: {
    padding: '14px 18px',
    borderBottom: '1px solid var(--color-gray-200)',
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  searchInput: {
    flex: 1,
    maxWidth: '360px',
    padding: '8px 14px',
    border: '1px solid var(--color-gray-300)',
    borderRadius: 'var(--radius-sm)',
    fontFamily: 'var(--font-body)',
    fontSize: '0.85rem',
    background: 'var(--color-gray-100)',
    transition: 'border-color 0.2s',
    outline: 'none',
  },
  count: {
    fontSize: '0.8rem',
    color: 'var(--color-gray-400)',
    marginLeft: 'auto',
  },
  tableContainer: {
    overflowX: 'auto',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
    fontSize: '0.88rem',
  },
  th: (sortable) => ({
    padding: '10px 16px',
    textAlign: 'left',
    fontWeight: 600,
    fontSize: '0.78rem',
    textTransform: 'uppercase',
    letterSpacing: '0.4px',
    color: 'var(--color-gray-500)',
    background: 'var(--color-gray-100)',
    borderBottom: '2px solid var(--color-gray-200)',
    cursor: sortable ? 'pointer' : 'default',
    userSelect: 'none',
    whiteSpace: 'nowrap',
  }),
  td: {
    padding: '10px 16px',
    borderBottom: '1px solid var(--color-gray-200)',
    verticalAlign: 'middle',
  },
  row: (index, clickable) => ({
    background: index % 2 === 0 ? '#fff' : 'var(--color-gray-100)',
    cursor: clickable ? 'pointer' : 'default',
    transition: 'background 0.1s',
  }),
  sortArrow: {
    marginLeft: '4px',
    fontSize: '0.7rem',
    opacity: 0.6,
  },
  empty: {
    padding: '40px 20px',
    textAlign: 'center',
    color: 'var(--color-gray-400)',
    fontSize: '0.9rem',
  },
};

export default function DataTable({ columns = [], data = [], onRowClick, title }) {
  const [search, setSearch] = useState('');
  const [sortKey, setSortKey] = useState(null);
  const [sortDir, setSortDir] = useState('asc');

  const filtered = useMemo(() => {
    if (!search.trim()) return data;
    const q = search.toLowerCase();
    return data.filter((row) =>
      columns.some((col) => {
        const val = row[col.key];
        return val != null && String(val).toLowerCase().includes(q);
      })
    );
  }, [data, search, columns]);

  const sorted = useMemo(() => {
    if (!sortKey) return filtered;
    const col = columns.find((c) => c.key === sortKey);
    if (!col || !col.sortable) return filtered;

    return [...filtered].sort((a, b) => {
      const va = a[sortKey];
      const vb = b[sortKey];
      if (va == null && vb == null) return 0;
      if (va == null) return 1;
      if (vb == null) return -1;

      let cmp;
      if (typeof va === 'number' && typeof vb === 'number') {
        cmp = va - vb;
      } else {
        cmp = String(va).localeCompare(String(vb), 'es');
      }
      return sortDir === 'asc' ? cmp : -cmp;
    });
  }, [filtered, sortKey, sortDir, columns]);

  function handleSort(key, sortable) {
    if (!sortable) return;
    if (sortKey === key) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(key);
      setSortDir('asc');
    }
  }

  function getSortIndicator(key) {
    if (sortKey !== key) return ' \u2195';
    return sortDir === 'asc' ? ' \u2191' : ' \u2193';
  }

  return (
    <div style={styles.wrapper}>
      <div style={styles.toolbar}>
        {title && (
          <span style={{ fontWeight: 600, fontSize: '0.9rem', color: 'var(--color-primary)' }}>
            {title}
          </span>
        )}
        <input
          type="text"
          placeholder="Buscar..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={styles.searchInput}
          onFocus={(e) => { e.target.style.borderColor = 'var(--color-green-mid)'; }}
          onBlur={(e) => { e.target.style.borderColor = 'var(--color-gray-300)'; }}
        />
        <span style={styles.count}>
          {sorted.length} de {data.length} registros
        </span>
      </div>

      <div style={styles.tableContainer}>
        <table style={styles.table}>
          <thead>
            <tr>
              {columns.map((col) => (
                <th
                  key={col.key}
                  style={styles.th(col.sortable)}
                  onClick={() => handleSort(col.key, col.sortable)}
                >
                  {col.label}
                  {col.sortable && (
                    <span style={styles.sortArrow}>{getSortIndicator(col.key)}</span>
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sorted.length === 0 ? (
              <tr>
                <td colSpan={columns.length} style={styles.empty}>
                  No se encontraron registros
                </td>
              </tr>
            ) : (
              sorted.map((row, i) => (
                <tr
                  key={row.id || i}
                  style={styles.row(i, !!onRowClick)}
                  onClick={() => onRowClick && onRowClick(row)}
                  onMouseEnter={(e) => {
                    if (onRowClick) e.currentTarget.style.background = 'var(--color-green-light)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background =
                      i % 2 === 0 ? '#fff' : 'var(--color-gray-100)';
                  }}
                >
                  {columns.map((col) => (
                    <td key={col.key} style={styles.td}>
                      {col.render ? col.render(row[col.key], row) : row[col.key]}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
