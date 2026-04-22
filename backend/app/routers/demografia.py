"""
Demografia - Indicadores demograficos del Visor DANE por pueblo indigena.
NBI, IPM, lengua, educacion, vivienda, perfil compuesto e ICV.
"""

import logging
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# GET /nbi — NBI + IPM para todos los pueblos (o filtrado por cod_pueblo)
# ---------------------------------------------------------------------------
@router.get("/nbi")
async def nbi_pueblos(
    cod_pueblo: int | None = Query(None, description="Filtrar por codigo de pueblo"),
    db: AsyncSession = Depends(get_db),
):
    """NBI e IPM para todos los pueblos o uno especifico.
    Cruza visor_dane.nbi_pueblo con visor_dane.ipm_pueblo y
    obtiene el nombre desde visor_dane.poblacion_pueblo.
    """
    try:
        params: dict = {}
        filtro = ""
        if cod_pueblo is not None:
            filtro = "AND n.cod_pueblo = :cod_pueblo"
            params["cod_pueblo"] = cod_pueblo

        result = await db.execute(
            text(f"""
                SELECT
                    n.cod_pueblo,
                    p.pueblo,
                    p.poblacion_2018,
                    n.pct_nbi,
                    n.pct_miseria,
                    n.nbi_vivienda,
                    n.nbi_servicios,
                    n.nbi_hacinamiento,
                    n.nbi_inasistencia,
                    n.nbi_dependencia,
                    n.total_personas,
                    i.ipm,
                    i.sin_privacion,
                    i.ipm_cabecera,
                    i.ipm_resto
                FROM visor_dane.nbi_pueblo n
                LEFT JOIN visor_dane.ipm_pueblo i
                    ON n.cod_pueblo = i.cod_pueblo
                LEFT JOIN visor_dane.poblacion_pueblo p
                    ON n.cod_pueblo = p.cod_pueblo AND p.cod_pueblo != 1
                WHERE n.cod_pueblo != 1 {filtro}
                ORDER BY n.pct_nbi DESC
            """),
            params,
        )
        rows = [dict(r._mapping) for r in result]
        if cod_pueblo is not None and not rows:
            raise HTTPException(
                status_code=404,
                detail=f"Pueblo con codigo '{cod_pueblo}' no encontrado en datos NBI",
            )
        return {"total": len(rows), "data": rows}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error en nbi_pueblos: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error consultando NBI: {str(e)}")


# ---------------------------------------------------------------------------
# GET /nbi/{cod_pueblo} — NBI detallado con desglose por area
# ---------------------------------------------------------------------------
@router.get("/nbi/{cod_pueblo}")
async def nbi_detalle(
    cod_pueblo: int,
    db: AsyncSession = Depends(get_db),
):
    """NBI detallado para un pueblo, incluyendo desglose cabecera/resto."""
    try:
        # General NBI
        general = await db.execute(
            text("""
                SELECT
                    n.cod_pueblo, p.pueblo,
                    n.pct_nbi, n.pct_miseria,
                    n.nbi_vivienda, n.nbi_servicios,
                    n.nbi_hacinamiento, n.nbi_inasistencia,
                    n.nbi_dependencia, n.total_personas,
                    i.ipm, i.sin_privacion, i.ipm_cabecera, i.ipm_resto
                FROM visor_dane.nbi_pueblo n
                LEFT JOIN visor_dane.ipm_pueblo i ON n.cod_pueblo = i.cod_pueblo
                LEFT JOIN visor_dane.poblacion_pueblo p
                    ON n.cod_pueblo = p.cod_pueblo AND p.cod_pueblo != 1
                WHERE n.cod_pueblo = :cod_pueblo
            """),
            {"cod_pueblo": cod_pueblo},
        )
        gen_row = general.first()
        if not gen_row:
            raise HTTPException(
                status_code=404,
                detail=f"Pueblo con codigo '{cod_pueblo}' no encontrado en datos NBI",
            )
        gen_data = dict(gen_row._mapping)

        # NBI por area (1=cabecera, 4=resto)
        areas = await db.execute(
            text("""
                SELECT
                    area,
                    CASE area WHEN '1' THEN 'Cabecera' WHEN '4' THEN 'Resto' ELSE area END AS area_nombre,
                    pct_nbi, pct_miseria,
                    nbi_vivienda, nbi_servicios,
                    nbi_hacinamiento, nbi_inasistencia,
                    nbi_dependencia, total_personas
                FROM visor_dane.nbi_pueblo_area
                WHERE cod_pueblo = :cod_pueblo
                ORDER BY area
            """),
            {"cod_pueblo": cod_pueblo},
        )
        areas_data = [dict(r._mapping) for r in areas]

        return {
            "cod_pueblo": cod_pueblo,
            "general": gen_data,
            "por_area": areas_data,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error en nbi_detalle('%s'): %s", cod_pueblo, e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error consultando NBI detalle: {str(e)}")


# ---------------------------------------------------------------------------
# GET /lengua — Vitalidad linguistica de todos los pueblos
# ---------------------------------------------------------------------------
@router.get("/lengua")
async def lengua_pueblos(
    cod_pueblo: int | None = Query(None, description="Filtrar por codigo de pueblo"),
    db: AsyncSession = Depends(get_db),
):
    """Vitalidad linguistica: % que habla, % que solo entiende, % que no habla ni entiende."""
    try:
        params: dict = {}
        filtro = ""
        if cod_pueblo is not None:
            filtro = "AND cod_pueblo = :cod_pueblo"
            params["cod_pueblo"] = cod_pueblo

        result = await db.execute(
            text(f"""
                WITH totales AS (
                    SELECT
                        cod_pueblo,
                        SUM(poblacion) AS pob_total
                    FROM visor_dane.lengua_pueblo
                    WHERE cod_pueblo != 1 {filtro}
                    GROUP BY cod_pueblo
                ),
                habla AS (
                    SELECT
                        cod_pueblo,
                        SUM(poblacion) AS pob_habla
                    FROM visor_dane.lengua_pueblo
                    WHERE habla_lengua = 'Sí'
                       AND cod_pueblo != 1 {filtro}
                    GROUP BY cod_pueblo
                ),
                solo_entiende AS (
                    SELECT
                        cod_pueblo,
                        SUM(poblacion) AS pob_entiende
                    FROM visor_dane.lengua_pueblo
                    WHERE habla_lengua = 'No' AND entiende_lengua = 'Sí'
                       AND cod_pueblo != 1 {filtro}
                    GROUP BY cod_pueblo
                ),
                no_habla_ni_entiende AS (
                    SELECT
                        cod_pueblo,
                        SUM(poblacion) AS pob_no
                    FROM visor_dane.lengua_pueblo
                    WHERE habla_lengua = 'No' AND entiende_lengua = 'No'
                       AND cod_pueblo != 1 {filtro}
                    GROUP BY cod_pueblo
                )
                SELECT
                    t.cod_pueblo,
                    p.pueblo,
                    t.pob_total,
                    COALESCE(h.pob_habla, 0) AS pob_habla,
                    COALESCE(se.pob_entiende, 0) AS pob_solo_entiende,
                    COALESCE(nh.pob_no, 0) AS pob_no_habla_ni_entiende,
                    CASE WHEN t.pob_total > 0
                        THEN ROUND(100.0 * COALESCE(h.pob_habla, 0) / t.pob_total, 2)
                        ELSE 0 END AS pct_habla,
                    CASE WHEN t.pob_total > 0
                        THEN ROUND(100.0 * COALESCE(se.pob_entiende, 0) / t.pob_total, 2)
                        ELSE 0 END AS pct_solo_entiende,
                    CASE WHEN t.pob_total > 0
                        THEN ROUND(100.0 * COALESCE(nh.pob_no, 0) / t.pob_total, 2)
                        ELSE 0 END AS pct_no_habla_ni_entiende
                FROM totales t
                LEFT JOIN habla h ON t.cod_pueblo = h.cod_pueblo
                LEFT JOIN solo_entiende se ON t.cod_pueblo = se.cod_pueblo
                LEFT JOIN no_habla_ni_entiende nh ON t.cod_pueblo = nh.cod_pueblo
                LEFT JOIN visor_dane.poblacion_pueblo p
                    ON t.cod_pueblo = p.cod_pueblo AND p.cod_pueblo != 1
                ORDER BY pct_habla DESC
            """),
            params,
        )
        rows = [dict(r._mapping) for r in result]
        return {"total": len(rows), "data": rows}
    except Exception as e:
        logger.error("Error en lengua_pueblos: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error consultando vitalidad linguistica: {str(e)}")


