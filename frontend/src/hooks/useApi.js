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

export function useDificultades(codDpto, grupoEtnico) {
  return useQuery({
    queryKey: ['dificultades', codDpto, grupoEtnico],
    queryFn: () => fetchDificultades(codDpto, grupoEtnico),
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
}

export function useSalud(codDpto) {
  return useQuery({
    queryKey: ['salud', codDpto],
    queryFn: () => fetchSalud(codDpto),
    enabled: !!codDpto,
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
}

export function useBrecha(codDpto) {
  return useQuery({
    queryKey: ['brecha', codDpto],
    queryFn: () => fetchBrecha(codDpto),
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

export function useFiltrosCascada(codDpto, codMpio) {
  return useQuery({
    queryKey: ['filtros-cascada', codDpto, codMpio],
    queryFn: () => fetchFiltrosCascada(codDpto, codMpio),
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
}

/* ---- Intercensal & SMT Resumen ---- */
export function useIntercensal(grupoEtnico) {
  return useQuery({
    queryKey: ['intercensal', grupoEtnico],
    queryFn: () => fetchIntercensal(grupoEtnico),
    staleTime: 5 * 60 * 1000,
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
export function usePueblos() {
  return useQuery({
    queryKey: ['pueblos'],
    queryFn: fetchPueblos,
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

export function useVictimasHechos(codDpto) {
  return useQuery({
    queryKey: ['victimas-hechos', codDpto],
    queryFn: () => fetchVictimasHechos(codDpto),
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
}

export function useVictimasPorPueblo(codDpto, limit = 20) {
  return useQuery({
    queryKey: ['victimas-por-pueblo', codDpto, limit],
    queryFn: () => fetchVictimasPorPueblo(codDpto, limit),
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
}

export function useVictimasPorHecho(codDpto) {
  return useQuery({
    queryKey: ['victimas-por-hecho', codDpto],
    queryFn: () => fetchVictimasPorHecho(codDpto),
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
}

export function useVictimasPorTipo(codDpto) {
  return useQuery({
    queryKey: ['victimas-por-tipo', codDpto],
    queryFn: () => fetchVictimasPorTipo(codDpto),
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
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
}

export function usePiramideTipoDisc(codPueblo) {
  return useQuery({
    queryKey: ['piramide-tipo-disc', codPueblo],
    queryFn: () => fetchPiramideTipoDisc(codPueblo),
    enabled: !!codPueblo,
    staleTime: 5 * 60 * 1000,
    retry: 1,
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
