/* ============================================
   SMT-ONIC v2.0 — React Query Hooks
   ============================================ */

import { useQuery } from '@tanstack/react-query';
import {
  fetchResumenNacional,
  fetchPrevalenciaDpto,
  fetchPrevalenciaMpio,
  fetchDificultades,
  fetchSalud,
  fetchBrecha,
  fetchPanoramaKpis,
  fetchFiltrosCascada,
  fetchIntercensal,
  fetchProyecciones,
  fetchSmtResumen,
  fetchPueblos,
  fetchPerfilPueblo,
  fetchTerritoriosPueblo,
  fetchPueblosMunicipio,
  fetchDepartamentosGeo,
  fetchMunicipiosGeo,
  fetchResguardos,
  fetchResguardosList,
  fetchMacrorregionesGeo,
  fetchMacrorregiones,
  fetchResguardosGeo,
  fetchComunidadesGeo,
  fetchVictimasResumen,
  fetchVictimasHechos,
  fetchVictimasPorPueblo,
  fetchVictimasPorHecho,
  fetchVictimasPorTipo,
  fetchVictimasPueblo,
  fetchIndicadores,
  fetchIndicadorSerie,
  fetchIndicadorValores,
  fetchNbiPueblos,
  fetchPerfilDemografico,
  fetchRankingVulnerabilidad,
  fetchLenguaPueblos,
  fetchEducacionPueblo,
  fetchViviendaPueblo,
  fetchNbiDetalle,
  fetchPiramideDemografica,
  fetchPiramideCapDiversas,
  fetchPiramideTipoDisc,
  fetchPiramideNacional,
  fetchPiramideDiscNacional,
  fetchPiramideDiscTipoNacional,
  fetchPerfilResguardo,
  fetchResguardosDemografia,
  fetchResguardosPorPueblo,
} from '../lib/api';

