"""
Dashboard endpoints - Resumen nacional y panorama general
de personas con capacidades diversas en pueblos indigenas.
"""

import logging
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/")
async def resumen_nacional(
    periodo: str = Query("2018", description="Periodo censal"),
    db: AsyncSession = Depends(get_db),
):
    """Resumen nacional de capacidades diversas por grupo etnico."""
    try:
        result = await db.execute(
            text("""
                SELECT grupo_etnico, pob_total, pob_disc,
                       prevalencia_pct, tasa_x_1000
                FROM cnpv.resumen_nacional_etnico
                WHERE periodo = :periodo
                ORDER BY pob_disc DESC
            """),
            {"periodo": periodo},
        )
        rows = [dict(r._mapping) for r in result]
        if not rows:
            raise HTTPException(status_code=404, detail=f"No hay datos para periodo '{periodo}'")
        return {"periodo": periodo, "data": rows}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error en resumen_nacional: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error consultando resumen nacional: {str(e)}")


@router.get("/prevalencia/departamento")
async def prevalencia_por_departamento(
    periodo: str = Query("2018"),
    grupo_etnico: str | None = Query(None, description="Filtrar por grupo etnico"),
    db: AsyncSession = Depends(get_db),
):
    """Prevalencia de capacidades diversas por grupo etnico y departamento."""
    try:
        params: dict = {"periodo": periodo}
        filtro_etnia = ""
        if grupo_etnico:
            filtro_etnia = "AND p.grupo_etnico = :grupo_etnico"
            params["grupo_etnico"] = grupo_etnico

        result = await db.execute(
            text(f"""
                SELECT p.cod_dpto, d.nom_dpto, p.grupo_etnico,
                       p.pob_total, p.pob_disc, p.pob_no_disc,
                       p.tasa_x_1000, p.prevalencia_pct
                FROM cnpv.prevalencia_etnia_dpto p
                LEFT JOIN geo.departamentos d ON p.cod_dpto = d.cod_dpto
                WHERE p.periodo = :periodo {filtro_etnia}
                ORDER BY p.cod_dpto, p.grupo_etnico
            """),
            params,
        )
        rows = [dict(r._mapping) for r in result]
        return {"periodo": periodo, "total": len(rows), "data": rows}
    except Exception as e:
        logger.error("Error en prevalencia_por_departamento: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error consultando prevalencia por departamento: {str(e)}")


@router.get("/prevalencia/municipio")
async def prevalencia_indigena_municipio(
    periodo: str = Query("2018"),
    cod_dpto: str | None = Query(None, description="Filtrar por departamento"),
    n_min: int = Query(30, description="Poblacion minima para incluir (filtro n>=30)"),
    db: AsyncSession = Depends(get_db),
):
    """Prevalencia de capacidades diversas en poblacion indigena por municipio.
    Solo incluye municipios con pob_indigena >= n_min (default 30).
    """
    try:
        params: dict = {"periodo": periodo, "n_min": n_min}
        filtro_dpto = ""
        if cod_dpto:
            filtro_dpto = "AND p.cod_dpto = :cod_dpto"
            params["cod_dpto"] = cod_dpto

        result = await db.execute(
            text(f"""
                SELECT p.cod_dpto, p.cod_mpio, m.nom_mpio,
                       p.pob_indigena, p.con_disc, p.tasa_x_1000
                FROM cnpv.disc_indigena_mpio p
                LEFT JOIN geo.municipios m ON p.cod_mpio = m.cod_mpio
                WHERE p.periodo = :periodo
                  AND p.pob_indigena >= :n_min
                  {filtro_dpto}
                ORDER BY p.tasa_x_1000 DESC
            """),
            params,
        )
        rows = [dict(r._mapping) for r in result]
        return {"periodo": periodo, "total": len(rows), "data": rows}
    except Exception as e:
        logger.error("Error en prevalencia_indigena_municipio: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error consultando prevalencia por municipio: {str(e)}")


