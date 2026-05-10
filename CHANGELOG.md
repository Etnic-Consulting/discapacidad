# CHANGELOG · SMT-ONIC

Formato: [Keep a Changelog](https://keepachangelog.com/es/1.1.0/) · SemVer.

---

## [1.4.1] · 2026-05-10 · Completitud render + handoff ingeniería ONIC

Sprint `S9_render_multinivel` continuación (T08-T20) · branch `restore/v2-styling`.

### Added

- Documentación handoff completa en `_docs/`:
  - `ARCHITECTURE.md` (3 capas Docker · 8 schemas DB · flujo datos REDATAM → render → API → Vite)
  - `MATRIZ_AUTH_v1.md` (endpoints públicos vs auth vs admin · rationale doctrinal)
  - `RUNBOOK_INCIDENTES.md` (10 incidentes con diagnóstico y acción)
  - `CHECKLIST_GO_LIVE.md` (40 items binarios pre-go-live)

### Fixed

- **Completitud render multinivel** (`backend/scripts/render_informes.py:_ids_para_nivel`): mpio ahora itera sobre `geo.municipios` (1.122 ids) en vez de `cnpv.disc_indigena_mpio` (967). Los 155 mpios sin datos CNPV indígena usan fallback `pob_indigena=0, _sin_datos:true` honesto (NO inventan cifras).
- **4 pueblos huérfanos cubiertos**: 433 JUHUP · 855 TAYRONAS · 860 CHITARERO · 940 INDIGENAS-BRASIL · ahora generan informe con `_sin_datos:true` vía UNION con `pueblo.pueblo_municipio`.
- **Bug crítico `infra/init_db.sh`**: ahora aplica seeds 010-013 además de 002-009. Sin esto, el deploy producía nacional indígena ~3.7M en lugar de ~1.83M esperado CNPV 2018 (Cumaribo/Vichada bug). Agregado sanity check 7b validando rango 1.7M-2.0M.

### Notes

- **Total post-T09**: 2.127 informes regenerados (5 macro + 33 dpto + 1.122 mpio + 137 pueblo + 830 resguardo).
- **Audit cells_dash_pct promedio 0.93%** (mejoró vs 1.01% pre-T08 · criterio plan <5% cumplido).
- **Deuda heredada activa**: drift universo poblacional +46% en `pueblo.disc_dpto` (afros/sin-pertenencia leak) · NO filtrable runtime · diferido a sprint S10 dedicado · ver `_doctrina/LECCIONES.md` Caso 11 y `_docs/RUNBOOK_INCIDENTES.md` Incidente 10.

---

## [1.4.0] · 2026-05-09 · Re-render multinivel honesto · Sprint S9

Sprint `S9_render_multinivel` (T01-T07) · branch `restore/v2-styling`.

### Added

- **Lógica W12-honesta extendida a 4 niveles**: dpto/mpio/pueblo/resguardo (antes solo macro).
- **JSON canonical con trazabilidad**: campo `_meta` por cifra (query SQL, table origen, period, confiabilidad CONFIABLE/BAJA), `_input_hash` SHA256[:16] para integridad.
- **HTML templates con k-anonimato VISUAL HONESTO**: badge `CONFIABLE` (verde) si `con_disc >= 30`, badge `n<30` (amarillo) con celdas `—` si menor. Reemplaza al generador histórico que usaba `n<30` falso.
- **Pirámide CD edad×sexo en informes pueblo** (`HTML_TEMPLATE_PUEBLO` con SVG/CSS · barras horizontales H verde-azul / M morado).
- **Tabla "Resguardos asociados" en informes mpio** (cruce `smt_geo.resguardos` × `mpio_cdpmp` · reusa lógica v1.3.0 sin copy-paste).

### Changed

- **Refactor `render_informes_macro.py` → `render_informes.py`** paramétrico con CLI `--nivel macro|dpto|mpio|pueblo|resguardo|todos` · `--ids` subset · `--dry-run` · `--output-root`.
- **Helpers compartidos extraídos**: `_conn` · `_confiabilidad_badge` · `_input_hash` · `_write_canonical` · `_write_html`. Renderers ahora son 5 funciones aisladas con misma estructura.

### Fixed

- **Audit cells_dash_pct promedio 1.01%** post-rerender (criterio plan <5% cumplido). 33 dpto con dash>5% son legítimos (pueblos n<30 honestos).

### Notes

- **Total regenerado**: 1.955/2.114 informes (5+33+967+120+830 · 92.5%). Los 159 huérfanos cubiertos en v1.4.1.
- **Modelos usados**: T01 Claude Opus 4.7 (arquitectura) · T02 gemini-2.5-pro (rechazo qwen-coder-7b previo) · T03/T04/T05 Claude Opus 4.7 (escalada regla #7 post fallo gemini-pro) · T06/T07 Claude Opus 4.7 (auditoría + manifest).
- **Deuda heredada documentada**: drift universo poblacional `pueblo.disc_dpto` +46% (afros/sin-pertenencia leak · NO filtrable con WHERE porque la tabla no tiene `grupo_etnico`/`tipo_etnia`). NO es bug del render · es leak upstream. Sprint S10 dedicado para fix REDATAM re-extracción. Ver `_doctrina/LECCIONES.md` Caso 11.

---

## [1.3.0] · 2026-05-09 · hotfix tabla resguardos en mpios

Sprint `S7_render_dptos` (1 tarea) · branch `restore/v2-styling`.

### Fixed

- **Tabla "Resguardos asociados" en informes mpio** (W17 · `backend/scripts/fix_mpio_resguardos_table.py`). 44 HTMLs mpio tenían las columnas Dpto/Municipio vacías (`—`). Fix quirúrgico con regex que mapea cada resguardo a su dpto/mpio real desde `smt_geo.resguardos`. Idempotente · 360 filas arregladas · audit `flagged_informes.csv` cae de 50 → 6 (88% reducción · los 6 restantes son truncados borderline esperados).

### Hallazgo

El plan original v1.3 era extender `render_informes_macro.py` a los 33 dptos. La auditoría reveló que los **32 dptos ya tenían cifras correctas** (solo cod_dpto=88 San Andrés está truncado por falta de datos indígenas significativos · esperado). El bug real estaba en los **44 mpios** con la tabla "Resguardos asociados" rota. Plan ajustado al diagnóstico real.

### Diferido a v1.4

- Re-render de 1.121 mpios + 125 pueblos + 830 resguardos completo (este v1.3 solo arregló filas problemáticas · no regeneró desde cero)
- Bug dispatcher cp1252 + telemetría task_id

---

## [1.2.0] · 2026-05-09

Sprint `S6_observatorio` · branch `restore/v2-styling` · 11 tareas drenadas.

### Added

- **Endpoints `/api/v1/observatorio/*`** (W13-API · `backend/app/routers/observatorio.py`). 6 endpoints read-only sobre `smt.respuestas_formulario` + `smt.resumen` con k-anonimato k≥5 enforced en agregaciones territoriales: `/kpis`, `/distribucion-territorial`, `/tipos-dificultad`, `/ayudas-tecnicas`, `/timeline?bucket=week|month`, `/ultimas-respuestas?limit=N`.
- **Página `/observatorio`** (W13-UI · `frontend/src/pages/ObservatorioPage.jsx`). Dashboard de captura territorial propia: 4 KPIs · 2 BarCharts territoriales · 2 BarCharts (tipos dificultad + ayudas técnicas) · LineChart timeline · tabla 20 últimas respuestas anonimizadas.
- **6 hooks fetch en `lib/api.js`** para consumir endpoints observatorio.
- **Script `render_informes_macro.py`** (W12-RENDER · `backend/scripts/`). Genera JSON+HTML correcto para los 5 macros desde `pueblo.disc_dpto + geo.macro_dptos`, k-anonimato HONESTO (n<30 solo si aplica de verdad). Reemplaza al pipeline histórico no commiteado.
- **Heurística `cells_dash_pct`** en `audit_informes.py` (W12-AUDIT). Flagea HTMLs con >30% celdas `—` en tablas. Detectó 44 informes a re-renderizar en sprints futuros.
- **Seed 200 fixtures** (W14 · `backend/scripts/W14_seed_smt_200.py`). 200 respuestas distribuidas (40/macro · 191 cpli=si · 9 cpli=no) con 9 tipos dificultades · 5 ayudas · 5 niveles educativos · 90 días dispersos. Idempotente.
- **Script localhost fix** (W15 · `backend/scripts/W15_fix_localhost_paths.py`). Reemplaza paths absolutos `http://localhost:*` por relativos en HTMLs de informes. Idempotente · backup en `_audits/localhost_backups/`.

### Fixed

- **Tabla "Departamentos con mayor presencia" en informes macro** (W12). Antes mostraba TODAS las celdas con `—` y badge `n<30` falso (cifras reales en BD eran >> 30: CESAR 3.093 · LA GUAJIRA 5.059 · CHOCÓ 4.198 · CÓRDOBA 10.394 · MAGDALENA 955). Ahora muestra cifras reales · k-anonimato honesto.
- **Duplicados cod_dpto en `territorial.departamentos` JSON canonical** macros (cod_dpto 23/44/47 con nombres confundidos). Resuelto al regenerar desde `geo.macro_dptos` con DISTINCT.
- **Endpoint `/dashboard/smt-resumen`** (parcial vía W14): trigger ahora alimenta dimensiones reales (no `2026-F1` hardcoded · `2026-05` con datos vivos).

### Changed

- **Pipeline informes macro** ahora versionado en repo (`render_informes_macro.py`) · re-ejecutable cualquier momento contra DB en vivo.
- **`backend/app/main.py`**: registra router `observatorio` (`/api/v1/observatorio` tag "Observatorio").

### Technical · doctrina LOCAL-FIRST estricta

100% tareas LLM pasaron por `dispatch_envuelto.py sembrar-uno` con cadena `local_first_codigo`. Ollama qwen2.5-coder:7b fue invocado como primer modelo siempre. Para tareas de modificación incremental en proyectos complejos, los outputs Ollama requirieron escalada a Claude Opus por calidad. Ver `outputs/W16_RELEASE_AUDIT.md` para distribución detallada.

### Diferido a v1.3

- Re-render de 33 dptos · 1.121 mpios · 125 pueblos · 830 resguardos con `render_informes_<nivel>.py`
- Bug dispatcher cp1252 UnicodeEncodeError
- Bug telemetría `task_id: unknown` en `metricas_v2.jsonl`
- 5 HTMLs con `localhost` residual

---

## [1.1.0] · 2026-05-09 · GA

Sprint `S5_v1_1` · branch `restore/v2-styling` · 17 tareas drenadas en sesión autónoma.

### Added

- **Endpoint `/api/v1/demografia/piramide-disc-tipo/{cod_pueblo}` con fallback regional** (W02). Query param `fallback=true` activa cascada `pueblo → dpto → macro → sin_datos` cuando un pueblo no tiene datos suficientes (k>=200 enforced en la fuente). Respuesta incluye campos `granularidad` y `entidad_origen`. Datos no inventados · agregaciones SQL con `HAVING SUM(valor) >= 30` (k-anonimato).
- **Componente frontend `RangoEdadTipoDisc.jsx`** (W03). 4 banners visuales por granularidad (pueblo / dpto / macro / sin_datos) con mensaje honesto sobre el k-anonimato cuando aplica fallback regional.
- **Componente frontend `PiramidePoblacional.jsx`** (W01). Pirámide poblacional vertical mariposa con `.slice().reverse()` para layout Recharts. Separado del componente genérico previo.
- **Componente frontend `RangoEdadDiscBar.jsx`** (W01). Barras horizontales de capacidades diversas con orden cronológico ascendente (0-4 izq → 85+ der), SIN reverse.
- **Tabla `smt.resumen` + trigger k-anonimato** (W04 · migración `012_smt_resumen.sql`). Función `smt.recalcular_resumen()` AFTER INSERT/UPDATE/DELETE en `respuestas_formulario` agrega por dimensión (macro · tipo_dificultad · completitud) con `HAVING COUNT(*) >= 30`.
- **Endpoint `/api/v1/dashboard/smt-resumen` extendido** (W06). Auto-detect periodo más reciente con datos · query params `dimension` y `periodo` opcionales · respuesta agrupada con `data` + `agrupado` + lista de dimensiones disponibles.
- **80 fixtures sembradas en `smt.respuestas_formulario`** (W05 · `_scripts/W05_seed_smt_fixtures.py`). Distribuidas en 5 macros · CPLI=si · datos JSONB completos (dificultades · ayudas · salud · educación · vivienda · trabajo) · idempotente (DELETE `_fixture=true` antes de insert).
- **Tests E2E formulario** (W07 · `backend/tests/test_formulario_e2e.py`). 3 tests cubren flujo completo POST → trigger → smt.resumen → GET smt-resumen + verificación k-anonimato + existencia de fixtures.
- **Auditor automático de informes** (W08 · `backend/scripts/audit_informes.py`). 5 heurísticas binarias (truncado · falta_seccion · llm_bloqueado · sin_citas · todos_cero) → `_audits/flagged_informes.csv`.
- **MANIFEST de informes con SHA256** (W09 · `backend/scripts/manifest_informes.py` + `backend/_static/informes/MANIFEST.json`). Hash SHA256 + size + modified_iso de los 2.114 informes pre-renderizados.
- **Re-render template-Python sin LLM externo** (W10 · `backend/scripts/rerender_flagged_informes.py`). Reemplaza secciones `.llm.json` con texto institucional template usando solo cifras del JSON canonical.
- **Datos REDATAM Vichada CNPV2018** (V01 · `bd_consolidada/vichada_redatam.csv`). 226 filas para 4 mpios (Cumaribo · Pto Carreño · La Primavera · Sta Rosalía) · SHA256 idempotente · `_docs/INTEGRIDAD_V01.md`.
- **Tests de routers backend** (V04 · V05 · V06). 132 tests nuevos cubriendo `pueblos.py` (100%) · `geo.py` (100%) · `indicadores.py` (100%) · `dashboard.py` (89%) · `informes.py` (97%) · `conflicto.py` (90%).
- **Smoke perf regression** (V10 · `backend/scripts/V10_lighthouse_regression.py`). Mide latencia + status de 5 páginas críticas · 5/5 OK <50ms (umbral 2000ms).
- **Hook enforcement_sin_retrocesos** (Visual_Agentes V2). Promueve a `tipo:critica` cualquier tarea con 2+ RECHAZADO consecutivos en INTERACCIONES.md.
- **Bloque `v1_1_consolidacion` en `criterios_audit.yml`** con 10 reglas bloqueantes para auditor (smoke 7/7 + cov ≥50% + imports prohibidos + sustento empírico + LOCAL-FIRST + ...).

### Fixed

- **Bug ordenamiento pirámide pueblo Pijao** (W01 · descubierto por Wilson 2026-05-09). El componente `PopulationPyramid` aplicaba `.reverse()` indistintamente para visualización vertical (correcto · 85+ arriba) y horizontal (incorrecto · invertía orden cronológico). Resuelto con split en 2 componentes especializados.
- **Bug crítico `smt_geo.dim_dptos` inexistente** en migración 012 (W07 · descubierto por subagente). Función `smt.recalcular_resumen()` referenciaba tabla inexistente. Migración `013_fix_trigger_dim_dptos.sql` sustituye por `smt_geo.comunidades` con fallback `datos->>'macrorregion'` del JSONB. Aplicada en vivo.
- **Falsos positivos en heurística audit_informes** (W08). Detectaba `info_basica` que no existía como sección · ajustado a `capacidades_diversas/territorial/conflicto/icv`. Heurística `sin_citas` inicial buscaba `DANE/CNPV` en JSON canonical donde no aparece como texto · refinada para buscar en `.llm.json` o detectar `_meta` con SQL trazable. De 1.320 falsos positivos a 1 real.
- **Bug periodo hardcoded en `/dashboard/smt-resumen`** (W06). Antes solo retornaba datos de `periodo='2026-F1'` · ahora auto-detecta el más reciente con datos.
- **`config.py` pydantic v2 deprecation** (V05 · subagente). Migrado de `class Config` a `model_config = ConfigDict(extra="ignore")`.

### Performance

- Lighthouse smoke 5/5 páginas OK · latencias 0-32ms (umbral 2000ms · margen 60×).
- Cobertura backend tests: **93% líneas** (881 statements totales · 825 cubiertos · supera umbral 50%).

### Diferido a v1.2

- Glitchtip Vite (V08 original) · observabilidad frontend
- Grafana alert rules (V09 original) · `infra/alerts.yml`
- 1 informe `dpto/88` borderline (4.2KB · umbral 5KB) · regenerable en hotfix

### Auditoría release

`outputs/W11_RELEASE_AUDIT.md` · firmado Claude Opus 4.7 · 16/16 tareas pre-W11 APROBADAS por auditor (scores 0.88-1.00 · sin RECHAZADOS).

---

## [1.0.3] · 2026-05-09 · UX hotfix

11 ajustes UX validados por Wilson en checklist 10 puntos.

### Fixed

- FASE 1 · CertificationFunnel · paso SMT en muted "Pendiente · captura territorial" (NO 0)
- FASE 2 · useApi.js + PuebloDetallePage · retry+staleTime hooks pirámide · placeholder honesto
- FASE 3 · TerritoriosPage · select "Indicador" inerte eliminado · cascada Dpto→Mpio→Resguardo OK
- FASE 4 · ConflictoPage · BarChart con labels legibles (truncado 38 chars + tooltip nativo)
- FASE 5 · VozPropiaPage · Sección A (3 charts CNPV) + Sección B "Captura territorial pendiente"
- FASE 6 · Sidebar + PanoramaPage · Indicadores fuera del top-nav + link discreto al final
- FASE 7 · informes.py + App.jsx + InformesPageV2 · cap 500 eliminado + endpoint `_catalog` + cascada Macro→Dpto→Mpio→Resguardo

Smoke 7/7 PASS · pytest backend 179/179 PASS · `_index` 2.114 informes · `_catalog` 5/33/1.121/125/830.

---

## [1.0.0] · 2026-04-30 · GA inicial

Pre-renderización de 2.114 informes territoriales · auth + formulario · 5 niveles cascada · go-live producción.
