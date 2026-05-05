"""
Pueblos indigenas - Perfiles de capacidades diversas por pueblo.
"""

import logging
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.routers.auth import get_current_user  # T24 · cierre H-ONIC-052

logger = logging.getLogger(__name__)
# T24 · auth global · todos los endpoints requieren Bearer token
router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/")
async def listar_pueblos(
    periodo: str = Query("2018"),
    cod_macro: str | None = Query(None, description="Macrorregión ONIC (filtra por presencia en zona)"),
    cod_dpto: str | None = Query(None, description="Departamento (filtra por presencia)"),
    cod_mpio: str | None = Query(None, description="Municipio (filtra por presencia)"),
    db: AsyncSession = Depends(get_db),
):
    """Lista todos los pueblos con poblacion y prevalencia de capacidades diversas.
    Solo incluye pueblos con total >= 30 para tasas confiables.

    Filtros geográficos restringen a pueblos PRESENTES en el ámbito.
    El cálculo de prevalencia sigue siendo nacional (de pueblo.disc_nacional)
    porque los datos a nivel mpio/resguardo no tienen suficientes casos por pueblo.
    """
    try:
        # Resolver lista de cod_pueblo presentes en el ámbito geográfico (si hay filtro)
        cod_pueblos_filtro: list[str] | None = None

        if cod_mpio:
            r = await db.execute(
                text("SELECT DISTINCT cod_pueblo FROM pueblo.pueblo_municipio WHERE cod_mpio = :m AND periodo = :p"),
                {"m": cod_mpio, "p": periodo},
            )
            cod_pueblos_filtro = [str(x[0]) for x in r.fetchall()]
        elif cod_dpto:
            r = await db.execute(
                text("SELECT DISTINCT cod_pueblo FROM pueblo.disc_dpto WHERE cod_dpto = :d AND periodo = :p AND total > 0"),
                {"d": cod_dpto, "p": periodo},
            )
            cod_pueblos_filtro = [str(x[0]) for x in r.fetchall()]
        elif cod_macro:
            # Resolver dptos/mpios de la macro vía smt_geo.resguardos
            r = await db.execute(
                text("""
                    SELECT DISTINCT pm.cod_pueblo
                    FROM pueblo.pueblo_municipio pm
                    JOIN smt_geo.resguardos g ON pm.cod_mpio = g.mpio_cdpmp
                    WHERE UPPER(TRIM(g.macro)) = UPPER(TRIM(:cm)) AND pm.periodo = :p
                """),
                {"cm": cod_macro, "p": periodo},
            )
            cod_pueblos_filtro = [str(x[0]) for x in r.fetchall()]

        # Query base con filtro opcional
        if cod_pueblos_filtro is not None:
            if not cod_pueblos_filtro:
                return {"periodo": periodo, "total": 0, "data": [],
                        "filtro_aplicado": {"cod_macro": cod_macro, "cod_dpto": cod_dpto, "cod_mpio": cod_mpio}}
            result = await db.execute(
                text("""
                    SELECT cod_pueblo, pueblo,
                           con_discapacidad, sin_discapacidad, total,
                           prevalencia_pct, tasa_x_1000,
                           COALESCE(confiabilidad, 'MEDIA') as confiabilidad
                    FROM pueblo.disc_nacional
                    WHERE periodo = :periodo AND total >= 30
                      AND COALESCE(confiabilidad, '') != 'EXCLUIR'
                      AND cod_pueblo = ANY(:cods)
                    ORDER BY total DESC
                """),
                {"periodo": periodo, "cods": cod_pueblos_filtro},
            )
        else:
            result = await db.execute(
                text("""
                    SELECT cod_pueblo, pueblo,
                           con_discapacidad, sin_discapacidad, total,
                           prevalencia_pct, tasa_x_1000,
                           COALESCE(confiabilidad, 'MEDIA') as confiabilidad
                    FROM pueblo.disc_nacional
                    WHERE periodo = :periodo AND total >= 30
                      AND COALESCE(confiabilidad, '') != 'EXCLUIR'
                    ORDER BY total DESC
                """),
                {"periodo": periodo},
            )
        rows = [dict(r._mapping) for r in result]
        resp = {"periodo": periodo, "total": len(rows), "data": rows}
        if cod_pueblos_filtro is not None:
            resp["filtro_aplicado"] = {"cod_macro": cod_macro, "cod_dpto": cod_dpto, "cod_mpio": cod_mpio}
        return resp
    except Exception as e:
        logger.error("Error en listar_pueblos: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error consultando pueblos: {str(e)}")


