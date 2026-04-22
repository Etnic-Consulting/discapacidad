"""
gen_notebook.py — Crea el notebook 'SMT-ONIC' en NotebookLM
y sube todos los archivos de memoria + fuentes criticas del proyecto.

Requisitos:
  - notebooklm-py instalada:  pip install notebooklm-py
  - Sesion autenticada:       notebooklm login   (una sola vez)

Uso:
  python .framework/gen_notebook.py              # crea + sube TODO
  python .framework/gen_notebook.py --solo-push  # salta creacion; usa URL ya en team.env
  python .framework/gen_notebook.py --solo-crear # crea y escribe URL/ID en team.env, sin subir
"""
import argparse
import asyncio
import os
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except AttributeError:
    pass

FW_DIR = Path(__file__).parent
PROJECT_ROOT = FW_DIR.parent
TEAM_ENV = FW_DIR / "team.env"
TITULO_NOTEBOOK = "SMT-ONIC"

# Memoria persistente Claude (auto-memory)
CLAUDE_MEMORY_DIR = Path(
    "C:/Users/wilso/.claude/projects/D--1-Programacion-1-onic-smt-dashboard/memory"
)


def cargar_team_env():
    if not TEAM_ENV.exists():
        return
    for line in TEAM_ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:]
        if "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def escribir_team_env(url: str, nb_id: str):
    txt = TEAM_ENV.read_text(encoding="utf-8")
    txt = re.sub(r'(NOTEBOOKLM_NOTEBOOK_URL=)"[^"]*"', f'\\1"{url}"', txt)
    txt = re.sub(r'(NOTEBOOKLM_NOTEBOOK_ID=)"[^"]*"', f'\\1"{nb_id}"', txt)
    TEAM_ENV.write_text(txt, encoding="utf-8")


def tail_jsonl(p: Path, n: int) -> str:
    """Devuelve las ultimas n lineas de un archivo grande."""
    if not p.exists():
        return ""
    lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
    return "\n".join(lines[-n:])


