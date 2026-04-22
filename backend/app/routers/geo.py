"""
Geografia - GeoJSON endpoints para departamentos, municipios y resguardos.
"""

import logging
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/departamentos")
async def departamentos_geojson(
    incluir_prevalencia: bool = Query(False, description="Unir con datos de prevalencia"),
    periodo: str = Query("2018"),
    db: AsyncSession = Depends(get_db),
):
    """GeoJSON FeatureCollection de departamentos, opcionalmente con prevalencia."""
    try:
        if incluir_prevalencia:
            result = await db.execute(
                text("""
                    SELECT d.cod_dpto, d.nom_dpto, d.area_km2,
                           ST_AsGeoJSON(d.geom)::json AS geometry,
                           p.pob_total, p.pob_disc, p.tasa_x_1000, p.prevalencia_pct
                    FROM geo.departamentos d
                    LEFT JOIN cnpv.prevalencia_etnia_dpto p
                        ON d.cod_dpto = p.cod_dpto
                        AND p.periodo = :periodo
                        AND p.grupo_etnico = 'Indigena'
                    ORDER BY d.cod_dpto
                """),
                {"periodo": periodo},
            )
        else:
            result = await db.execute(
                text("""
                    SELECT cod_dpto, nom_dpto, area_km2,
                           ST_AsGeoJSON(geom)::json AS geometry
                    FROM geo.departamentos
                    ORDER BY cod_dpto
                """)
            )

        rows = result.all()
        features = []
        for row in rows:
            m = dict(row._mapping)
            geom = m.pop("geometry", None)
            features.append({
                "type": "Feature",
                "geometry": geom,
                "properties": m,
            })

        return {
            "type": "FeatureCollection",
            "features": features,
        }
    except Exception as e:
        logger.error("Error en departamentos_geojson: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error consultando departamentos: {str(e)}")


@router.get("/municipios")
async def municipios_geojson(
    cod_dpto: str | None = Query(None, description="Filtrar por departamento"),
    db: AsyncSession = Depends(get_db),
):
    """GeoJSON FeatureCollection de municipios, filtrable por departamento."""
    try:
        params: dict = {}
        filtro_dpto = ""
        if cod_dpto:
            filtro_dpto = "WHERE m.cod_dpto = :cod_dpto"
            params["cod_dpto"] = cod_dpto

        result = await db.execute(
            text(f"""
                SELECT m.cod_mpio, m.cod_dpto, m.nom_mpio, m.area_km2,
                       ST_AsGeoJSON(m.geom)::json AS geometry
                FROM geo.municipios m
                {filtro_dpto}
                ORDER BY m.cod_mpio
            """),
            params,
        )

        rows = result.all()
        features = []
        for row in rows:
            m = dict(row._mapping)
            geom = m.pop("geometry", None)
            features.append({
                "type": "Feature",
                "geometry": geom,
                "properties": m,
            })

        return {
            "type": "FeatureCollection",
            "features": features,
        }
    except Exception as e:
        logger.error("Error en municipios_geojson: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error consultando municipios: {str(e)}")


@router.get("/resguardos")
async def listar_resguardos(
    cod_mpio: str | None = Query(None, description="Filtrar por municipio"),
    db: AsyncSession = Depends(get_db),
):
    """Lista de resguardos indigenas, filtrable por municipio."""
    try:
        params: dict = {}
        filtro = ""
        if cod_mpio:
            filtro = "WHERE r.cod_mpio = :cod_mpio OR rm.cod_mpio = :cod_mpio"
            params["cod_mpio"] = cod_mpio

        result = await db.execute(
            text(f"""
                SELECT DISTINCT r.cod_resguardo, r.nombre,
                       r.nom_departamento, r.nom_municipio,
                       r.poblacion_proy
                FROM geo.resguardos r
                LEFT JOIN geo.resguardo_municipio rm
                    ON r.cod_resguardo = rm.cod_resguardo
                {filtro}
                ORDER BY r.nombre
            """),
            params,
        )
        rows = [dict(r._mapping) for r in result]
        return {"total": len(rows), "data": rows}
    except Exception as e:
        logger.error("Error en listar_resguardos: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error consultando resguardos: {str(e)}")


# ---- SMT-ONIC spatial layers (smt_geo schema, loaded via geopandas) ----


@router.get("/macrorregiones")
async def listar_macrorregiones(db: AsyncSession = Depends(get_db)):
    """Lista de las 5 macrorregiones ONIC con conteo de municipios asociados."""
    try:
        result = await db.execute(text("""
            SELECT m.id, m.macro,
                   COUNT(DISTINCT r.mpio_cdpmp) AS municipios,
                   COUNT(DISTINCT r.ccdgo_terr) AS resguardos,
                   COUNT(DISTINCT r.pueblo_onic) AS pueblos
            FROM smt_geo.macrorregiones m
            LEFT JOIN smt_geo.resguardos r ON r.macro = m.macro
            GROUP BY m.id, m.macro
            ORDER BY m.id
        """))
        rows = [dict(r._mapping) for r in result]
        return {"total": len(rows), "data": rows}
    except Exception as e:
        logger.error("Error en listar_macrorregiones: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error consultando macrorregiones: {str(e)}")


