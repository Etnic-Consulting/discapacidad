/* ============================================
   SMT-ONIC v2.0 — Global Selector Bar
   Persistent filter bar powered by FilterContext.
   Cascading: Departamento -> Municipio -> Pueblo / Resguardo
   Selections stored in URL search params.
   ============================================ */

import { useFilters } from '../context/FilterContext';
import { useMacrorregiones } from '../hooks/useApi';

/* ---- Static department list (DIVIPOLA codes) — used as export for legacy compatibility ---- */
const DEPARTAMENTOS = [
  { cod: '05', nombre: 'Antioquia' },
  { cod: '08', nombre: 'Atlantico' },
  { cod: '11', nombre: 'Bogota D.C.' },
  { cod: '13', nombre: 'Bolivar' },
  { cod: '15', nombre: 'Boyaca' },
  { cod: '17', nombre: 'Caldas' },
  { cod: '18', nombre: 'Caqueta' },
  { cod: '19', nombre: 'Cauca' },
  { cod: '20', nombre: 'Cesar' },
  { cod: '23', nombre: 'Cordoba' },
  { cod: '25', nombre: 'Cundinamarca' },
  { cod: '27', nombre: 'Choco' },
  { cod: '41', nombre: 'Huila' },
  { cod: '44', nombre: 'La Guajira' },
  { cod: '47', nombre: 'Magdalena' },
  { cod: '50', nombre: 'Meta' },
  { cod: '52', nombre: 'Narino' },
  { cod: '54', nombre: 'Norte de Santander' },
  { cod: '63', nombre: 'Quindio' },
  { cod: '66', nombre: 'Risaralda' },
  { cod: '68', nombre: 'Santander' },
  { cod: '70', nombre: 'Sucre' },
  { cod: '73', nombre: 'Tolima' },
  { cod: '76', nombre: 'Valle del Cauca' },
  { cod: '81', nombre: 'Arauca' },
  { cod: '85', nombre: 'Casanare' },
  { cod: '86', nombre: 'Putumayo' },
  { cod: '88', nombre: 'San Andres' },
  { cod: '91', nombre: 'Amazonas' },
  { cod: '94', nombre: 'Guainia' },
  { cod: '95', nombre: 'Guaviare' },
  { cod: '97', nombre: 'Vaupes' },
  { cod: '99', nombre: 'Vichada' },
];

/* ---- Static pueblos list (top pueblos from CNPV 2018) ---- */
const PUEBLOS_LIST = [
  { cod: '720', nombre: 'Wayuu' },
  { cod: '800', nombre: 'Zenu' },
  { cod: '500', nombre: 'Nasa' },
  { cod: '560', nombre: 'Pastos' },
  { cod: '282', nombre: 'Embera Chami' },
  { cod: '280', nombre: 'Embera' },
  { cod: '200', nombre: 'Pijao' },
  { cod: '580', nombre: 'Sikuani' },
  { cod: '281', nombre: 'Embera Katio' },
  { cod: '210', nombre: 'Awa' },
  { cod: '820', nombre: 'Mokana' },
  { cod: '750', nombre: 'Yanacona' },
  { cod: '040', nombre: 'Arhuaco' },
  { cod: '290', nombre: 'Misak' },
  { cod: '340', nombre: 'Inga' },
  { cod: '180', nombre: 'Coconuco' },
  { cod: '050', nombre: 'Wiwa' },
  { cod: '850', nombre: 'Kankuamo' },
  { cod: '370', nombre: 'Kogui' },
  { cod: '710', nombre: 'Wounaan' },
  { cod: '660', nombre: 'Tikuna' },
  { cod: '510', nombre: 'Piapoco' },
  { cod: '220', nombre: 'Cubeo' },
  { cod: '470', nombre: 'Muisca' },
  { cod: '730', nombre: 'Murui' },
  { cod: '250', nombre: 'Curripaco' },
  { cod: '690', nombre: "U'wa" },
  { cod: '650', nombre: 'Totoro' },
  { cod: '550', nombre: 'Puinave' },
  { cod: '350', nombre: 'Kamentsa' },
  { cod: '565', nombre: 'Quillacinga' },
  { cod: '283', nombre: 'Eperara Siapidara' },
  { cod: '570', nombre: 'Saliba' },
  { cod: '284', nombre: 'Embera Dobida' },
  { cod: '780', nombre: 'Yukpa' },
  { cod: '680', nombre: 'Tukano' },
  { cod: '260', nombre: 'Desano' },
  { cod: '170', nombre: 'Cocama' },
  { cod: '190', nombre: 'Coreguaje' },
  { cod: '080', nombre: 'Bari' },
  { cod: '320', nombre: 'Jiw' },
  { cod: '240', nombre: 'Cuna Tule' },
  { cod: '590', nombre: 'Siona' },
  { cod: '360', nombre: 'Cofan' },
  { cod: '150', nombre: 'Chimila' },
  { cod: '740', nombre: 'Yagua' },
  { cod: '400', nombre: 'Hitnu' },
  { cod: '430', nombre: 'Nukak' },
  { cod: '090', nombre: 'Betoye' },
];

