/* ============================================
   SMT-ONIC v2.0 — Global Filter Context
   Cascading filters synced to URL search params.
   Departamento -> Municipio -> Pueblo / Resguardo
   ============================================ */

import { createContext, useContext, useCallback, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useFiltrosCascada } from '../hooks/useApi';

/* ---- Static fallback data (same as GlobalSelector) ---- */
const DEPARTAMENTOS_STATIC = [
  { cod_dpto: '05', nom_dpto: 'Antioquia' },
  { cod_dpto: '08', nom_dpto: 'Atlantico' },
  { cod_dpto: '11', nom_dpto: 'Bogota D.C.' },
  { cod_dpto: '13', nom_dpto: 'Bolivar' },
  { cod_dpto: '15', nom_dpto: 'Boyaca' },
  { cod_dpto: '17', nom_dpto: 'Caldas' },
  { cod_dpto: '18', nom_dpto: 'Caqueta' },
  { cod_dpto: '19', nom_dpto: 'Cauca' },
  { cod_dpto: '20', nom_dpto: 'Cesar' },
  { cod_dpto: '23', nom_dpto: 'Cordoba' },
  { cod_dpto: '25', nom_dpto: 'Cundinamarca' },
  { cod_dpto: '27', nom_dpto: 'Choco' },
  { cod_dpto: '41', nom_dpto: 'Huila' },
  { cod_dpto: '44', nom_dpto: 'La Guajira' },
  { cod_dpto: '47', nom_dpto: 'Magdalena' },
  { cod_dpto: '50', nom_dpto: 'Meta' },
  { cod_dpto: '52', nom_dpto: 'Narino' },
  { cod_dpto: '54', nom_dpto: 'Norte de Santander' },
  { cod_dpto: '63', nom_dpto: 'Quindio' },
  { cod_dpto: '66', nom_dpto: 'Risaralda' },
  { cod_dpto: '68', nom_dpto: 'Santander' },
  { cod_dpto: '70', nom_dpto: 'Sucre' },
  { cod_dpto: '73', nom_dpto: 'Tolima' },
  { cod_dpto: '76', nom_dpto: 'Valle del Cauca' },
  { cod_dpto: '81', nom_dpto: 'Arauca' },
  { cod_dpto: '85', nom_dpto: 'Casanare' },
  { cod_dpto: '86', nom_dpto: 'Putumayo' },
  { cod_dpto: '88', nom_dpto: 'San Andres' },
  { cod_dpto: '91', nom_dpto: 'Amazonas' },
  { cod_dpto: '94', nom_dpto: 'Guainia' },
  { cod_dpto: '95', nom_dpto: 'Guaviare' },
  { cod_dpto: '97', nom_dpto: 'Vaupes' },
  { cod_dpto: '99', nom_dpto: 'Vichada' },
];

const FilterContext = createContext(null);

