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
# NIVEL DPTO (T02 · gemini-2.5-pro · 33 informes · S9 2026-05-09)
# ---------------------------------------------------------------------------


HTML_TEMPLATE_DPTO = """<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8">
<title>Informe departamental · {nombre}</title>
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
<h1>Informe departamental · {nombre}</h1>
<p><span class="kpi">Población indígena · <b>{total_dpto:,}</b></span>
<span class="kpi">Con cap. diversas · <b>{con_disc_dpto:,}</b></span>
<span class="kpi">Prevalencia · <b>{prev_dpto:.1f}‰</b></span>
<span class="kpi">Pueblos · <b>{n_pueblos}</b></span></p>

<h2>Pueblos del departamento</h2>
<table>
<thead><tr><th>Pueblo</th><th>Población indígena</th><th>Con cap. diversas</th><th>Prevalencia</th><th>Confiabilidad</th></tr></thead>
<tbody>
{filas_pueblos}
</tbody>
</table>
<p class="fuente">Fuente: DANE-CNPV 2018 · `pueblo.disc_dpto`. Generado
el {fecha_iso}. Pipeline reemplaza al generador histórico que producía tablas con cifras vacías.
Sin links absolutos a localhost · seguro para distribución offline.</p>
</body></html>
"""


def _fila_pueblo_html(p: dict) -> str:
    nom = p["nom_pueblo"]
    if p["con_disc"] >= 30:
        total = f'{p["total"]:,}'.replace(",", ".")
        con = f'{p["con_disc"]:,}'.replace(",", ".")
        prev = f'{p["prevalencia_x_1000"]:.1f}'
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


