# ROUTING — Asignación de tareas por modelo

**Principio:** el modelo más barato que pueda hacer el trabajo bien. Escalar solo cuando hay evidencia de que el modelo inferior fallará.

---

## Jerarquía de modelos (de barato a caro)

| Tier | Modelo | Costo/llamada | Velocidad | Uso |
|---|---|---|---|---|
| 0 | **Ollama local** (7 modelos) | $0.00 | 5–60s | Tareas con spec cerrada, ediciones simples, dominio SMT-ONIC |
| 1 | **Claude Sonnet 4.6** | bajo | 2–10s | UI multi-archivo, refactors medios, code review, fallback Ollama |
| 2 | **Claude Opus 4.6** | medio-alto | 5–20s | Arquitectura, debug distribuido, seguridad crítica |
| 3 | **Claude Opus 4.7** (este) | alto | 5–30s | Crown jewels, decisiones irreversibles, orquestación, audit complejo |

---

## Tier 0 — Ollama (routing por `task_type`)

| `task_type` | Modelo | Cuándo usarlo |
|---|---|---|
| `simple_edit` | `qwen3-coder:30b-a3b-q4_K_M` | Edición ≤3 líneas, spec literal, sin decisión |
| `standard_code` | `qwen2.5-coder:32b-instruct-q5_K_M` | Función nueva, módulo simple, test happy-path |
| `complex_code` | `qwen3-coder-next:q4_K_M` | Refactor ≤2 archivos, lógica no trivial pero acotada |
| `reasoning` | `deepseek-r1:32b` | Diagnóstico, análisis arquitectural acotado, gap detection |
| `domain` | (no aplica en SMT-ONIC) | Reservado para futuros LoRA específicos del dominio SMT |
| `agentic` | `devstral:latest` | Tarea multi-paso autónoma con herramientas |
| `vision` | `qwen2.5vl:7b` | Análisis de capturas, screenshots |

**Invocación:** `python framework_runtime/scripts/delegate_to_ollama.py --task-type X --target Y --spec "..."`

**Crown jewel guard:** automático — exige `--crown-jewel-ack`.

---

## Tier 1 — Sonnet 4.6 (Claude API)

**Triggers:**
- Tarea toca ≥3 archivos con dependencias (Ollama pierde contexto entre archivos)
- Refactor que requiere comprender invariantes globales
- Frontend Next.js con state management complejo
- Code review de PR humano antes de merge
- Ollama falló 2 veces en la misma tarea

**Invocación:** Claude Code abre nueva sesión con flag de modelo o el director cambia con `/model claude-sonnet-4-6`

**Costo orientativo:** $0.005–$0.05 por tarea. Mantener log en `.framework/comms/cost_log.jsonl`.

---

## Tier 2 — Opus 4.6 (Claude API)

**Triggers:**
- Decisión de arquitectura con costo de error alto (e.g. esquema DB que afecta migrations futuras)
- Debug de race condition / problema distribuido
- Seguridad: revisar autenticación, autorización, manejo de tokens
- Migración con potencial de downtime
- Análisis cross-impacto de cambio en >5 archivos

**Costo orientativo:** $0.05–$0.50 por tarea. Justificar en pizarra antes.

---

## Tier 3 — Opus 4.7 (Claude API, actual sesión)

**Triggers (cualquiera de estos):**
- Modificación de **crown jewel** con lógica nueva (no patch trivial)
- Orquestación del framework multi-agente (esta sesión es ejemplo)
- Postmortem de incidente P0 con causa raíz no obvia
- Decisión irreversible: borrado masivo de datos, cambio de proveedor LLM, downgrade de modelo en producción
- Audit completo punta-a-punta

**Costo orientativo:** $0.10–$2.00 por tarea. Director firma antes.

---

## Reglas de escalado y degradado

### Cuándo escalar (subir tier)

1. **Ollama falla 2 veces** con la misma `task_type` → reintentar con Sonnet
2. **Sonnet entrega código sintácticamente OK pero con bug lógico** detectado en review → Opus 4.6
3. **Opus 4.6 entrega solución que rompe gate de producción** → Opus 4.7

### Cuándo degradar (bajar tier)

1. Si Opus 4.7 está haciendo `simple_edit` → mover a Ollama inmediatamente
2. Si Sonnet está respondiendo preguntas de "¿dónde está X?" → no es escalado, es búsqueda; usar grep
3. Si tres tareas seguidas del mismo tier salen perfectas → la próxima similar baja un tier para validar

### Crown jewel set — quién puede tocar

| Archivo | Ollama | Sonnet | Opus 4.6 | Opus 4.7 |
|---|---|---|---|---|
| `backend/app/main.py` | ❌ | ⚠️ con audit | ✅ con audit | ✅ |
| `backend/app/database.py` | ❌ | ⚠️ con audit | ✅ con audit | ✅ |
| `backend/app/services/auth.py` | ❌ | ⚠️ con audit | ✅ con audit | ✅ |
| `backend/app/routers/dashboard.py` | ❌ | ✅ | ✅ | ✅ |
| `backend/app/routers/formulario.py` | ❌ | ✅ | ✅ | ✅ |
| `backend/scripts/load_*.py` | ❌ | ⚠️ con audit | ✅ con audit | ✅ |
| `docker-compose.yml` | ❌ | ❌ | ✅ con director | ✅ |
| `backend/requirements.txt` | ❌ | ❌ | ✅ | ✅ |
| `frontend/package.json` | ❌ | ❌ | ✅ | ✅ |
| `frontend/src/context/FilterContext.jsx` | ❌ | ✅ | ✅ | ✅ |

⚠️ = permitido pero exige `[PRE-MERGE-AUDIT-REQ]` ANTES + diff revisado por tier superior.

---

## Decisión rápida — flowchart mental

```
¿La spec está 100% cerrada y es ≤3 líneas?
  └─ SÍ → Ollama simple_edit
  └─ NO ↓
¿Es una función nueva, módulo simple, test happy-path?
  └─ SÍ → Ollama standard_code
  └─ NO ↓
¿Toca crown jewel?
  └─ SÍ → Opus 4.6 mínimo (4.7 si lógica nueva)
  └─ NO ↓
¿Multi-archivo con state shared?
  └─ SÍ → Sonnet
  └─ NO ↓
¿Refactor dentro de 1-2 archivos?
  └─ SÍ → Ollama complex_code
  └─ NO ↓
¿Diagnóstico / análisis?
  └─ SÍ → Ollama reasoning (deepseek-r1)
  └─ NO ↓
¿Decisión irreversible o arquitectura?
  └─ SÍ → Opus 4.6 o 4.7
```

---

## Telemetría obligatoria

Cada llamada a Ollama escribe a pizarra (`.framework/comms/log.jsonl`) con:
- `model`, `tokens`, `duration_s`, `target`, `task_id`, `cost=0`

Cada llamada a Claude (cualquier tier) debe escribir a pizarra con:
- `model`, `input_tokens`, `output_tokens`, `cost_usd`, `task_id`

Esto alimenta el dashboard `:8097` panel "Costos Claude" y permite al director auditar el gasto.

---

## Estado actual (2026-04-21)

- **Ollama nativo Windows**: ✅ corriendo `:11434`. 11 modelos disponibles.
- **Claude Sonnet/Opus**: disponibles vía Claude Code (`/model`).
- **Routing actual**: solo Ollama tier 0 está auto-routed. Sonnet/Opus son manuales por ahora (futuro: auto-escalado en `delegate_to_ollama.py`).