def listar_arbol(root: Path, max_depth: int = 3, ignore: set[str] = None) -> str:
    ignore = ignore or {".git", "node_modules", "__pycache__", ".venv", "dist",
                        "build", ".next", ".pytest_cache", "Trabajo_desing",
                        ".framework"}
    out = [f"# Arbol de directorios — {root.name}", ""]

    def walk(d: Path, depth: int, prefix: str = ""):
        if depth > max_depth:
            return
        try:
            entries = sorted(d.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
        except (PermissionError, OSError):
            return
        for e in entries:
            if e.name in ignore or e.name.startswith("."):
                continue
            if e.is_dir():
                out.append(f"{prefix}{e.name}/")
                walk(e, depth + 1, prefix + "  ")
            else:
                out.append(f"{prefix}{e.name}")

    walk(root, 0)
    return "\n".join(out)


def recolectar_fuentes() -> list[tuple[str, str]]:
    """Retorna [(titulo, contenido_str), ...] para subir al notebook."""
    fuentes = []

    # 1. INDICE / metadatos del proyecto
    indice = f"""# SMT-ONIC — Indice de fuentes (NotebookLM)

Sistema de Monitoreo Territorial — Personas con Capacidades Diversas de Pueblos Indigenas.
Coordinador: Wilson Herrera (poblacion@onic.org.co).

## Fuentes incluidas
- MEM_*: memoria persistente Claude (preferencias usuario, decisiones, contexto).
- STATE: estado actual del proyecto (framework v2.1).
- README: README del repo.
- WORKSPACE_CLAUDE: instrucciones del workspace D:/1.Programacion (rol auditor, inventario proyectos).
- ARBOL_REPO: estructura de directorios.
- BACKEND_MAIN: main.py del backend FastAPI (middleware seguridad + logging + rate-limit).
- BACKEND_CONFIG: configuracion (CORS, BD).
- FRONTEND_APP: rutas + AuthContext del frontend React/Vite.
- BACKLOG_QUEUE: tareas pendientes (queue.jsonl).
- PIZARRA_TAIL: ultimas 100 entradas de la pizarra (comms/log.jsonl).

## Usar este notebook
Al iniciar una sesion con Claude:
  /notebook query <pregunta sobre el proyecto>
Asi se evita recargar todo el contexto en cada turno = ahorro de tokens.
"""
    fuentes.append(("00_INDICE", indice))

    # 2. Memoria Claude (auto-memory) — todos los archivos .md
    if CLAUDE_MEMORY_DIR.exists():
        for p in sorted(CLAUDE_MEMORY_DIR.glob("*.md")):
            titulo = f"MEM_{p.stem}"
            fuentes.append((titulo, p.read_text(encoding="utf-8")))

    # 3. STATE del framework
    state = FW_DIR / "STATE.md"
    if state.exists():
        fuentes.append(("STATE", state.read_text(encoding="utf-8")))

    # 4. README del repo
    readme = PROJECT_ROOT / "README.md"
    if readme.exists():
        fuentes.append(("README", readme.read_text(encoding="utf-8")))

    # 5. CLAUDE.md del workspace (instrucciones globales)
    workspace_claude = Path("D:/1.Programacion/CLAUDE.md")
    if workspace_claude.exists():
        fuentes.append(("WORKSPACE_CLAUDE", workspace_claude.read_text(encoding="utf-8")))

    # 6. Arbol de directorios
    fuentes.append(("ARBOL_REPO", listar_arbol(PROJECT_ROOT, max_depth=3)))

    # 7. Codigo backend critico
    for rel, titulo in [
        ("backend/app/main.py", "BACKEND_MAIN"),
        ("backend/app/config.py", "BACKEND_CONFIG"),
        ("backend/app/database.py", "BACKEND_DATABASE"),
        ("backend/app/services/auth.py", "BACKEND_AUTH_SERVICE"),
        ("backend/app/routers/dashboard.py", "BACKEND_ROUTER_DASHBOARD"),
        ("backend/app/routers/formulario.py", "BACKEND_ROUTER_FORMULARIO"),
        ("backend/app/routers/auth.py", "BACKEND_ROUTER_AUTH"),
        ("backend/requirements.txt", "BACKEND_REQUIREMENTS"),
        ("docker-compose.yml", "DOCKER_COMPOSE"),
    ]:
        p = PROJECT_ROOT / rel
        if p.exists():
            fuentes.append((titulo, p.read_text(encoding="utf-8", errors="ignore")))

    # 8. Codigo frontend critico
    for rel, titulo in [
        ("frontend/src/App.jsx", "FRONTEND_APP"),
        ("frontend/src/context/AuthContext.jsx", "FRONTEND_AUTH_CONTEXT"),
        ("frontend/src/context/FilterContext.jsx", "FRONTEND_FILTER_CONTEXT"),
        ("frontend/src/lib/api.js", "FRONTEND_API_CLIENT"),
        ("frontend/src/lib/glossary.js", "FRONTEND_GLOSSARY"),
        ("frontend/package.json", "FRONTEND_PACKAGE"),
    ]:
        p = PROJECT_ROOT / rel
        if p.exists():
            fuentes.append((titulo, p.read_text(encoding="utf-8", errors="ignore")))

    # 9. Backlog y pizarra
    queue = FW_DIR / "tasks" / "queue.jsonl"
    if queue.exists():
        fuentes.append(("BACKLOG_QUEUE", queue.read_text(encoding="utf-8")))

    pizarra = FW_DIR / "comms" / "log.jsonl"
    if pizarra.exists():
        tail = tail_jsonl(pizarra, 100)
        fuentes.append(("PIZARRA_TAIL_100", tail))

    return fuentes


async def crear_notebook_async():
    from notebooklm import NotebookLMClient
    async with await NotebookLMClient.from_storage() as client:
        nb = await client.notebooks.create(title=TITULO_NOTEBOOK)
        print(f"[OK] Notebook creado: id={nb.id}")
        url = f"https://notebooklm.google.com/notebook/{nb.id}"
        return nb.id, url


async def subir_fuentes_async(nb_id: str, fuentes: list[tuple[str, str]]):
    from notebooklm import NotebookLMClient
    async with await NotebookLMClient.from_storage() as client:
        sources = client.sources
        add_fn = getattr(sources, "add_text", None) or getattr(sources, "add_source_text", None)
        if add_fn is None:
            raise AttributeError("sources.add_text no encontrado en notebooklm-py")

        total = len(fuentes)
        for i, (titulo, contenido) in enumerate(fuentes, 1):
            if not contenido.strip():
                print(f"  [{i:02d}/{total}] SKIP {titulo}: vacio")
                continue
            try:
                await add_fn(notebook_id=nb_id, title=titulo, content=contenido)
                print(f"  [{i:02d}/{total}] OK  {titulo}  ({len(contenido):,} chars)")
            except Exception as e:
                print(f"  [{i:02d}/{total}] FAIL {titulo}: {type(e).__name__}: {e}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--solo-push", action="store_true")
    parser.add_argument("--solo-crear", action="store_true")
    args = parser.parse_args()

    cargar_team_env()

    print("=" * 60)
    print(f"  GEN_NOTEBOOK — '{TITULO_NOTEBOOK}'")
    print("=" * 60)

    nb_id = os.environ.get("NOTEBOOKLM_NOTEBOOK_ID", "").strip()
    nb_url = os.environ.get("NOTEBOOKLM_NOTEBOOK_URL", "").strip()

    if args.solo_push:
        if not nb_id:
            print("[ERROR] NOTEBOOKLM_NOTEBOOK_ID vacio en team.env. "
                  "Ejecuta sin --solo-push la primera vez.")
            return 1
    else:
        print("Creando notebook ...")
        try:
            nb_id, nb_url = asyncio.run(crear_notebook_async())
            escribir_team_env(nb_url, nb_id)
            print(f"[OK] team.env actualizado con URL: {nb_url}")
        except Exception as e:
            print(f"[ERROR] creacion fallo: {type(e).__name__}: {e}")
            if "expired" in str(e).lower() or "invalid" in str(e).lower():
                print()
                print("Sesion Google expirada. Ejecuta:")
                print("  notebooklm login")
                print("y luego reintenta este script.")
            return 2

    if args.solo_crear:
        print("Creacion completa. No se suben fuentes (--solo-crear).")
        return 0

    print()
    print("Recolectando fuentes ...")
    fuentes = recolectar_fuentes()
    print(f"  total: {len(fuentes)} fuentes")

    print()
    print("Subiendo ...")
    try:
        asyncio.run(subir_fuentes_async(nb_id, fuentes))
    except Exception as e:
        print(f"[ERROR] push fallo: {type(e).__name__}: {e}")
        return 3

    print()
    print(f"[OK] Listo. Notebook: {nb_url}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
