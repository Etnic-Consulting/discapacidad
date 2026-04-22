/* ============================================
   SMT-ONIC v2.0 — API Client
   All endpoints proxied via Vite: /api/v1/
   ============================================ */

const BASE = '/api/v1';
const TOKEN_KEY = 'smt_onic_auth';

function readToken() {
  try {
    const raw = localStorage.getItem(TOKEN_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    return parsed?.token || null;
  } catch {
    return null;
  }
}

async function request(path, params = {}) {
  const url = new URL(path, window.location.origin);
  Object.entries(params).forEach(([key, val]) => {
    if (val !== undefined && val !== null && val !== '') {
      url.searchParams.set(key, val);
    }
  });

  const token = readToken();
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  const res = await fetch(url.toString(), { headers });
  if (res.status === 401) {
    try { localStorage.removeItem(TOKEN_KEY); } catch { /* ignore */ }
  }
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`API ${res.status}: ${text || res.statusText}`);
  }
  return res.json();
}

// ---- Dashboard ----
export function fetchResumenNacional() {
  return request(`${BASE}/dashboard/`);
}

export function fetchPrevalenciaDpto(grupoEtnico) {
  return request(`${BASE}/dashboard/prevalencia/departamento`, { grupo_etnico: grupoEtnico });
}

export function fetchPrevalenciaMpio(codDpto) {
  return request(`${BASE}/dashboard/prevalencia/municipio`, { cod_dpto: codDpto });
}

export function fetchDificultades(codDpto, grupoEtnico) {
  return request(`${BASE}/dashboard/dificultades`, {
    cod_dpto: codDpto,
    grupo_etnico: grupoEtnico,
  });
}

export function fetchSalud(codDpto) {
  return request(`${BASE}/dashboard/salud`, { cod_dpto: codDpto });
}

export function fetchBrecha(codDpto) {
  return request(`${BASE}/dashboard/brecha`, { cod_dpto: codDpto });
}

export function fetchPanoramaKpis(params = {}) {
  return request(`${BASE}/dashboard/panorama-kpis`, {
    cod_dpto: params.cod_dpto,
    cod_mpio: params.cod_mpio,
    cod_pueblo: params.cod_pueblo,
    cod_resguardo: params.cod_resguardo,
    cod_macro: params.cod_macro,
  });
}

export function fetchMacrorregiones() {
  return request(`${BASE}/geo/macrorregiones`);
}

// ---- Formulario: territorios cascada ----
export function fetchFormMacros() {
  return request(`${BASE}/formulario/territorios/macros`);
}
export function fetchFormDptos({ cod_macro, q } = {}) {
  return request(`${BASE}/formulario/territorios/dptos`, { cod_macro, q });
}
export function fetchFormMpios({ cod_dpto, q } = {}) {
  return request(`${BASE}/formulario/territorios/mpios`, { cod_dpto, q });
}
export function fetchFormResguardos({ cod_mpio, cod_dpto, q } = {}) {
  return request(`${BASE}/formulario/territorios/resguardos`, { cod_mpio, cod_dpto, q });
}
export function fetchFormComunidades({ cod_mpio, cod_dpto, cod_resguardo, q } = {}) {
  return request(`${BASE}/formulario/territorios/comunidades`, { cod_mpio, cod_dpto, cod_resguardo, q });
}

export function fetchFiltrosCascada(codDpto, codMpio) {
  return request(`${BASE}/dashboard/filtros`, {
    cod_dpto: codDpto,
    cod_mpio: codMpio,
  });
}

// ---- Pueblos ----
export function fetchPueblos() {
  return request(`${BASE}/pueblos/`);
}

export function fetchPerfilPueblo(codPueblo) {
  return request(`${BASE}/pueblos/${codPueblo}/perfil`);
}

export function fetchTerritoriosPueblo(codPueblo) {
  return request(`${BASE}/pueblos/${codPueblo}/territorios`);
}

export function fetchPueblosMunicipio(codMpio) {
  return request(`${BASE}/pueblos/por-municipio/${codMpio}`);
}

// ---- Geo ----
export function fetchDepartamentosGeo() {
  return request(`${BASE}/geo/departamentos`);
}

export function fetchMunicipiosGeo(codDpto) {
  return request(`${BASE}/geo/municipios`, { cod_dpto: codDpto });
}

export function fetchResguardos(codMpio) {
  return request(`${BASE}/geo/resguardos`, { cod_mpio: codMpio });
}

export function fetchResguardosList() {
  return request(`${BASE}/geo/resguardos`);
}

// ---- Geo SMT-ONIC (spatial layers from smt_geo schema) ----
export function fetchMacrorregionesGeo() {
  return request(`${BASE}/geo/smt/macrorregiones`);
}

export function fetchResguardosGeo() {
  return request(`${BASE}/geo/smt/resguardos`);
}

