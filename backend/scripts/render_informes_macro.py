#!/usr/bin/env python3
"""W12-RENDER · genera JSON+HTML correcto para los 5 macros.

Reemplaza el generador histórico (no commiteado en repo) que producía tablas
con `—` y badge `n<30` falso. Lee cifras reales desde `pueblo.disc_dpto`,
`geo.macro_dptos` y `smt_geo.macrorregiones`. k-anonimato HONESTO: solo marca
n<30 si la cifra agregada del dpto es realmente menor a 30.

Origen: prompt `_scripts/prompts/W12_render_macro.md` despachado vía
`local_first_codigo` · Ollama qwen2.5-coder:7b primer intento (output 70%
estructural) · refinado por Claude Opus 4.7 (escalada waterfall · ver
bitácora S6_observatorio).
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import psycopg2

DB_CFG = {
    "host": os.environ.get("PG_HOST", "localhost"),
    "port": int(os.environ.get("PG_PORT", "5450")),
    "user": os.environ.get("PG_USER", "smt_admin"),
    "password": os.environ.get("PG_PASSWORD", "smt_onic_2026"),
    "dbname": os.environ.get("PG_DB", "smt_onic"),
}


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


HTML_TEMPLATE = """<!DOCTYPE html>
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

<h2>§ 1. Síntesis</h2>
<p>La macrorregión <strong>{nombre}</strong> agrupa <strong>{n_dptos}</strong> departamentos.
La población indígena registrada en CNPV 2018 es <strong>{total_macro:,}</strong> personas,
de las cuales <strong>{con_disc_macro:,}</strong> ({prev_macro:.1f}‰) presentan capacidades diversas.
Las cifras provienen del Censo Nacional de Población y Vivienda 2018 (DANE) y deben interpretarse
considerando el subregistro estructural en territorios indígenas.</p>

<h2>§ 2. Departamentos con mayor presencia</h2>
<table>
  <thead><tr><th>Departamento</th><th>Población</th><th>Con cap. diversas</th><th>Prevalencia</th><th>Confiabilidad</th></tr></thead>
  <tbody>
{filas_dptos}
  </tbody>
</table>
<div class="fuente">Fuente: pueblo.disc_dpto · CNPV 2018 (DANE) · cifras agregadas por departamento. k-anonimato enforced (n&lt;30 oculta cifra exacta).</div>

<h2>§ 3. Generación</h2>
<p class="fuente">Generado automáticamente por <code>backend/scripts/render_informes_macro.py</code>
el {fecha_iso}. Pipeline reemplaza al generador histórico que producía tablas con cifras vacías.
Sin links absolutos a localhost · seguro para distribución offline.</p>
</body></html>
"""


def render_macro(cod_macro_id: int, output_root: Path) -> dict:
    conn = psycopg2.connect(**DB_CFG)
    conn.autocommit = True
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
            input_signature = f"{cod_macro_id}|{macro_nombre}|{total_con_disc}|{total_total}"
            input_hash = hashlib.sha256(input_signature.encode()).hexdigest()[:16]

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
                                "confiabilidad": "CONFIABLE" if total_con_disc >= 30 else "BAJA",
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
            json_path.parent.mkdir(parents=True, exist_ok=True)
            json_path.write_text(json.dumps(canonical, ensure_ascii=False, indent=2), encoding="utf-8")

            filas_dptos = "\n".join("    " + _fila_dpto_html(d) for d in departamentos_info)
            html = HTML_TEMPLATE.format(
                nombre=macro_nombre,
                total_macro=total_total,
                con_disc_macro=total_con_disc,
                prev_macro=prev_macro,
                n_dptos=len(departamentos_info),
                filas_dptos=filas_dptos,
                fecha_iso=fecha_iso,
            )
            html_path.write_text(html, encoding="utf-8")

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


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    output_root = repo_root / "_static" / "informes"
    print(f"W12-RENDER · output_root: {output_root}")
    for cod_macro_id in range(1, 6):
        try:
            info = render_macro(cod_macro_id, output_root)
            print(
                f"  OK macro {info['id']} · {info['nombre']:20s} · {info['n_dptos']} dptos · "
                f"con_disc={info['total_con_disc']:,} · prev={info['prev_macro']:.1f}‰"
            )
        except Exception as e:  # noqa: BLE001
            print(f"  ERR macro {cod_macro_id}: {e}", file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
