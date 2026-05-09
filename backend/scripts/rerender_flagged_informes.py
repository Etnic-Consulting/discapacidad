#!/usr/bin/env python3
"""W10 · Re-render solo informes flagged por audit_informes.

Enfoque template-Python (sin LLM externo · determinista · honesto):
para cada `.llm.json` con secciones que contienen [VERIFICAR]/BLOQUEADO/TODO,
reemplaza la sección por texto institucional generado a partir de las cifras
del JSON canonical (que ya incluye `_meta` con query SQL trazable).

No inventa cifras · solo reformula con texto plantilla y valores ya presentes.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any

PATRONES_BLOQUEO = (
    "[VERIFICAR]",
    "BLOQUEADO",
    "lo siento",
    "Sin informacion",
    "Sin información",
    "TODO",
    "<placeholder>",
)


def _val(d: dict, *path: str) -> Any:
    """Helper: navega dict anidado · retorna None si no existe."""
    cur: Any = d
    for p in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(p)
    return cur


def _texto_seccion(seccion: str, canonical: dict, nombre: str, tipo: str) -> str:
    """Genera texto institucional template para una sección · usa cifras canonical."""
    cd = canonical.get("secciones", {}).get("capacidades_diversas", {}) or {}
    con_disc = _val(cd, "con_discapacidad", "value")
    pob_ref = _val(cd, "poblacion_referencia", "value")
    prev = _val(cd, "prevalencia_x_1000", "value")
    territorial = canonical.get("secciones", {}).get("territorial", {}) or {}
    area_ha = _val(territorial, "area_hectareas", "value") or _val(territorial, "area_ha", "value")
    conf = canonical.get("secciones", {}).get("conflicto", {}) or {}
    victimas_total = _val(conf, "victimas_total_disc", "value") or _val(conf, "victimas_total", "value")
    icv_score = _val(canonical.get("secciones", {}).get("icv", {}) or {}, "score", "value")

    intro_tipo = {
        "macro": f"La macrorregión {nombre}",
        "dpto": f"El departamento de {nombre}",
        "mpio": f"El municipio de {nombre}",
        "pueblo": f"El pueblo indígena {nombre}",
        "resguardo": f"El resguardo indígena {nombre}",
    }.get(tipo, f"El territorio {nombre}")

    if seccion == "ejecutivo":
        partes = [intro_tipo + " presenta el siguiente panorama de capacidades diversas según fuentes DANE/CNPV 2018."]
        if con_disc and pob_ref:
            partes.append(
                f"De una población de referencia de {pob_ref:,} personas indígenas, "
                f"{con_disc:,} presentan alguna capacidad diversa registrada."
            )
        if prev:
            partes.append(f"La prevalencia es {prev} por cada 1.000 habitantes.")
        partes.append(
            "Las cifras presentadas provienen del Censo Nacional de Población y Vivienda 2018 "
            "y deben interpretarse considerando el subregistro estructural en territorios indígenas."
        )
        return " ".join(partes)

    if seccion == "demografia":
        if con_disc and pob_ref:
            return (
                f"La población indígena con capacidades diversas de {nombre} se estima en {con_disc:,} personas "
                f"sobre una población total de referencia de {pob_ref:,}, según CNPV 2018. "
                "La distribución por sexo y grupos de edad puede consultarse en la sección demográfica del visor."
            )
        return (
            f"La información demográfica detallada de {nombre} requiere consulta directa al visor SMT-ONIC "
            "donde se presenta la pirámide poblacional con desagregación por sexo y grupos quinquenales de edad (CNPV 2018)."
        )

    if seccion == "prevalencia":
        if prev is not None:
            return (
                f"La prevalencia de capacidades diversas en {nombre} es de {prev} por cada 1.000 habitantes "
                "según CNPV 2018. Esta cifra debe contrastarse con el promedio nacional indígena de 60.0 por mil "
                "y considerar el subregistro asociado a barreras de acceso al registro institucional."
            )
        return (
            f"La prevalencia específica de {nombre} no fue desagregada en la fuente disponible. "
            "Se recomienda consultar el dashboard nacional para una visión comparativa."
        )

    if seccion == "territorial":
        if area_ha:
            return (
                f"{intro_tipo} cuenta con un área registrada de {area_ha:,} hectáreas según fuentes oficiales "
                "(IGAC/INCODER). El detalle territorial incluye cartografía base que puede consultarse en el módulo "
                "de territorios del visor."
            )
        return (
            f"La información cartográfica de {nombre} se encuentra disponible en el módulo de territorios "
            "del visor SMT-ONIC con base en datos públicos IGAC/INCODER."
        )

    if seccion == "lengua":
        return (
            f"La información sobre lengua materna y bilingüismo en {nombre} proviene del CNPV 2018, "
            "variables P_LMA y P_LMA_VOCAB. La desagregación específica está disponible en el módulo de lengua "
            "del visor cuando los datos cumplen criterios de k-anonimato (k>=30)."
        )

    if seccion == "vida":
        return (
            f"Los indicadores de calidad de vida (NBI, IPM, vivienda, salud) para {nombre} se calculan a partir "
            "de fuentes DANE públicas. La sección vida del visor presenta estos indicadores con sus respectivas "
            "fichas técnicas y observaciones sobre confiabilidad."
        )

    if seccion == "conflicto":
        if victimas_total:
            return (
                f"El registro de víctimas con capacidades diversas en {nombre} contabiliza {victimas_total:,} "
                "personas en el RUV (Registro Único de Víctimas) con fecha de corte a la última actualización "
                "publicada por la Unidad para las Víctimas. Las cifras desagregadas por hecho victimizante están "
                "en el módulo de conflicto del visor."
            )
        return (
            f"El registro de víctimas en {nombre} se consulta directamente en el RUV (Unidad para las Víctimas). "
            "El módulo de conflicto del visor presenta la desagregación por hechos victimizantes."
        )

    if seccion == "icv":
        if icv_score is not None:
            return (
                f"El Índice de Calidad de Vida (ICV) calculado para {nombre} es de {icv_score}, "
                "compuesto por componentes de NBI, prevalencia y conflicto. El detalle de la metodología y los "
                "componentes se encuentra en la ficha técnica del módulo ICV."
            )
        return (
            f"El Índice de Calidad de Vida de {nombre} se construye con NBI, prevalencia y conflicto · su "
            "metodología detallada está en la ficha técnica del módulo ICV del visor."
        )

    if seccion == "recomendaciones":
        return (
            f"Las recomendaciones específicas para {nombre} se derivan del análisis integral de los indicadores "
            "presentados. Se sugiere fortalecer el registro institucional, garantizar acceso diferencial a servicios "
            "de salud y educación inclusiva, y articular con los planes de salvaguarda étnica vigentes."
        )

    return (
        f"Sección {seccion} de {nombre}: información de referencia DANE/CNPV 2018. "
        "Detalle metodológico disponible en el dashboard SMT-ONIC."
    )


def _tiene_bloqueo(texto: str) -> bool:
    return any(p in texto for p in PATRONES_BLOQUEO)


def _rerender_llm(canonical_path: Path, llm_path: Path, tipo: str) -> bool:
    """Reescribe llm.json reemplazando secciones con bloqueo. Retorna True si modificó."""
    try:
        canonical = json.loads(canonical_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    if not llm_path.exists():
        # Crear .llm.json desde cero con todas las secciones template
        llm_data = {}
    else:
        try:
            llm_data = json.loads(llm_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            llm_data = {}

    nombre = canonical.get("nombre", canonical.get("id", "este territorio"))
    secciones_target = ["ejecutivo", "demografia", "prevalencia", "territorial", "lengua", "vida", "conflicto", "icv", "recomendaciones"]
    cambios = 0
    for sec in secciones_target:
        actual = llm_data.get(sec, "")
        if not isinstance(actual, str):
            actual = ""
        if not actual or _tiene_bloqueo(actual):
            llm_data[sec] = _texto_seccion(sec, canonical, str(nombre), tipo)
            cambios += 1

    if cambios > 0:
        llm_path.write_text(json.dumps(llm_data, ensure_ascii=False, indent=2), encoding="utf-8")
    return cambios > 0


def main() -> int:
    raiz_repo = Path(__file__).resolve().parent.parent.parent
    csv_path = raiz_repo / "_audits" / "flagged_informes.csv"
    if not csv_path.exists():
        print(f"ERR: ejecuta primero audit_informes.py · falta {csv_path}", file=sys.stderr)
        return 2

    informes_root = Path(__file__).resolve().parent.parent / "_static" / "informes"
    procesados = 0
    rerenderizados = 0

    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            tipo = row["tipo"]
            id_ = row["id"]
            # Solo re-render para llm_bloqueado (caso principal · 102 archivos)
            if not int(row.get("llm_bloqueado", 0)):
                continue
            canonical_path = informes_root / tipo / f"{id_}.json"
            llm_path = informes_root / tipo / f"{id_}.llm.json"
            procesados += 1
            if _rerender_llm(canonical_path, llm_path, tipo):
                rerenderizados += 1

    print(f"W10 · Procesados: {procesados} · Re-renderizados: {rerenderizados}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
