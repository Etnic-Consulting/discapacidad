# SMT-ONIC — Framework v2.1

**Un director humano + un agente de IA orquestador + un builder local gratis, coordinados por una pizarra append-only, una cola de tareas tipificada por costo/modelo, y un dashboard que mide la salud del equipo — no la del proyecto.**

Instancia del framework Team-of-Two v2.1 dedicada al proyecto **SMT-ONIC** (Sistema de Monitoreo Territorial — ONIC). Cada proyecto del workspace tiene su propia instancia con configs, pizarra, cola y dashboard aislados; el nombre del framework coincide con el nombre del proyecto. Origen del runtime: ConvocaIA (`D:/1.Programacion/1.Identificacion_de_convocatorias`), adoptado aquí el 2026-04-21.

---

## 1 · Qué es y qué no es

### Es
- Un **protocolo** para coordinar humano + Claude + Ollama en un mismo repo.
- Un **runtime** en Python que lee/escribe 4 JSON configs, una pizarra JSONL, una cola JSONL, expone una API FastAPI (`:8096`) y pinta un dashboard Streamlit (`:8097`).
- Un **sistema de costos vivo** con tarifas Anthropic reales editables (no hardcode).
- Un **gate de calidad** con crown jewels + `[PRE-MERGE-AUDIT-REQ]` sobre los archivos irreversibles.

### No es
- Un framework de agentes autónomos (Auto-GPT, etc). El humano decide.
- Un reemplazo de Git/CI. Vive al lado del código.
- Especulativo: todo vive en `.framework/` del proyecto y es inspeccionable.

---

## 2 · Actores y tiers

| Rol | Quién | Cuándo actúa | Tier |
|---|---|---|---|
| **Director** | humano (Wilson Herrera) | Prioridades, firma gates, edita configs | — |
| **clip** | Claude Code | Orquesta + audita + builder para crown jewels | 1–3 (Sonnet 4.6 / Opus 4.6 / Opus 4.7) |
| **ollama** | 7 modelos locales | Spec cerrada, docs, edits simples | 0 ($0/llamada) |

**Regla dura:** el modelo más barato que pueda hacer el trabajo bien. Escalar solo con evidencia de que el inferior fallará.

```
¿Spec 100% cerrada ≤3 líneas?         → Ollama simple_edit (qwen3-coder 30b)
¿Función nueva, test happy-path?       → Ollama standard_code (qwen2.5-coder 32b)
¿Refactor 1–2 archivos?                 → Ollama complex_code (qwen3-coder-next)
¿Diagnóstico / análisis acotado?       → Ollama reasoning (deepseek-r1 32b)
¿Dominio SMT-ONIC (cnpv/victimas/smt_geo)? → Ollama standard_code (qwen2.5-coder)
¿≥3 archivos con state compartido?     → Sonnet 4.6
¿Arquitectura / seguridad / migración? → Opus 4.6
¿Crown jewel con lógica nueva?         → Opus 4.7
```

---

## 3 · Árbol de archivos

```
.framework/
├── README_FRAMEWORK_V2.1.md            ← este archivo
├── ROADMAP_FRAMEWORK_V2.1.md           ← roadmap 8 fases del framework
├── ADOPTION_GUIDE.md                   ← portar a otro proyecto
├── ROUTING.md                          ← reglas de routing por tier
├── STATE.md                            ← fase activa, en-marcha, bloqueos, historia
├── config/                             ← editable sin redeploy (5s cache)
│   ├── rates.json                      ← tarifas Anthropic + Ollama
│   ├── thresholds.json                 ← SLAs, heartbeat, gates, infra
│   ├── tiers.json                      ← catálogo de modelos + escalado
│   └── actors.json                     ← director + agentes + tags
├── api/                                ← FastAPI :8096
│   ├── server.py
│   ├── models.py                       ← Pydantic
│   ├── services/
│   │   ├── config_reader.py            ← TTL cache 5s
│   │   ├── pizarra_reader.py           ← normaliza 2 formatos JSONL
│   │   └── queue_reader.py
│   └── run_api.sh
├── dashboard.py                         ← Streamlit :8097 consume API
├── dashboard_v1_legacy.py               ← versión previa (KPIs proyecto, archivada)
├── comms/
│   └── log.jsonl                        ← PIZARRA ÚNICA append-only
├── tasks/
│   └── queue.jsonl                      ← cola con model_tier por tarea
├── runbooks/                            ← docs operacionales (deploy, rollback)
├── postmortems/                         ← P0 incidents, causas raíz
├── research/                            ← evaluaciones técnicas
└── memory/                              ← memoria persistente entre sesiones
```

