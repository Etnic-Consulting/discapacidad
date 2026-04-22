# NotebookLM — Memoria persistente "SMT-ONIC"

Notebook creado: https://notebooklm.google.com/notebook/58ebff66-ee37-4098-93f6-23c86a6a14f5

## Que contiene

34 fuentes:
- 12 archivos de memoria persistente Claude (preferencias usuario, decisiones, contexto Wilson).
- STATE.md del framework v2.1.
- README del repo + CLAUDE.md del workspace.
- Arbol de directorios.
- 9 archivos backend (main, config, database, auth, routers dashboard/formulario/auth, requirements, docker-compose).
- 6 archivos frontend (App, AuthContext, FilterContext, lib/api, glossary, package.json).
- BACKLOG_QUEUE (queue.jsonl) + PIZARRA_TAIL_100 (ultimas 100 entradas del log).

## Como ahorra tokens

**Sin NotebookLM**: cada sesion con Claude Code re-explora archivos para entender el proyecto = 30-100k tokens iniciales.

**Con NotebookLM**: preguntas el contexto a NotebookLM (gratis), luego solo le das a Claude la respuesta + el cambio que quieres = 1-5k tokens iniciales.

## Uso recurrente

### Antes de iniciar sesion en Claude Code

Abre el notebook y pregunta lo que necesitas refrescar:
- "¿en que estado quedo el proyecto?"
- "¿cual es la convencion de puertos?"
- "¿que tareas quedaron pendientes?"
- "¿que decisiones tomo Wilson sobre auth?"

Pega esa respuesta como contexto inicial al abrir Claude. Eso reemplaza re-explorar el repo.

### Al cerrar sesion (cuando hayas hecho cambios significativos)

```bash
cd D:/1.Programacion/1.onic-smt-dashboard
python .framework/gen_notebook.py --solo-push
```

Esto re-sube las fuentes (sobre el mismo notebook) con los cambios mas recientes:
memoria actualizada, STATE actualizado, pizarra actualizada, codigo modificado.

## Renovar sesion Google (cuando expire ~1 semana)

```bash
notebooklm login
```

Abre browser, login con tu cuenta de Google, guarda en `C:\Users\wilso\.notebooklm\storage_state.json`.

## Re-crear notebook desde cero (raro)

Si el notebook se corrompe o quieres uno nuevo:

```bash
# Borra las variables NOTEBOOKLM_NOTEBOOK_ID/URL en .framework/team.env
python .framework/gen_notebook.py
```

## Troubleshooting

| Error | Causa | Solucion |
|---|---|---|
| `Authentication expired` | Sesion Google caducada | `notebooklm login` |
| `sources.add_text not found` | API cambio en notebooklm-py | `pip install --upgrade notebooklm-py` |
| `NOTEBOOKLM_NOTEBOOK_ID vacio` | team.env no cargado | `source .framework/team.env` antes del script |

## Convenciones para mantener al dia

- **STATE.md**: actualizar al cierre de cada sesion productiva.
- **queue.jsonl**: agregar/cerrar tareas a medida que se trabajan.
- **comms/log.jsonl**: append-only (no editar manual). Solo las ultimas 100 lineas se suben.
- **memoria Claude**: se actualiza automaticamente cada sesion. Si agregaste algo crucial, corre `--solo-push`.