@router.get("/{cod_pueblo}/perfil")
async def perfil_pueblo(
    cod_pueblo: str,
    periodo: str = Query("2018"),
    db: AsyncSession = Depends(get_db),
):
    """Perfil completo de capacidades diversas para un pueblo indigena."""
    try:
        params = {"cod_pueblo": cod_pueblo, "periodo": periodo}

        # Prevalencia general
        prevalencia = await db.execute(
            text("""
                SELECT cod_pueblo, pueblo,
                       con_discapacidad, sin_discapacidad, total,
                       prevalencia_pct, tasa_x_1000,
                       COALESCE(confiabilidad, 'MEDIA') as confiabilidad
                FROM pueblo.disc_nacional
                WHERE cod_pueblo = :cod_pueblo AND periodo = :periodo
            """),
            params,
        )
        prev_row = prevalencia.first()
        if not prev_row:
            raise HTTPException(
                status_code=404,
                detail=f"Pueblo con codigo '{cod_pueblo}' no encontrado para periodo '{periodo}'"
            )
        prev_data = dict(prev_row._mapping)

        # Check n>=30 for reliability warning
        confiabilidad = prev_data.get("confiabilidad", "MEDIA")
        if prev_data["total"] < 30:
            confiabilidad = "BAJA"

        # Sexo
        sexo = await db.execute(
            text("""
                SELECT hombres, mujeres, total
                FROM pueblo.sexo_nacional
                WHERE cod_pueblo = :cod_pueblo AND periodo = :periodo
            """),
            params,
        )
        sexo_row = sexo.first()
        sexo_data = dict(sexo_row._mapping) if sexo_row else None

        # Piramide de edad
        edad = await db.execute(
            text("""
                SELECT grupo_edad, valor
                FROM pueblo.edad_nacional
                WHERE cod_pueblo = :cod_pueblo AND periodo = :periodo
                ORDER BY grupo_edad
            """),
            params,
        )
        edad_data = [dict(r._mapping) for r in edad]

        # Limitaciones
        limitaciones = await db.execute(
            text("""
                SELECT limitacion, valor
                FROM pueblo.limitacion_nacional
                WHERE cod_pueblo = :cod_pueblo AND periodo = :periodo
                ORDER BY valor DESC
            """),
            params,
        )
        lim_data = [dict(r._mapping) for r in limitaciones]

        # Tratamiento
        tratamiento = await db.execute(
            text("""
                SELECT tratamiento, valor
                FROM pueblo.tratamiento_nacional
                WHERE cod_pueblo = :cod_pueblo AND periodo = :periodo
                ORDER BY valor DESC
            """),
            params,
        )
        trat_data = [dict(r._mapping) for r in tratamiento]

        # Causas
        causas = await db.execute(
            text("""
                SELECT causa, valor
                FROM pueblo.causa_nacional
                WHERE cod_pueblo = :cod_pueblo AND periodo = :periodo
                ORDER BY valor DESC
            """),
            params,
        )
        causas_data = [dict(r._mapping) for r in causas]

        # Enfermedad
        enfermedad = await db.execute(
            text("""
                SELECT enfermo_si, enfermo_no, no_informa, total
                FROM pueblo.enfermo_nacional
                WHERE cod_pueblo = :cod_pueblo AND periodo = :periodo
            """),
            params,
        )
        enf_row = enfermedad.first()
        enf_data = dict(enf_row._mapping) if enf_row else None

        return {
            "periodo": periodo,
            "cod_pueblo": cod_pueblo,
            "confiabilidad": confiabilidad,
            "prevalencia": prev_data,
            "sexo": sexo_data,
            "piramide_edad": edad_data,
            "limitaciones": lim_data,
            "tratamiento": trat_data,
            "causas": causas_data,
            "enfermedad": enf_data,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error en perfil_pueblo('%s'): %s", cod_pueblo, e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error consultando perfil de pueblo: {str(e)}")