---

## 4 · Pizarra única (`comms/log.jsonl`)

**Una sola pizarra concentra TODO**: mensajes humano ↔ agente, heartbeats, entregas, hallazgos, decisiones de routing, cambios de config, auditorías. No hay chat file separado.

Formato canónico (append-only JSONL):
```json
{
  "id": "CLI260421115600",
  "de": "clip",
  "para": "wilson",
  "fecha": "2026-04-21",
  "hora": "11:56:00",
  "ts": "2026-04-21T11:56:00-05:00",
  "mensaje": "[ENTREGADO] F1.1 | warm 7.37s convocav51 | fix validado",
  "meta": {"tag": "ENTREGADO", "task_id": "F1.1", "phase": "F1", "model": "opus-4.7"}
}
```

Tags reservados (`actors.json → comms.tags`):
`EMPEZANDO` · `ENTREGADO` · `PRE-MERGE-AUDIT-REQ` · `APROBADO` · `RECHAZADO` · `HALLAZGO` · `HEARTBEAT` · `BLOQUEADO` · `VERIFICADO` · `CHAT-HUMANO` · `CHAT-CLIP` · `CHAT-OLLAMA` · `NL-PARSE` · `ROUTING-DECISION` · `TASK-CREATED` · `CONFIG-CHANGED` · `CONFIG-MISSING` · `SESSION-START` · `SESSION-END`

El parser (`pizarra_reader.py`) tolera un segundo formato heredado (`{ts, actor, type, task, summary}`) y normaliza ambos.

---

## 5 · Cola de tareas (`tasks/queue.jsonl`)

Cada línea = una tarea. Campo `model_tier` marca el tier destino. Campo `depends_on` define dependencias. Status: `pending | in_progress | completed | blocked | deleted`.

```json
{
  "id": "F1.5-FIX-TELEMETRY-SOURCE-ID",
  "phase": "F1",
  "owner": "clip",
  "model_tier": "opus-4.6",
  "task_type": "complex_code",
  "priority": "P1",
  "quadrant": "Q2",
  "title": "ALTER extraction_telemetry.source_id VARCHAR(100) -> TEXT",
  "files": ["backend/alembic/versions/"],
  "spec": "Alembic revision ...",
  "status": "completed",
  "depends_on": [],
  "blocks": []
}
```

Eisenhower matrix (Q1=urgente+importante, Q4=ni uno ni otro) + prioridades P0–P3.

---

## 6 · Configs (sin hardcode)

Cuatro archivos JSON editables. Cambios se reflejan en ≤5s gracias al TTL cache. **El director edita, no el agente.**

### `rates.json` — tarifas Anthropic verificadas (2026-04)
```
opus-4.6 / opus-4.7: $15 / $75 por MTok
sonnet-4.6:          $3  / $15
haiku-4.5:           $1  / $5
cache_write ×1.25 · cache_read ×0.10 · batch ×0.50
ollama-local:        $0
budgets: daily_warn=$5, daily_hard=$20, monthly_warn=$100, monthly_hard=$400
```

### `thresholds.json` — SLAs
```
heartbeat: expected=30min, warn=45min, stale=90min
pre_merge_audit_max: 4h
hallazgo_critical: 8h · high: 24h · medium: 72h
burst_mode_response: 15min
rework_warn_pct: 15 · critical_pct: 30
ollama_recovery_floor: 0.55
gpu_temp_warn: 65°C · critical: 70°C
```