export function FilterProvider({ children }) {
  const [searchParams, setSearchParams] = useSearchParams();

  /* ---- Read current selections from URL ---- */
  const dpto = searchParams.get('dpto') || '';
  const mpio = searchParams.get('mpio') || '';
  const pueblo = searchParams.get('pueblo') || '';
  const resguardo = searchParams.get('resguardo') || '';

  /* ---- Fetch cascading options from API ---- */
  const { data: cascadeData, isLoading: cascadeLoading } = useFiltrosCascada(
    dpto || undefined,
    mpio || undefined
  );

  /* ---- Derived option lists ---- */
  const departamentos = useMemo(() => {
    return cascadeData?.departamentos || DEPARTAMENTOS_STATIC;
  }, [cascadeData]);

  const municipios = useMemo(() => {
    if (!dpto) return [];
    return cascadeData?.municipios || [];
  }, [dpto, cascadeData]);

  const pueblos = useMemo(() => {
    return cascadeData?.pueblos || [];
  }, [cascadeData]);

  const resguardos = useMemo(() => {
    if (!dpto && !mpio) return [];
    return cascadeData?.resguardos || [];
  }, [dpto, mpio, cascadeData]);

  /* ---- Resolved names ---- */
  const dptoNombre = useMemo(() => {
    if (!dpto) return '';
    const found = departamentos.find((d) => d.cod_dpto === dpto);
    return found?.nom_dpto || '';
  }, [dpto, departamentos]);

  const mpioNombre = useMemo(() => {
    if (!mpio) return '';
    const found = municipios.find((m) => m.cod_mpio === mpio);
    return found?.nom_mpio || '';
  }, [mpio, municipios]);

  const puebloNombre = useMemo(() => {
    if (!pueblo) return '';
    const found = pueblos.find((p) => p.cod_pueblo === pueblo);
    return found?.pueblo || pueblo;
  }, [pueblo, pueblos]);

  const resguardoNombre = useMemo(() => {
    if (!resguardo) return '';
    const found = resguardos.find((r) => r.cod_resguardo === resguardo);
    return found?.nombre || resguardo;
  }, [resguardo, resguardos]);

  /* ---- URL param updater ---- */
  const updateParams = useCallback(
    (updates) => {
      setSearchParams(
        (prev) => {
          const next = new URLSearchParams(prev);
          Object.entries(updates).forEach(([key, val]) => {
            if (val) {
              next.set(key, val);
            } else {
              next.delete(key);
            }
          });
          return next;
        },
        { replace: true }
      );
    },
    [setSearchParams]
  );

  /* ---- Cascading setters ---- */
  const setDpto = useCallback(
    (val) => {
      // Clear downstream: mpio, pueblo, resguardo
      updateParams({ dpto: val, mpio: '', pueblo: '', resguardo: '' });
    },
    [updateParams]
  );

  const setMpio = useCallback(
    (val) => {
      // Clear downstream: pueblo, resguardo
      updateParams({ mpio: val, pueblo: '', resguardo: '' });
    },
    [updateParams]
  );

  const setPueblo = useCallback(
    (val) => {
      updateParams({ pueblo: val });
    },
    [updateParams]
  );

  const setResguardo = useCallback(
    (val) => {
      updateParams({ resguardo: val });
    },
    [updateParams]
  );

  const clearAll = useCallback(() => {
    updateParams({ dpto: '', mpio: '', pueblo: '', resguardo: '' });
  }, [updateParams]);

  /* ---- Breadcrumb segments ---- */
  const breadcrumbs = useMemo(() => {
    const parts = [{ label: 'Nacional', level: 'nacional' }];
    if (dpto && dptoNombre) {
      parts.push({ label: dptoNombre, level: 'dpto', value: dpto });
    }
    if (mpio && mpioNombre) {
      parts.push({ label: mpioNombre, level: 'mpio', value: mpio });
    }
    if (pueblo && puebloNombre) {
      parts.push({ label: puebloNombre, level: 'pueblo', value: pueblo });
    }
    if (resguardo && resguardoNombre) {
      parts.push({ label: resguardoNombre, level: 'resguardo', value: resguardo });
    }
    return parts;
  }, [dpto, dptoNombre, mpio, mpioNombre, pueblo, puebloNombre, resguardo, resguardoNombre]);

  const hasFilters = !!(dpto || mpio || pueblo || resguardo);
  const activeCount = [dpto, mpio, pueblo, resguardo].filter(Boolean).length;

  const value = useMemo(
    () => ({
      // Current selections
      dpto,
      mpio,
      pueblo,
      resguardo,
      // Resolved names
      dptoNombre,
      mpioNombre,
      puebloNombre,
      resguardoNombre,
      // Option lists (for dropdowns)
      departamentos,
      municipios,
      pueblos,
      resguardos,
      // Setters (cascading)
      setDpto,
      setMpio,
      setPueblo,
      setResguardo,
      clearAll,
      // Utility
      hasFilters,
      activeCount,
      breadcrumbs,
      cascadeLoading,
    }),
    [
      dpto, mpio, pueblo, resguardo,
      dptoNombre, mpioNombre, puebloNombre, resguardoNombre,
      departamentos, municipios, pueblos, resguardos,
      setDpto, setMpio, setPueblo, setResguardo, clearAll,
      hasFilters, activeCount, breadcrumbs, cascadeLoading,
    ]
  );

  return (
    <FilterContext.Provider value={value}>
      {children}
    </FilterContext.Provider>
  );
}

export function useFilters() {
  const ctx = useContext(FilterContext);
  if (!ctx) {
    throw new Error('useFilters must be used within a FilterProvider');
  }
  return ctx;
}

export default FilterContext;
