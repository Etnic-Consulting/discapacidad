# Adoption Guide — Adopta Framework v2.1 en otro proyecto

Pasos para portar el **framework Team-of-Two v2.1** a otro repositorio y tenerlo operando en ~30 minutos.

Prerequisitos: Python 3.12, `pip install fastapi uvicorn streamlit requests pydantic pydantic-settings`. Ollama nativo recomendado pero opcional (puedes empezar con solo Claude).

---

## Paso 1 · Copiar estructura base

Desde ConvocaIA:

```bash
TARGET=/ruta/a/tu_proyecto
mkdir -p $TARGET/.framework/{config,api/services,api/routers,comms,tasks,runbooks,postmortems,research,memory}

# Copiar archivos canónicos (ajustables)
cp .framework/api/server.py          $TARGET/.framework/api/
cp .framework/api/models.py          $TARGET/.framework/api/
cp .framework/api/services/*.py      $TARGET/.framework/api/services/
cp .framework/api/run_api.sh         $TARGET/.framework/api/
cp .framework/dashboard.py           $TARGET/.framework/
cp .framework/config/*.json          $TARGET/.framework/config/
cp .framework/README_FRAMEWORK_V2.1.md $TARGET/.framework/
cp .framework/ROUTING.md             $TARGET/.framework/
```

Empty seeds:
```bash
: > $TARGET/.framework/comms/log.jsonl
: > $TARGET/.framework/tasks/queue.jsonl
```

---

## Paso 2 · Customizar `config/actors.json`

Editá a mano:

```json
{
  "director": {"id": "tu_alias", "name": "Tu Nombre", "alias": ["..."], "role": "director", "color": "#22c55e"},
  "agents": [
    {"id": "clip", "default_model": "claude-sonnet-4-6", "color": "#3b82f6", "..."},
    {"id": "ollama", "default_model": "qwen2.5-coder:32b", "color": "#a855f7", "..."}
  ],
  "comms": {"pizarra_path": ".framework/comms/log.jsonl", ...}
}
```

Si no usás Ollama: quitá el agente `ollama` del array.

---

## Paso 3 · Customizar `config/tiers.json`

Clave `crown_jewel_permissions`: reemplazá los paths de ConvocaIA por los **de tu proyecto**. Ejemplos:

```json
"crown_jewel_permissions": {
  "backend/main.py":          {"ollama": false, "sonnet": "audit_required", "opus_4_6": true, "opus_4_7": true},
  "infra/terraform/main.tf":  {"ollama": false, "sonnet": false, "opus_4_6": "director_required", "opus_4_7": true},
  "package.json":             {"ollama": false, "sonnet": false, "opus_4_6": true, "opus_4_7": true}
}
```

Clave `tiers[0].task_types`: ajustá los modelos Ollama según los que tengas localmente (`ollama list`).

---

## Paso 4 · Customizar `config/thresholds.json`

Reemplazá:
- `infra.docker_required_containers` → los containers de tu stack.
- `infra.ollama_required_models` → los modelos que tu proyecto necesita.
- `quality_gates.ollama_recovery_floor` → si usás pipeline LLM; si no, quitalo.

Budgets en `rates.json` → ajustá `daily_warn/hard`, `monthly_warn/hard` al bolsillo del proyecto.

---

## Paso 5 · Crear `STATE.md` de arranque

Plantilla mínima:

```markdown
# STATE.md — <TuProyecto>

**Proyecto:** <...> · **Director:** <nombre> · **Framework:** Team-of-Two v2.1
**Fase actual:** F0 — adopción del framework

## [EQUIPO ACTIVO]
| Actor | Rol | Modelo |
|---|---|---|
| clip | Builder + auditor | Sonnet 4.6 / Opus 4.6 |
| ollama | Builder tareas cerradas | 7 modelos |
| <director> | Director | humano |

## [EN_MARCHA]
- (arranque)

## [CROWN_JEWEL_SET]
Ver `.framework/config/tiers.json`.
```

---

## Paso 6 · Seed de la cola

Archivo `.framework/tasks/queue.jsonl` con una primera tarea para que el dashboard tenga algo que mostrar:

```json
{"id":"INIT-1","phase":"F0","owner":"clip","model_tier":"sonnet-4.6","task_type":"standard_code","priority":"P1","quadrant":"Q1","title":"Primer scan del repo","files":["README.md"],"spec":"Leer README y STATE, producir summary de 10 bullets en .framework/research/initial_scan.md","status":"pending","depends_on":[],"blocks":[]}
```

---

## Paso 7 · Arrancar

```bash
# Terminal 1 — API
bash .framework/api/run_api.sh
# → :8096 arriba

# Terminal 2 — Dashboard
streamlit run .framework/dashboard.py --server.port 8097 --server.headless true
# → http://localhost:8097
```

Primer check:
```bash
curl -s http://127.0.0.1:8096/framework/health
curl -s http://127.0.0.1:8096/framework/overview | python -m json.tool
```

