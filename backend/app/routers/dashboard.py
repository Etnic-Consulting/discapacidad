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

        # Step 3: SMT characterized — legacy caracterizacion + formulario nuevo
        # Filtra por depto si aplica (caracterizacion tiene cod_dpto, respuestas_formulario tambien)
        smt_params = {}
        if cod_dpto:
            smt_filter_car = "WHERE LEFT(cod_mpio, 2) = :cod_dpto"
            smt_filter_resp = "WHERE cod_dpto = :cod_dpto AND cpli_consentimiento = 'si'"
            smt_params["cod_dpto"] = cod_dpto
        else:
            smt_filter_car = ""
            smt_filter_resp = "WHERE cpli_consentimiento = 'si'"
        r3 = await db.execute(text(f"""
            SELECT
              (SELECT COUNT(*) FROM smt.caracterizacion {smt_filter_car})
              + (SELECT COUNT(*) FROM smt.respuestas_formulario {smt_filter_resp})
            AS total
        """), smt_params)
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
                {"label": "Caracterizados SMT-ONIC", "valor": smt_count, "fuente": "SMT-ONIC 2026"},
                {"label": "Con certificado oficial (est.)", "valor": certificados, "fuente": "SMT-ONIC, calculado"},
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


@router.get("/panorama-kpis")
async def panorama_kpis(
    cod_dpto: str | None = Query(None),
    cod_mpio: str | None = Query(None),
    cod_pueblo: str | None = Query(None),
    cod_resguardo: str | None = Query(None),
    cod_macro: str | None = Query(None, description="Macrorregión ONIC (NORTE, OCCIDENTE, CENTRO - ORIENTE, AMAZONIA, ORINOQUIA)"),
    db: AsyncSession = Depends(get_db),
):
    """KPIs consolidados del Panorama. Filtrables por macro/dpto/mpio/pueblo/resguardo.

    Fuentes:
      - total_personas / prevalencia / pob_total: cnpv.prevalencia_etnia_* / pueblo.disc_nacional / cnpv.disc_resguardo;
        para macro se agrega via smt_geo.resguardos (mpios de la zona).
      - pueblos: count distinct pueblo.pueblo_municipio dentro del scope
      - caracterizados_smt / cobertura_smt: smt.respuestas_formulario con cpli='si' (live source),
        filtrado por cod_dpto/cod_mpio/cod_pueblo o por mpios del resguardo/macro
      - brecha_certificacion: calculado en vivo desde respuestas_formulario cert_cd
      - victimas_conflicto / pueblos_con_victimas: victimas.universo filtrable
    """
    try:
        # --- pob_total, pob_disc, tasa segun nivel ---
        total_personas = 0
        pob_total = 0
        prevalencia = 0.0
        scope = "nacional"
        resguardo_mpios: list[str] = []
        macro_mpios: list[str] = []

        # Si se pasó cod_macro, resolver lista de mpios de la zona (usa smt_geo.resguardos.macro)
        if cod_macro:
            r = await db.execute(
                text("""
                    SELECT DISTINCT mpio_cdpmp
                    FROM smt_geo.resguardos
                    WHERE UPPER(TRIM(macro)) = UPPER(TRIM(:cm))
                      AND mpio_cdpmp IS NOT NULL
                """),
                {"cm": cod_macro},
            )
            macro_mpios = [x[0] for x in r.fetchall()]

        resguardo_pueblo_onic: str | None = None
        # cod_macro tiene precedencia más baja que dpto/mpio/pueblo/resguardo
        if cod_resguardo:
            scope = "resguardo"
            r = await db.execute(
                text("""
                    SELECT con_cap_diversas, pob_total_visor, tasa_x_1000
                    FROM cnpv.disc_resguardo
                    WHERE cod_resguardo = :cr AND periodo = '2018'
                    LIMIT 1
                """),
                {"cr": cod_resguardo},
            )
            row = r.first()
            if row:
                total_personas = int(row[0] or 0)
                pob_total = int(row[1] or 0)
                prevalencia = float(row[2] or 0)
            rm = await db.execute(
                text("""
                    SELECT DISTINCT mpio_cdpmp, pueblo_onic
                    FROM smt_geo.resguardos
                    WHERE ccdgo_terr = :cr
                """),
                {"cr": cod_resguardo},
            )
            rows_sg = rm.fetchall()
            resguardo_mpios = [x[0] for x in rows_sg if x[0]]
            for x in rows_sg:
                if x[1]:
                    resguardo_pueblo_onic = x[1]
                    break
        elif cod_pueblo:
            scope = "pueblo"
            r = await db.execute(
                text("""
                    SELECT COALESCE(SUM(poblacion),0) AS pob_total
                    FROM pueblo.pueblo_municipio
                    WHERE cod_pueblo::text = :cp
                """),
                {"cp": cod_pueblo},
            )
            row = r.first()
            pob_total = int(row[0] or 0) if row else 0
            r2 = await db.execute(
                text("""
                    SELECT con_discapacidad, total, tasa_x_1000
                    FROM pueblo.disc_nacional
                    WHERE cod_pueblo::text = :cp AND periodo = '2018'
                    LIMIT 1
                """),
                {"cp": cod_pueblo},
            )
            row2 = r2.first()
            if row2:
                total_personas = int(row2[0] or 0)
                pob_total = int(row2[1] or 0) or pob_total
                prevalencia = float(row2[2] or 0)
        elif cod_mpio:
            scope = "mpio"
            r = await db.execute(
                text("""
                    SELECT pob_total, pob_disc, tasa_x_1000
                    FROM cnpv.prevalencia_etnia_mpio
                    WHERE cod_mpio = :cm AND grupo_etnico = 'Indigena' AND periodo = '2018'
                    LIMIT 1
                """),
                {"cm": cod_mpio},
            )
            row = r.first()
            if row:
                pob_total = int(row[0] or 0)
                total_personas = int(row[1] or 0)
                prevalencia = float(row[2] or 0)
        elif cod_dpto:
            scope = "dpto"
            r = await db.execute(
                text("""
                    SELECT pob_total, pob_disc, tasa_x_1000
                    FROM cnpv.prevalencia_etnia_dpto
                    WHERE cod_dpto = :cd AND grupo_etnico = 'Indigena' AND periodo = '2018'
                    LIMIT 1
                """),
                {"cd": cod_dpto},
            )
            row = r.first()
            if row:
                pob_total = int(row[0] or 0)
                total_personas = int(row[1] or 0)
                prevalencia = float(row[2] or 0)
        elif cod_macro and macro_mpios:
            scope = "macro"
            r = await db.execute(
                text("""
                    SELECT COALESCE(SUM(pob_total),0)  AS pob_total,
                           COALESCE(SUM(pob_disc),0)   AS pob_disc
                    FROM cnpv.prevalencia_etnia_mpio
                    WHERE cod_mpio = ANY(:mpios)
                      AND grupo_etnico = 'Indigena'
                      AND periodo = '2018'
                """),
                {"mpios": macro_mpios},
            )
            row = r.first()
            if row:
                pob_total = int(row[0] or 0)
                total_personas = int(row[1] or 0)
                prevalencia = round(1000.0 * total_personas / pob_total, 2) if pob_total else 0.0
        else:
            r = await db.execute(
                text("""
                    SELECT pob_total, pob_disc, tasa_x_1000
                    FROM cnpv.resumen_nacional_etnico
                    WHERE grupo_etnico = 'Indigena' AND periodo = '2018'
                    LIMIT 1
                """)
            )
            row = r.first()
            if row:
                pob_total = int(row[0] or 0)
                total_personas = int(row[1] or 0)
                prevalencia = float(row[2] or 0)

        # --- pueblos (count distinct) ---
        if cod_resguardo:
            if resguardo_mpios:
                r = await db.execute(
                    text("""
                        SELECT COUNT(DISTINCT cod_pueblo)
                        FROM pueblo.pueblo_municipio
                        WHERE cod_mpio = ANY(:mpios) AND periodo = '2018' AND poblacion > 0
                    """),
                    {"mpios": resguardo_mpios},
                )
                pueblos_count = int(r.scalar() or 0)
            else:
                pueblos_count = 0
        elif cod_pueblo:
            pueblos_count = 1
        elif cod_mpio:
            r = await db.execute(
                text("""
                    SELECT COUNT(DISTINCT cod_pueblo)
                    FROM pueblo.pueblo_municipio
                    WHERE cod_mpio = :cm AND periodo = '2018'
                """),
                {"cm": cod_mpio},
            )
            pueblos_count = int(r.scalar() or 0)
        elif cod_dpto:
            r = await db.execute(
                text("""
                    SELECT COUNT(DISTINCT cod_pueblo)
                    FROM pueblo.pueblo_municipio
                    WHERE LEFT(cod_mpio::text, 2) = :cd AND periodo = '2018'
                """),
                {"cd": cod_dpto},
            )
            pueblos_count = int(r.scalar() or 0)
        elif cod_macro and macro_mpios:
            r = await db.execute(
                text("""
                    SELECT COUNT(DISTINCT cod_pueblo)
                    FROM pueblo.pueblo_municipio
                    WHERE cod_mpio = ANY(:mpios) AND periodo = '2018' AND poblacion > 0
                """),
                {"mpios": macro_mpios},
            )
            pueblos_count = int(r.scalar() or 0)
        else:
            r = await db.execute(
                text("""
                    SELECT COUNT(DISTINCT cod_pueblo)
                    FROM pueblo.pueblo_municipio
                    WHERE periodo = '2018'
                """)
            )
            pueblos_count = int(r.scalar() or 0)

        # --- caracterizados SMT y brecha certificacion ---
        # Fuente en vivo: smt.respuestas_formulario (consentimiento 'si').
        # A medida que entren formularios web, los KPIs se recalculan automaticamente.
        # Aplicable a TODOS los scopes (nacional / macro / dpto / mpio / pueblo / resguardo).
        s_params: dict = {}
        s_filtros = ["cpli_consentimiento = 'si'"]
        if cod_resguardo and resguardo_mpios:
            s_filtros.append("cod_mpio = ANY(:rmpios)")
            s_params["rmpios"] = resguardo_mpios
        if cod_macro and macro_mpios and not cod_resguardo:
            s_filtros.append("cod_mpio = ANY(:mmpios)")
            s_params["mmpios"] = macro_mpios
        if cod_dpto:
            s_filtros.append("cod_dpto = :cd")
            s_params["cd"] = cod_dpto
        if cod_mpio:
            s_filtros.append("cod_mpio = :cm")
            s_params["cm"] = cod_mpio
        if cod_pueblo:
            s_filtros.append("cod_pueblo = :cp")
            s_params["cp"] = cod_pueblo
        s_where = "WHERE " + " AND ".join(s_filtros)

        r = await db.execute(
            text(f"SELECT COUNT(*) FROM smt.respuestas_formulario {s_where}"),
            s_params,
        )
        caracterizados_smt = int(r.scalar() or 0)

        # Cobertura: caracterizados_smt como % de personas con capacidades diversas en el scope
        cobertura_smt = (
            round(caracterizados_smt / total_personas * 100, 2)
            if total_personas
            else None
        )

        # Brecha de certificacion: % de respuestas con cert_cd vacio o distinto de 'si'
        # Sobre el universo caracterizado en el scope. Si caracterizados_smt = 0, brecha = None.
        if caracterizados_smt > 0:
            r = await db.execute(
                text(f"""
                    SELECT
                      COUNT(*) FILTER (
                        WHERE COALESCE(NULLIF(TRIM(LOWER(datos->>'cert_cd')), ''), 'sin_dato')
                              NOT IN ('si','sí','yes','true')
                      ) AS sin_cert
                    FROM smt.respuestas_formulario {s_where}
                """),
                s_params,
            )
            sin_cert = int(r.scalar() or 0)
            brecha_certificacion = round(100.0 * sin_cert / caracterizados_smt, 2)
        else:
            brecha_certificacion = None

        # --- victimas conflicto (filtrable) ---
        v_params: dict = {}
        v_filtros = []
        if cod_resguardo and resguardo_mpios:
            v_filtros.append("cod_mpio_ocurrencia = ANY(:rmpios)")
            v_params["rmpios"] = resguardo_mpios
        if cod_macro and macro_mpios and not cod_resguardo:
            v_filtros.append("cod_mpio_ocurrencia = ANY(:vmmpios)")
            v_params["vmmpios"] = macro_mpios
        if cod_dpto:
            v_filtros.append("LEFT(cod_mpio_ocurrencia, 2) = :cd")
            v_params["cd"] = cod_dpto
        if cod_mpio:
            v_filtros.append("cod_mpio_ocurrencia = :cm")
            v_params["cm"] = cod_mpio
        if cod_pueblo:
            v_filtros.append("cod_pueblo_imputado = :cp")
            v_params["cp"] = cod_pueblo
        v_where = ("WHERE " + " AND ".join(v_filtros)) if v_filtros else ""
        r = await db.execute(
            text(f"SELECT COUNT(*) FROM victimas.universo {v_where}"),
            v_params,
        )
        victimas_conflicto = int(r.scalar() or 0)

        r = await db.execute(
            text(f"""
                SELECT COUNT(DISTINCT pueblo_imputado)
                FROM victimas.universo
                {v_where}
                {'AND' if v_filtros else 'WHERE'} pueblo_imputado IS NOT NULL
            """),
            v_params,
        )
        pueblos_con_victimas = int(r.scalar() or 0)

        return {
            "scope": scope,
            "filtros": {
                "cod_dpto": cod_dpto,
                "cod_mpio": cod_mpio,
                "cod_pueblo": cod_pueblo,
                "cod_resguardo": cod_resguardo,
                "cod_macro": cod_macro,
            },
            "total_personas": total_personas,
            "pob_total": pob_total,
            "pueblos": pueblos_count,
            "prevalencia": round(prevalencia, 2),
            "caracterizados_smt": caracterizados_smt,
            "cobertura_smt": cobertura_smt,
            "brecha_certificacion": brecha_certificacion,
            "victimas_conflicto": victimas_conflicto,
            "pueblos_con_victimas": pueblos_con_victimas,
        }
    except Exception as e:
        logger.error("Error en panorama_kpis: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error consultando KPIs: {str(e)}")