# ---------------------------------------------------------------------------
# GET /educacion/{cod_pueblo} — Educacion y alfabetismo
# ---------------------------------------------------------------------------
@router.get("/educacion/{cod_pueblo}")
async def educacion_pueblo(
    cod_pueblo: int,
    db: AsyncSession = Depends(get_db),
):
    """Educacion (nivel educativo) y alfabetismo para un pueblo."""
    try:
        # Verificar pueblo
        check = await db.execute(
            text("""
                SELECT pueblo FROM visor_dane.poblacion_pueblo
                WHERE cod_pueblo = :cod_pueblo AND cod_pueblo != 1
            """),
            {"cod_pueblo": cod_pueblo},
        )
        check_row = check.first()
        if not check_row:
            raise HTTPException(status_code=404, detail=f"Pueblo '{cod_pueblo}' no encontrado")
        pueblo_nombre = check_row._mapping["pueblo"]

        # Nivel educativo agregado (sin desglose por sexo/edad)
        educacion = await db.execute(
            text("""
                SELECT
                    nivel_educativo,
                    SUM(poblacion_2018) AS poblacion
                FROM visor_dane.educacion_pueblo
                WHERE cod_pueblo = :cod_pueblo
                  AND nivel_educativo IS NOT NULL
                  AND nivel_educativo != ''
                GROUP BY nivel_educativo
                ORDER BY poblacion DESC
            """),
            {"cod_pueblo": cod_pueblo},
        )
        edu_data = [dict(r._mapping) for r in educacion]

        # Alfabetismo agregado
        alfabetismo = await db.execute(
            text("""
                SELECT
                    alfabetismo,
                    SUM(poblacion_2018) AS poblacion
                FROM visor_dane.alfabetismo_pueblo
                WHERE cod_pueblo = :cod_pueblo
                  AND alfabetismo IS NOT NULL
                  AND alfabetismo != ''
                GROUP BY alfabetismo
                ORDER BY poblacion DESC
            """),
            {"cod_pueblo": cod_pueblo},
        )
        alfa_data = [dict(r._mapping) for r in alfabetismo]

        # Calcular tasa alfabetismo
        total_alfa = sum(r["poblacion"] for r in alfa_data)
        si_alfa = sum(r["poblacion"] for r in alfa_data if r["alfabetismo"] == "Sí")
        tasa_alfabetismo = round(100.0 * si_alfa / total_alfa, 2) if total_alfa > 0 else None

        return {
            "cod_pueblo": cod_pueblo,
            "pueblo": pueblo_nombre,
            "educacion": edu_data,
            "alfabetismo": alfa_data,
            "tasa_alfabetismo": tasa_alfabetismo,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error en educacion_pueblo('%s'): %s", cod_pueblo, e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error consultando educacion: {str(e)}")


# ---------------------------------------------------------------------------
# GET /vivienda/{cod_pueblo} — Vivienda y servicios
# ---------------------------------------------------------------------------
@router.get("/vivienda/{cod_pueblo}")
async def vivienda_pueblo(
    cod_pueblo: int,
    db: AsyncSession = Depends(get_db),
):
    """Tipo de vivienda, materiales y acceso a servicios para un pueblo."""
    try:
        # Verificar pueblo
        check = await db.execute(
            text("""
                SELECT pueblo FROM visor_dane.poblacion_pueblo
                WHERE cod_pueblo = :cod_pueblo AND cod_pueblo != 1
            """),
            {"cod_pueblo": cod_pueblo},
        )
        check_row = check.first()
        if not check_row:
            raise HTTPException(status_code=404, detail=f"Pueblo '{cod_pueblo}' no encontrado")
        pueblo_nombre = check_row._mapping["pueblo"]

        # Tipo de vivienda
        tipo_viv = await db.execute(
            text("""
                SELECT tipo_vivienda, poblacion_2018 AS poblacion
                FROM visor_dane.tipo_vivienda_pueblo
                WHERE cod_pueblo = :cod_pueblo
                  AND tipo_vivienda IS NOT NULL AND tipo_vivienda != ''
                ORDER BY poblacion_2018 DESC
            """),
            {"cod_pueblo": cod_pueblo},
        )
        tipo_data = [dict(r._mapping) for r in tipo_viv]

        # Materiales de vivienda
        materiales = await db.execute(
            text("""
                SELECT tipo_material, material, poblacion_2018 AS poblacion
                FROM visor_dane.material_vivienda_pueblo
                WHERE cod_pueblo = :cod_pueblo
                  AND material IS NOT NULL AND material != ''
                ORDER BY tipo_material, poblacion_2018 DESC
            """),
            {"cod_pueblo": cod_pueblo},
        )
        mat_data = [dict(r._mapping) for r in materiales]

        # Servicios publicos
        servicios = await db.execute(
            text("""
                SELECT servicio, tiene, SUM(poblacion_2018) AS poblacion
                FROM visor_dane.servicios_vivienda_pueblo
                WHERE cod_pueblo = :cod_pueblo
                  AND tiene IS NOT NULL AND tiene != ''
                GROUP BY servicio, tiene
                ORDER BY servicio, tiene
            """),
            {"cod_pueblo": cod_pueblo},
        )
        serv_rows = [dict(r._mapping) for r in servicios]

        # Calcular % sin servicio por tipo
        sin_servicio = {}
        for s in serv_rows:
            srv = s["servicio"]
            if srv not in sin_servicio:
                sin_servicio[srv] = {"si": 0, "no": 0}
            if s["tiene"] == "Sí":
                sin_servicio[srv]["si"] += s["poblacion"]
            elif s["tiene"] == "No":
                sin_servicio[srv]["no"] += s["poblacion"]

        resumen_servicios = []
        for srv, vals in sin_servicio.items():
            total = vals["si"] + vals["no"]
            pct_sin = round(100.0 * vals["no"] / total, 2) if total > 0 else None
            resumen_servicios.append({
                "servicio": srv,
                "con_servicio": vals["si"],
                "sin_servicio": vals["no"],
                "pct_sin_servicio": pct_sin,
            })

        # % vivienda tradicional
        total_viv = sum(t["poblacion"] for t in tipo_data)
        trad = sum(
            t["poblacion"] for t in tipo_data
            if "tradicional ind" in (t["tipo_vivienda"] or "").lower()
        )
        pct_tradicional = round(100.0 * trad / total_viv, 2) if total_viv > 0 else None

        return {
            "cod_pueblo": cod_pueblo,
            "pueblo": pueblo_nombre,
            "tipo_vivienda": tipo_data,
            "materiales": mat_data,
            "servicios": serv_rows,
            "resumen_servicios": resumen_servicios,
            "pct_vivienda_tradicional": pct_tradicional,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error en vivienda_pueblo('%s'): %s", cod_pueblo, e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error consultando vivienda: {str(e)}")


