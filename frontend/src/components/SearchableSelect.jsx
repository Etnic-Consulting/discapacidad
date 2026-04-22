/* ============================================
   SMT-ONIC — SearchableSelect
   Combobox con typeahead. Sin libs externas.

   Props:
     - value:        string|null  (id seleccionado)
     - displayValue: string       (texto visible si value esta seleccionado)
     - placeholder:  string
     - disabled:     boolean
     - fetcher:      async (q: string) => Array<{id, label, value, ...extra}>
     - fetcherKey:   string  (cambiar fuerza recarga; ej. cod_dpto)
     - onSelect:     (option | null) => void
     - prefetch:     boolean  (cargar al focus aunque q esté vacío)
     - minChars:     number   (def 0)
     - autoOpenIfSingle: boolean (auto-seleccionar si la API devuelve 1 sola opcion)
   ============================================ */

import { useState, useEffect, useRef, useCallback } from 'react';

const styles = {
  wrapper: { position: 'relative', width: '100%' },
  input: {
    width: '100%',
    padding: '8px 30px 8px 12px',
    border: '1px solid var(--color-gray-300, #cbd5d3)',
    borderRadius: 6,
    fontSize: '0.9rem',
    fontFamily: 'inherit',
    background: '#fff',
    color: 'var(--color-charcoal, #0E1F1A)',
    outline: 'none',
  },
  inputDisabled: { background: '#f5f5f4', color: '#94928e', cursor: 'not-allowed' },
  clearBtn: {
    position: 'absolute', right: 6, top: '50%', transform: 'translateY(-50%)',
    background: 'transparent', border: 'none', cursor: 'pointer',
    color: '#94928e', fontSize: '1rem', padding: '0 6px',
  },
  dropdown: {
    position: 'absolute', top: '100%', left: 0, right: 0, marginTop: 2,
    background: '#fff', border: '1px solid var(--color-gray-300, #cbd5d3)',
    borderRadius: 6, maxHeight: 240, overflowY: 'auto', zIndex: 50,
    boxShadow: '0 4px 12px rgba(14,31,26,0.12)',
  },
  option: {
    padding: '8px 12px', fontSize: '0.88rem', cursor: 'pointer',
    borderBottom: '1px solid #f0efed',
  },
  optionActive: { background: 'rgba(2,171,68,0.08)' },
  empty: { padding: '10px 12px', color: '#94928e', fontStyle: 'italic', fontSize: '0.85rem' },
  loading: { padding: '10px 12px', color: '#94928e', fontSize: '0.85rem' },
};

export default function SearchableSelect({
  value,
  displayValue = '',
  placeholder = 'Buscar...',
  disabled = false,
  fetcher,
  fetcherKey = '',
  onSelect,
  prefetch = false,
  minChars = 0,
  autoOpenIfSingle = false,
}) {
  const [query, setQuery] = useState('');
  const [open, setOpen] = useState(false);
  const [options, setOptions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeIdx, setActiveIdx] = useState(-1);
  const wrapRef = useRef(null);
  const inputRef = useRef(null);
  const debounceRef = useRef(null);

  // Texto que aparece en el input cuando NO está abierto
  const inputText = open ? query : (value ? displayValue : '');

  const runFetch = useCallback(async (q) => {
    if (!fetcher) return;
    if (q.length < minChars) {
      setOptions([]);
      return;
    }
    setLoading(true);
    try {
      const res = await fetcher(q);
      setOptions(Array.isArray(res) ? res : []);
      if (autoOpenIfSingle && Array.isArray(res) && res.length === 1) {
        // No auto-seleccionar al teclear; solo informativo
      }
    } catch (e) {
      setOptions([]);
    } finally {
      setLoading(false);
    }
  }, [fetcher, minChars, autoOpenIfSingle]);

  // Debounce de queries
  useEffect(() => {
    if (!open) return;
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => runFetch(query), 200);
    return () => debounceRef.current && clearTimeout(debounceRef.current);
  }, [query, open, runFetch]);

  // Recargar cuando cambia la clave padre (ej. cod_dpto)
  useEffect(() => {
    setOptions([]);
    setQuery('');
    if (open) runFetch('');
  }, [fetcherKey]); // eslint-disable-line react-hooks/exhaustive-deps

  // Click fuera cierra
  useEffect(() => {
    const onDocClick = (e) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target)) {
        setOpen(false);
        setActiveIdx(-1);
      }
    };
    document.addEventListener('mousedown', onDocClick);
    return () => document.removeEventListener('mousedown', onDocClick);
  }, []);

  const handleFocus = () => {
    if (disabled) return;
    setOpen(true);
    if (prefetch && options.length === 0) runFetch('');
  };

  const handleSelect = (opt) => {
    onSelect?.(opt);
    setQuery('');
    setOpen(false);
    setActiveIdx(-1);
    inputRef.current?.blur();
  };

  const handleClear = (e) => {
    e.stopPropagation();
    onSelect?.(null);
    setQuery('');
    setOptions([]);
  };

  const handleKey = (e) => {
    if (!open) return;
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveIdx((i) => Math.min(i + 1, options.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveIdx((i) => Math.max(i - 1, 0));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (activeIdx >= 0 && options[activeIdx]) handleSelect(options[activeIdx]);
    } else if (e.key === 'Escape') {
      setOpen(false);
      setActiveIdx(-1);
      inputRef.current?.blur();
    }
  };

  return (
    <div ref={wrapRef} style={styles.wrapper}>
      <input
        ref={inputRef}
        type="text"
        value={inputText}
        placeholder={placeholder}
        disabled={disabled}
        onChange={(e) => { setQuery(e.target.value); setOpen(true); setActiveIdx(-1); }}
        onFocus={handleFocus}
        onKeyDown={handleKey}
        style={{ ...styles.input, ...(disabled ? styles.inputDisabled : {}) }}
        autoComplete="off"
      />
      {value && !disabled && (
        <button type="button" onClick={handleClear} style={styles.clearBtn} title="Limpiar">×</button>
      )}
      {open && !disabled && (
        <div style={styles.dropdown}>
          {loading && <div style={styles.loading}>Buscando...</div>}
          {!loading && options.length === 0 && (
            <div style={styles.empty}>
              {query.length < minChars
                ? `Escribe al menos ${minChars} caracteres`
                : 'Sin resultados'}
            </div>
          )}
          {!loading && options.map((opt, i) => (
            <div
              key={opt.id ?? i}
              style={{ ...styles.option, ...(i === activeIdx ? styles.optionActive : {}) }}
              onMouseDown={(e) => { e.preventDefault(); handleSelect(opt); }}
              onMouseEnter={() => setActiveIdx(i)}
            >
              {opt.label}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
