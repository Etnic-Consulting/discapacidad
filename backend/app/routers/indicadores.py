"""
Indicadores - Definiciones, valores y series de tiempo.
"""

import logging
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/")
async def listar_definiciones(
    db: AsyncSession = Depends(get_db),
):
    """Lista todas las definiciones de indicadores."""
    try:
        result = await db.execute(
            text("""
                SELECT id, codigo, nombre, grupo, formula,
                       meta, fuente_primaria, fuente_cruce,
                       unidad, descripcion
                FROM indicadores.definiciones
                ORDER BY codigo
            """)
        )
        rows = [dict(r._mapping) for r in result]
        return {"total": len(rows), "data": rows}
    except Exception as e:
        logger.error("Error en listar_definiciones: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error consultando definiciones: {str(e)}")


@router.get("/valores")
async def valores_indicadores(
    periodo: str | None = Query(None, description="Filtrar por periodo"),
    nivel_geo: str | None = Query(None, description="nacional, dpto, mpio, pueblo"),
    pueblo: str | None = Query(None, description="Filtrar por nombre de pueblo"),
    cod_indicador: str | None = Query(None, description="Filtrar por codigo de indicador"),
    n_min: int = Query(30, description="Denominador minimo para incluir tasas (filtro n>=30)"),
    db: AsyncSession = Depends(get_db),
):
    """Valores de indicadores filtrables por periodo, nivel geografico y pueblo.
    Solo incluye valores donde denominador >= n_min (default 30) para tasas confiables.
    """
    try:
        params: dict = {"n_min": n_min}
        filtros = ["(v.denominador IS NULL OR v.denominador >= :n_min)"]

        if periodo:
            filtros.append("v.periodo = :periodo")
            params["periodo"] = periodo
        if nivel_geo:
            filtros.append("v.nivel_geo = :nivel_geo")
            params["nivel_geo"] = nivel_geo
        if pueblo:
            filtros.append("v.pueblo ILIKE :pueblo")
            params["pueblo"] = f"%{pueblo}%"
        if cod_indicador:
            filtros.append("v.cod_indicador = :cod_indicador")
            params["cod_indicador"] = cod_indicador

        where_clause = "WHERE " + " AND ".join(filtros)

        result = await db.execute(
            text(f"""
                SELECT v.cod_indicador, d.nombre AS indicador_nombre,
                       d.grupo, d.unidad,
                       v.periodo, v.nivel_geo, v.cod_geo, v.nombre_geo,
                       v.grupo_etnico, v.pueblo,
                       v.valor, v.numerador, v.denominador, v.confianza
                FROM indicadores.valores v
                JOIN indicadores.definiciones d ON v.cod_indicador = d.codigo
                {where_clause}
                ORDER BY v.cod_indicador, v.periodo, v.nivel_geo
            """),
            params,
        )
        rows = [dict(r._mapping) for r in result]
        return {"total": len(rows), "data": rows}
    except Exception as e:
        logger.error("Error en valores_indicadores: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error consultando valores de indicadores: {str(e)}")


@router.get("/serie-tiempo/{cod_indicador}")
async def serie_tiempo(
    cod_indicador: str,
    nivel_geo: str | None = Query(None),
    cod_geo: str | None = Query(None),
    pueblo: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Serie de tiempo para un indicador especifico a traves de todos los periodos."""
    try:
        params: dict = {"cod_indicador": cod_indicador}
        filtros = ["v.cod_indicador = :cod_indicador"]

        if nivel_geo:
            filtros.append("v.nivel_geo = :nivel_geo")
            params["nivel_geo"] = nivel_geo
        if cod_geo:
            filtros.append("v.cod_geo = :cod_geo")
            params["cod_geo"] = cod_geo
        if pueblo:
            filtros.append("v.pueblo ILIKE :pueblo")
            params["pueblo"] = f"%{pueblo}%"

        where_clause = " AND ".join(filtros)

        # Definicion del indicador
        defn = await db.execute(
            text("""
                SELECT codigo, nombre, grupo, formula, meta, unidad
                FROM indicadores.definiciones
                WHERE codigo = :cod_indicador
            """),
            {"cod_indicador": cod_indicador},
        )
        defn_row = defn.first()
        if not defn_row:
            raise HTTPException(status_code=404, detail=f"Indicador '{cod_indicador}' no encontrado")
        defn_data = dict(defn_row._mapping)

        # Valores por periodo
        result = await db.execute(
            text(f"""
                SELECT v.periodo, v.nivel_geo, v.cod_geo, v.nombre_geo,
                       v.pueblo, v.valor, v.numerador, v.denominador
                FROM indicadores.valores v
                WHERE {where_clause}
                ORDER BY v.periodo
            """),
            params,
        )
        rows = [dict(r._mapping) for r in result]
        return {
            "indicador": defn_data,
            "total_periodos": len(rows),
            "serie": rows,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error en serie_tiempo('%s'): %s", cod_indicador, e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error consultando serie de tiempo: {str(e)}")


@router.post("/recalcular")
async def recalcular_indicadores(
    periodo: str = Query("2018", description="Periodo a recalcular"),
    db: AsyncSession = Depends(get_db),
):
    """Dispara el recalculo de todos los indicadores para un periodo dado."""
    try:
        result = await db.execute(
            text("SELECT indicadores.calcular_todos(:periodo) AS n_generados"),
            {"periodo": periodo},
        )
        row = result.first()
        n = row._mapping["n_generados"] if row else 0
        await db.commit()
        return {
            "status": "ok",
            "periodo": periodo,
            "indicadores_generados": n,
        }
    except Exception as e:
        await db.rollback()
        logger.error("Error en recalcular_indicadores('%s'): %s", periodo, e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error recalculando indicadores: {str(e)}")