# ---------------------------------------------------------------------------
# GET /perfil/{cod_pueblo} — Perfil demografico completo
# ---------------------------------------------------------------------------
@router.get("/perfil/{cod_pueblo}")
async def perfil_demografico(
    cod_pueblo: int,
    db: AsyncSession = Depends(get_db),
):
    """Perfil demografico integral combinando todos los indicadores DANE."""
    try:
        params = {"cod_pueblo": cod_pueblo}

        # 1. Poblacion
        pob = await db.execute(
            text("""
                SELECT pueblo, poblacion_2005, poblacion_2018
                FROM visor_dane.poblacion_pueblo
                WHERE cod_pueblo = :cod_pueblo AND cod_pueblo != 1
            """),
            params,
        )
        pob_row = pob.first()
        if not pob_row:
            raise HTTPException(status_code=404, detail=f"Pueblo '{cod_pueblo}' no encontrado")
        pob_data = dict(pob_row._mapping)

        # Tasa de crecimiento intercensal
        p2005 = pob_data.get("poblacion_2005")
        p2018 = pob_data.get("poblacion_2018")
        if p2005 and p2018 and p2005 > 0:
            tasa_crecimiento = round(100.0 * (p2018 - p2005) / p2005, 2)
        else:
            tasa_crecimiento = None

        # 2. NBI + IPM
        nbi = await db.execute(
            text("""
                SELECT n.pct_nbi, n.pct_miseria, n.total_personas,
                       i.ipm, i.ipm_cabecera, i.ipm_resto
                FROM visor_dane.nbi_pueblo n
                LEFT JOIN visor_dane.ipm_pueblo i ON n.cod_pueblo = i.cod_pueblo
                WHERE n.cod_pueblo = :cod_pueblo
            """),
            params,
        )
        nbi_row = nbi.first()
        nbi_data = dict(nbi_row._mapping) if nbi_row else {}

        # 3. Lengua
        lengua = await db.execute(
            text("""
                WITH t AS (
                    SELECT SUM(poblacion) AS total FROM visor_dane.lengua_pueblo
                    WHERE cod_pueblo = :cod_pueblo
                ),
                h AS (
                    SELECT SUM(poblacion) AS habla FROM visor_dane.lengua_pueblo
                    WHERE cod_pueblo = :cod_pueblo AND habla_lengua = 'Sí'
                ),
                nh AS (
                    SELECT SUM(poblacion) AS no_habla FROM visor_dane.lengua_pueblo
                    WHERE cod_pueblo = :cod_pueblo AND habla_lengua = 'No' AND entiende_lengua = 'No'
                )
                SELECT
                    t.total AS pob_total_lengua,
                    COALESCE(h.habla, 0) AS pob_habla,
                    COALESCE(nh.no_habla, 0) AS pob_no_habla,
                    CASE WHEN t.total > 0
                        THEN ROUND(100.0 * COALESCE(h.habla, 0) / t.total, 2)
                        ELSE 0 END AS pct_habla,
                    CASE WHEN t.total > 0
                        THEN ROUND(100.0 * COALESCE(nh.no_habla, 0) / t.total, 2)
                        ELSE 0 END AS pct_no_habla
                FROM t, h, nh
            """),
            params,
        )
        lengua_row = lengua.first()
        lengua_data = dict(lengua_row._mapping) if lengua_row else {}

        # 4. Alfabetismo
        alfa = await db.execute(
            text("""
                SELECT
                    SUM(CASE WHEN alfabetismo = 'Sí' THEN poblacion_2018 ELSE 0 END) AS si_lee,
                    SUM(CASE WHEN alfabetismo = 'No' THEN poblacion_2018 ELSE 0 END) AS no_lee,
                    SUM(CASE WHEN alfabetismo IN ('Sí','No') THEN poblacion_2018 ELSE 0 END) AS total_alfa
                FROM visor_dane.alfabetismo_pueblo
                WHERE cod_pueblo = :cod_pueblo
            """),
            params,
        )
        alfa_row = alfa.first()
        alfa_data = dict(alfa_row._mapping) if alfa_row else {}
        total_alfa = alfa_data.get("total_alfa") or 0
        si_lee = alfa_data.get("si_lee") or 0
        tasa_alfabetismo = round(100.0 * si_lee / total_alfa, 2) if total_alfa > 0 else None

        # 5. Vivienda
        viv = await db.execute(
            text("""
                SELECT tipo_vivienda, poblacion_2018
                FROM visor_dane.tipo_vivienda_pueblo
                WHERE cod_pueblo = :cod_pueblo
                  AND tipo_vivienda IS NOT NULL AND tipo_vivienda != ''
            """),
            params,
        )
        viv_rows = [dict(r._mapping) for r in viv]
        total_viv = sum(v["poblacion_2018"] for v in viv_rows)
        trad_viv = sum(
            v["poblacion_2018"] for v in viv_rows
            if "tradicional ind" in (v["tipo_vivienda"] or "").lower()
        )
        pct_viv_tradicional = round(100.0 * trad_viv / total_viv, 2) if total_viv > 0 else None

        # 6. Servicios -- % sin acueducto como proxy
        serv = await db.execute(
            text("""
                SELECT
                    SUM(CASE WHEN tiene = 'No' THEN poblacion_2018 ELSE 0 END) AS sin_serv,
                    SUM(CASE WHEN tiene IN ('Sí','No') THEN poblacion_2018 ELSE 0 END) AS total_serv
                FROM visor_dane.servicios_vivienda_pueblo
                WHERE cod_pueblo = :cod_pueblo AND servicio = 'Acueducto'
            """),
            params,
        )
        serv_row = serv.first()
        serv_data = dict(serv_row._mapping) if serv_row else {}
        total_serv = serv_data.get("total_serv") or 0
        sin_serv = serv_data.get("sin_serv") or 0
        pct_sin_acueducto = round(100.0 * sin_serv / total_serv, 2) if total_serv > 0 else None

        # 7. Piramide para indice de dependencia e indice de envejecimiento
        piramide = await db.execute(
            text("""
                SELECT edad, SUM(poblacion_2018) AS pob
                FROM visor_dane.piramide_pueblo
                WHERE cod_pueblo = :cod_pueblo
                GROUP BY edad ORDER BY edad
            """),
            params,
        )
        pir_data = [dict(r._mapping) for r in piramide]

        pob_0_14 = 0
        pob_15_64 = 0
        pob_65_plus = 0
        for row in pir_data:
            edad = row["edad"]
            pob_val = row["pob"] or 0
            # Parse the first number from the age range
            try:
                start_age = int(edad.split("-")[0].replace("+", ""))
            except (ValueError, IndexError):
                start_age = 0
            if start_age < 15:
                pob_0_14 += pob_val
            elif start_age < 65:
                pob_15_64 += pob_val
            else:
                pob_65_plus += pob_val

        dependencia = round(100.0 * (pob_0_14 + pob_65_plus) / pob_15_64, 2) if pob_15_64 > 0 else None
        envejecimiento = round(100.0 * pob_65_plus / pob_0_14, 2) if pob_0_14 > 0 else None

        # 8. Urbanizacion
        clase = await db.execute(
            text("""
                SELECT clase, SUM(poblacion_2018) AS pob
                FROM visor_dane.poblacion_clase
                WHERE cod_pueblo = :cod_pueblo AND cod_pueblo != 1
                GROUP BY clase
            """),
            params,
        )
        clase_data = [dict(r._mapping) for r in clase]
        total_clase = sum(c["pob"] for c in clase_data)
        pob_cabecera = sum(
            c["pob"] for c in clase_data
            if "cabecera" in (c["clase"] or "").lower()
        )
        urbanizacion = round(100.0 * pob_cabecera / total_clase, 2) if total_clase > 0 else None

        # 9. Capacidades diversas (condicion fisica - funcionamiento)
        func = await db.execute(
            text("""
                SELECT
                    SUM(CASE WHEN condicion_fisica = 'Sí' THEN poblacion_2018 ELSE 0 END) AS con_cap_div,
                    SUM(CASE WHEN condicion_fisica IN ('Sí','No') THEN poblacion_2018 ELSE 0 END) AS total_func
                FROM visor_dane.funcionamiento_pueblo
                WHERE cod_pueblo = :cod_pueblo
            """),
            params,
        )
        func_row = func.first()
        func_data = dict(func_row._mapping) if func_row else {}
        total_func = func_data.get("total_func") or 0
        con_cap_div = func_data.get("con_cap_div") or 0
        tasa_cap_diversas = round(1000.0 * con_cap_div / total_func, 2) if total_func > 0 else None

        # 10. ICV (Indice Compuesto de Vulnerabilidad) -- calculado en /ranking
        pct_nbi = float(nbi_data.get("pct_nbi") or 0)
        pct_ipm = float(nbi_data.get("ipm") or 0)
        # We include ICV components but the full ranking is in /ranking
        icv_componentes = {
            "pct_nbi": pct_nbi,
            "pct_ipm": pct_ipm,
            "tasa_cap_diversas": tasa_cap_diversas,
        }

        return {
            "cod_pueblo": cod_pueblo,
            "pueblo": pob_data.get("pueblo"),
            "poblacion": {
                "poblacion_2005": pob_data.get("poblacion_2005"),
                "poblacion_2018": pob_data.get("poblacion_2018"),
                "tasa_crecimiento_pct": tasa_crecimiento,
            },
            "nbi": {
                "pct_nbi": pct_nbi,
                "pct_miseria": float(nbi_data.get("pct_miseria") or 0),
                "ipm": pct_ipm,
                "ipm_cabecera": float(nbi_data.get("ipm_cabecera") or 0),
                "ipm_resto": float(nbi_data.get("ipm_resto") or 0),
            },
            "lengua": {
                "pct_habla": float(lengua_data.get("pct_habla") or 0),
                "pct_no_habla": float(lengua_data.get("pct_no_habla") or 0),
                "pob_habla": int(lengua_data.get("pob_habla") or 0),
                "pob_no_habla": int(lengua_data.get("pob_no_habla") or 0),
            },
            "educacion": {
                "tasa_alfabetismo": tasa_alfabetismo,
            },
            "vivienda": {
                "pct_vivienda_tradicional": pct_viv_tradicional,
                "pct_sin_acueducto": pct_sin_acueducto,
            },
            "demografia": {
                "indice_dependencia": dependencia,
                "indice_envejecimiento": envejecimiento,
                "indice_urbanizacion": urbanizacion,
            },
            "capacidades_diversas": {
                "tasa_x_1000": tasa_cap_diversas,
                "con_cap_diversas": con_cap_div,
                "total_evaluados": total_func,
            },
            "icv_componentes": icv_componentes,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error en perfil_demografico('%s'): %s", cod_pueblo, e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error consultando perfil demografico: {str(e)}")


