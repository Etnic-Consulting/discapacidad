"""W13-API · Router /api/v1/observatorio/* · dashboard datos formulario SMT.

Endpoints read-only sobre `smt.respuestas_formulario` + `smt.resumen` (poblada
por trigger de migración 012). Anonimizados · k>=5 enforced en agregaciones
territoriales.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/kpis")
async def kpis(db: AsyncSession = Depends(get_db)):
    """KPIs generales del formulario · totales + cobertura territorial."""
    try:
        result = await db.execute(
            text(
                """
                SELECT
                    COUNT(*)                                                  AS total,
                    COUNT(DISTINCT datos->>'macrorregion')                    AS macros_cubiertos,
                    COUNT(DISTINCT cod_dpto)                                  AS dptos_cubiertos,
                    MAX(fecha_envio)                                          AS ultima
                FROM smt.respuestas_formulario
                WHERE cpli_consentimiento = 'si'
                """
            )
        )
        r = result.first()
        m = r._mapping if r else {}

        result_compl = await db.execute(
            text(
                """
                SELECT AVG(jsonb_array_length(
                    (SELECT jsonb_agg(k) FROM jsonb_object_keys(datos) k)
                ))::int AS promedio_keys
                FROM smt.respuestas_formulario
                WHERE cpli_consentimiento = 'si'
                """
            )
        )
        r2 = result_compl.first()
        promedio = (r2._mapping.get("promedio_keys") if r2 else 0) or 0
        completitud_pct = min(100, int(promedio * 10))

        return {
            "total_respuestas": int(m.get("total") or 0),
            "macros_cubiertos": int(m.get("macros_cubiertos") or 0),
            "dptos_cubiertos": int(m.get("dptos_cubiertos") or 0),
            "completitud_pct": completitud_pct,
            "ultima_respuesta_iso": m.get("ultima").isoformat() if m.get("ultima") else None,
        }
    except Exception as e:  # noqa: BLE001
        logger.error("Error en observatorio.kpis: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/distribucion-territorial")
async def distribucion_territorial(db: AsyncSession = Depends(get_db)):
    """Distribución por macro y dpto · k>=5 enforced."""
    try:
        result_total = await db.execute(
            text("SELECT COUNT(*) FROM smt.respuestas_formulario WHERE cpli_consentimiento='si'")
        )
        total = int((result_total.first() or [0])[0])

        result_macro = await db.execute(
            text(
                """
                SELECT
                    COALESCE(datos->>'macrorregion', 'SIN_MACRO') AS macro,
                    COUNT(*)::int                                  AS n
                FROM smt.respuestas_formulario
                WHERE cpli_consentimiento = 'si'
                GROUP BY datos->>'macrorregion'
                HAVING COUNT(*) >= 5
                ORDER BY n DESC
                """
            )
        )
        por_macro = [
            {"macro": r._mapping["macro"], "n": r._mapping["n"],
             "pct": round(100.0 * r._mapping["n"] / total, 1) if total else 0.0}
            for r in result_macro
        ]

        result_dpto = await db.execute(
            text(
                """
                SELECT cod_dpto,
                       COALESCE(MAX(datos->>'nom_dpto'), '') AS nom_dpto,
                       COUNT(*)::int                          AS n
                FROM smt.respuestas_formulario
                WHERE cpli_consentimiento = 'si' AND cod_dpto IS NOT NULL
                GROUP BY cod_dpto
                HAVING COUNT(*) >= 5
                ORDER BY n DESC
                LIMIT 20
                """
            )
        )
        por_dpto = [
            {"cod_dpto": r._mapping["cod_dpto"], "nom_dpto": r._mapping["nom_dpto"],
             "n": r._mapping["n"],
             "pct": round(100.0 * r._mapping["n"] / total, 1) if total else 0.0}
            for r in result_dpto
        ]
        return {"total": total, "por_macro": por_macro, "por_dpto": por_dpto}
    except Exception as e:  # noqa: BLE001
        logger.error("Error en observatorio.distribucion_territorial: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tipos-dificultad")
async def tipos_dificultad(db: AsyncSession = Depends(get_db)):
    """Conteo por tipo de dificultad reportada en `datos.dificultades` JSONB."""
    try:
        result = await db.execute(
            text(
                """
                SELECT tipo, COUNT(*)::int AS n
                FROM smt.respuestas_formulario rf,
                     jsonb_array_elements_text(COALESCE(rf.datos->'dificultades','[]'::jsonb)) AS tipo
                WHERE rf.cpli_consentimiento = 'si'
                GROUP BY tipo
                ORDER BY n DESC
                """
            )
        )
        rows = [{"tipo": r._mapping["tipo"], "n": int(r._mapping["n"])} for r in result]
        total = sum(r["n"] for r in rows)
        for r in rows:
            r["pct"] = round(100.0 * r["n"] / total, 1) if total else 0.0
        return {"total": total, "tipos": rows}
    except Exception as e:  # noqa: BLE001
        logger.error("Error en observatorio.tipos_dificultad: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ayudas-tecnicas")
async def ayudas_tecnicas(db: AsyncSession = Depends(get_db)):
    """Conteo por ayuda técnica reportada en `datos.ayudas_tecnicas` JSONB."""
    try:
        result = await db.execute(
            text(
                """
                SELECT ayuda, COUNT(*)::int AS n
                FROM smt.respuestas_formulario rf,
                     jsonb_array_elements_text(COALESCE(rf.datos->'ayudas_tecnicas','[]'::jsonb)) AS ayuda
                WHERE rf.cpli_consentimiento = 'si'
                GROUP BY ayuda
                ORDER BY n DESC
                """
            )
        )
        rows = [{"ayuda": r._mapping["ayuda"], "n": int(r._mapping["n"])} for r in result]
        total = sum(r["n"] for r in rows)
        for r in rows:
            r["pct"] = round(100.0 * r["n"] / total, 1) if total else 0.0
        return {"total": total, "ayudas": rows}
    except Exception as e:  # noqa: BLE001
        logger.error("Error en observatorio.ayudas_tecnicas: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/timeline")
async def timeline(
    bucket: str = Query("week", regex="^(week|month)$"),
    db: AsyncSession = Depends(get_db),
):
    """Línea de tiempo · respuestas por semana ISO o mes."""
    try:
        fmt = "IYYY-\"W\"IW" if bucket == "week" else "YYYY-MM"
        result = await db.execute(
            text(
                f"""
                SELECT to_char(fecha_envio, '{fmt}') AS periodo, COUNT(*)::int AS n
                FROM smt.respuestas_formulario
                WHERE cpli_consentimiento = 'si'
                GROUP BY periodo
                ORDER BY periodo
                """
            )
        )
        data = [{"periodo": r._mapping["periodo"], "n": int(r._mapping["n"])} for r in result]
        return {"bucket": bucket, "data": data}
    except Exception as e:  # noqa: BLE001
        logger.error("Error en observatorio.timeline: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ultimas-respuestas")
async def ultimas_respuestas(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Últimas N respuestas anonimizadas · sin documento, sin nombre comunidad."""
    try:
        result = await db.execute(
            text(
                """
                SELECT
                    id,
                    fecha_envio,
                    datos->>'macrorregion'                AS macrorregion,
                    cod_dpto,
                    jsonb_array_length(COALESCE(datos->'dificultades','[]'::jsonb)) AS n_dificultades,
                    jsonb_array_length(COALESCE(datos->'ayudas_tecnicas','[]'::jsonb)) AS n_ayudas,
                    (SELECT COUNT(*) FROM jsonb_object_keys(datos) k) AS n_keys
                FROM smt.respuestas_formulario
                WHERE cpli_consentimiento = 'si'
                ORDER BY fecha_envio DESC
                LIMIT :lim
                """
            ),
            {"lim": limit},
        )
        rows = []
        for r in result:
            m = r._mapping
            rows.append({
                "id": int(m["id"]),
                "fecha_envio": m["fecha_envio"].isoformat() if m["fecha_envio"] else None,
                "macrorregion": m["macrorregion"],
                "cod_dpto": m["cod_dpto"],
                "n_dificultades": int(m["n_dificultades"] or 0),
                "n_ayudas": int(m["n_ayudas"] or 0),
                "completitud_pct": min(100, int((m["n_keys"] or 0) * 10)),
            })
        return rows
    except Exception as e:  # noqa: BLE001
        logger.error("Error en observatorio.ultimas_respuestas: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
