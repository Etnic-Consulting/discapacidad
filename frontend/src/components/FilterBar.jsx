import { useFilters } from '../context/FilterContext';

export default function FilterBar() {
  const {
    dpto, mpio, pueblo,
    departamentos, municipios, pueblos,
    setDpto, setMpio, setPueblo,
    clearAll, activeCount,
  } = useFilters();

  return (
    <div className="filter-bar">
      <span className="filter-label">Filtrar por</span>

      <select
        className="filter-sel"
        value={dpto}
        onChange={(e) => setDpto(e.target.value)}
      >
        <option value="">Departamento</option>
        {departamentos.map((d) => (
          <option key={d.cod_dpto} value={d.cod_dpto}>{d.nom_dpto}</option>
        ))}
      </select>

      <select
        className="filter-sel"
        value={mpio}
        disabled={!dpto}
        onChange={(e) => setMpio(e.target.value)}
      >
        <option value="">Municipio</option>
        {municipios.map((m) => (
          <option key={m.cod_mpio} value={m.cod_mpio}>{m.nom_mpio}</option>
        ))}
      </select>

      <select
        className="filter-sel"
        value={pueblo}
        onChange={(e) => setPueblo(e.target.value)}
      >
        <option value="">Pueblo{dpto && pueblos.length ? ` (${pueblos.length})` : ''}</option>
        {pueblos.map((p) => (
          <option key={p.cod_pueblo} value={p.cod_pueblo}>{p.pueblo}</option>
        ))}
      </select>

      {activeCount > 0 && (
        <button className="filter-clear" onClick={clearAll}>Limpiar</button>
      )}
      {activeCount > 0 && (
        <span className="filter-count">{activeCount} filtro{activeCount > 1 ? 's' : ''}</span>
      )}
    </div>
  );
}
