"""
Conflicto armado - Victimas indigenas con capacidades diversas.
Fuentes: RUV (ext.ruv_hechos_municipal) y victimas.universo.
"""

import logging
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/victimas/resumen")
async def victimas_resumen(
    db: AsyncSession = Depends(get_db),
):
    """Resumen de victimas por grupo etnico y tipo de capacidad diversa."""
    try:
        result = await db.execute(
            text("""
                SELECT etnia, discapacidad,
                       SUM(per_ocu) AS personas_ocurrencia,
                       SUM(per_sa) AS sujetos_atencion,
                       SUM(eventos) AS total_eventos
                FROM ext.ruv_hechos_municipal
                WHERE etnia IS NOT NULL
                GROUP BY etnia, discapacidad
                ORDER BY etnia, total_eventos DESC NULLS LAST
            """)
        )
        rows = [dict(r._mapping) for r in result]
        return {"total": len(rows), "data": rows}
    except Exception as e:
        logger.error("Error en victimas_resumen: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error consultando resumen de victimas: {str(e)}")


@router.get("/victimas/hechos")
async def victimas_hechos_municipio(
    cod_dpto: str | None = Query(None, description="Filtrar por departamento"),
    hecho: str | None = Query(None, description="Filtrar por tipo de hecho"),
    db: AsyncSession = Depends(get_db),
):
    """Hechos victimizantes por municipio para poblacion indigena con capacidades diversas."""
    try:
        params: dict = {}
        filtros = ["r.etnia = 'Indigena'"]

        if cod_dpto:
            filtros.append("r.cod_dpto = :cod_dpto")
            params["cod_dpto"] = cod_dpto
        if hecho:
            filtros.append("r.hecho ILIKE :hecho")
            params["hecho"] = f"%{hecho}%"

        where_clause = " AND ".join(filtros)

        result = await db.execute(
            text(f"""
                SELECT r.cod_dpto, r.estado_depto,
                       r.cod_mpio, r.ciudad_municipio,
                       r.hecho, r.discapacidad,
                       SUM(r.per_ocu) AS personas_ocurrencia,
                       SUM(r.per_sa) AS sujetos_atencion,
                       SUM(r.eventos) AS total_eventos
                FROM ext.ruv_hechos_municipal r
                WHERE {where_clause}
                GROUP BY r.cod_dpto, r.estado_depto,
                         r.cod_mpio, r.ciudad_municipio,
                         r.hecho, r.discapacidad
                ORDER BY total_eventos DESC NULLS LAST
            """),
            params,
        )
        rows = [dict(r._mapping) for r in result]
        return {"total": len(rows), "data": rows}
    except Exception as e:
        logger.error("Error en victimas_hechos_municipio: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error consultando hechos victimizantes: {str(e)}")


@router.get("/victimas/por-pueblo")
async def victimas_por_pueblo_ranking(
    cod_dpto: str | None = Query(None, description="Filtrar por departamento"),
    limit: int = Query(20, ge=1, le=100, description="Cantidad de pueblos a retornar"),
    db: AsyncSession = Depends(get_db),
):
    """Top pueblos indígenas por total de víctimas con capacidades diversas."""
    try:
        params: dict = {"limit": limit}
        filtro_dpto = ""
        if cod_dpto:
            filtro_dpto = "AND LEFT(cod_mpio_ocurrencia, 2) = :cod_dpto"
            params["cod_dpto"] = cod_dpto

        result = await db.execute(
            text(f"""
                SELECT pueblo_imputado AS pueblo,
                       COUNT(*) AS total_victimas,
                       COUNT(*) FILTER (WHERE tipo_discapacidad_limpia = 'FISICA') AS fisica,
                       COUNT(*) FILTER (WHERE tipo_discapacidad_limpia = 'VISUAL') AS visual,
                       COUNT(*) FILTER (WHERE tipo_discapacidad_limpia = 'AUDITIVA') AS auditiva,
                       COUNT(*) FILTER (WHERE tipo_discapacidad_limpia = 'INTELECTUAL') AS intelectual,
                       COUNT(*) FILTER (WHERE tipo_discapacidad_limpia = 'PSICOSOCIAL') AS psicosocial,
                       COUNT(*) FILTER (WHERE tipo_discapacidad_limpia = 'SIN_INFORMACION') AS sin_informacion,
                       MODE() WITHIN GROUP (ORDER BY confianza_imputacion) AS confianza_imputacion
                FROM victimas.universo
                WHERE pueblo_imputado IS NOT NULL
                {filtro_dpto}
                GROUP BY pueblo_imputado
                ORDER BY total_victimas DESC
                LIMIT :limit
            """),
            params,
        )
        rows = [dict(r._mapping) for r in result]
        total_general = sum(r["total_victimas"] for r in rows)
        return {"total": len(rows), "total_victimas": total_general, "data": rows}
    except Exception as e:
        logger.error("Error en victimas_por_pueblo_ranking: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error consultando ranking de pueblos: {str(e)}")