/* ---- Municipality data by department (static fallback) ---- */
const MUNICIPIOS_POR_DPTO = {};

const styles = {
  bar: {
    background: '#fff',
    borderBottom: '1px solid var(--color-gray-200)',
    padding: '12px 20px',
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    flexWrap: 'wrap',
    boxShadow: '0 1px 4px rgba(0,0,0,0.05)',
    borderRadius: 'var(--radius-md)',
    marginBottom: '20px',
  },
  label: {
    fontSize: '0.78rem',
    fontWeight: 600,
    textTransform: 'uppercase',
    letterSpacing: '0.4px',
    color: 'var(--color-gray-500)',
    whiteSpace: 'nowrap',
  },
  select: {
    padding: '7px 12px',
    border: '1px solid var(--color-gray-300)',
    borderRadius: 'var(--radius-sm)',
    fontSize: '0.85rem',
    fontFamily: 'var(--font-body)',
    background: '#fff',
    color: 'var(--color-charcoal)',
    minWidth: '180px',
    cursor: 'pointer',
    outline: 'none',
    transition: 'border-color 0.2s',
  },
  clearBtn: {
    padding: '7px 16px',
    border: '1px solid var(--color-gray-300)',
    borderRadius: 'var(--radius-sm)',
    background: 'var(--color-gray-100)',
    color: 'var(--color-gray-600)',
    fontSize: '0.82rem',
    fontFamily: 'var(--font-body)',
    cursor: 'pointer',
    transition: 'all 0.15s',
    fontWeight: 500,
  },
  activeFilters: {
    fontSize: '0.78rem',
    color: 'var(--color-green-mid)',
    fontWeight: 600,
    marginLeft: 'auto',
  },
};