# ---------------------------------------------------------------------------
# GET /ranking — Ranking de pueblos por ICV (Indice Compuesto de Vulnerabilidad)
# ---------------------------------------------------------------------------
@router.get("/ranking")
async def ranking_vulnerabilidad(
    limit: int = Query(0, description="Limitar resultados (0 = todos)"),
    db: AsyncSession = Depends(get_db),
):
    """Ranking de pueblos por ICV (Indice Compuesto de Vulnerabilidad).

    ICV = (tasa_cap_diversas_norm * 0.3) + (pct_nbi_norm * 0.3) +
          (pct_ipm_norm * 0.2) + (tasa_victimas_norm * 0.2)

    Cada componente se normaliza min-max al rango [0, 1].
    """
    try:
        result = await db.execute(
            text("""
                WITH base AS (
                    SELECT
                        n.cod_pueblo,
                        p.pueblo,
                        p.poblacion_2018,
                        n.pct_nbi,
                        i.ipm AS pct_ipm,
                        -- tasa cap diversas
                        CASE WHEN f.total_func > 0
                            THEN ROUND(1000.0 * f.con_cap_div / f.total_func, 2)
                            ELSE NULL END AS tasa_cap_diversas,
                        -- tasa victimas (por 1000 hab)
                        CASE WHEN p.poblacion_2018 > 0
                            THEN ROUND(1000.0 * COALESCE(v.total_victimas, 0) / p.poblacion_2018, 2)
                            ELSE NULL END AS tasa_victimas
                    FROM visor_dane.nbi_pueblo n
                    JOIN visor_dane.poblacion_pueblo p
                        ON n.cod_pueblo = p.cod_pueblo AND p.cod_pueblo != 1
                    LEFT JOIN visor_dane.ipm_pueblo i
                        ON n.cod_pueblo = i.cod_pueblo
                    LEFT JOIN (
                        SELECT cod_pueblo,
                            SUM(CASE WHEN condicion_fisica = 'Sí' THEN poblacion_2018 ELSE 0 END) AS con_cap_div,
                            SUM(CASE WHEN condicion_fisica IN ('Sí','No') THEN poblacion_2018 ELSE 0 END) AS total_func
                        FROM visor_dane.funcionamiento_pueblo
                        GROUP BY cod_pueblo
                    ) f ON n.cod_pueblo = f.cod_pueblo
                    LEFT JOIN (
                        SELECT cod_pueblo_imputado::integer AS cod_pueblo,
                               SUM(cantidad) AS total_victimas
                        FROM victimas.resumen_pueblo_hecho
                        WHERE cod_pueblo_imputado ~ '^[0-9]+$'
                        GROUP BY cod_pueblo_imputado
                    ) v ON n.cod_pueblo = v.cod_pueblo
                    WHERE n.cod_pueblo != 1
                ),
                norm AS (
                    SELECT *,
                        -- min-max normalization per component
                        CASE WHEN MAX(tasa_cap_diversas) OVER() - MIN(tasa_cap_diversas) OVER() > 0
                            THEN (tasa_cap_diversas - MIN(tasa_cap_diversas) OVER())
                                / (MAX(tasa_cap_diversas) OVER() - MIN(tasa_cap_diversas) OVER())
                            ELSE 0 END AS tasa_cap_norm,
                        CASE WHEN MAX(pct_nbi) OVER() - MIN(pct_nbi) OVER() > 0
                            THEN (pct_nbi - MIN(pct_nbi) OVER())
                                / (MAX(pct_nbi) OVER() - MIN(pct_nbi) OVER())
                            ELSE 0 END AS nbi_norm,
                        CASE WHEN MAX(pct_ipm) OVER() - MIN(pct_ipm) OVER() > 0
                            THEN (pct_ipm - MIN(pct_ipm) OVER())
                                / (MAX(pct_ipm) OVER() - MIN(pct_ipm) OVER())
                            ELSE 0 END AS ipm_norm,
                        CASE WHEN MAX(tasa_victimas) OVER() - MIN(tasa_victimas) OVER() > 0
                            THEN (tasa_victimas - MIN(tasa_victimas) OVER())
                                / (MAX(tasa_victimas) OVER() - MIN(tasa_victimas) OVER())
                            ELSE 0 END AS victimas_norm
                    FROM base
                    WHERE tasa_cap_diversas IS NOT NULL
                      AND pct_nbi IS NOT NULL
                      AND pct_ipm IS NOT NULL
                )
                SELECT
                    cod_pueblo,
                    pueblo,
                    poblacion_2018,
                    pct_nbi,
                    pct_ipm,
                    tasa_cap_diversas,
                    tasa_victimas,
                    ROUND((tasa_cap_norm * 0.3 + nbi_norm * 0.3 + ipm_norm * 0.2 + victimas_norm * 0.2)::numeric, 4) AS icv,
                    ROUND(tasa_cap_norm::numeric, 4) AS icv_cap_diversas,
                    ROUND(nbi_norm::numeric, 4) AS icv_nbi,
                    ROUND(ipm_norm::numeric, 4) AS icv_ipm,
                    ROUND(victimas_norm::numeric, 4) AS icv_victimas
                FROM norm
                ORDER BY icv DESC
            """)
        )
        rows = [dict(r._mapping) for r in result]

        if limit > 0:
            rows = rows[:limit]

        return {
            "total": len(rows),
            "formula": "ICV = (tasa_cap_diversas_norm * 0.3) + (pct_nbi_norm * 0.3) + (pct_ipm_norm * 0.2) + (tasa_victimas_norm * 0.2)",
            "data": rows,
        }
    except Exception as e:
        logger.error("Error en ranking_vulnerabilidad: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error consultando ranking ICV: {str(e)}")


