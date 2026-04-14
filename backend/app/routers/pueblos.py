"""
Pueblos indigenas - Perfiles de capacidades diversas por pueblo.
"""

import logging
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/")
async def listar_pueblos(
    periodo: str = Query("2018"),
    db: AsyncSession = Depends(get_db),
):
    """Lista todos los pueblos con poblacion y prevalencia de capacidades diversas.
    Solo incluye pueblos con total >= 30 para tasas confiables.
    """
    try:
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
        return {"periodo": periodo, "total": len(rows), "data": rows}
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