### `tiers.json` — catálogo
Mapea task_type → modelo Ollama. Define triggers de escalado (`ollama_failures≥2 → Sonnet`) y matriz de permisos sobre crown jewels (qué tier puede tocar qué archivo).

### `actors.json` — equipo
Director + agentes con `color`, `default_model`, `escalation_models`, `responsibilities`. Tags reservados aquí.

---

## 7 · API FastAPI `:8096`

| Endpoint | Qué devuelve |
|---|---|
| `GET /framework/health` | checks config/pizarra/queue + status |
| `GET /framework/config` | los 4 JSON configs |
| `GET /framework/overview` | snapshot agregado: director, agentes, activity, queue, findings |
| `GET /framework/pizarra?limit=100` | mensajes recientes normalizados |
| `GET /framework/queue` | tareas + by_status/owner/tier + blocked |

Endpoints futuros (roadmap F7): `POST /framework/chat` para NL → Ollama parse → Claude route → cola.

Lanzar: `bash .framework/api/run_api.sh` (uvicorn :8096).

---

## 8 · Dashboard Streamlit `:8097`

**NO muestra KPIs del proyecto** (oportunidades, donantes, patrones). **SOLO** muestra la salud del equipo:

- **6 KPIs top:** pending/in_progress/completed/blocked/audits/findings
- **Panel Equipo:** cards por actor (director + agentes) con heartbeat (🟢🟡🔴), mensajes 1h/24h, segundos desde último
- **6 tabs:**
  1. 💬 **Pizarra** — todos los mensajes con colores por actor + chat input (F7)
  2. 📋 **Cola** — tabla de tareas pageable
  3. 🧭 **Routing** — distribución por tier / owner
  4. 💰 **Costos** — tarifas vivas + proyecciones
  5. 🩺 **Salud Ops** — checks API + infra requerida
  6. ⚙️ **Config** — los 4 JSON en read-only con expanders

Auto-refresh 10s. Consume solo `:8096`, no toca Postgres.

---

## 9 · Delegación a Ollama

Script: `framework_runtime_v1.1/framework_runtime/scripts/delegate_to_ollama.py`

```bash
python delegate_to_ollama.py \
  --task-id "F5.1-RUNBOOK-DEPLOY" \
  --task-type standard_code \
  --target "path/to/out.md" \
  --mode newfile \
  --spec "..." \
  --timeout 180
```

**Modos:**
- `patch` — Ollama produce archivo completo, sobreescribe. ⚠️ no aplica diff real.
- `replace` — idem, explícito.
- `append` — agrega al final.
- `newfile` — crea archivo nuevo.
- `print` — solo imprime resultado (para revisar antes).

**Crown jewel guard:** si `target` matchea globs en `actors.json → crown_jewel_globs`, aborta salvo `--crown-jewel-ack`.

**Auto-logging:** cada llamada escribe `[ENTREGADO]` o `[OLLAMA-FAIL]` a pizarra con model, tokens, duration, cost=$0.

Routing automático de modelo vía `OllamaClient.select_model_for_task(task_type)` leyendo `OLLAMA_ROUTING` env o `tiers.json`.

---

## 10 · Protocolo de sesión

**Inicio:**
1. Leer `.framework/STATE.md` (fase activa, en-marcha, bloqueos)
2. Leer `.framework/tasks/queue.jsonl` (P0→P1→Q1→Q2)
3. Identificar próxima tarea desbloqueada

**Durante (checkpoint 30–45min):**
1. `[EMPEZANDO] <task-id>` en pizarra
2. Trabajo (usar tier correcto)
3. `[ENTREGADO] <task-id> | resumen` + actualizar queue.jsonl
4. Si crown jewel: `[PRE-MERGE-AUDIT-REQ]` antes de merge

**Cierre:**
1. `[SESSION-END]` en pizarra
2. Actualizar `STATE.md` con entregado + próximo
3. Checkpoint memoria si existe `memory_sync.py`