# ---------------------------------------------------------------------------
# GET /piramide/{cod_pueblo} — Piramide poblacional quinquenal por sexo
# ---------------------------------------------------------------------------
@router.get("/piramide/{cod_pueblo}")
async def piramide_demografica(
    cod_pueblo: int,
    db: AsyncSession = Depends(get_db),
):
    """Piramide poblacional quinquenal por sexo - formato demografico profesional."""
    try:
        # Obtener nombre del pueblo
        check = await db.execute(
            text("""
                SELECT pueblo FROM visor_dane.poblacion_pueblo
                WHERE cod_pueblo = :cod AND cod_pueblo != 1
            """),
            {"cod": cod_pueblo},
        )
        check_row = check.first()
        if not check_row:
            raise HTTPException(status_code=404, detail=f"Pueblo '{cod_pueblo}' no encontrado")
        pueblo_nombre = check_row._mapping["pueblo"]

        result = await db.execute(
            text("""
                SELECT sexo, edad, poblacion_2018
                FROM visor_dane.piramide_pueblo
                WHERE cod_pueblo = :cod
                ORDER BY
                    CASE edad
                        WHEN '0-4' THEN 1 WHEN '5-9' THEN 2 WHEN '10-14' THEN 3
                        WHEN '15-19' THEN 4 WHEN '20-24' THEN 5 WHEN '25-29' THEN 6
                        WHEN '30-34' THEN 7 WHEN '35-39' THEN 8 WHEN '40-44' THEN 9
                        WHEN '45-49' THEN 10 WHEN '50-54' THEN 11 WHEN '55-59' THEN 12
                        WHEN '60-64' THEN 13 WHEN '65-69' THEN 14 WHEN '70-74' THEN 15
                        WHEN '75-79' THEN 16 WHEN '80-84' THEN 17 ELSE 18
                    END,
                    sexo
            """),
            {"cod": cod_pueblo},
        )

        rows = [dict(r._mapping) for r in result]
        if not rows:
            raise HTTPException(
                status_code=404,
                detail=f"No hay datos de piramide para pueblo '{cod_pueblo}'",
            )

        # Build professional pyramid format
        age_groups = [
            '0-4', '5-9', '10-14', '15-19', '20-24', '25-29', '30-34', '35-39',
            '40-44', '45-49', '50-54', '55-59', '60-64', '65-69', '70-74', '75-79',
            '80-84', '85+',
        ]

        hombres = {r['edad']: r['poblacion_2018'] for r in rows if r['sexo'] == 'HOMBRE'}
        mujeres = {r['edad']: r['poblacion_2018'] for r in rows if r['sexo'] == 'MUJER'}

        total_h = sum(v for v in hombres.values() if v)
        total_m = sum(v for v in mujeres.values() if v)
        total = total_h + total_m

        pyramid = []
        for ag in age_groups:
            # The DB stores 85+ as '85-121'
            key = '85-121' if ag == '85+' else ag
            h = (hombres.get(key) or hombres.get(ag) or 0)
            m = (mujeres.get(key) or mujeres.get(ag) or 0)
            pyramid.append({
                'grupo_edad': ag,
                'hombres': -h,           # Negative for left side of pyramid
                'mujeres': m,
                'hombres_abs': h,
                'mujeres_abs': m,
                'pct_hombres': round(h / total * 100, 2) if total > 0 else 0,
                'pct_mujeres': round(m / total * 100, 2) if total > 0 else 0,
            })

        # Demographic indices
        p_0_14 = sum(
            r['hombres_abs'] + r['mujeres'] for r in pyramid
            if r['grupo_edad'] in ('0-4', '5-9', '10-14')
        )
        p_65_plus = sum(
            r['hombres_abs'] + r['mujeres'] for r in pyramid
            if r['grupo_edad'] in ('65-69', '70-74', '75-79', '80-84', '85+')
        )
        p_15_64 = total - p_0_14 - p_65_plus

        return {
            'cod_pueblo': cod_pueblo,
            'pueblo': pueblo_nombre,
            'total': total,
            'total_hombres': total_h,
            'total_mujeres': total_m,
            'razon_masculinidad': round(total_h / total_m * 100, 1) if total_m > 0 else 0,
            'indice_dependencia': round((p_0_14 + p_65_plus) / p_15_64 * 100, 1) if p_15_64 > 0 else 0,
            'indice_envejecimiento': round(p_65_plus / p_0_14 * 100, 1) if p_0_14 > 0 else 0,
            'piramide': pyramid,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error en piramide_demografica('%s'): %s", cod_pueblo, e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error consultando piramide: {str(e)}")


# ---------------------------------------------------------------------------
# GET /resguardos — Lista de resguardos con poblacion (filtrables por mpio/dpto)
# ---------------------------------------------------------------------------
@router.get("/resguardos")
async def listar_resguardos_demo(
    cod_mpio: str | None = Query(None, description="Filtrar por municipio (DIVIPOLA)"),
    cod_dpto: str | None = Query(None, description="Filtrar por departamento (2 digitos)"),
    db: AsyncSession = Depends(get_db),
):
    """Lista resguardos con poblacion agregada, filtrables por municipio o departamento.
    Cruza visor_dane.resguardo_pueblo con smt_geo.resguardos.
    """
    try:
        filtros = []
        params: dict = {}

        if cod_mpio:
            filtros.append("g.mpio_cdpmp = :cod_mpio")
            params["cod_mpio"] = cod_mpio
        elif cod_dpto:
            filtros.append("g.mpio_cdpmp LIKE :cod_dpto_prefix")
            params["cod_dpto_prefix"] = f"{cod_dpto}%"

        where_clause = ("WHERE " + " AND ".join(filtros)) if filtros else ""

        result = await db.execute(
            text(f"""
                WITH resguardo_agg AS (
                    SELECT
                        SUBSTRING(v.resguardo FROM '\\((\\d+)\\)') AS cod_resguardo,
                        v.resguardo AS nombre_resguardo,
                        SUM(v.poblacion) AS poblacion_total,
                        COUNT(DISTINCT v.cod_pueblo) AS num_pueblos
                    FROM visor_dane.resguardo_pueblo v
                    WHERE v.poblacion > 0
                    GROUP BY SUBSTRING(v.resguardo FROM '\\((\\d+)\\)'), v.resguardo
                )
                SELECT
                    ra.cod_resguardo,
                    ra.nombre_resguardo,
                    ra.poblacion_total,
                    ra.num_pueblos,
                    g.territorio,
                    g.pueblo_onic,
                    g.dpto_cnmbr AS departamento,
                    g.mpio_cnmbr AS municipio,
                    g.mpio_cdpmp AS cod_mpio,
                    g.org_regnal AS organizacion,
                    g.area_pg_ha
                FROM resguardo_agg ra
                LEFT JOIN smt_geo.resguardos g
                    ON ra.cod_resguardo = g.ccdgo_terr
                {where_clause}
                ORDER BY ra.poblacion_total DESC
            """),
            params,
        )
        rows = [dict(r._mapping) for r in result]

        # Cast numeric fields
        for row in rows:
            if row.get("area_pg_ha") is not None:
                row["area_pg_ha"] = float(row["area_pg_ha"])

        return {"total": len(rows), "data": rows}
    except Exception as e:
        logger.error("Error en listar_resguardos_demo: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error consultando resguardos: {str(e)}")