---

## Paso 8 · Primer mensaje en pizarra

Manual, para dar vida al dashboard:

```python
python -c "
import json, datetime
e = {
  'id': 'INIT001', 'de': 'clip', 'para': '<tu_alias>',
  'ts': datetime.datetime.now().isoformat(),
  'mensaje': '[SESSION-START] Framework v2.1 adoptado. Comenzamos.',
  'meta': {'tag': 'SESSION-START', 'phase': 'F0'}
}
with open('.framework/comms/log.jsonl', 'a') as f:
    f.write(json.dumps(e, ensure_ascii=False) + '\\n')
"
```

Recargá `http://localhost:8097` → debés ver el mensaje en la pizarra y clip con heartbeat `ok`.

---

## Paso 9 · (opcional) Delegación a Ollama

Necesitás el script `delegate_to_ollama.py` del runtime v1.1 + `ollama_client.py`. Copiar desde:

```
D:/1.Programacion/framework_runtime_v1.1/framework_runtime/scripts/
  ├── delegate_to_ollama.py
  └── ollama_client.py
```

Env vars que podés setear en tu `.envrc` / `team.env`:

```bash
export TEAM_LOG_DIR=".framework/comms"
export TEAM_STATE_FILE=".framework/STATE.md"
export OLLAMA_URL="http://127.0.0.1:11434"   # preferido
export OLLAMA_BUILDER_MODEL="qwen2.5-coder:32b-instruct-q5_K_M"
export OLLAMA_COMPLEX_MODEL="qwen3-coder-next:q4_K_M"
export OLLAMA_FAST_MODEL="qwen3-coder:30b-a3b-q4_K_M"
export OLLAMA_REASONING_MODEL="deepseek-r1:32b"
export OLLAMA_AGENTIC_MODEL="devstral:latest"
# OLLAMA_ROUTING JSON opcional para per-proyecto override
```

Primer test:
```bash
python delegate_to_ollama.py \
  --task-id TEST-1 \
  --task-type simple_edit \
  --target /tmp/hello.md \
  --mode newfile \
  --spec "Escribir un Markdown de 3 líneas que diga hola"
```

Si ves `[ENTREGADO] TEST-1 | model=... | duration_s=...` en `.framework/comms/log.jsonl`, funcionó.

---

## Paso 10 · Convenciones de trabajo recomendadas

1. **Un archivo = un owner.** En queue.jsonl, `owner` indica quién implementa. Nunca dos owners escribiendo el mismo archivo sin audit.
2. **Todo crown jewel** requiere `[PRE-MERGE-AUDIT-REQ]` + aprobación tier superior antes de merge.
3. **Tags obligatorios** en mensajes (ver lista en actors.json). Un `[VERIFICADO]` implica Playwright u otra verificación empírica, no solo tests unitarios.
4. **`model_tier` por tarea**. Nunca dejar `null`. Default a `ollama-simple` si hay duda.
5. **Heartbeat ≤30min** durante sesión activa. El dashboard alerta si te pasás.

---

## Troubleshooting

**API 500 en `/framework/overview`:** suele ser datetime-naive mezclado con datetime-aware. `pizarra_reader.py` normaliza a UTC-aware. Si agregás un parser nuevo, asegurarlo.

**Dashboard muestra "API no responde":** `curl -s http://127.0.0.1:8096/framework/health`. Si falla: verificar que `run_api.sh` corre y que `uvicorn` no dio error en arranque (stderr en la misma consola).

**Ollama endpoint `http://host:port:port` (doble puerto):** `OLLAMA_HOST` automático de Ollama trae `host:port`. El fix en `ollama_client.py` (commit del 2026-04-21) parsea y separa. Si ves ese error, actualizá el archivo.

**Streamlit recarga loop:** desactivá el `<script>setTimeout(...reload)</script>` final si chocás con auto-refresh nativo de Streamlit.

---

## Qué puedes **quitar** si tu proyecto es más chico

- `postmortems/`, `research/`, `memory/` son opcionales.
- `runbooks/` opcional si no tenés infra.
- `dashboard.py` podés reemplazarlo por solo `curl :8096/framework/overview | jq` si no querés UI.
- Ollama es opcional; el framework vale igual con solo clip.

---

## Qué **añadir** para escalar

- **Auto-routing NL** (roadmap F7): POST `/framework/chat` que toma lenguaje natural y crea tarea.
- **Cost calculator real** (F4): agregar telemetría de Claude Code API al pizarra y sumar.
- **Watchdog Docker** (plataforma-específico): auto-restart cuando engine API da 500.
- **Alertas externas**: webhook Slack/Discord cuando `[HALLAZGO] severity=critical` se abre.

---

**Última versión:** v2.1 · **Probado en:** Windows 11 + Docker Desktop 29.2 + Python 3.12 + Ollama nativo (RTX 5080). Debería funcionar igual en macOS/Linux ajustando paths.