/* ---- Dashboard ---- */
export function useResumenNacional() {
  return useQuery({
    queryKey: ['resumen-nacional'],
    queryFn: fetchResumenNacional,
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
}

export function usePrevalenciaDpto(grupoEtnico) {
  return useQuery({
    queryKey: ['prevalencia-dpto', grupoEtnico],
    queryFn: () => fetchPrevalenciaDpto(grupoEtnico),
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
}

export function usePrevalenciaMpio(codDpto) {
  return useQuery({
    queryKey: ['prevalencia-mpio', codDpto],
    queryFn: () => fetchPrevalenciaMpio(codDpto),
    enabled: !!codDpto,
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
}

export function useDificultades(filters = {}, grupoEtnico) {
  // Soporta legacy (codDpto, grupoEtnico) y nuevo (filtersObj, grupoEtnico)
  const f = typeof filters === 'string' ? { cod_dpto: filters } : filters;
  return useQuery({
    queryKey: ['dificultades', f.cod_macro || null, f.cod_dpto || null, f.cod_mpio || null, f.cod_pueblo || null, f.cod_resguardo || null, grupoEtnico],
    queryFn: () => fetchDificultades(f, grupoEtnico),
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
}

export function useSalud(filters = {}) {
  const f = typeof filters === 'string' ? { cod_dpto: filters } : filters;
  const enabled = !!(f.cod_dpto || f.cod_macro || f.cod_mpio);
  return useQuery({
    queryKey: ['salud', f.cod_macro || null, f.cod_dpto || null, f.cod_mpio || null],
    queryFn: () => fetchSalud(f),
    enabled,
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
}

export function useBrecha(filters = {}) {
  const f = typeof filters === 'string' ? { cod_dpto: filters } : filters;
  return useQuery({
    queryKey: ['brecha', f.cod_macro || null, f.cod_dpto || null, f.cod_mpio || null, f.cod_pueblo || null],
    queryFn: () => fetchBrecha(f),
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
}

export function usePanoramaKpis(filters = {}) {
  const { cod_dpto, cod_mpio, cod_pueblo, cod_resguardo, cod_macro } = filters;
  return useQuery({
    queryKey: [
      'panorama-kpis',
      cod_dpto || null,
      cod_mpio || null,
      cod_pueblo || null,
      cod_resguardo || null,
      cod_macro || null,
    ],
    queryFn: () => fetchPanoramaKpis({ cod_dpto, cod_mpio, cod_pueblo, cod_resguardo, cod_macro }),
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
}

export function useMacrorregiones() {
  return useQuery({
    queryKey: ['macrorregiones-list'],
    queryFn: fetchMacrorregiones,
    staleTime: 30 * 60 * 1000,
    retry: 1,
  });
}

export function useFiltrosCascada(codDpto, codMpio, codMacro) {
  return useQuery({
    queryKey: ['filtros-cascada', codDpto, codMpio, codMacro],
    queryFn: () => fetchFiltrosCascada(codDpto, codMpio, codMacro),
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
}

/* ---- Intercensal & SMT Resumen ---- */
export function useIntercensal(grupoEtnico, aplicarFac = false) {
  return useQuery({
    queryKey: ['intercensal', grupoEtnico, aplicarFac],
    queryFn: () => fetchIntercensal(grupoEtnico, aplicarFac),
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
}

// T08 Sprint S1.A · proyecciones Lee-Carter con bandas IC
// Endpoint: /api/v1/dashboard/proyecciones?grupo_etnico=...&periodo_inicio=...&periodo_fin=...
// Lee tabla proyecciones.escenarios (832 filas · 8 grupos × 26 años × 4 escenarios)
export function useProyecciones(opts = {}) {
  return useQuery({
    queryKey: ['proyecciones', opts.grupoEtnico, opts.periodoInicio, opts.periodoFin, opts.escenario],
    queryFn: () => fetchProyecciones(opts),
    staleTime: 10 * 60 * 1000,
    retry: 1,
  });
}

export function useSmtResumen(dimension) {
  return useQuery({
    queryKey: ['smt-resumen', dimension],
    queryFn: () => fetchSmtResumen(dimension),
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
}

/* ---- Pueblos ---- */
export function usePueblos(filters = {}) {
  const { cod_macro, cod_dpto, cod_mpio } = filters;
  return useQuery({
    queryKey: ['pueblos', cod_macro || null, cod_dpto || null, cod_mpio || null],
    queryFn: () => fetchPueblos({ cod_macro, cod_dpto, cod_mpio }),
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
}

export function usePerfilPueblo(codPueblo) {
  return useQuery({
    queryKey: ['perfil-pueblo', codPueblo],
    queryFn: () => fetchPerfilPueblo(codPueblo),
    enabled: !!codPueblo,
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
}

export function useTerritoriosPueblo(codPueblo) {
  return useQuery({
    queryKey: ['territorios-pueblo', codPueblo],
    queryFn: () => fetchTerritoriosPueblo(codPueblo),
    enabled: !!codPueblo,
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
}

export function usePueblosMunicipio(codMpio) {
  return useQuery({
    queryKey: ['pueblos-municipio', codMpio],
    queryFn: () => fetchPueblosMunicipio(codMpio),
    enabled: !!codMpio,
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
}

/* ---- Geo ---- */
export function useDepartamentosGeo() {
  return useQuery({
    queryKey: ['geo-departamentos'],
    queryFn: fetchDepartamentosGeo,
    staleTime: 30 * 60 * 1000,
    retry: 1,
  });
}

export function useMunicipiosGeo(codDpto) {
  return useQuery({
    queryKey: ['geo-municipios', codDpto],
    queryFn: () => fetchMunicipiosGeo(codDpto),
    enabled: !!codDpto,
    staleTime: 30 * 60 * 1000,
    retry: 1,
  });
}

export function useResguardos(codMpio) {
  return useQuery({
    queryKey: ['geo-resguardos', codMpio],
    queryFn: () => fetchResguardos(codMpio),
    enabled: !!codMpio,
    staleTime: 30 * 60 * 1000,
    retry: 1,
  });
}

export function useResguardosList() {
  return useQuery({
    queryKey: ['resguardos-list'],
    queryFn: fetchResguardosList,
    staleTime: 30 * 60 * 1000,
    retry: 1,
  });
}

/* ---- Geo SMT-ONIC (spatial layers) ---- */
export function useMacrorregionesGeo() {
  return useQuery({
    queryKey: ['geo-smt-macrorregiones'],
    queryFn: fetchMacrorregionesGeo,
    staleTime: 30 * 60 * 1000,
    retry: 1,
  });
}

export function useResguardosGeo() {
  return useQuery({
    queryKey: ['geo-smt-resguardos'],
    queryFn: fetchResguardosGeo,
    staleTime: 30 * 60 * 1000,
    retry: 1,
  });
}

export function useComunidadesGeo(codDpto, { enabled = true } = {}) {
  return useQuery({
    queryKey: ['geo-smt-comunidades', codDpto],
    queryFn: () => fetchComunidadesGeo(codDpto),
    enabled,
    staleTime: 30 * 60 * 1000,
    retry: 1,
  });
}

/* ---- Conflicto ---- */
export function useVictimasResumen() {
  return useQuery({
    queryKey: ['victimas-resumen'],
    queryFn: fetchVictimasResumen,
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
}

function _normFiltros(filters) {
  return typeof filters === 'string' ? { cod_dpto: filters } : (filters || {});
}

export function useVictimasHechos(filters = {}) {
  const f = _normFiltros(filters);
  return useQuery({
    queryKey: ['victimas-hechos', f.cod_macro || null, f.cod_dpto || null, f.cod_mpio || null, f.cod_resguardo || null],
    queryFn: () => fetchVictimasHechos(f),
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
}

export function useVictimasPorPueblo(filters = {}, limit = 20) {
  const f = _normFiltros(filters);
  return useQuery({
    queryKey: ['victimas-por-pueblo', f.cod_macro || null, f.cod_dpto || null, f.cod_mpio || null, f.cod_resguardo || null, limit],
    queryFn: () => fetchVictimasPorPueblo(f, limit),
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
}

export function useVictimasPorHecho(filters = {}) {
  const f = _normFiltros(filters);
  return useQuery({
    queryKey: ['victimas-por-hecho', f.cod_macro || null, f.cod_dpto || null, f.cod_mpio || null],
    queryFn: () => fetchVictimasPorHecho(f),
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
}

export function useVictimasPorTipo(filters = {}) {
  const f = _normFiltros(filters);
  return useQuery({
    queryKey: ['victimas-por-tipo', f.cod_macro || null, f.cod_dpto || null, f.cod_mpio || null],
    queryFn: () => fetchVictimasPorTipo(f),
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
}

export function useVictimasPueblo(codPueblo) {
  return useQuery({
    queryKey: ['victimas-pueblo', codPueblo],
    queryFn: () => fetchVictimasPueblo(codPueblo),
    enabled: !!codPueblo,
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
}

/* ---- Demografia (Visor DANE) ---- */
export function useNbiPueblos(codPueblo) {
  return useQuery({
    queryKey: ['nbi-pueblos', codPueblo],
    queryFn: () => fetchNbiPueblos(codPueblo),
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
}

export function usePerfilDemografico(codPueblo) {
  return useQuery({
    queryKey: ['perfil-demografico', codPueblo],
    queryFn: () => fetchPerfilDemografico(codPueblo),
    enabled: !!codPueblo,
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
}

export function useRankingVulnerabilidad(limit) {
  return useQuery({
    queryKey: ['ranking-vulnerabilidad', limit],
    queryFn: () => fetchRankingVulnerabilidad(limit),
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
}

export function useLenguaPueblos(codPueblo) {
  return useQuery({
    queryKey: ['lengua-pueblos', codPueblo],
    queryFn: () => fetchLenguaPueblos(codPueblo),
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
}

export function useEducacionPueblo(codPueblo) {
  return useQuery({
    queryKey: ['educacion-pueblo', codPueblo],
    queryFn: () => fetchEducacionPueblo(codPueblo),
    enabled: !!codPueblo,
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
}

export function useViviendaPueblo(codPueblo) {
  return useQuery({
    queryKey: ['vivienda-pueblo', codPueblo],
    queryFn: () => fetchViviendaPueblo(codPueblo),
    enabled: !!codPueblo,
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
}

export function useNbiDetalle(codPueblo) {
  return useQuery({
    queryKey: ['nbi-detalle', codPueblo],
    queryFn: () => fetchNbiDetalle(codPueblo),
    enabled: !!codPueblo,
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
}

export function usePiramideDemografica(codPueblo) {
  return useQuery({
    queryKey: ['piramide-demografica', codPueblo],
    queryFn: () => fetchPiramideDemografica(codPueblo),
    enabled: !!codPueblo,
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
}

export function usePiramideCapDiversas(codPueblo) {
  return useQuery({
    queryKey: ['piramide-cap-diversas', codPueblo],
    queryFn: () => fetchPiramideCapDiversas(codPueblo),
    enabled: !!codPueblo,
    staleTime: 60 * 1000,
    retry: 3,
    retryDelay: (attempt) => Math.min(500 * 2 ** attempt, 4000),
  });
}

export function usePiramideTipoDisc(codPueblo) {
  return useQuery({
    queryKey: ['piramide-tipo-disc', codPueblo],
    queryFn: () => fetchPiramideTipoDisc(codPueblo),
    enabled: !!codPueblo,
    staleTime: 60 * 1000,
    retry: 3,
    retryDelay: (attempt) => Math.min(500 * 2 ** attempt, 4000),
  });
}

export function usePiramideNacional(filters = {}) {
  const { cod_dpto, cod_mpio, cod_pueblo } = filters;
  return useQuery({
    queryKey: ['piramide-nacional', cod_dpto || null, cod_mpio || null, cod_pueblo || null],
    queryFn: () => fetchPiramideNacional({ cod_dpto, cod_mpio, cod_pueblo }),
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
}

export function usePiramideDiscNacional(filters = {}) {
  const { cod_dpto, cod_mpio, cod_pueblo } = filters;
  return useQuery({
    queryKey: ['piramide-disc-nacional', cod_dpto || null, cod_mpio || null, cod_pueblo || null],
    queryFn: () => fetchPiramideDiscNacional({ cod_dpto, cod_mpio, cod_pueblo }),
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
}

export function usePiramideDiscTipoNacional(filters = {}) {
  const { cod_dpto, cod_mpio, cod_pueblo } = filters;
  return useQuery({
    queryKey: ['piramide-disc-tipo-nacional', cod_dpto || null, cod_mpio || null, cod_pueblo || null],
    queryFn: () => fetchPiramideDiscTipoNacional({ cod_dpto, cod_mpio, cod_pueblo }),
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
}

export function usePerfilResguardo(codResguardo) {
  return useQuery({
    queryKey: ['perfil-resguardo', codResguardo],
    queryFn: () => fetchPerfilResguardo(codResguardo),
    enabled: !!codResguardo,
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
}

export function useResguardosDemografia(codMpio, codDpto) {
  return useQuery({
    queryKey: ['resguardos-demografia', codMpio, codDpto],
    queryFn: () => fetchResguardosDemografia(codMpio, codDpto),
    enabled: !!(codMpio || codDpto),
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
}

export function useResguardosPorPueblo(codPueblo) {
  return useQuery({
    queryKey: ['resguardos-por-pueblo', codPueblo],
    queryFn: () => fetchResguardosPorPueblo(codPueblo),
    enabled: !!codPueblo,
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
}

/* ---- Indicadores ---- */
export function useIndicadores() {
  return useQuery({
    queryKey: ['indicadores'],
    queryFn: fetchIndicadores,
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
}

export function useIndicadorSerie(codIndicador) {
  return useQuery({
    queryKey: ['indicador-serie', codIndicador],
    queryFn: () => fetchIndicadorSerie(codIndicador),
    enabled: !!codIndicador,
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
}

export function useIndicadorValores(periodo, nivelGeo) {
  return useQuery({
    queryKey: ['indicador-valores', periodo, nivelGeo],
    queryFn: () => fetchIndicadorValores(periodo, nivelGeo),
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
}