# ---------------------------------------------------------------------------
# GET /resguardo/{cod_resguardo} — Perfil de un resguardo
# ---------------------------------------------------------------------------
@router.get("/resguardo/{cod_resguardo}")
async def perfil_resguardo(
    cod_resguardo: str,
    db: AsyncSession = Depends(get_db),
):
    """Perfil de un resguardo: poblacion por pueblo, ubicacion, area.
    Cruza visor_dane.resguardo_pueblo (por codigo en parentesis)
    con smt_geo.resguardos y pueblo.disc_nacional para tasas por pueblo.
    """
    try:
        result = await db.execute(
            text("""
                SELECT v.resguardo, v.cod_pueblo, v.poblacion,
                       p.pueblo, p.tasa_x_1000 AS tasa_pueblo,
                       g.territorio, g.pueblo_onic, g.dpto_cnmbr, g.mpio_cnmbr,
                       g.mpio_cdpmp, g.area_pg_ha, g.org_regnal
                FROM visor_dane.resguardo_pueblo v
                LEFT JOIN pueblo.disc_nacional p
                    ON LPAD(v.cod_pueblo::text, 3, '0') = p.cod_pueblo
                    AND p.periodo = '2018'
                LEFT JOIN smt_geo.resguardos g
                    ON SUBSTRING(v.resguardo FROM '\\((\\d+)\\)') = g.ccdgo_terr
                WHERE SUBSTRING(v.resguardo FROM '\\((\\d+)\\)') = :cod
                  AND v.poblacion > 0
                ORDER BY v.poblacion DESC
            """),
            {"cod": cod_resguardo},
        )
        rows = [dict(r._mapping) for r in result]
        if not rows:
            raise HTTPException(
                status_code=404,
                detail=f"Resguardo {cod_resguardo} no encontrado",
            )

        # Build response
        total_pob = sum(r["poblacion"] for r in rows)

        # Try REAL data from cnpv.disc_resguardo (extracted from REDATAM)
        real_result = await db.execute(
            text("""
                SELECT con_cap_diversas, total_evaluados, tasa_x_1000
                FROM cnpv.disc_resguardo
                WHERE cod_resguardo = :cod AND periodo = '2018'
            """),
            {"cod": cod_resguardo},
        )
        real_row = real_result.first()

        if real_row:
            cap_div = real_row._mapping["con_cap_diversas"]
            cap_total = real_row._mapping["total_evaluados"]
            cap_tasa = float(real_row._mapping["tasa_x_1000"])
            fuente_cap_div = "REDATAM CNPV 2018 (dato censal)"
        else:
            # Fallback: estimate from pueblo rates
            cap_div = round(sum(
                r["poblacion"] * (r["tasa_pueblo"] or 0) / 1000 for r in rows
            ))
            cap_total = total_pob
            cap_tasa = round(cap_div / total_pob * 1000, 1) if total_pob > 0 else 0
            fuente_cap_div = "Estimacion por tasa de pueblo (no hay dato censal directo)"

        return {
            "cod_resguardo": cod_resguardo,
            "nombre": rows[0]["resguardo"] or rows[0]["territorio"],
            "territorio": rows[0]["territorio"],
            "departamento": rows[0]["dpto_cnmbr"],
            "municipio": rows[0]["mpio_cnmbr"],
            "cod_mpio": rows[0]["mpio_cdpmp"],
            "organizacion": rows[0]["org_regnal"],
            "area_ha": float(rows[0]["area_pg_ha"]) if rows[0]["area_pg_ha"] else None,
            "poblacion_total": total_pob,
            "con_cap_diversas": cap_div,
            "total_evaluados": cap_total,
            "tasa_x_1000": cap_tasa,
            "fuente_cap_diversas": fuente_cap_div,
            "pueblos": [
                {
                    "cod_pueblo": str(r["cod_pueblo"]).zfill(3),
                    "pueblo": r["pueblo"] or f"Pueblo {r['cod_pueblo']}",
                    "poblacion": r["poblacion"],
                    "pct": round(r["poblacion"] / total_pob * 100, 1) if total_pob > 0 else 0,
                    "tasa_pueblo": r["tasa_pueblo"],
                }
                for r in rows
            ],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error en perfil_resguardo('%s'): %s", cod_resguardo, e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error consultando perfil de resguardo: {str(e)}")