@router.get("/{cod_pueblo}/territorios")
async def territorios_pueblo(
    cod_pueblo: str,
    periodo: str = Query("2018"),
    db: AsyncSession = Depends(get_db),
):
    """Donde vive este pueblo a traves de los departamentos.
    Solo incluye departamentos con total >= 30 para tasas confiables.
    """
    try:
        # Verify the pueblo exists
        check = await db.execute(
            text("""
                SELECT pueblo FROM pueblo.disc_nacional
                WHERE cod_pueblo = :cod_pueblo AND periodo = :periodo
            """),
            {"cod_pueblo": cod_pueblo, "periodo": periodo},
        )
        check_row = check.first()
        if not check_row:
            raise HTTPException(
                status_code=404,
                detail=f"Pueblo con codigo '{cod_pueblo}' no encontrado para periodo '{periodo}'"
            )

        result = await db.execute(
            text("""
                SELECT d.cod_dpto, g.nom_dpto, d.pueblo,
                       d.con_discapacidad, d.sin_discapacidad, d.total,
                       CASE WHEN d.total >= 30
                            THEN d.tasa_x_1000
                            ELSE NULL END AS tasa_x_1000,
                       CASE WHEN d.total >= 30 THEN 'CONFIABLE'
                            ELSE 'NO_CONFIABLE' END AS confiabilidad
                FROM pueblo.disc_dpto d
                LEFT JOIN geo.departamentos g ON d.cod_dpto = g.cod_dpto
                WHERE d.cod_pueblo = :cod_pueblo AND d.periodo = :periodo
                  AND d.cod_dpto != '99'
                ORDER BY d.total DESC
            """),
            {"cod_pueblo": cod_pueblo, "periodo": periodo},
        )
        rows = [dict(r._mapping) for r in result]
        return {"periodo": periodo, "cod_pueblo": cod_pueblo, "total": len(rows), "data": rows}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error en territorios_pueblo('%s'): %s", cod_pueblo, e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error consultando territorios: {str(e)}")


@router.get("/por-municipio/{cod_mpio}")
async def pueblos_en_municipio(
    cod_mpio: str,
    periodo: str = Query("2018"),
    db: AsyncSession = Depends(get_db),
):
    """Que pueblos indigenas estan presentes en un municipio."""
    try:
        result = await db.execute(
            text("""
                SELECT pm.cod_pueblo, pm.pueblo, pm.poblacion,
                       pm.pct_en_mpio, pm.es_dominante,
                       m.nom_mpio
                FROM pueblo.pueblo_municipio pm
                LEFT JOIN geo.municipios m ON pm.cod_mpio = m.cod_mpio
                WHERE pm.cod_mpio = :cod_mpio AND pm.periodo = :periodo
                ORDER BY pm.poblacion DESC
            """),
            {"cod_mpio": cod_mpio, "periodo": periodo},
        )
        rows = [dict(r._mapping) for r in result]
        if not rows:
            raise HTTPException(
                status_code=404,
                detail=f"No se encontraron pueblos en municipio '{cod_mpio}' para periodo '{periodo}'"
            )
        return {"periodo": periodo, "cod_mpio": cod_mpio, "total": len(rows), "data": rows}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error en pueblos_en_municipio('%s'): %s", cod_mpio, e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error consultando pueblos en municipio: {str(e)}")