@router.get("/dificultades")
async def dificultades_radar(
    periodo: str = Query("2018"),
    cod_dpto: str | None = Query(None, description="Filtrar por departamento"),
    grupo_etnico: str | None = Query(None, description="Filtrar por grupo etnico"),
    db: AsyncSession = Depends(get_db),
):
    """Datos radar de dificultades (Washington Group) por grupo etnico."""
    try:
        params: dict = {"periodo": periodo}
        filtros = []
        if cod_dpto:
            filtros.append("d.cod_dpto = :cod_dpto")
            params["cod_dpto"] = cod_dpto
        if grupo_etnico:
            filtros.append("d.grupo_etnico = :grupo_etnico")
            params["grupo_etnico"] = grupo_etnico

        where_extra = ("AND " + " AND ".join(filtros)) if filtros else ""

        result = await db.execute(
            text(f"""
                SELECT d.grupo_etnico, d.dificultad,
                       SUM(d.pob_total) AS pob_total,
                       SUM(d.con_dificultad) AS con_dificultad,
                       CASE WHEN SUM(d.pob_total) >= 30
                            THEN ROUND(1000.0 * SUM(d.con_dificultad) / SUM(d.pob_total), 2)
                            ELSE NULL END AS tasa_x_1000
                FROM cnpv.dificultades_etnia_dpto d
                WHERE d.periodo = :periodo {where_extra}
                GROUP BY d.grupo_etnico, d.dificultad
                HAVING SUM(d.pob_total) >= 30
                ORDER BY d.grupo_etnico, d.dificultad
            """),
            params,
        )
        rows = [dict(r._mapping) for r in result]
        return {"periodo": periodo, "data": rows}
    except Exception as e:
        logger.error("Error en dificultades_radar: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error consultando dificultades: {str(e)}")