export function fetchComunidadesGeo(codDpto) {
  return request(`${BASE}/geo/smt/comunidades`, { cod_dpto: codDpto });
}

// ---- Conflicto ----
export function fetchVictimasResumen() {
  return request(`${BASE}/conflicto/victimas/resumen`);
}

export function fetchVictimasHechos(codDpto) {
  return request(`${BASE}/conflicto/victimas/hechos`, { cod_dpto: codDpto });
}

export function fetchVictimasPorPueblo(codDpto, limit = 20) {
  return request(`${BASE}/conflicto/victimas/por-pueblo`, { cod_dpto: codDpto, limit });
}

export function fetchVictimasPorHecho(codDpto) {
  return request(`${BASE}/conflicto/victimas/por-hecho`, { cod_dpto: codDpto });
}

export function fetchVictimasPorTipo(codDpto) {
  return request(`${BASE}/conflicto/victimas/por-tipo`, { cod_dpto: codDpto });
}

export function fetchVictimasPueblo(codPueblo) {
  return request(`${BASE}/conflicto/victimas/pueblo/${codPueblo}`);
}

// ---- Intercensal & SMT Resumen ----
export function fetchIntercensal(grupoEtnico) {
  return request(`${BASE}/dashboard/intercensal`, {
    grupo_etnico: grupoEtnico,
  });
}

export function fetchSmtResumen(dimension) {
  return request(`${BASE}/dashboard/smt-resumen`, {
    dimension,
  });
}

// ---- Demografia (Visor DANE) ----
export function fetchNbiPueblos(codPueblo) {
  return request(`${BASE}/demografia/nbi`, { cod_pueblo: codPueblo });
}

export function fetchPerfilDemografico(codPueblo) {
  return request(`${BASE}/demografia/perfil/${codPueblo}`);
}

export function fetchRankingVulnerabilidad(limit) {
  return request(`${BASE}/demografia/ranking`, { limit });
}

export function fetchLenguaPueblos(codPueblo) {
  return request(`${BASE}/demografia/lengua`, { cod_pueblo: codPueblo });
}

export function fetchEducacionPueblo(codPueblo) {
  return request(`${BASE}/demografia/educacion/${codPueblo}`);
}

export function fetchViviendaPueblo(codPueblo) {
  return request(`${BASE}/demografia/vivienda/${codPueblo}`);
}

export function fetchNbiDetalle(codPueblo) {
  return request(`${BASE}/demografia/nbi/${codPueblo}`);
}

export function fetchPiramideDemografica(codPueblo) {
  return request(`${BASE}/demografia/piramide/${codPueblo}`);
}

export function fetchPerfilResguardo(codResguardo) {
  return request(`${BASE}/demografia/resguardo/${codResguardo}`);
}

export function fetchResguardosDemografia(codMpio, codDpto) {
  return request(`${BASE}/demografia/resguardos`, {
    cod_mpio: codMpio,
    cod_dpto: codDpto,
  });
}

export function fetchResguardosPorPueblo(codPueblo) {
  return request(`${BASE}/demografia/resguardos-pueblo/${codPueblo}`);
}

// ---- Indicadores ----
export function fetchIndicadores() {
  return request(`${BASE}/indicadores/`);
}

export function fetchIndicadorSerie(codIndicador) {
  return request(`${BASE}/indicadores/serie-tiempo/${codIndicador}`);
}

export function fetchIndicadorValores(periodo, nivelGeo) {
  return request(`${BASE}/indicadores/valores`, { periodo, nivel_geo: nivelGeo });
}

export function fetchPiramideCapDiversas(codPueblo) {
  return request(`/api/v1/demografia/piramide-disc/${codPueblo}`);
}

export function fetchPiramideTipoDisc(codPueblo) {
  return request(`/api/v1/demografia/piramide-disc-tipo/${codPueblo}`);
}

// ---- Piramides nacionales (agregadas o filtradas por dpto/mpio/pueblo) ----
export function fetchPiramideNacional(params = {}) {
  return request(`${BASE}/demografia/piramide-nacional`, {
    cod_dpto: params.cod_dpto,
    cod_mpio: params.cod_mpio,
    cod_pueblo: params.cod_pueblo,
  });
}

export function fetchPiramideDiscNacional(params = {}) {
  return request(`${BASE}/demografia/piramide-disc-nacional`, {
    cod_dpto: params.cod_dpto,
    cod_mpio: params.cod_mpio,
    cod_pueblo: params.cod_pueblo,
  });
}

export function fetchPiramideDiscTipoNacional(params = {}) {
  return request(`${BASE}/demografia/piramide-disc-tipo-nacional`, {
    cod_dpto: params.cod_dpto,
    cod_mpio: params.cod_mpio,
    cod_pueblo: params.cod_pueblo,
  });
}
