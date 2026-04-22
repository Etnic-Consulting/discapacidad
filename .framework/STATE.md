# STATE.md — SMT-ONIC

**Proyecto:** SMT-ONIC Dashboard (Sistema de Monitoreo Territorial — ONIC)
**Director:** Wilson Herrera
**Framework:** Team-of-Two v2.1 (adoptado desde ConvocaIA, 2026-04-21)

## [FASE_ACTUAL]
F0 — Adopcion del framework v2.1.
Pizarra y dashboard aislados por proyecto (decision Wilson, 2026-04-21).

## [EQUIPO_ACTIVO]
| Actor   | Rol                       | Modelo default       |
|---------|---------------------------|----------------------|
| wilson  | Director                  | humano               |
| clip    | Builder + auditor         | claude-sonnet-4-6    |
| ollama  | Builder tareas cerradas   | qwen2.5-coder:32b    |

## [INFRA_LOCAL]
- API framework SMT-ONIC: `:8096` (uvicorn)
- Dashboard framework SMT-ONIC: `:8097` (streamlit)
- Backend de la app: `smt-onic-api` Docker `:8095`
- Postgres de la app: `smt-onic-db` Docker `:5450`
- Frontend Vite: `:5173` (npm run dev en `frontend/`)

## [EN_MARCHA]
- F0.1 Estructura .framework/ + configs SMT-ONIC ........ DONE (clip)
- F0.2 API FastAPI :8096 ................................ DONE
- F0.3 Dashboard Streamlit :8097 ........................ DONE
- F0.4 STATE.md + seed pizarra + queue .................. DONE
- F0.5 team.env local (identidad + routing + gateway) .... DONE (2026-04-21)
- S1  Shared Ollama Gateway (semáforo filelock) .......... DONE (2026-04-21)
- S2  Benchmark 6 modelos generalistas (24 llamadas) ..... DONE (ranking en `.team-shared/models_ranking.json`)
- S3  delegate_to_ollama.py usa gateway + ranking ........ DONE (validado E2E 2026-04-21)

## [CROWN_JEWEL_SET]
Ver `.framework/config/tiers.json → crown_jewel_permissions`. Resumen:
- `backend/app/main.py`, `backend/app/database.py`, `backend/app/services/auth.py`
- `backend/app/routers/dashboard.py`, `backend/app/routers/formulario.py`
- `backend/scripts/load_*.py`
- `docker-compose.yml`, `backend/requirements.txt`, `frontend/package.json`
- `frontend/src/context/FilterContext.jsx`

## [ARRANCAR]
```bash
# Terminal A — API framework
bash .framework/api/run_api.sh
# Terminal B — Dashboard
bash .framework/run_dashboard.sh
```

## [PROXIMO]
1. Verificar /framework/health responde 200
2. Verificar dashboard pinta cards de equipo
3. Cargar tareas reales del proyecto a queue.jsonl (form Bloque B-J pendientes, mojibake smt_geo, etc.)

## [HISTORIA]
- 2026-04-21 — Framework v2.1 adoptado en SMT-ONIC con .framework/ propio. Puertos :8096/:8097.
- 2026-04-21 — Shared Ollama Gateway en `framework_runtime_v1.1/shared/ollama_gateway.py` con semáforo filelock (cap=2, config env `OLLAMA_GLOBAL_CONCURRENCY`). Log cross-project en `.team-shared/ollama.calls.jsonl`.
- 2026-04-21 — `delegate_to_ollama.py` ahora enruta vía gateway y consulta `models_ranking.json` (benchmark) antes de heurística. Flag `--no-gateway` para bypass en debug.
- 2026-04-21 — `team.env` local creado con identidad smt-onic, crown jewels, routing de tareas, config del semáforo global.
- 2026-04-21 — Benchmark 6 modelos × 4 task_types (24 llamadas). Ganadores: simple_edit→qwen3-coder:30b (85.7), standard_code/complex_code→devstral≈qwen3-coder:30b (100.0), reasoning→qwen3-coder:30b (100.0, **reemplaza a deepseek-r1 que sacó q=0.50**). qwen3:32b inutilizable para código (q=0.00 en todo). Ranking en `.team-shared/models_ranking.json`.
- 2026-04-21 — Hallazgo H-ONIC-001 (auditor cowork) corregido: removido task_type `domain` apuntando a convocav51 LoRA en `config/tiers.json` — no hay LoRA SMT-ONIC.
- 2026-04-21 — README/ADOPTION_GUIDE/api/server.py: puertos `:8098/:8099` → `:8096/:8097` (eran copia de ConvocaIA).