@router.get("/victimas/por-hecho")
async def victimas_por_hecho(
    cod_dpto: str | None = Query(None, description="Filtrar por departamento"),
    db: AsyncSession = Depends(get_db),
):
    """Víctimas indígenas con capacidades diversas agregadas por hecho victimizante."""
    try:
        params: dict = {}
        filtro_dpto = ""
        if cod_dpto:
            filtro_dpto = "AND LEFT(cod_mpio_ocurrencia, 2) = :cod_dpto"
            params["cod_dpto"] = cod_dpto

        result = await db.execute(
            text(f"""
                SELECT hecho,
                       COUNT(*) AS total_victimas,
                       COUNT(*) FILTER (WHERE tipo_discapacidad_limpia = 'FISICA') AS fisica,
                       COUNT(*) FILTER (WHERE tipo_discapacidad_limpia = 'VISUAL') AS visual,
                       COUNT(*) FILTER (WHERE tipo_discapacidad_limpia = 'AUDITIVA') AS auditiva,
                       COUNT(*) FILTER (WHERE tipo_discapacidad_limpia = 'INTELECTUAL') AS intelectual,
                       COUNT(*) FILTER (WHERE tipo_discapacidad_limpia = 'PSICOSOCIAL') AS psicosocial
                FROM victimas.universo
                WHERE hecho IS NOT NULL
                {filtro_dpto}
                GROUP BY hecho
                ORDER BY total_victimas DESC
            """),
            params,
        )
        rows = [dict(r._mapping) for r in result]
        total_general = sum(r["total_victimas"] for r in rows)
        return {"total": len(rows), "total_victimas": total_general, "data": rows}
    except Exception as e:
        logger.error("Error en victimas_por_hecho: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error consultando hechos victimizantes: {str(e)}")


@router.get("/victimas/por-tipo")
async def victimas_por_tipo(
    cod_dpto: str | None = Query(None, description="Filtrar por departamento"),
    db: AsyncSession = Depends(get_db),
):
    """Víctimas indígenas agregadas por tipo de capacidad diversa."""
    try:
        params: dict = {}
        filtro_dpto = ""
        if cod_dpto:
            filtro_dpto = "AND LEFT(cod_mpio_ocurrencia, 2) = :cod_dpto"
            params["cod_dpto"] = cod_dpto

        result = await db.execute(
            text(f"""
                SELECT tipo_discapacidad_limpia AS tipo,
                       COUNT(*) AS total_victimas
                FROM victimas.universo
                WHERE tipo_discapacidad_limpia IS NOT NULL
                {filtro_dpto}
                GROUP BY tipo_discapacidad_limpia
                ORDER BY total_victimas DESC
            """),
            params,
        )
        rows = [dict(r._mapping) for r in result]
        total_general = sum(r["total_victimas"] for r in rows)
        return {"total": len(rows), "total_victimas": total_general, "data": rows}
    except Exception as e:
        logger.error("Error en victimas_por_tipo: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error consultando tipos de capacidad diversa: {str(e)}")


@router.get("/victimas/pueblo/{pueblo_id}")
async def victimas_por_pueblo(
    pueblo_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Victimas imputadas a un pueblo indigena especifico.
    Acepta codigo de pueblo (ej: '001') o nombre de pueblo (ej: 'Wayuu').
    Usa victimas.resumen_pueblo_hecho si existe, de lo contrario imp.ruv_pueblo.
    """
    # Determine if pueblo_id is a code (digits only) or a name
    is_code = pueblo_id.isdigit()

    # --- Try victimas.resumen_pueblo_hecho first ---
    try:
        if is_code:
            query_rph = text("""
                SELECT cod_pueblo_imputado, pueblo_imputado,
                       hecho, tipo_disc_limpia,
                       cod_dpto, cod_mpio,
                       cantidad
                FROM victimas.resumen_pueblo_hecho
                WHERE cod_pueblo_imputado = :pueblo_id
                ORDER BY cantidad DESC
            """)
        else:
            query_rph = text("""
                SELECT cod_pueblo_imputado, pueblo_imputado,
                       hecho, tipo_disc_limpia,
                       cod_dpto, cod_mpio,
                       cantidad
                FROM victimas.resumen_pueblo_hecho
                WHERE pueblo_imputado ILIKE :pueblo_id
                ORDER BY cantidad DESC
            """)

        param_val = pueblo_id if is_code else f"%{pueblo_id}%"
        result = await db.execute(query_rph, {"pueblo_id": param_val})
        rows = [dict(r._mapping) for r in result]
        if rows:
            cod = rows[0]["cod_pueblo_imputado"]
            nombre = rows[0]["pueblo_imputado"]
            return {
                "fuente": "victimas.universo",
                "cod_pueblo": cod,
                "pueblo": nombre,
                "total": len(rows),
                "data": rows,
            }
    except Exception as e:
        logger.warning("Error consultando victimas.resumen_pueblo_hecho para '%s': %s", pueblo_id, e)

    # --- Fallback: datos imputados de RUV ---
    try:
        if is_code:
            query_ruv = text("""
                SELECT cod_pueblo_imputado, pueblo_imputado,
                       hecho, discapacidad, sexo, ciclo_vital,
                       eventos, confianza, metodo_imputacion
                FROM imp.ruv_pueblo
                WHERE cod_pueblo_imputado = :pueblo_id
                ORDER BY eventos DESC
            """)
        else:
            query_ruv = text("""
                SELECT cod_pueblo_imputado, pueblo_imputado,
                       hecho, discapacidad, sexo, ciclo_vital,
                       eventos, confianza, metodo_imputacion
                FROM imp.ruv_pueblo
                WHERE pueblo_imputado ILIKE :pueblo_id
                ORDER BY eventos DESC
            """)

        param_val = pueblo_id if is_code else f"%{pueblo_id}%"
        result = await db.execute(query_ruv, {"pueblo_id": param_val})
        rows = [dict(r._mapping) for r in result]

        if not rows:
            raise HTTPException(
                status_code=404,
                detail=f"Pueblo '{pueblo_id}' no encontrado en datos de victimas"
            )

        cod = rows[0]["cod_pueblo_imputado"]
        nombre = rows[0]["pueblo_imputado"]
        return {
            "fuente": "imp.ruv_pueblo",
            "cod_pueblo": cod,
            "pueblo": nombre,
            "total": len(rows),
            "data": rows,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error en victimas_por_pueblo('%s'): %s", pueblo_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error consultando victimas por pueblo: {str(e)}")