@router.get("/filtros")
async def filtros_cascada(
    cod_dpto: str | None = Query(None, description="Codigo departamento para filtrar municipios/pueblos/resguardos"),
    cod_mpio: str | None = Query(None, description="Codigo municipio para filtrar pueblos/resguardos"),
    periodo: str = Query("2018"),
    db: AsyncSession = Depends(get_db),
):
    """Endpoint de filtros en cascada.
    - Sin parametros: retorna los 33 departamentos.
    - Con cod_dpto: retorna municipios del departamento + pueblos presentes + resguardos.
    - Con cod_mpio: retorna pueblos del municipio + resguardos del municipio.
    """
    try:
        response: dict = {}

        # Always return departamentos
        dptos_result = await db.execute(
            text("""
                SELECT cod_dpto, nom_dpto
                FROM geo.departamentos
                ORDER BY nom_dpto
            """)
        )
        response["departamentos"] = [dict(r._mapping) for r in dptos_result]

        # If departamento selected, return its municipios
        if cod_dpto:
            mpios_result = await db.execute(
                text("""
                    SELECT cod_mpio, nom_mpio, cod_dpto
                    FROM geo.municipios
                    WHERE cod_dpto = :cod_dpto
                    ORDER BY nom_mpio
                """),
                {"cod_dpto": cod_dpto},
            )
            response["municipios"] = [dict(r._mapping) for r in mpios_result]

            # Pueblos present in that department
            pueblos_dpto_result = await db.execute(
                text("""
                    SELECT DISTINCT d.cod_pueblo, d.pueblo
                    FROM pueblo.disc_dpto d
                    WHERE d.cod_dpto = :cod_dpto AND d.periodo = :periodo AND d.total >= 30
                    ORDER BY d.pueblo
                """),
                {"cod_dpto": cod_dpto, "periodo": periodo},
            )
            response["pueblos"] = [dict(r._mapping) for r in pueblos_dpto_result]

            # Resguardos in that department (smt_geo + visor_dane population)
            resg_result = await db.execute(
                text("""
                    SELECT DISTINCT
                        g.ccdgo_terr AS cod_resguardo,
                        g.territorio AS nombre,
                        g.pueblo_onic,
                        g.dpto_cnmbr AS nom_departamento,
                        g.mpio_cnmbr AS nom_municipio,
                        g.mpio_cdpmp AS cod_mpio,
                        agg.poblacion_total
                    FROM smt_geo.resguardos g
                    LEFT JOIN (
                        SELECT SUBSTRING(v.resguardo FROM '\\((\\d+)\\)') AS cod,
                               SUM(v.poblacion) AS poblacion_total
                        FROM visor_dane.resguardo_pueblo v
                        WHERE v.poblacion > 0
                        GROUP BY SUBSTRING(v.resguardo FROM '\\((\\d+)\\)')
                    ) agg ON g.ccdgo_terr = agg.cod
                    WHERE g.mpio_cdpmp LIKE :cod_dpto_prefix
                    ORDER BY g.territorio
                """),
                {"cod_dpto_prefix": f"{cod_dpto}%"},
            )
            response["resguardos"] = [dict(r._mapping) for r in resg_result]

        # If municipio selected, override pueblos with municipio-level data
        if cod_mpio:
            pueblos_mpio_result = await db.execute(
                text("""
                    SELECT pm.cod_pueblo, pm.pueblo, pm.poblacion,
                           pm.pct_en_mpio, pm.es_dominante
                    FROM pueblo.pueblo_municipio pm
                    WHERE pm.cod_mpio = :cod_mpio AND pm.periodo = :periodo
                    ORDER BY pm.poblacion DESC
                """),
                {"cod_mpio": cod_mpio, "periodo": periodo},
            )
            response["pueblos"] = [dict(r._mapping) for r in pueblos_mpio_result]

            # Resguardos in that municipio (smt_geo + visor_dane population)
            resg_mpio_result = await db.execute(
                text("""
                    SELECT DISTINCT
                        g.ccdgo_terr AS cod_resguardo,
                        g.territorio AS nombre,
                        g.pueblo_onic,
                        g.dpto_cnmbr AS nom_departamento,
                        g.mpio_cnmbr AS nom_municipio,
                        g.mpio_cdpmp AS cod_mpio,
                        agg.poblacion_total
                    FROM smt_geo.resguardos g
                    LEFT JOIN (
                        SELECT SUBSTRING(v.resguardo FROM '\\((\\d+)\\)') AS cod,
                               SUM(v.poblacion) AS poblacion_total
                        FROM visor_dane.resguardo_pueblo v
                        WHERE v.poblacion > 0
                        GROUP BY SUBSTRING(v.resguardo FROM '\\((\\d+)\\)')
                    ) agg ON g.ccdgo_terr = agg.cod
                    WHERE g.mpio_cdpmp = :cod_mpio
                    ORDER BY g.territorio
                """),
                {"cod_mpio": cod_mpio},
            )
            response["resguardos"] = [dict(r._mapping) for r in resg_mpio_result]

        return response
    except Exception as e:
        logger.error("Error en filtros_cascada: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error consultando filtros: {str(e)}")