export default function GlobalSelector() {
  const {
    dpto,
    mpio,
    pueblo,
    resguardo,
    macro,
    departamentos,
    municipios,
    pueblos,
    resguardos,
    setDpto,
    setMpio,
    setPueblo,
    setResguardo,
    setMacro,
    clearAll,
    hasFilters,
    activeCount,
    cascadeLoading,
  } = useFilters();

  const { data: macrosData } = useMacrorregiones();
  const macrorregiones = macrosData?.data || [];

  return (
    <div style={styles.bar}>
      <span style={styles.label}>Filtros:</span>

      {/* Macrorregion selector — corte alternativo al de dpto/mpio */}
      <select
        value={macro}
        onChange={(e) => setMacro(e.target.value)}
        style={styles.select}
        title="Macrorregiones ONIC: 5 zonas que agrupan resguardos por afinidad territorial"
        onFocus={(e) => {
          e.target.style.borderColor = 'var(--color-green-mid)';
        }}
        onBlur={(e) => {
          e.target.style.borderColor = 'var(--color-gray-300)';
        }}
      >
        <option value="">Macrorregión ONIC</option>
        {macrorregiones.map((m) => (
          <option key={m.id} value={m.macro}>
            {m.macro} ({m.resguardos} resg.)
          </option>
        ))}
      </select>

      {/* Department selector */}
      <select
        value={dpto}
        onChange={(e) => setDpto(e.target.value)}
        style={styles.select}
        onFocus={(e) => {
          e.target.style.borderColor = 'var(--color-green-mid)';
        }}
        onBlur={(e) => {
          e.target.style.borderColor = 'var(--color-gray-300)';
        }}
      >
        <option value="">Seleccionar departamento</option>
        {departamentos.map((d) => (
          <option key={d.cod_dpto} value={d.cod_dpto}>
            {d.nom_dpto}
          </option>
        ))}
      </select>

      {/* Municipality selector - enabled only when dept selected */}
      <select
        value={mpio}
        onChange={(e) => setMpio(e.target.value)}
        style={{
          ...styles.select,
          opacity: dpto ? 1 : 0.5,
        }}
        disabled={!dpto}
        onFocus={(e) => {
          e.target.style.borderColor = 'var(--color-green-mid)';
        }}
        onBlur={(e) => {
          e.target.style.borderColor = 'var(--color-gray-300)';
        }}
      >
        <option value="">
          {cascadeLoading && dpto ? 'Cargando...' : 'Seleccionar municipio'}
        </option>
        {municipios.map((m) => (
          <option key={m.cod_mpio} value={m.cod_mpio}>
            {m.nom_mpio}
          </option>
        ))}
      </select>

      {/* Pueblo selector - shows filtered pueblos when territory selected */}
      <select
        value={pueblo}
        onChange={(e) => setPueblo(e.target.value)}
        style={{
          ...styles.select,
          opacity: dpto && pueblos.length === 0 && cascadeLoading ? 0.5 : 1,
        }}
        onFocus={(e) => {
          e.target.style.borderColor = 'var(--color-green-mid)';
        }}
        onBlur={(e) => {
          e.target.style.borderColor = 'var(--color-gray-300)';
        }}
      >
        <option value="">
          {cascadeLoading && dpto
            ? 'Cargando...'
            : dpto && pueblos.length > 0
            ? `Seleccionar pueblo (${pueblos.length})`
            : 'Seleccionar pueblo'}
        </option>
        {pueblos.map((p) => (
          <option key={p.cod_pueblo} value={p.cod_pueblo}>
            {p.pueblo}
          </option>
        ))}
      </select>

      {/* Resguardo selector - enabled only when municipio selected */}
      <select
        value={resguardo}
        onChange={(e) => setResguardo(e.target.value)}
        style={{
          ...styles.select,
          opacity: mpio && resguardos.length > 0 ? 1 : 0.5,
        }}
        disabled={!mpio || resguardos.length === 0}
        onFocus={(e) => {
          e.target.style.borderColor = 'var(--color-green-mid)';
        }}
        onBlur={(e) => {
          e.target.style.borderColor = 'var(--color-gray-300)';
        }}
      >
        <option value="">
          {cascadeLoading && mpio
            ? 'Cargando...'
            : mpio && resguardos.length > 0
            ? `Seleccionar resguardo (${resguardos.length})`
            : 'Seleccionar resguardo'}
        </option>
        {resguardos.map((r) => (
          <option key={r.cod_resguardo} value={r.cod_resguardo}>
            {r.nombre}{r.pueblo_onic ? ` - ${r.pueblo_onic}` : ''}
          </option>
        ))}
      </select>

      {/* Clear button */}
      {hasFilters && (
        <button
          style={styles.clearBtn}
          onClick={clearAll}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'var(--color-gray-200)';
            e.currentTarget.style.color = 'var(--color-charcoal)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'var(--color-gray-100)';
            e.currentTarget.style.color = 'var(--color-gray-600)';
          }}
        >
          Limpiar filtros
        </button>
      )}

      {/* Active filters count */}
      {activeCount > 0 && (
        <span style={styles.activeFilters}>
          {activeCount} filtro{activeCount > 1 ? 's' : ''} activo
          {activeCount > 1 ? 's' : ''}
        </span>
      )}
    </div>
  );
}

/* Export data for use by other components (legacy compatibility) */
export { DEPARTAMENTOS, PUEBLOS_LIST, MUNICIPIOS_POR_DPTO };