@router.get("/smt/macrorregiones")
async def get_macrorregiones(db: AsyncSession = Depends(get_db)):
    """GeoJSON of 5 ONIC macroregions."""
    try:
        result = await db.execute(text("""
            SELECT macro, ST_AsGeoJSON(geometry)::json AS geojson
            FROM smt_geo.macrorregiones
        """))
        features = []
        for row in result.mappings():
            if row["geojson"]:
                features.append({
                    "type": "Feature",
                    "properties": {"macro": row["macro"]},
                    "geometry": row["geojson"],
                })
        return {"type": "FeatureCollection", "features": features}
    except Exception as e:
        logger.error("Error en get_macrorregiones: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error consultando macrorregiones: {str(e)}")


@router.get("/smt/resguardos")
async def get_resguardos_geo(db: AsyncSession = Depends(get_db)):
    """GeoJSON of 830 ONIC resguardos with pueblo and disability indicators."""
    try:
        result = await db.execute(text("""
            SELECT r.territorio, r.pueblo_onic, r.dpto_cnmbr, r.mpio_cnmbr,
                   r.mpio_cdpmp, r.ccdgo_terr, r.org_regnal, r.area_pg_ha,
                   COALESCE(dr.tasa_x_1000, d.tasa_x_1000, 0) AS tasa_prevalencia,
                   COALESCE(dr.con_cap_diversas, d.con_disc, 0) AS con_cap_diversas,
                   COALESCE(dr.total_evaluados, d.pob_indigena, 0) AS poblacion,
                   CASE WHEN dr.cod_resguardo IS NOT NULL THEN 'censal'
                        WHEN d.cod_mpio IS NOT NULL THEN 'municipal'
                        ELSE 'sin_dato' END AS fuente_dato,
                   ST_AsGeoJSON(r.geometry)::json AS geojson
            FROM smt_geo.resguardos r
            LEFT JOIN cnpv.disc_resguardo dr
                ON r.ccdgo_terr = dr.cod_resguardo AND dr.periodo = '2018'
            LEFT JOIN cnpv.disc_indigena_mpio d
                ON r.mpio_cdpmp = d.cod_mpio AND d.periodo = '2018'
        """))
        features = []
        for row in result.mappings():
            if row["geojson"]:
                features.append({
                    "type": "Feature",
                    "properties": {
                        "territorio": row["territorio"],
                        "pueblo": row["pueblo_onic"],
                        "departamento": row["dpto_cnmbr"],
                        "municipio": row["mpio_cnmbr"],
                        "cod_mpio": row["mpio_cdpmp"],
                        "cod_resguardo": row["ccdgo_terr"],
                        "organizacion": row["org_regnal"],
                        "area_ha": float(row["area_pg_ha"]) if row["area_pg_ha"] else 0,
                        "tasa_prevalencia": float(row["tasa_prevalencia"]),
                        "con_cap_diversas": int(row["con_cap_diversas"]),
                        "poblacion": int(row["poblacion"]),
                        "fuente_dato": row["fuente_dato"],
                    },
                    "geometry": row["geojson"],
                })
        return {"type": "FeatureCollection", "features": features}
    except Exception as e:
        logger.error("Error en get_resguardos_geo: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error consultando resguardos SMT: {str(e)}")


@router.get("/smt/comunidades")
async def get_comunidades_geo(
    cod_dpto: str | None = Query(None, description="Filtrar por departamento"),
    db: AsyncSession = Depends(get_db),
):
    """GeoJSON of community points, optionally filtered by departamento."""
    try:
        query = """
            SELECT comun_cnmbr, pueblo_onic, dpto_cnmbr, mpio_cnmbr,
                   mpio_cdpmp, personas, viviendas,
                   ST_AsGeoJSON(geometry)::json AS geojson
            FROM smt_geo.comunidades
        """
        params: dict = {}
        if cod_dpto:
            query += " WHERE dpto_ccdgo = :cod_dpto"
            params["cod_dpto"] = cod_dpto
        query += " LIMIT 5000"

        result = await db.execute(text(query), params)
        features = []
        for row in result.mappings():
            if row["geojson"]:
                features.append({
                    "type": "Feature",
                    "properties": {
                        "nombre": row["comun_cnmbr"],
                        "pueblo": row["pueblo_onic"],
                        "departamento": row["dpto_cnmbr"],
                        "municipio": row["mpio_cnmbr"],
                        "personas": row["personas"],
                        "viviendas": row["viviendas"],
                    },
                    "geometry": row["geojson"],
                })
        return {"type": "FeatureCollection", "features": features}
    except Exception as e:
        logger.error("Error en get_comunidades_geo: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error consultando comunidades: {str(e)}")
