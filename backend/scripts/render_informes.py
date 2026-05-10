#!/usr/bin/env python3
"""W12-RENDER multinivel · genera JSON+HTML correcto para macro/dpto/mpio/pueblo/resguardo.

Reemplaza el generador histórico (no commiteado en repo) que producía tablas con `—`
y badge `n<30` falso. Lee cifras reales desde Postgres (smt_onic). k-anonimato HONESTO:
solo marca n<30 si la cifra agregada es realmente menor a 30.

Origen: prompt `_scripts/prompts/W12_render_macro.md` despachado vía `local_first_codigo`
(Ollama qwen2.5-coder:7b primer intento · refinado por Claude Opus 4.7). Refactor S9
2026-05-09 (T01) extiende el script al resto de niveles para v1.4.0.

Uso:
    python -m backend.scripts.render_informes --nivel macro
    python -m backend.scripts.render_informes --nivel mpio --ids 05001 11001
    python -m backend.scripts.render_informes --nivel todos --output-root /tmp/test
    python -m backend.scripts.render_informes --nivel pueblo --dry-run

Renderers por nivel:
    render_macro       (T01 · ya implementado)
    render_dpto        (T02 · pendiente Antigravity)
    render_mpio        (T03 · pendiente Antigravity)
    render_pueblo      (T04 · pendiente Antigravity)
    render_resguardo   (T05 · pendiente Antigravity)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable

import psycopg2

DB_CFG = {
    "host": os.environ.get("PG_HOST", "localhost"),
    "port": int(os.environ.get("PG_PORT", "5450")),
    "user": os.environ.get("PG_USER", "smt_admin"),
    "password": os.environ.get("PG_PASSWORD", "smt_onic_2026"),
    "dbname": os.environ.get("PG_DB", "smt_onic"),
}

NIVELES = ("macro", "dpto", "mpio", "pueblo", "resguardo")


def _conn():
    """Abre conexión psycopg2 con autocommit."""
    conn = psycopg2.connect(**DB_CFG)
    conn.autocommit = True
    return conn


def _confiabilidad_badge(con_disc: int) -> str:
    """k-anonimato honesto: CONFIABLE si >=30, BAJA si <30. No falsea cifras."""
    return "CONFIABLE" if con_disc >= 30 else "BAJA"


def _input_hash(*partes: object) -> str:
    """SHA256 corto (16 chars) sobre concatenación pipe-separada · trazabilidad JSON canonical."""
    sig = "|".join(str(p) for p in partes)
    return hashlib.sha256(sig.encode()).hexdigest()[:16]


def _write_canonical(path: Path, canonical: dict, dry_run: bool = False) -> None:
    """Escribe JSON canonical con indent=2 ensure_ascii=False · crea parent dirs."""
    if dry_run:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(canonical, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_html(path: Path, html: str, dry_run: bool = False) -> None:
    """Escribe HTML render · crea parent dirs."""
    if dry_run:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")


# ---------------------------------------------------------------------------
# NIVEL MACRO (T01 · funcional · idéntico al render_informes_macro.py original)
# ---------------------------------------------------------------------------


def _fila_dpto_html(d: dict) -> str:
    nom = d["nom_dpto"]
    if d["con_disc"] >= 30:
        total = f'{d["total"]:,}'.replace(",", ".")
        con = f'{d["con_disc"]:,}'.replace(",", ".")
        prev = f'{d["prevalencia_x_1000"]:.1f}'
        return (
            f'<tr><td>{nom}</td>'
            f'<td class="num">{total}</td>'
            f'<td class="num">{con}</td>'
            f'<td class="num">{prev}‰</td>'
            f'<td><span class="badge ok">CONFIABLE</span></td></tr>'
        )
    return (
        f'<tr><td>{nom}</td>'
        f'<td class="num">—</td>'
        f'<td class="num">—</td>'
        f'<td class="num">—‰</td>'
        f'<td><span class="badge warn">n&lt;30</span></td></tr>'
    )


HTML_TEMPLATE_MACRO = """<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8">
<title>{nombre} · Informe macrorregional</title>
<style>
body{{font-family:system-ui,sans-serif;max-width:900px;margin:2rem auto;padding:1rem;color:#222;line-height:1.6}}
h1{{color:#02432D;border-bottom:3px solid #02432D;padding-bottom:.5rem}}
h2{{color:#02432D;margin-top:2rem}}
table{{width:100%;border-collapse:collapse;margin:1rem 0}}
th{{background:#02432D;color:#fff;padding:.5rem;text-align:left}}
td{{padding:.5rem;border-bottom:1px solid #eee}}
td.num{{text-align:right;font-variant-numeric:tabular-nums}}
.badge{{padding:.15rem .5rem;border-radius:4px;font-size:.8rem}}
.badge.warn{{background:#fef3c7;color:#92400e}}
.badge.ok{{background:#d1fae5;color:#065f46}}
.fuente{{font-size:.8rem;color:#666;margin-top:.5rem;font-style:italic}}
.kpi{{display:inline-block;margin:0 1rem .5rem 0;padding:.5rem 1rem;background:#f3f4f6;border-radius:6px}}
.kpi b{{color:#02432D;font-size:1.2rem}}
</style></head>
<body>
<h1>Informe macrorregional · {nombre}</h1>
<p><span class="kpi">Población indígena · <b>{total_macro:,}</b></span>
<span class="kpi">Con cap. diversas · <b>{con_disc_macro:,}</b></span>
<span class="kpi">Prevalencia · <b>{prev_macro:.1f}‰</b></span>
<span class="kpi">Departamentos · <b>{n_dptos}</b></span></p>

<h2>Departamentos de la macrorregión</h2>
<table>
<thead><tr><th>Departamento</th><th>Población indígena</th><th>Con cap. diversas</th><th>Prevalencia</th><th>Confiabilidad</th></tr></thead>
<tbody>
{filas_dptos}
</tbody>
</table>
<p class="fuente">Fuente: DANE-CNPV 2018 · `pueblo.disc_dpto` × `geo.macro_dptos` × `smt_geo.macrorregiones`. Generado
el {fecha_iso}. Pipeline reemplaza al generador histórico que producía tablas con cifras vacías.
Sin links absolutos a localhost · seguro para distribución offline.</p>
</body></html>
"""


def render_macro(cod_id: int | str, output_root: Path, dry_run: bool = False) -> dict:
    """Renderiza informe macro · 5 macrorregiones (id 1-5)."""
    cod_macro_id = int(cod_id)
    conn = _conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT macro FROM smt_geo.macrorregiones WHERE id = %s",
                (cod_macro_id,),
            )
            r = cur.fetchone()
            if not r:
                raise ValueError(f"Macro id={cod_macro_id} no existe")
            macro_nombre = r[0].strip()

            cur.execute(
                """
                SELECT cod_dpto, nom_dpto
                FROM geo.macro_dptos
                WHERE UPPER(TRIM(macro)) = UPPER(TRIM(%s))
                ORDER BY cod_dpto
                """,
                (macro_nombre,),
            )
            dptos_macro = [{"cod_dpto": row[0], "nom_dpto": row[1]} for row in cur.fetchall()]

            departamentos_info = []
            n_pueblos_total = 0
            for d in dptos_macro:
                cur.execute(
                    """
                    SELECT
                        COALESCE(SUM(con_discapacidad), 0)::int,
                        COALESCE(SUM(total), 0)::int,
                        COUNT(DISTINCT cod_pueblo)
                    FROM pueblo.disc_dpto
                    WHERE cod_dpto = %s AND periodo = '2018'
                    """,
                    (d["cod_dpto"],),
                )
                con_disc, total, n_pueblos = cur.fetchone()
                prev = round(con_disc * 1000.0 / total, 2) if total > 0 else 0.0
                departamentos_info.append({
                    **d,
                    "con_disc": int(con_disc),
                    "total": int(total),
                    "prevalencia_x_1000": prev,
                    "n_pueblos": int(n_pueblos),
                    "k_anonimato_aplicado": int(con_disc) < 30,
                })
                n_pueblos_total += int(n_pueblos)

            departamentos_info.sort(key=lambda x: -x["con_disc"])

            total_con_disc = sum(d["con_disc"] for d in departamentos_info)
            total_total = sum(d["total"] for d in departamentos_info)
            prev_macro = round(total_con_disc * 1000.0 / total_total, 2) if total_total > 0 else 0.0

            fecha_iso = datetime.now(tz=timezone.utc).isoformat()
            input_hash = _input_hash(cod_macro_id, macro_nombre, total_con_disc, total_total)

            canonical = {
                "tipo": "macro",
                "id": str(cod_macro_id),
                "nombre": macro_nombre,
                "secciones": {
                    "capacidades_diversas": {
                        "con_discapacidad": {
                            "value": total_con_disc,
                            "_meta": {
                                "query": "SELECT SUM(con_discapacidad) FROM pueblo.disc_dpto WHERE cod_dpto IN (...) AND periodo='2018'",
                                "table": "pueblo.disc_dpto",
                                "period": "2018",
                                "confiabilidad": _confiabilidad_badge(total_con_disc),
                            },
                        },
                        "poblacion_referencia": {
                            "value": total_total,
                            "_meta": {"table": "pueblo.disc_dpto", "period": "2018"},
                        },
                        "prevalencia_x_1000": {
                            "value": prev_macro,
                            "_meta": {"formula": "con_disc/total*1000"},
                        },
                    },
                    "territorial": {
                        "n_departamentos": len(departamentos_info),
                        "n_pueblos_total": n_pueblos_total,
                        "departamentos": departamentos_info,
                        "_meta": {
                            "fuente": "pueblo.disc_dpto + geo.macro_dptos",
                            "period": "2018",
                        },
                    },
                    "demografia": {"_sin_datos": True, "_nota": "ver informe por dpto/pueblo"},
                    "lengua": {"_sin_datos": True, "_nota": "ver informe por pueblo"},
                    "nbi": {"_sin_datos": True, "_nota": "ver informe por pueblo"},
                    "conflicto": {"_sin_datos": True, "_nota": "ver informe nacional o por pueblo"},
                    "icv": {"_sin_datos": True, "_nota": "ver informe por dpto/pueblo"},
                },
                "fecha_generacion": fecha_iso,
                "periodo": "2018",
                "_input_hash": input_hash,
                "_generador": "render_informes_macro.py",
            }

            json_path = output_root / "macro" / f"{cod_macro_id}.json"
            html_path = output_root / "macro" / f"{cod_macro_id}.html"
            _write_canonical(json_path, canonical, dry_run=dry_run)

            filas_dptos = "\n".join("    " + _fila_dpto_html(d) for d in departamentos_info)
            html = HTML_TEMPLATE_MACRO.format(
                nombre=macro_nombre,
                total_macro=total_total,
                con_disc_macro=total_con_disc,
                prev_macro=prev_macro,
                n_dptos=len(departamentos_info),
                filas_dptos=filas_dptos,
                fecha_iso=fecha_iso,
            )
            _write_html(html_path, html, dry_run=dry_run)

            return {
                "id": cod_macro_id,
                "nombre": macro_nombre,
                "n_dptos": len(departamentos_info),
                "total_con_disc": total_con_disc,
                "total_total": total_total,
                "prev_macro": prev_macro,
                "json_path": str(json_path),
                "html_path": str(html_path),
            }
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# NIVEL DPTO (T02 · pendiente · Antigravity Codex GPT-5)
# ---------------------------------------------------------------------------


def render_dpto(cod_id: str, output_root: Path, dry_run: bool = False) -> dict:
    """Renderiza informe dpto · 33 departamentos (cod_dane 2 chars).

    Pendiente T02 · Antigravity Codex GPT-5.
    Query principal: pueblo.disc_dpto filtrado por cod_dpto, agregando por pueblo.
    Plantilla: KPIs (total indígena, con CD, prevalencia) + tabla pueblos del dpto
    con badge CONFIABLE/n<30 honesto.
    """
    raise NotImplementedError("render_dpto pendiente T02 · ver pizarra S9_render_multinivel")


# ---------------------------------------------------------------------------
# NIVEL MPIO (T03 · pendiente · Antigravity Codex GPT-5)
# ---------------------------------------------------------------------------


def render_mpio(cod_id: str, output_root: Path, dry_run: bool = False) -> dict:
    """Renderiza informe mpio · 1.121 municipios (cod_dane 5 chars).

    Pendiente T03 · Antigravity Codex GPT-5.
    Query principal: cnpv.disc_indigena_mpio (cod_mpio, pob_indigena, con_disc, tasa_x_1000).
    Tabla "Resguardos asociados" reusa lógica de fix_mpio_resguardos_table.py (importar función).
    """
    raise NotImplementedError("render_mpio pendiente T03 · ver pizarra S9_render_multinivel")


# ---------------------------------------------------------------------------
# NIVEL PUEBLO (T04 · pendiente · Antigravity Codex GPT-5)
# ---------------------------------------------------------------------------


def render_pueblo(cod_id: int | str, output_root: Path, dry_run: bool = False) -> dict:
    """Renderiza informe pueblo · 125 pueblos indígenas (cod_pueblo int).

    Pendiente T04 · Antigravity Codex GPT-5.
    Queries: pueblo.disc_nacional (KPIs) + pueblo.piramide_disc (pirámide CD edad×sexo).
    Plantilla incluye SVG/HTML pirámide.
    """
    raise NotImplementedError("render_pueblo pendiente T04 · ver pizarra S9_render_multinivel")


# ---------------------------------------------------------------------------
# NIVEL RESGUARDO (T05 · pendiente · Antigravity Codex GPT-5)
# ---------------------------------------------------------------------------


def render_resguardo(cod_id: str, output_root: Path, dry_run: bool = False) -> dict:
    """Renderiza informe resguardo · 830 resguardos ONIC (cod_resguardo).

    Pendiente T05 · Antigravity Codex GPT-5.
    Query: cnpv.disc_resguardo + smt_geo.resguardos (geometría · pueblo_onic · mpio).
    Plantilla cruza pueblo×mpio.
    """
    raise NotImplementedError("render_resguardo pendiente T05 · ver pizarra S9_render_multinivel")


# ---------------------------------------------------------------------------
# Despachador y CLI
# ---------------------------------------------------------------------------


RENDERERS: dict[str, Callable[..., dict]] = {
    "macro": render_macro,
    "dpto": render_dpto,
    "mpio": render_mpio,
    "pueblo": render_pueblo,
    "resguardo": render_resguardo,
}


def _ids_para_nivel(nivel: str, conn) -> list:
    """Devuelve lista de IDs disponibles en DB para el nivel · falla rápido si tabla no existe."""
    queries = {
        "macro": "SELECT id FROM smt_geo.macrorregiones ORDER BY id",
        "dpto": "SELECT DISTINCT cod_dpto FROM geo.macro_dptos ORDER BY cod_dpto",
        "mpio": "SELECT cod_mpio FROM cnpv.disc_indigena_mpio WHERE periodo = '2018' ORDER BY cod_mpio",
        "pueblo": "SELECT cod_pueblo FROM pueblo.disc_nacional WHERE periodo = '2018' ORDER BY cod_pueblo",
        "resguardo": "SELECT cod_resguardo FROM cnpv.disc_resguardo WHERE periodo = '2018' ORDER BY cod_resguardo",
    }
    sql = queries.get(nivel)
    if not sql:
        raise ValueError(f"Nivel desconocido: {nivel}. Válidos: {NIVELES}")
    with conn.cursor() as cur:
        cur.execute(sql)
        return [row[0] for row in cur.fetchall()]


def _parse_cli(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="W12-RENDER multinivel · genera JSON+HTML para informes pre-renderizados.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Ejemplos:\n"
            "  python -m backend.scripts.render_informes --nivel macro\n"
            "  python -m backend.scripts.render_informes --nivel mpio --ids 05001 11001\n"
            "  python -m backend.scripts.render_informes --nivel todos --output-root /tmp/test\n"
            "  python -m backend.scripts.render_informes --nivel pueblo --dry-run\n"
        ),
    )
    parser.add_argument(
        "--nivel",
        required=True,
        choices=(*NIVELES, "todos"),
        help="Nivel a regenerar. 'todos' itera macro->dpto->mpio->pueblo->resguardo.",
    )
    parser.add_argument(
        "--ids",
        nargs="*",
        default=None,
        help="Subset de IDs a regenerar (default: todos los disponibles en DB).",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=None,
        help="Directorio raíz de salida (default: <repo>/_static/informes).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="No escribe archivos · útil para validar queries.",
    )
    return parser.parse_args(argv)


def _run_nivel(nivel: str, ids: Iterable | None, output_root: Path, dry_run: bool) -> int:
    """Ejecuta el renderer del nivel sobre los IDs · imprime una línea por ID. Retorna 0 si OK."""
    renderer = RENDERERS[nivel]
    if ids is None:
        conn = _conn()
        try:
            ids = _ids_para_nivel(nivel, conn)
        finally:
            conn.close()

    print(f"W12-RENDER · nivel={nivel} · output_root={output_root} · n_ids={len(list(ids)) if not isinstance(ids, list) else len(ids)}")
    ids_list = list(ids)
    errores = 0
    for cod_id in ids_list:
        try:
            info = renderer(cod_id, output_root, dry_run=dry_run)
            nombre = info.get("nombre", "")
            print(f"  OK {nivel} {info.get('id', cod_id)} · {nombre}")
        except NotImplementedError as e:
            print(f"  PENDIENTE {nivel} {cod_id}: {e}", file=sys.stderr)
            errores += 1
            break
        except Exception as e:  # noqa: BLE001
            print(f"  ERR {nivel} {cod_id}: {e}", file=sys.stderr)
            errores += 1
    return 2 if errores else 0


def main(argv: list[str] | None = None) -> int:
    args = _parse_cli(argv)
    repo_root = Path(__file__).resolve().parent.parent
    output_root = args.output_root or (repo_root / "_static" / "informes")

    niveles_a_correr = list(NIVELES) if args.nivel == "todos" else [args.nivel]
    if args.ids and args.nivel == "todos":
        print("ERR --ids no compatible con --nivel todos", file=sys.stderr)
        return 2

    for nivel in niveles_a_correr:
        rc = _run_nivel(nivel, args.ids, output_root, args.dry_run)
        if rc != 0:
            return rc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