---

## 11 · Crown jewel set

Archivos cuyo cambio requiere tier ≥ Opus 4.6 + `[PRE-MERGE-AUDIT-REQ]` antes de merge. Definidos en `config/tiers.json → crown_jewel_permissions`:

| Archivo | Ollama | Sonnet | Opus 4.6 | Opus 4.7 |
|---|---|---|---|---|
| backend/app/main.py | ❌ | ⚠️ con audit | ✅ con audit | ✅ |
| backend/app/api/deps.py | ❌ | ⚠️ | ✅ | ✅ |
| docker-compose.yml | ❌ | ❌ | ✅ con director | ✅ |
| requirements.txt | ❌ | ❌ | ✅ | ✅ |
| package.json | ❌ | ❌ | ✅ | ✅ |
| start_all.sh | ❌ | ⚠️ | ✅ | ✅ |

Ajustar la lista en `tiers.json` según el proyecto.

---

## 12 · Costos y telemetría

- **Ollama:** $0 por llamada. Siempre.
- **Claude:** calculado con `rates.json` × tokens. Cache-write y cache-read usan multipliers.
- Cada llamada (Ollama o Claude) escribe a pizarra con `model`, `tokens`, `duration_s`, `task_id`, `cost_usd`.
- Budgets: alerta cuando `daily_warn` se alcanza, bloqueo duro en `daily_hard`.

---

## 13 · Qué sigue (roadmap v2.1 · faltan F1–F7)

| Fase | Qué añade | Builder |
|---|---|---|
| F1 | Panel Activity (heartbeats vivos) | Ollama + review |
| F2 | Panel Progress (cola, throughput) | Ollama |
| F3 | Panel Quality (findings, rework, audits) | Sonnet |
| F4 | Cost calculator (tokens × rates) | Sonnet |
| F5 | Panel Health Ops (docker ps, ollama, psutil) | Ollama devstral |
| F6 | Panel Routing (escalados, degradados) | Sonnet |
| F7 | **Chat NL** (humano → Ollama parsea → Claude rutea → cola) | Opus 4.6 |

---

## 14 · Limitaciones conocidas

- **Docker Desktop se degrada** bajo carga sostenida (engine API HTTP 500). Restart manual obligatorio. No tenemos watchdog todavía (planificado F4 del roadmap ConvocaIA).
- **`delegate_to_ollama.py --mode patch`** sobrescribe archivo completo; no aplica diff. Para edits parciales: usar `--mode print` y aplicar manualmente.
- **SSE detrás de BaseHTTPMiddleware** rompe; usar `EventSource` nativo con `?token=` query param.
- **Ollama saturación**: 1 call OK, 6 en paralelo → 5s→360s timeouts. Fix: semaphore Redis `max_parallel=4` + timeout 90s.
- **NOTA OLLAMA_HOST**: Ollama setea `OLLAMA_HOST=host:port` automáticamente. El cliente del framework parseaba mal → doble puerto. Fix en `ollama_client.py` (2026-04-21).
- **API :8096 arranca cache-write con DateTimes mixtos.** Solucionado normalizando todo a UTC-aware en `pizarra_reader.py`.

---

## 15 · Filosofía

1. **Todo observable.** No hay decisiones invisibles: cada acción deja traza en pizarra.
2. **Modelo mínimo suficiente.** Caro solo cuando hay evidencia.
3. **Humano decide, framework ejecuta.** Wilson firma gates; no hay auto-promotion sin evidencia.
4. **Configs vivos, código estático.** Umbrales, tarifas, tiers → JSON. Lógica → código.
5. **Framework mide framework.** Dashboard no muestra KPIs de negocio; muestra salud del equipo.

---

**Versión:** v2.1 · **Instancia:** SMT-ONIC · **Origen del runtime:** ConvocaIA (D:/1.Programacion/1.Identificacion_de_convocatorias) · **Adoptado:** 2026-04-21