@router.get("/brecha")
async def brecha_certificacion(
    cod_dpto: str = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Brecha de certificacion: poblacion vs registrados vs certificados."""
    try:
        params = {}
        dpto_filter = ""
        if cod_dpto:
            dpto_filter = "AND p.cod_dpto = :cod_dpto"
            params["cod_dpto"] = cod_dpto

        # Step 1: Total indigenous population
        r1 = await db.execute(text(f"""
            SELECT COALESCE(SUM(pob_total), 0) as pob_total,
                   COALESCE(SUM(pob_disc), 0) as pob_disc
            FROM cnpv.prevalencia_etnia_dpto p
            WHERE p.grupo_etnico = 'Indigena' AND p.periodo = '2018'
            {dpto_filter}
        """), params)
        row1 = dict(r1.first()._mapping)

        # Step 2: RLCPD registered (from ext.rlcpd_nacional)
        rlcpd_filter = ""
        if cod_dpto:
            rlcpd_filter = f"AND departamento_registro LIKE '{cod_dpto} -%'"
        r2 = await db.execute(text(f"""
            SELECT COALESCE(SUM(num_personas), 0) as registrados
            FROM ext.rlcpd_nacional
            WHERE 1=1 {rlcpd_filter}
        """))
        registrados = r2.scalar() or 0

        # Step 3: SMT characterized
        r3 = await db.execute(text("SELECT COUNT(*) FROM smt.caracterizacion"))
        smt_count = r3.scalar() or 0

        # Estimate indigenous proportion of RLCPD (~15% nationally)
        rlcpd_indigena = int(registrados * 0.15)
        certificados = int(smt_count * 0.41) if smt_count > 0 else 0

        return {
            "cod_dpto": cod_dpto,
            "pasos": [
                {"label": "Poblacion indigena total", "valor": int(row1["pob_total"]), "fuente": "CNPV 2018"},
                {"label": "Con capacidades diversas", "valor": int(row1["pob_disc"]), "fuente": "CNPV 2018"},
                {"label": "Registrados RLCPD (est. indigena)", "valor": rlcpd_indigena, "fuente": "RLCPD/MinSalud"},
                {"label": "Caracterizados SMT-ONIC", "valor": smt_count if not cod_dpto else 0, "fuente": "SMT-ONIC 2026"},
                {"label": "Con certificado oficial (est.)", "valor": certificados if not cod_dpto else 0, "fuente": "SMT-ONIC, calculado"},
            ]
        }
    except Exception as e:
        logger.error("Error en brecha_certificacion: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error consultando brecha de certificacion: {str(e)}")


@router.get("/salud")
async def salud_embudo(
    periodo: str = Query("2018"),
    cod_dpto: str | None = Query(None, description="Filtrar por departamento"),
    db: AsyncSession = Depends(get_db),
):
    """Datos de acceso a salud (embudo) por grupo etnico."""
    try:
        params: dict = {"periodo": periodo}
        filtro_dpto = ""
        if cod_dpto:
            filtro_dpto = "AND s.cod_dpto = :cod_dpto"
            params["cod_dpto"] = cod_dpto

        result = await db.execute(
            text(f"""
                SELECT s.grupo_etnico, s.variable, s.categoria,
                       SUM(s.valor) AS valor,
                       SUM(s.total_grupo) AS total_grupo
                FROM cnpv.salud_etnia_dpto s
                WHERE s.periodo = :periodo {filtro_dpto}
                GROUP BY s.grupo_etnico, s.variable, s.categoria
                ORDER BY s.grupo_etnico, s.variable, s.categoria
            """),
            params,
        )
        rows = [dict(r._mapping) for r in result]
        return {"periodo": periodo, "data": rows}
    except Exception as e:
        logger.error("Error en salud_embudo: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error consultando datos de salud: {str(e)}")


@router.get("/intercensal")
async def comparacion_intercensal(
    grupo_etnico: str = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Comparacion intercensal 2005 vs 2018 para series de tiempo."""
    try:
        filtro = ""
        params = {}
        if grupo_etnico:
            filtro = "WHERE grupo_etnico = :grupo_etnico"
            params["grupo_etnico"] = grupo_etnico
        result = await db.execute(
            text(f"""
                SELECT grupo_etnico, periodo, pob_total, pob_disc,
                       prevalencia_pct, tasa_x_1000
                FROM cnpv.comparacion_intercensal
                {filtro}
                ORDER BY grupo_etnico, periodo
            """),
            params,
        )
        rows = [dict(r._mapping) for r in result]
        return {"total": len(rows), "data": rows}
    except Exception as e:
        logger.error("Error en intercensal: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/smt-resumen")
async def smt_resumen(
    dimension: str = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Resumen de datos propios SMT-ONIC."""
    try:
        filtro = ""
        params = {"periodo": "2026-F1"}
        if dimension:
            filtro = "AND dimension = :dimension"
            params["dimension"] = dimension
        result = await db.execute(
            text(f"""
                SELECT dimension, categoria, valor, pct
                FROM smt.resumen
                WHERE periodo = :periodo {filtro}
                ORDER BY dimension, valor DESC
            """),
            params,
        )
        rows = [dict(r._mapping) for r in result]
        return {"periodo": "2026-F1", "total": len(rows), "data": rows}
    except Exception as e:
        logger.error("Error en smt_resumen: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