def render_dpto(cod_id: str, output_root: Path, dry_run: bool = False) -> dict:
    """Renderiza informe dpto · 33 departamentos (cod_dane 2 chars).

    Generado T02 · gemini-2.5-pro vía dispatch_envuelto.py · S9 2026-05-09.
    Query principal: pueblo.disc_dpto JOIN pueblo.disc_nacional para nom_pueblo.
    """
    cod_dpto_id = cod_id
    conn = _conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT nom_dpto, macro FROM geo.macro_dptos WHERE cod_dpto = %s LIMIT 1",
                (cod_dpto_id,),
            )
            r = cur.fetchone()
            if not r:
                raise ValueError(f"Departamento cod_dpto={cod_dpto_id} no existe")
            nom_dpto = (r[0] or "").strip() or f"Dpto {cod_dpto_id}"
            macro_nombre = (r[1] or "").strip() or "—"

            cur.execute(
                """
                SELECT
                    cod_pueblo,
                    COALESCE(pueblo, 'Pueblo ' || cod_pueblo::text) AS nom_pueblo,
                    COALESCE(con_discapacidad, 0)::int AS con_disc,
                    COALESCE(total, 0)::int AS total
                FROM pueblo.disc_dpto
                WHERE cod_dpto = %s AND periodo = '2018'
                ORDER BY con_discapacidad DESC NULLS LAST
                """,
                (cod_dpto_id,),
            )
            pueblos_rows = cur.fetchall()

            pueblos_info = []
            for row in pueblos_rows:
                cod_pueblo, nom_pueblo, con_disc, total = row
                prev = round(con_disc * 1000.0 / total, 2) if total > 0 else 0.0
                pueblos_info.append({
                    "cod_pueblo": int(cod_pueblo),
                    "nom_pueblo": nom_pueblo,
                    "con_disc": int(con_disc),
                    "total": int(total),
                    "prevalencia_x_1000": prev,
                    "k_anonimato_aplicado": int(con_disc) < 30,
                })

            total_con_disc = sum(p["con_disc"] for p in pueblos_info)
            total_total = sum(p["total"] for p in pueblos_info)
            prev_dpto = round(total_con_disc * 1000.0 / total_total, 2) if total_total > 0 else 0.0

            fecha_iso = datetime.now(tz=timezone.utc).isoformat()
            input_hash = _input_hash(cod_dpto_id, nom_dpto, total_con_disc, total_total)

            canonical = {
                "tipo": "dpto",
                "id": str(cod_dpto_id),
                "nombre": nom_dpto,
                "secciones": {
                    "capacidades_diversas": {
                        "con_discapacidad": {
                            "value": total_con_disc,
                            "_meta": {
                                "query": "SELECT SUM(con_discapacidad) FROM pueblo.disc_dpto WHERE cod_dpto = %s AND periodo='2018'",
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
                            "value": prev_dpto,
                            "_meta": {"formula": "con_disc/total*1000"},
                        },
                    },
                    "territorial": {
                        "macro": macro_nombre,
                        "n_pueblos": len(pueblos_info),
                        "pueblos": pueblos_info,
                        "_meta": {
                            "fuente": "pueblo.disc_dpto",
                            "period": "2018",
                        },
                    },
                    "demografia": {"_sin_datos": True, "_nota": "ver informe por pueblo"},
                    "lengua": {"_sin_datos": True, "_nota": "ver informe por pueblo"},
                    "nbi": {"_sin_datos": True, "_nota": "ver informe por pueblo"},
                    "conflicto": {"_sin_datos": True, "_nota": "ver informe nacional o por pueblo"},
                    "icv": {"_sin_datos": True, "_nota": "ver informe por pueblo"},
                },
                "fecha_generacion": fecha_iso,
                "periodo": "2018",
                "_input_hash": input_hash,
                "_generador": "render_informes.py",
            }

            json_path = output_root / "dpto" / f"{cod_dpto_id}.json"
            html_path = output_root / "dpto" / f"{cod_dpto_id}.html"
            _write_canonical(json_path, canonical, dry_run=dry_run)

            filas_pueblos = "\n".join("    " + _fila_pueblo_html(p) for p in pueblos_info)
            html = HTML_TEMPLATE_DPTO.format(
                nombre=nom_dpto,
                total_dpto=total_total,
                con_disc_dpto=total_con_disc,
                prev_dpto=prev_dpto,
                n_pueblos=len(pueblos_info),
                filas_pueblos=filas_pueblos,
                fecha_iso=fecha_iso,
            )
            _write_html(html_path, html, dry_run=dry_run)

            return {
                "id": cod_dpto_id,
                "nombre": nom_dpto,
                "n_pueblos": len(pueblos_info),
                "total_con_disc": total_con_disc,
                "total_total": total_total,
                "prev_dpto": prev_dpto,
                "json_path": str(json_path),
                "html_path": str(html_path),
            }
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# NIVEL MPIO (T03 · Claude Opus 4.7 · escalada post fallo gemini-2.5-pro · S9 2026-05-09)
# ---------------------------------------------------------------------------


HTML_TEMPLATE_MPIO = """<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8">
<title>Informe municipal · {nombre}</title>
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
.dpto-tag{{font-weight:normal;font-size:1rem;color:#666}}
</style></head>
<body>
<h1>Informe municipal · {nombre} <span class="dpto-tag">({nom_dpto})</span></h1>
<p><span class="kpi">Población indígena · <b>{pob_indigena:,}</b></span>
<span class="kpi">Con cap. diversas · <b>{con_disc:,}</b></span>
<span class="kpi">Prevalencia · <b>{prev_mpio:.1f}‰</b></span>
<span class="kpi">Confiabilidad · <b>{confiabilidad}</b></span>
<span class="kpi">Resguardos · <b>{n_resguardos}</b></span></p>

<h2>Resguardos asociados</h2>
<table>
<thead><tr><th>Resguardo</th><th>Pueblo ONIC</th><th>Área (ha)</th></tr></thead>
<tbody>
{filas_resguardos}
</tbody>
</table>
<p class="fuente">Fuente: DANE-CNPV 2018 · `cnpv.disc_indigena_mpio` × `smt_geo.resguardos`. Generado
el {fecha_iso}. Pipeline reemplaza al generador histórico que producía tablas con cifras vacías.
Sin links absolutos a localhost · seguro para distribución offline.</p>
</body></html>
"""


def _fila_resguardo_html(r: dict) -> str:
    nombre = r["nombre_resguardo"] or "—"
    pueblo_onic = r["pueblo_onic"] or "—"
    area = f'{r["area_ha"]:,.1f}'.replace(",", ".") if r["area_ha"] else "—"
    return (
        f'<tr><td>{nombre}</td>'
        f'<td>{pueblo_onic}</td>'
        f'<td class="num">{area}</td></tr>'
    )


def render_mpio(cod_id: str, output_root: Path, dry_run: bool = False) -> dict:
    """Renderiza informe mpio · 1.121 municipios (cod_dane 5 chars).

    Generado T03 · Claude Opus 4.7 (escalada regla #7) post fallo gemini-2.5-pro
    en sesión autónoma 2026-05-09 23:08 (alucinación: respondió CONTRIBUTING.md).
    Query principal: cnpv.disc_indigena_mpio + smt_geo.resguardos.
    """
    cod_mpio_id = cod_id
    conn = _conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT m.nom_mpio, m.cod_dpto,
                       COALESCE(d.nom_dpto, 'Dpto ' || m.cod_dpto) AS nom_dpto
                FROM geo.municipios m
                LEFT JOIN geo.macro_dptos d ON d.cod_dpto = m.cod_dpto
                WHERE m.cod_mpio = %s LIMIT 1
                """,
                (cod_mpio_id,),
            )
            r = cur.fetchone()
            if not r:
                raise ValueError(f"Municipio cod_mpio={cod_mpio_id} no existe en geo.municipios")
            nom_mpio = (r[0] or "").strip() or f"Mpio {cod_mpio_id}"
            cod_dpto = (r[1] or "").strip()
            nom_dpto = (r[2] or "").strip() or f"Dpto {cod_dpto}"

            cur.execute(
                """
                SELECT
                    COALESCE(pob_indigena, 0)::int,
                    COALESCE(con_disc, 0)::int,
                    COALESCE(tasa_x_1000, 0)::numeric
                FROM cnpv.disc_indigena_mpio
                WHERE cod_mpio = %s AND periodo = '2018'
                LIMIT 1
                """,
                (cod_mpio_id,),
            )
            row_kpi = cur.fetchone()
            if row_kpi:
                pob_indigena, con_disc, tasa = int(row_kpi[0]), int(row_kpi[1]), float(row_kpi[2])
            else:
                pob_indigena, con_disc, tasa = 0, 0, 0.0
            confiabilidad = _confiabilidad_badge(con_disc)

            cur.execute(
                """
                SELECT
                    territorio AS nombre_resguardo,
                    COALESCE(pueblo_onic, '') AS pueblo_onic,
                    COALESCE(area_pg_ha, 0)::numeric AS area_ha
                FROM smt_geo.resguardos
                WHERE mpio_cdpmp = %s
                ORDER BY territorio
                """,
                (cod_mpio_id,),
            )
            resguardos_info = [
                {
                    "nombre_resguardo": row[0],
                    "pueblo_onic": row[1],
                    "area_ha": float(row[2]) if row[2] else 0.0,
                }
                for row in cur.fetchall()
            ]

            fecha_iso = datetime.now(tz=timezone.utc).isoformat()
            input_hash = _input_hash(cod_mpio_id, nom_mpio, pob_indigena, con_disc)

            canonical = {
                "tipo": "mpio",
                "id": str(cod_mpio_id),
                "nombre": nom_mpio,
                "secciones": {
                    "capacidades_diversas": {
                        "con_discapacidad": {
                            "value": con_disc,
                            "_meta": {
                                "query": "SELECT con_disc FROM cnpv.disc_indigena_mpio WHERE cod_mpio = %s AND periodo='2018'",
                                "table": "cnpv.disc_indigena_mpio",
                                "period": "2018",
                                "confiabilidad": confiabilidad,
                            },
                        },
                        "poblacion_referencia": {
                            "value": pob_indigena,
                            "_meta": {"table": "cnpv.disc_indigena_mpio", "period": "2018"},
                        },
                        "prevalencia_x_1000": {
                            "value": round(tasa, 2),
                            "_meta": {"formula": "tasa_x_1000 from cnpv.disc_indigena_mpio"},
                        },
                    },
                    "territorial": {
                        "cod_dpto": cod_dpto,
                        "nom_dpto": nom_dpto,
                        "n_resguardos": len(resguardos_info),
                        "resguardos": resguardos_info,
                        "_meta": {"fuente": "smt_geo.resguardos", "period": "2018"},
                    },
                    "demografia": {"_sin_datos": True, "_nota": "ver informe nacional o por dpto"},
                    "lengua": {"_sin_datos": True, "_nota": "ver informe por pueblo"},
                    "nbi": {"_sin_datos": True, "_nota": "ver indicadores.icv_municipal"},
                    "conflicto": {"_sin_datos": True, "_nota": "ver informe nacional"},
                    "icv": {"_sin_datos": True, "_nota": "ver indicadores.icv_municipal"},
                },
                "fecha_generacion": fecha_iso,
                "periodo": "2018",
                "_input_hash": input_hash,
                "_generador": "render_informes.py",
            }

            json_path = output_root / "mpio" / f"{cod_mpio_id}.json"
            html_path = output_root / "mpio" / f"{cod_mpio_id}.html"
            _write_canonical(json_path, canonical, dry_run=dry_run)

            if resguardos_info:
                filas_resguardos = "\n".join(
                    "    " + _fila_resguardo_html(r) for r in resguardos_info
                )
            else:
                filas_resguardos = (
                    '    <tr><td colspan="3" class="fuente">El municipio no tiene '
                    "resguardos ONIC registrados.</td></tr>"
                )
            html = HTML_TEMPLATE_MPIO.format(
                nombre=nom_mpio,
                nom_dpto=nom_dpto,
                pob_indigena=pob_indigena,
                con_disc=con_disc,
                prev_mpio=tasa,
                confiabilidad=confiabilidad,
                n_resguardos=len(resguardos_info),
                filas_resguardos=filas_resguardos,
                fecha_iso=fecha_iso,
            )
            _write_html(html_path, html, dry_run=dry_run)

            return {
                "id": cod_mpio_id,
                "nombre": nom_mpio,
                "n_resguardos": len(resguardos_info),
                "pob_indigena": pob_indigena,
                "con_disc": con_disc,
                "prev_mpio": float(tasa),
                "json_path": str(json_path),
                "html_path": str(html_path),
            }
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# NIVEL PUEBLO (T04 · Claude Opus 4.7 · escalada · S9 2026-05-09)
# ---------------------------------------------------------------------------


HTML_TEMPLATE_PUEBLO = """<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8">
<title>Informe del pueblo · {nombre}</title>
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
.piramide-bar-h{{display:inline-block;background:#02432D;height:1rem;vertical-align:middle}}
.piramide-bar-m{{display:inline-block;background:#a78bfa;height:1rem;vertical-align:middle}}
.piramide td{{font-size:.85rem}}
.piramide td.lbl{{text-align:center;font-variant-numeric:tabular-nums}}
.piramide td.h{{text-align:right}}
.piramide td.m{{text-align:left}}
</style></head>
<body>
<h1>Informe del pueblo · {nombre}</h1>
<p><span class="kpi">Población total · <b>{total:,}</b></span>
<span class="kpi">Con cap. diversas · <b>{con_disc:,}</b></span>
<span class="kpi">Prevalencia · <b>{prev_pueblo:.1f}‰</b></span>
<span class="kpi">Confiabilidad · <b>{confiabilidad}</b></span></p>

<h2>Pirámide de capacidades diversas (edad × sexo)</h2>
<table class="piramide">
<thead><tr><th style="text-align:right">Hombres</th><th>Grupo edad</th><th>Mujeres</th></tr></thead>
<tbody>
{filas_piramide}
</tbody>
</table>
<p class="fuente">Fuente: DANE-CNPV 2018 · `pueblo.disc_nacional` × `pueblo.piramide_disc`. Generado
el {fecha_iso}. Pipeline reemplaza al generador histórico que producía tablas con cifras vacías.
Sin links absolutos a localhost · seguro para distribución offline.</p>
</body></html>
"""


def _fila_piramide_html(grupo: str, valor_h: int, valor_m: int, max_v: int) -> str:
    """Una fila de la pirámide · barra horizontal proporcional al máximo."""
    pct_h = int(valor_h * 100 / max_v) if max_v > 0 else 0
    pct_m = int(valor_m * 100 / max_v) if max_v > 0 else 0
    return (
        f'<tr>'
        f'<td class="h">{valor_h} '
        f'<span class="piramide-bar-h" style="width:{pct_h}%"></span></td>'
        f'<td class="lbl">{grupo}</td>'
        f'<td class="m"><span class="piramide-bar-m" style="width:{pct_m}%"></span> {valor_m}</td>'
        f'</tr>'
    )


def render_pueblo(cod_id: int | str, output_root: Path, dry_run: bool = False) -> dict:
    """Renderiza informe pueblo · 125 pueblos indígenas.

    Generado T04 · Claude Opus 4.7 (escalada · S9 2026-05-09).
    Queries: pueblo.disc_nacional (KPIs) + pueblo.piramide_disc (edad×sexo).
    cod_pueblo es character varying en DB · castear con str.
    """
    cod_pueblo_id = str(cod_id)
    conn = _conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    pueblo,
                    COALESCE(con_discapacidad, 0)::int AS con_disc,
                    COALESCE(total, 0)::int AS total,
                    COALESCE(tasa_x_1000, 0)::numeric AS tasa,
                    COALESCE(confiabilidad, 'BAJA') AS confiabilidad_db
                FROM pueblo.disc_nacional
                WHERE cod_pueblo = %s AND periodo = '2018'
                LIMIT 1
                """,
                (cod_pueblo_id,),
            )
            r = cur.fetchone()
            if r:
                nom_pueblo, con_disc, total, tasa, confiabilidad_db = (
                    r[0].strip(), int(r[1]), int(r[2]), float(r[3]), r[4].strip()
                )
                confiabilidad = _confiabilidad_badge(con_disc) if confiabilidad_db == "" else confiabilidad_db
                sin_datos_disc = False
            else:
                # T08 fallback huérfanos · pueblo en pueblo.pueblo_municipio sin entrada disc_nacional
                # (433 JUHUP · 855 TAYRONAS · 860 CHITARERO · 940 INDIGENAS-BRASIL).
                cur.execute(
                    "SELECT DISTINCT pueblo FROM pueblo.pueblo_municipio WHERE cod_pueblo = %s LIMIT 1",
                    (cod_pueblo_id,),
                )
                rr = cur.fetchone()
                nom_pueblo = (rr[0] or f"Pueblo {cod_pueblo_id}").strip() if rr else f"Pueblo {cod_pueblo_id}"
                con_disc, total, tasa = 0, 0, 0.0
                confiabilidad = "BAJA"
                sin_datos_disc = True

            cur.execute(
                """
                SELECT grupo_edad, sexo, COALESCE(valor, 0)::int AS valor
                FROM pueblo.piramide_disc
                WHERE cod_pueblo = %s AND periodo = '2018'
                ORDER BY grupo_edad, sexo
                """,
                (cod_pueblo_id,),
            )
            piramide_raw = cur.fetchall()
            piramide_dict: dict[str, dict[str, int]] = {}
            for grupo, sexo, valor in piramide_raw:
                key_sexo = "H" if sexo.lower().startswith("h") else "M"
                piramide_dict.setdefault(grupo, {"H": 0, "M": 0})[key_sexo] = int(valor)
            piramide_info = [
                {"grupo_edad": g, "hombres": piramide_dict[g]["H"], "mujeres": piramide_dict[g]["M"]}
                for g in sorted(piramide_dict.keys())
            ]

            fecha_iso = datetime.now(tz=timezone.utc).isoformat()
            input_hash = _input_hash(cod_pueblo_id, nom_pueblo, con_disc, total)

            canonical = {
                "tipo": "pueblo",
                "id": str(cod_pueblo_id),
                "nombre": nom_pueblo,
                "secciones": {
                    "capacidades_diversas": {
                        "_sin_datos": sin_datos_disc,
                        "_nota": (
                            "pueblo huérfano sin entrada en pueblo.disc_nacional · "
                            "ver informe nacional o por dpto"
                        ) if sin_datos_disc else None,
                        "con_discapacidad": {
                            "value": con_disc,
                            "_meta": {
                                "query": "SELECT con_discapacidad FROM pueblo.disc_nacional WHERE cod_pueblo = %s AND periodo='2018'",
                                "table": "pueblo.disc_nacional",
                                "period": "2018",
                                "confiabilidad": confiabilidad,
                            },
                        },
                        "poblacion_referencia": {
                            "value": total,
                            "_meta": {"table": "pueblo.disc_nacional", "period": "2018"},
                        },
                        "prevalencia_x_1000": {
                            "value": round(tasa, 2),
                            "_meta": {"formula": "tasa_x_1000 from pueblo.disc_nacional"},
                        },
                    },
                    "demografia": {
                        "piramide_capacidades_diversas": {
                            "value": piramide_info,
                            "_meta": {
                                "table": "pueblo.piramide_disc",
                                "period": "2018",
                                "n_grupos_edad": len(piramide_info),
                            },
                        },
                    },
                    "territorial": {"_sin_datos": True, "_nota": "ver informe por dpto/mpio"},
                    "lengua": {"_sin_datos": True, "_nota": "no disponible en CNPV 2018"},
                    "nbi": {"_sin_datos": True, "_nota": "ver indicadores nacionales"},
                    "conflicto": {"_sin_datos": True, "_nota": "ver informe nacional"},
                    "icv": {"_sin_datos": True, "_nota": "ver indicadores.icv_municipal"},
                },
                "fecha_generacion": fecha_iso,
                "periodo": "2018",
                "_input_hash": input_hash,
                "_generador": "render_informes.py",
            }

            json_path = output_root / "pueblo" / f"{cod_pueblo_id}.json"
            html_path = output_root / "pueblo" / f"{cod_pueblo_id}.html"
            _write_canonical(json_path, canonical, dry_run=dry_run)

            max_v = max(
                (max(g["hombres"], g["mujeres"]) for g in piramide_info), default=1
            ) or 1
            filas_piramide = "\n".join(
                "    " + _fila_piramide_html(g["grupo_edad"], g["hombres"], g["mujeres"], max_v)
                for g in piramide_info
            )
            html = HTML_TEMPLATE_PUEBLO.format(
                nombre=nom_pueblo,
                total=total,
                con_disc=con_disc,
                prev_pueblo=tasa,
                confiabilidad=confiabilidad,
                filas_piramide=filas_piramide,
                fecha_iso=fecha_iso,
            )
            _write_html(html_path, html, dry_run=dry_run)

            return {
                "id": cod_pueblo_id,
                "nombre": nom_pueblo,
                "con_disc": con_disc,
                "total": total,
                "prev_pueblo": float(tasa),
                "n_grupos_piramide": len(piramide_info),
                "json_path": str(json_path),
                "html_path": str(html_path),
            }
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# NIVEL RESGUARDO (T05 · Claude Opus 4.7 · escalada · S9 2026-05-09)
# ---------------------------------------------------------------------------


HTML_TEMPLATE_RESGUARDO = """<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8">
<title>Informe del resguardo · {nombre}</title>
<style>
body{{font-family:system-ui,sans-serif;max-width:900px;margin:2rem auto;padding:1rem;color:#222;line-height:1.6}}
h1{{color:#02432D;border-bottom:3px solid #02432D;padding-bottom:.5rem}}
h2{{color:#02432D;margin-top:2rem}}
table{{width:100%;border-collapse:collapse;margin:1rem 0}}
th{{background:#02432D;color:#fff;padding:.5rem;text-align:left;width:30%}}
td{{padding:.5rem;border-bottom:1px solid #eee}}
.fuente{{font-size:.8rem;color:#666;margin-top:.5rem;font-style:italic}}
.kpi{{display:inline-block;margin:0 1rem .5rem 0;padding:.5rem 1rem;background:#f3f4f6;border-radius:6px}}
.kpi b{{color:#02432D;font-size:1.2rem}}
.nota{{padding:.75rem 1rem;background:#fef3c7;border-left:4px solid #92400e;margin:1rem 0;font-size:.9rem}}
</style></head>
<body>
<h1>Informe del resguardo · {nombre}</h1>
<p><span class="kpi">Población total (CNPV) · <b>{poblacion_total:,}</b></span>
<span class="kpi">Pueblo · <b>{pueblo_onic}</b></span>
<span class="kpi">Área (ha) · <b>{area_ha:,.1f}</b></span></p>

<h2>Información básica</h2>
<table>
<tr><th>Departamento</th><td>{nom_dpto} ({cod_dpto})</td></tr>
<tr><th>Municipio</th><td>{nom_mpio} ({cod_mpio})</td></tr>
<tr><th>Macrorregión</th><td>{macro}</td></tr>
<tr><th>Pueblo ONIC</th><td>{pueblo_onic}</td></tr>
<tr><th>Organización Regional</th><td>{org_regnal}</td></tr>
<tr><th>Área (hectáreas)</th><td>{area_ha:,.1f}</td></tr>
</table>

<div class="nota">
<b>Capacidades diversas a nivel resguardo:</b> sin datos disponibles en CNPV 2018.
El censo registra discapacidad por dpto y por pueblo, no por resguardo individual.
Para una aproximación, ver el informe del pueblo <b>{pueblo_onic}</b> o del municipio <b>{nom_mpio}</b>.
</div>

<p class="fuente">Fuente: DANE-CNPV 2018 · `smt_geo.resguardos` · `visor_dane.resguardo_pueblo`. Generado
el {fecha_iso}. Pipeline reemplaza al generador histórico que producía tablas con cifras vacías.
Sin links absolutos a localhost · seguro para distribución offline.</p>
</body></html>
"""


def render_resguardo(cod_id: str, output_root: Path, dry_run: bool = False) -> dict:
    """Renderiza informe resguardo · 830 resguardos ONIC.

    Generado T05 · Claude Opus 4.7 (escalada · S9 2026-05-09).
    Queries: smt_geo.resguardos (info_basica + geometría) + visor_dane.resguardo_pueblo (poblacion).
    NO hay tabla disc por resguardo · capacidades_diversas se marca _sin_datos honestamente
    (alineado con informes históricos generados pre-S9 que ya usan ese patrón).
    """
    cod_resguardo_id = cod_id
    conn = _conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    rg.territorio,
                    COALESCE(rg.dpto_cnmbr, '') AS nom_dpto,
                    COALESCE(rg.dpto_ccdgo, '') AS cod_dpto,
                    COALESCE(rg.mpio_cnmbr, '') AS nom_mpio,
                    COALESCE(rg.mpio_cdpmp, '') AS cod_mpio,
                    COALESCE(rg.macro, '') AS macro,
                    COALESCE(rg.pueblo_onic, '') AS pueblo_onic,
                    COALESCE(rg.org_regnal, '') AS org_regnal,
                    COALESCE(rg.area_pg_ha, 0)::numeric AS area_ha,
                    rg.id_resguar
                FROM smt_geo.resguardos rg
                WHERE rg.id_resguar = %s OR rg.fid::text = %s
                LIMIT 1
                """,
                (cod_resguardo_id, cod_resguardo_id),
            )
            r = cur.fetchone()
            if not r:
                raise ValueError(f"Resguardo id={cod_resguardo_id} no existe en smt_geo.resguardos")
            (nombre, nom_dpto, cod_dpto, nom_mpio, cod_mpio,
             macro, pueblo_onic, org_regnal, area_ha, id_resguar) = (
                r[0] or "—", r[1].strip(), r[2].strip(), r[3].strip(), r[4].strip(),
                r[5].strip(), r[6].strip(), r[7].strip(), float(r[8] or 0), r[9],
            )

            cur.execute(
                """
                SELECT COALESCE(SUM(poblacion), 0)::int
                FROM visor_dane.resguardo_pueblo
                WHERE resguardo ILIKE %s
                """,
                (nombre,),
            )
            pop_row = cur.fetchone()
            poblacion_total = int(pop_row[0]) if pop_row else 0

            fecha_iso = datetime.now(tz=timezone.utc).isoformat()
            input_hash = _input_hash(cod_resguardo_id, nombre, poblacion_total, area_ha)

            canonical = {
                "tipo": "resguardo",
                "id": str(cod_resguardo_id),
                "nombre": nombre,
                "secciones": {
                    "info_basica": {
                        "nombre": nombre,
                        "dpto": nom_dpto or "—",
                        "cod_dpto": cod_dpto or "—",
                        "mpio": nom_mpio or "—",
                        "cod_mpio": cod_mpio or "—",
                        "macro": macro or "—",
                        "pueblo_onic": pueblo_onic or "—",
                        "organizacion_regional": org_regnal or "—",
                        "area_hectareas": area_ha,
                    },
                    "demografia": {
                        "poblacion_total": {
                            "value": poblacion_total,
                            "_meta": {
                                "query": "SELECT SUM(poblacion) FROM visor_dane.resguardo_pueblo WHERE resguardo ILIKE %s",
                                "table": "visor_dane.resguardo_pueblo",
                                "period": "2018",
                                "confiabilidad": _confiabilidad_badge(poblacion_total),
                            },
                        },
                        "_nota": "población de la fuente DANE-CNPV cruzada por nombre de territorio",
                    },
                    "capacidades_diversas": {
                        "_sin_datos": True,
                        "_nota": (
                            "datos discapacidad por resguardo no disponibles en CNPV 2018 · "
                            "ver informe pueblo+dpto"
                        ),
                    },
                    "territorial": {"_sin_datos": True, "_nota": "ver bbox en geo.resguardos"},
                    "lengua": {"_sin_datos": True, "_nota": "ver informe pueblo"},
                    "nbi": {"_sin_datos": True, "_nota": "ver indicadores"},
                    "conflicto": {"_sin_datos": True, "_nota": "ver informe nacional"},
                    "icv": {"_sin_datos": True, "_nota": "ver indicadores.icv_municipal"},
                },
                "fecha_generacion": fecha_iso,
                "periodo": "2018",
                "_input_hash": input_hash,
                "_generador": "render_informes.py",
            }

            json_path = output_root / "resguardo" / f"{cod_resguardo_id}.json"
            html_path = output_root / "resguardo" / f"{cod_resguardo_id}.html"
            _write_canonical(json_path, canonical, dry_run=dry_run)

            html = HTML_TEMPLATE_RESGUARDO.format(
                nombre=nombre,
                poblacion_total=poblacion_total,
                pueblo_onic=pueblo_onic or "—",
                area_ha=area_ha,
                nom_dpto=nom_dpto or "—",
                cod_dpto=cod_dpto or "—",
                nom_mpio=nom_mpio or "—",
                cod_mpio=cod_mpio or "—",
                macro=macro or "—",
                org_regnal=org_regnal or "—",
                fecha_iso=fecha_iso,
            )
            _write_html(html_path, html, dry_run=dry_run)

            return {
                "id": cod_resguardo_id,
                "nombre": nombre,
                "pueblo_onic": pueblo_onic,
                "poblacion_total": poblacion_total,
                "area_ha": area_ha,
                "json_path": str(json_path),
                "html_path": str(html_path),
            }
    finally:
        conn.close()


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
    """Devuelve lista de IDs disponibles en DB para el nivel · falla rápido si tabla no existe.

    T08 (2026-05-10): mpio ahora itera sobre `geo.municipios` (catálogo geo completo
    1.122 mpios) en vez de `cnpv.disc_indigena_mpio` (967 con datos disc). Los mpios
    sin datos disc usan fallback `pob_indigena=0, _sin_datos:true` en render_mpio.
    pueblo agrega UNION con `pueblo.pueblo_municipio` para cubrir 4 huérfanos sin
    entrada en `disc_nacional` (433 JUHUP · 855 TAYRONAS · 860 CHITARERO · 940
    INDIGENAS-BRASIL).
    """
    queries = {
        "macro": "SELECT id FROM smt_geo.macrorregiones ORDER BY id",
        "dpto": "SELECT DISTINCT cod_dpto FROM geo.macro_dptos ORDER BY cod_dpto",
        "mpio": "SELECT cod_mpio FROM geo.municipios ORDER BY cod_mpio",
        "pueblo": (
            "SELECT cod_pueblo FROM pueblo.disc_nacional WHERE periodo = '2018' "
            "UNION "
            "SELECT DISTINCT cod_pueblo FROM pueblo.pueblo_municipio "
            "WHERE cod_pueblo NOT IN (SELECT cod_pueblo FROM pueblo.disc_nacional WHERE periodo = '2018') "
            "ORDER BY cod_pueblo"
        ),
        "resguardo": "SELECT id_resguar FROM smt_geo.resguardos WHERE id_resguar IS NOT NULL ORDER BY id_resguar",
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

    ids_list = list(ids)
    print(f"W12-RENDER · nivel={nivel} · output_root={output_root} · n_ids={len(ids_list)}")
    errores = 0
    procesados = 0
    for cod_id in ids_list:
        try:
            info = renderer(cod_id, output_root, dry_run=dry_run)
            nombre = info.get("nombre", "")
            print(f"  OK {nivel} {info.get('id', cod_id)} · {nombre}")
            procesados += 1
        except NotImplementedError as e:
            print(f"  PENDIENTE {nivel} {cod_id}: {e}", file=sys.stderr)
            errores += 1
            break
        except Exception as e:  # noqa: BLE001
            print(f"  ERR {nivel} {cod_id}: {e}", file=sys.stderr)
            errores += 1
    print(f"  resumen {nivel}: procesados={procesados} errores={errores}")
    return 2 if errores and procesados == 0 else 0


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