# ---------------------------------------------------------------------------
# GET /resguardos-pueblo/{cod_pueblo} — Resguardos donde habita un pueblo
# ---------------------------------------------------------------------------
@router.get("/resguardos-pueblo/{cod_pueblo}")
async def resguardos_por_pueblo(
    cod_pueblo: int,
    db: AsyncSession = Depends(get_db),
):
    """Lista resguardos donde habita un pueblo especifico, con poblacion y ubicacion."""
    try:
        result = await db.execute(
            text("""
                SELECT
                    SUBSTRING(v.resguardo FROM '\\((\\d+)\\)') AS cod_resguardo,
                    v.resguardo AS nombre_resguardo,
                    v.poblacion,
                    g.territorio,
                    g.pueblo_onic,
                    g.dpto_cnmbr AS departamento,
                    g.mpio_cnmbr AS municipio,
                    g.mpio_cdpmp AS cod_mpio,
                    g.org_regnal AS organizacion,
                    g.area_pg_ha
                FROM visor_dane.resguardo_pueblo v
                LEFT JOIN smt_geo.resguardos g
                    ON SUBSTRING(v.resguardo FROM '\\((\\d+)\\)') = g.ccdgo_terr
                WHERE v.cod_pueblo = :cod_pueblo
                  AND v.poblacion > 0
                ORDER BY v.poblacion DESC
            """),
            {"cod_pueblo": cod_pueblo},
        )
        rows = [dict(r._mapping) for r in result]

        # Cast numeric fields
        for row in rows:
            if row.get("area_pg_ha") is not None:
                row["area_pg_ha"] = float(row["area_pg_ha"])

        return {"total": len(rows), "cod_pueblo": cod_pueblo, "data": rows}
    except Exception as e:
        logger.error("Error en resguardos_por_pueblo('%s'): %s", cod_pueblo, e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error consultando resguardos del pueblo: {str(e)}")


@router.get("/piramide-disc/{cod_pueblo}")
async def piramide_capacidades_diversas(
    cod_pueblo: str,
    db: AsyncSession = Depends(get_db),
):
    """Piramide de personas CON capacidades diversas por sexo y edad quinquenal."""
    try:
        result = await db.execute(
            text("""
                SELECT grupo_edad, sexo, valor
                FROM pueblo.piramide_disc
                WHERE cod_pueblo = :cod AND periodo = '2018'
                ORDER BY
                    CASE grupo_edad
                        WHEN '00-04' THEN 1 WHEN '05-09' THEN 2 WHEN '10-14' THEN 3
                        WHEN '15-19' THEN 4 WHEN '20-24' THEN 5 WHEN '25-29' THEN 6
                        WHEN '30-34' THEN 7 WHEN '35-39' THEN 8 WHEN '40-44' THEN 9
                        WHEN '45-49' THEN 10 WHEN '50-54' THEN 11 WHEN '55-59' THEN 12
                        WHEN '60-64' THEN 13 WHEN '65-69' THEN 14 WHEN '70-74' THEN 15
                        WHEN '75-79' THEN 16 WHEN '80-84' THEN 17 ELSE 18
                    END,
                    sexo
            """),
            {"cod": cod_pueblo},
        )
        rows = [dict(r._mapping) for r in result]
        if not rows:
            raise HTTPException(status_code=404, detail=f"No hay piramide de cap. diversas para pueblo {cod_pueblo}")

        age_groups = ['00-04','05-09','10-14','15-19','20-24','25-29','30-34','35-39',
                      '40-44','45-49','50-54','55-59','60-64','65-69','70-74','75-79','80-84','85+']

        hombres = {r['grupo_edad']: r['valor'] for r in rows if r['sexo'] == 'Hombre'}
        mujeres = {r['grupo_edad']: r['valor'] for r in rows if r['sexo'] == 'Mujer'}
        total_h = sum(hombres.values())
        total_m = sum(mujeres.values())
        total = total_h + total_m

        piramide = []
        for ag in age_groups:
            h = hombres.get(ag, 0)
            m = mujeres.get(ag, 0)
            piramide.append({
                'grupo_edad': ag,
                'hombres': -h,
                'mujeres': m,
                'hombres_abs': h,
                'mujeres_abs': m,
                'pct_hombres': round(h / total * 100, 2) if total > 0 else 0,
                'pct_mujeres': round(m / total * 100, 2) if total > 0 else 0,
            })

        return {
            'cod_pueblo': cod_pueblo,
            'tipo': 'capacidades_diversas',
            'total': total,
            'total_hombres': total_h,
            'total_mujeres': total_m,
            'razon_masculinidad': round(total_h / total_m * 100, 1) if total_m > 0 else 0,
            'piramide': piramide,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error en piramide_disc('%s'): %s", cod_pueblo, e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/piramide-disc-tipo/{cod_pueblo}")
async def piramide_disc_por_tipo(
    cod_pueblo: str,
    db: AsyncSession = Depends(get_db),
):
    """Piramide de cap. diversas desglosada por TIPO de limitacion, sexo y edad."""
    try:
        result = await db.execute(
            text("""
                SELECT tipo_limitacion, grupo_edad, sexo, valor
                FROM pueblo.piramide_disc_tipo
                WHERE cod_pueblo = :cod AND periodo = '2018'
                ORDER BY tipo_limitacion, grupo_edad, sexo
            """),
            {"cod": cod_pueblo},
        )
        rows = [dict(r._mapping) for r in result]
        if not rows:
            raise HTTPException(status_code=404, detail=f"No hay datos por tipo para pueblo {cod_pueblo}")

        age_groups = ['00-04','05-09','10-14','15-19','20-24','25-29','30-34','35-39',
                      '40-44','45-49','50-54','55-59','60-64','65-69','70-74','75-79','80-84','85+']
        tipos = sorted(set(r['tipo_limitacion'] for r in rows))

        # Build stacked pyramid data: each age group has hombres/mujeres split by tipo
        piramide = []
        grand_total = sum(r['valor'] for r in rows)

        for ag in age_groups:
            entry = {'grupo_edad': ag}
            total_h_ag = 0
            total_m_ag = 0
            for tipo in tipos:
                h = sum(r['valor'] for r in rows if r['grupo_edad'] == ag and r['sexo'] == 'Hombre' and r['tipo_limitacion'] == tipo)
                m = sum(r['valor'] for r in rows if r['grupo_edad'] == ag and r['sexo'] == 'Mujer' and r['tipo_limitacion'] == tipo)
                key_h = f"h_{tipo}"
                key_m = f"m_{tipo}"
                entry[key_h] = -h  # negative for left side
                entry[key_m] = m
                entry[f"abs_h_{tipo}"] = h
                entry[f"abs_m_{tipo}"] = m
                total_h_ag += h
                total_m_ag += m
            entry['total_h'] = total_h_ag
            entry['total_m'] = total_m_ag
            piramide.append(entry)

        # Summary by type
        resumen_tipos = []
        for tipo in tipos:
            total_tipo = sum(r['valor'] for r in rows if r['tipo_limitacion'] == tipo)
            h_tipo = sum(r['valor'] for r in rows if r['tipo_limitacion'] == tipo and r['sexo'] == 'Hombre')
            m_tipo = sum(r['valor'] for r in rows if r['tipo_limitacion'] == tipo and r['sexo'] == 'Mujer')
            resumen_tipos.append({
                'tipo': tipo,
                'total': total_tipo,
                'hombres': h_tipo,
                'mujeres': m_tipo,
                'pct': round(total_tipo / grand_total * 100, 1) if grand_total > 0 else 0,
            })
        resumen_tipos.sort(key=lambda x: x['total'], reverse=True)

        return {
            'cod_pueblo': cod_pueblo,
            'total': grand_total,
            'tipos': tipos,
            'resumen_tipos': resumen_tipos,
            'piramide': piramide,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error en piramide_disc_tipo('%s'): %s", cod_pueblo, e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Piramides AGREGADAS NACIONAL — suma sobre todos los pueblos indigenas
# ---------------------------------------------------------------------------
AGE_GROUPS_VISOR = [
    '0-4','5-9','10-14','15-19','20-24','25-29','30-34','35-39',
    '40-44','45-49','50-54','55-59','60-64','65-69','70-74','75-79','80-84','85+',
]
AGE_GROUPS_PUEBLO = [
    '00-04','05-09','10-14','15-19','20-24','25-29','30-34','35-39',
    '40-44','45-49','50-54','55-59','60-64','65-69','70-74','75-79','80-84','85+',
]


@router.get("/piramide-nacional")
async def piramide_nacional(
    cod_dpto: str | None = Query(None),
    cod_mpio: str | None = Query(None),
    cod_pueblo: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Piramide poblacional indigena (CNPV 2018).
    Sin filtro -> agregada nacional.
    cod_pueblo -> exacto (piramide_pueblo filtrada).
    cod_dpto/cod_mpio -> escalada por share de pob_pueblo en area.
    """
    try:
        # Build filter: share per pueblo in area
        if cod_pueblo:
            result = await db.execute(text("""
                SELECT sexo, edad, SUM(COALESCE(poblacion_2018,0)) AS valor
                FROM visor_dane.piramide_pueblo
                WHERE cod_pueblo::text = :cp
                GROUP BY sexo, edad
            """), {"cp": str(cod_pueblo)})
        elif cod_mpio or cod_dpto:
            # Weighted: for each pueblo, scale national piramide by (pob_in_area / pob_national_pueblo)
            where_area = "pm.cod_mpio = :area" if cod_mpio else "LEFT(pm.cod_mpio, 2) = :area"
            area_val = cod_mpio if cod_mpio else cod_dpto
            result = await db.execute(text(f"""
                WITH share AS (
                    SELECT pm.cod_pueblo,
                           SUM(pm.poblacion)::float / NULLIF(SUM(SUM(pm.poblacion)) OVER (PARTITION BY pm.cod_pueblo), 0) AS w
                    FROM pueblo.pueblo_municipio pm
                    WHERE {where_area}
                    GROUP BY pm.cod_pueblo
                ),
                national AS (
                    SELECT pm.cod_pueblo, SUM(pm.poblacion) AS pob_nat
                    FROM pueblo.pueblo_municipio pm
                    GROUP BY pm.cod_pueblo
                ),
                area_pob AS (
                    SELECT pm.cod_pueblo, SUM(pm.poblacion) AS pob_area
                    FROM pueblo.pueblo_municipio pm
                    WHERE {where_area}
                    GROUP BY pm.cod_pueblo
                )
                SELECT pp.sexo, pp.edad,
                       SUM(COALESCE(pp.poblacion_2018,0) * ap.pob_area::float / NULLIF(n.pob_nat,0))::int AS valor
                FROM visor_dane.piramide_pueblo pp
                JOIN area_pob ap ON ap.cod_pueblo = pp.cod_pueblo::text
                JOIN national n ON n.cod_pueblo = pp.cod_pueblo::text
                GROUP BY pp.sexo, pp.edad
            """), {"area": area_val})
        else:
            result = await db.execute(text("""
                SELECT sexo, edad, SUM(COALESCE(poblacion_2018,0)) AS valor
                FROM visor_dane.piramide_pueblo
                GROUP BY sexo, edad
            """))
        rows = [dict(r._mapping) for r in result]
        hombres, mujeres = {}, {}
        for r in rows:
            key = r['edad']
            if key == '85-121':
                key = '85+'
            if r['sexo'] == 'HOMBRE':
                hombres[key] = hombres.get(key, 0) + int(r['valor'] or 0)
            elif r['sexo'] == 'MUJER':
                mujeres[key] = mujeres.get(key, 0) + int(r['valor'] or 0)
        total_h = sum(hombres.values())
        total_m = sum(mujeres.values())
        total = total_h + total_m
        pyramid = []
        for ag in AGE_GROUPS_VISOR:
            h = hombres.get(ag, 0)
            m = mujeres.get(ag, 0)
            pyramid.append({
                'grupo_edad': ag,
                'hombres': -h,
                'mujeres': m,
                'hombres_abs': h,
                'mujeres_abs': m,
                'pct_hombres': round(h / total * 100, 2) if total > 0 else 0,
                'pct_mujeres': round(m / total * 100, 2) if total > 0 else 0,
            })
        return {
            'cod_pueblo': cod_pueblo or 'NACIONAL',
            'cod_dpto': cod_dpto,
            'cod_mpio': cod_mpio,
            'pueblo': 'Nacional indigena' if not cod_pueblo else f'Pueblo {cod_pueblo}',
            'total': total,
            'total_hombres': total_h,
            'total_mujeres': total_m,
            'razon_masculinidad': round(total_h / total_m * 100, 1) if total_m > 0 else 0,
            'piramide': pyramid,
        }
    except Exception as e:
        logger.error("Error en piramide_nacional: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/piramide-disc-nacional")
async def piramide_disc_nacional(
    cod_dpto: str | None = Query(None),
    cod_mpio: str | None = Query(None),
    cod_pueblo: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Piramide de personas con capacidades diversas.
    Sin filtro -> nacional. cod_pueblo -> exacto. dpto/mpio -> escalada por share.
    """
    try:
        if cod_pueblo:
            result = await db.execute(text("""
                SELECT grupo_edad, sexo, SUM(valor) AS valor
                FROM pueblo.piramide_disc
                WHERE periodo = '2018' AND cod_pueblo = :cp
                GROUP BY grupo_edad, sexo
            """), {"cp": str(cod_pueblo)})
        elif cod_mpio or cod_dpto:
            where_area = "pm.cod_mpio = :area" if cod_mpio else "LEFT(pm.cod_mpio, 2) = :area"
            area_val = cod_mpio if cod_mpio else cod_dpto
            result = await db.execute(text(f"""
                WITH national AS (
                    SELECT pm.cod_pueblo, SUM(pm.poblacion) AS pob_nat
                    FROM pueblo.pueblo_municipio pm
                    GROUP BY pm.cod_pueblo
                ),
                area_pob AS (
                    SELECT pm.cod_pueblo, SUM(pm.poblacion) AS pob_area
                    FROM pueblo.pueblo_municipio pm
                    WHERE {where_area}
                    GROUP BY pm.cod_pueblo
                )
                SELECT pd.grupo_edad, pd.sexo,
                       SUM(pd.valor * ap.pob_area::float / NULLIF(n.pob_nat,0))::int AS valor
                FROM pueblo.piramide_disc pd
                JOIN area_pob ap ON ap.cod_pueblo = pd.cod_pueblo
                JOIN national n ON n.cod_pueblo = pd.cod_pueblo
                WHERE pd.periodo = '2018'
                GROUP BY pd.grupo_edad, pd.sexo
            """), {"area": area_val})
        else:
            result = await db.execute(text("""
                SELECT grupo_edad, sexo, SUM(valor) AS valor
                FROM pueblo.piramide_disc
                WHERE periodo = '2018'
                GROUP BY grupo_edad, sexo
            """))
        rows = [dict(r._mapping) for r in result]
        hombres = {r['grupo_edad']: int(r['valor']) for r in rows if r['sexo'] == 'Hombre'}
        mujeres = {r['grupo_edad']: int(r['valor']) for r in rows if r['sexo'] == 'Mujer'}
        total_h = sum(hombres.values())
        total_m = sum(mujeres.values())
        total = total_h + total_m
        piramide = []
        for ag in AGE_GROUPS_PUEBLO:
            h = hombres.get(ag, 0)
            m = mujeres.get(ag, 0)
            piramide.append({
                'grupo_edad': ag,
                'hombres': -h,
                'mujeres': m,
                'hombres_abs': h,
                'mujeres_abs': m,
                'pct_hombres': round(h / total * 100, 2) if total > 0 else 0,
                'pct_mujeres': round(m / total * 100, 2) if total > 0 else 0,
            })
        return {
            'cod_pueblo': cod_pueblo or 'NACIONAL',
            'cod_dpto': cod_dpto,
            'cod_mpio': cod_mpio,
            'tipo': 'capacidades_diversas',
            'total': total,
            'total_hombres': total_h,
            'total_mujeres': total_m,
            'razon_masculinidad': round(total_h / total_m * 100, 1) if total_m > 0 else 0,
            'piramide': piramide,
        }
    except Exception as e:
        logger.error("Error en piramide_disc_nacional: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/piramide-disc-tipo-nacional")
async def piramide_disc_tipo_nacional(
    cod_dpto: str | None = Query(None),
    cod_mpio: str | None = Query(None),
    cod_pueblo: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Piramide apilada por tipo de limitacion.
    Sin filtro -> nacional. cod_pueblo -> exacto. dpto/mpio -> escalada por share.
    """
    try:
        if cod_pueblo:
            result = await db.execute(text("""
                SELECT tipo_limitacion, grupo_edad, sexo, SUM(valor) AS valor
                FROM pueblo.piramide_disc_tipo
                WHERE periodo = '2018' AND cod_pueblo = :cp
                GROUP BY tipo_limitacion, grupo_edad, sexo
            """), {"cp": str(cod_pueblo)})
        elif cod_mpio or cod_dpto:
            where_area = "pm.cod_mpio = :area" if cod_mpio else "LEFT(pm.cod_mpio, 2) = :area"
            area_val = cod_mpio if cod_mpio else cod_dpto
            result = await db.execute(text(f"""
                WITH national AS (
                    SELECT pm.cod_pueblo, SUM(pm.poblacion) AS pob_nat
                    FROM pueblo.pueblo_municipio pm
                    GROUP BY pm.cod_pueblo
                ),
                area_pob AS (
                    SELECT pm.cod_pueblo, SUM(pm.poblacion) AS pob_area
                    FROM pueblo.pueblo_municipio pm
                    WHERE {where_area}
                    GROUP BY pm.cod_pueblo
                )
                SELECT pt.tipo_limitacion, pt.grupo_edad, pt.sexo,
                       SUM(pt.valor * ap.pob_area::float / NULLIF(n.pob_nat,0))::int AS valor
                FROM pueblo.piramide_disc_tipo pt
                JOIN area_pob ap ON ap.cod_pueblo = pt.cod_pueblo
                JOIN national n ON n.cod_pueblo = pt.cod_pueblo
                WHERE pt.periodo = '2018'
                GROUP BY pt.tipo_limitacion, pt.grupo_edad, pt.sexo
            """), {"area": area_val})
        else:
            result = await db.execute(text("""
                SELECT tipo_limitacion, grupo_edad, sexo, SUM(valor) AS valor
                FROM pueblo.piramide_disc_tipo
                WHERE periodo = '2018'
                GROUP BY tipo_limitacion, grupo_edad, sexo
            """))
        rows = [dict(r._mapping) for r in result]
        if not rows:
            raise HTTPException(status_code=404, detail="No hay datos nacionales por tipo")
        tipos = sorted(set(r['tipo_limitacion'] for r in rows))
        grand_total = sum(int(r['valor']) for r in rows)
        piramide = []
        for ag in AGE_GROUPS_PUEBLO:
            entry = {'grupo_edad': ag}
            total_h_ag = 0
            total_m_ag = 0
            for tipo in tipos:
                h = sum(int(r['valor']) for r in rows if r['grupo_edad'] == ag and r['sexo'] == 'Hombre' and r['tipo_limitacion'] == tipo)
                m = sum(int(r['valor']) for r in rows if r['grupo_edad'] == ag and r['sexo'] == 'Mujer' and r['tipo_limitacion'] == tipo)
                entry[f"h_{tipo}"] = -h
                entry[f"m_{tipo}"] = m
                entry[f"abs_h_{tipo}"] = h
                entry[f"abs_m_{tipo}"] = m
                total_h_ag += h
                total_m_ag += m
            entry['total_h'] = total_h_ag
            entry['total_m'] = total_m_ag
            piramide.append(entry)
        resumen_tipos = []
        for tipo in tipos:
            total_tipo = sum(int(r['valor']) for r in rows if r['tipo_limitacion'] == tipo)
            h_tipo = sum(int(r['valor']) for r in rows if r['tipo_limitacion'] == tipo and r['sexo'] == 'Hombre')
            m_tipo = sum(int(r['valor']) for r in rows if r['tipo_limitacion'] == tipo and r['sexo'] == 'Mujer')
            resumen_tipos.append({
                'tipo': tipo,
                'total': total_tipo,
                'hombres': h_tipo,
                'mujeres': m_tipo,
                'pct': round(total_tipo / grand_total * 100, 1) if grand_total > 0 else 0,
            })
        resumen_tipos.sort(key=lambda x: x['total'], reverse=True)
        return {
            'cod_pueblo': cod_pueblo or 'NACIONAL',
            'cod_dpto': cod_dpto,
            'cod_mpio': cod_mpio,
            'total': grand_total,
            'tipos': tipos,
            'resumen_tipos': resumen_tipos,
            'piramide': piramide,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error en piramide_disc_tipo_nacional: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
