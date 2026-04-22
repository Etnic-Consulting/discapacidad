from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.auth import Usuario
from app.models.formulario import RespuestaFormulario
from app.schemas.formulario import RespuestaCreate, RespuestaListItem, RespuestaOut, RespuestaStats
from app.services.auth import get_current_user

router = APIRouter()


@router.post("/respuesta", response_model=RespuestaOut, status_code=status.HTTP_201_CREATED)
async def crear_respuesta(
    payload: RespuestaCreate,
    current: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if payload.cpli_consentimiento != "si":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El consentimiento CPLI es obligatorio para registrar informacion",
        )
    respuesta = RespuestaFormulario(
        usuario_id=current.id,
        cod_pueblo=payload.cod_pueblo,
        cod_dpto=payload.cod_dpto,
        cod_mpio=payload.cod_mpio,
        nombre_comunidad=payload.nombre_comunidad,
        documento_persona=payload.documento_persona,
        datos=payload.datos,
        cpli_consentimiento=payload.cpli_consentimiento,
        notas=payload.notas,
    )
    db.add(respuesta)
    await db.commit()
    await db.refresh(respuesta)
    return RespuestaOut.model_validate(respuesta)


@router.get("/respuestas", response_model=list[RespuestaListItem])
async def listar_respuestas(
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0),
    current: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(RespuestaFormulario).order_by(RespuestaFormulario.fecha_envio.desc())
    if current.rol != "admin":
        stmt = stmt.where(RespuestaFormulario.usuario_id == current.id)
    stmt = stmt.limit(limit).offset(offset)
    result = await db.execute(stmt)
    rows = result.scalars().all()
    return [RespuestaListItem.model_validate(r) for r in rows]


@router.get("/respuestas/{respuesta_id}", response_model=RespuestaOut)
async def obtener_respuesta(
    respuesta_id: int,
    current: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(RespuestaFormulario).where(RespuestaFormulario.id == respuesta_id))
    respuesta = result.scalar_one_or_none()
    if respuesta is None:
        raise HTTPException(status_code=404, detail="No encontrada")
    if current.rol != "admin" and respuesta.usuario_id != current.id:
        raise HTTPException(status_code=403, detail="Sin permiso")
    return RespuestaOut.model_validate(respuesta)


@router.get("/stats", response_model=RespuestaStats)
async def stats(
    current: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    total_q = await db.execute(select(func.count(RespuestaFormulario.id)))
    total = total_q.scalar_one()

    por_pueblo_q = await db.execute(
        select(
            RespuestaFormulario.cod_pueblo,
            func.count(RespuestaFormulario.id).label("n"),
        ).group_by(RespuestaFormulario.cod_pueblo).order_by(func.count(RespuestaFormulario.id).desc()).limit(20)
    )
    por_pueblo = [{"cod_pueblo": r.cod_pueblo, "n": r.n} for r in por_pueblo_q.all()]

    desde = datetime.now(timezone.utc) - timedelta(days=7)
    u7_q = await db.execute(
        select(func.count(RespuestaFormulario.id)).where(RespuestaFormulario.fecha_envio >= desde)
    )
    ultimos_7d = u7_q.scalar_one()

    return RespuestaStats(total=total, por_pueblo=por_pueblo, ultimos_7d=ultimos_7d)


# ============================================================================
# Territorios — combobox cascada para Bloque A del formulario
# Fuente: smt_geo (cartografia ONIC). Endpoints publicos, sin auth.
# ============================================================================


@router.get("/territorios/macros")
async def territorios_macros(db: AsyncSession = Depends(get_db)):
    """5 macrorregiones ONIC. Pre-cargado al abrir el formulario."""
    r = await db.execute(text("""
        SELECT id, macro AS label
        FROM smt_geo.macrorregiones
        ORDER BY macro
    """))
    return [{"id": str(row.id), "label": row.label, "value": row.label} for row in r]


@router.get("/territorios/dptos")
async def territorios_dptos(
    cod_macro: str | None = Query(None, description="Filtrar por macro ONIC"),
    q: str = Query("", description="Filtro por nombre"),
    db: AsyncSession = Depends(get_db),
):
    """Departamentos. Si se pasa cod_macro, restringe a los presentes en esa zona."""
    sql = """
        SELECT DISTINCT c.dpto_ccdgo AS cod, c.dpto_cnmbr AS nombre
        FROM smt_geo.comunidades c
        WHERE c.dpto_ccdgo IS NOT NULL
    """
    params: dict = {}
    if cod_macro:
        sql += " AND UPPER(TRIM(c.macro)) = UPPER(TRIM(:cm))"
        params["cm"] = cod_macro
    if q:
        sql += " AND c.dpto_cnmbr ILIKE :q"
        params["q"] = f"%{q}%"
    sql += " ORDER BY c.dpto_cnmbr LIMIT 60"
    r = await db.execute(text(sql), params)
    return [{"id": row.cod, "label": f"{row.nombre} ({row.cod})", "value": row.cod, "nombre": row.nombre} for row in r]


@router.get("/territorios/mpios")
async def territorios_mpios(
    cod_dpto: str = Query(..., description="Codigo DANE departamento"),
    q: str = Query(""),
    db: AsyncSession = Depends(get_db),
):
    """Municipios del departamento."""
    sql = """
        SELECT DISTINCT c.mpio_cdpmp AS cod, c.mpio_cnmbr AS nombre
        FROM smt_geo.comunidades c
        WHERE c.dpto_ccdgo = :cd AND c.mpio_cdpmp IS NOT NULL
    """
    params = {"cd": cod_dpto}
    if q:
        sql += " AND c.mpio_cnmbr ILIKE :q"
        params["q"] = f"%{q}%"
    sql += " ORDER BY c.mpio_cnmbr LIMIT 100"
    r = await db.execute(text(sql), params)
    return [{"id": row.cod, "label": f"{row.nombre} ({row.cod})", "value": row.cod, "nombre": row.nombre} for row in r]


@router.get("/territorios/resguardos")
async def territorios_resguardos(
    cod_mpio: str | None = Query(None),
    cod_dpto: str | None = Query(None),
    q: str = Query(""),
    db: AsyncSession = Depends(get_db),
):
    """Resguardos / territorios. Filtrables por mpio o dpto, con typeahead por nombre o pueblo."""
    sql = """
        SELECT DISTINCT r.ccdgo_terr AS cod,
               r.territorio        AS nombre,
               r.pueblo_onic       AS pueblo,
               r.mpio_cdpmp        AS cod_mpio
        FROM smt_geo.resguardos r
        WHERE r.ccdgo_terr IS NOT NULL
    """
    params: dict = {}
    if cod_mpio:
        sql += " AND r.mpio_cdpmp = :cm"
        params["cm"] = cod_mpio
    elif cod_dpto:
        sql += " AND LEFT(r.mpio_cdpmp, 2) = :cd"
        params["cd"] = cod_dpto
    if q:
        sql += " AND (r.territorio ILIKE :q OR r.pueblo_onic ILIKE :q)"
        params["q"] = f"%{q}%"
    sql += " ORDER BY r.territorio LIMIT 100"
    r = await db.execute(text(sql), params)
    return [
        {
            "id": row.cod,
            "label": f"{row.nombre}" + (f" — {row.pueblo}" if row.pueblo else ""),
            "value": row.cod,
            "nombre": row.nombre,
            "pueblo": row.pueblo,
            "cod_mpio": row.cod_mpio,
        }
        for row in r
    ]


@router.get("/territorios/comunidades")
async def territorios_comunidades(
    cod_mpio: str | None = Query(None),
    cod_dpto: str | None = Query(None),
    cod_resguardo: str | None = Query(None),
    q: str = Query(""),
    db: AsyncSession = Depends(get_db),
):
    """Comunidades indigenas (puntos cartografia ONIC). Typeahead por nombre.

    Sin filtro padre y q vacio → vacio (lista demasiado grande, ~13.8k).
    """
    if not (cod_mpio or cod_dpto or cod_resguardo or q):
        return []
    sql = """
        SELECT DISTINCT c.comun_ccdgo AS cod,
               c.comun_cnmbr        AS nombre,
               c.mpio_cnmbr         AS mpio,
               c.mpio_cdpmp         AS cod_mpio,
               c.dpto_ccdgo         AS cod_dpto,
               c.macro              AS macro,
               c.ccdgo_terr         AS cod_resguardo,
               c.territorio         AS resguardo,
               c.pueblo_onic        AS pueblo
        FROM smt_geo.comunidades c
        WHERE c.comun_cnmbr IS NOT NULL
    """
    params: dict = {}
    if cod_resguardo:
        sql += " AND c.ccdgo_terr = :cr"
        params["cr"] = cod_resguardo
    if cod_mpio:
        sql += " AND c.mpio_cdpmp = :cm"
        params["cm"] = cod_mpio
    elif cod_dpto:
        sql += " AND c.dpto_ccdgo = :cd"
        params["cd"] = cod_dpto
    if q:
        sql += " AND c.comun_cnmbr ILIKE :q"
        params["q"] = f"%{q}%"
    sql += " ORDER BY c.comun_cnmbr LIMIT 80"
    r = await db.execute(text(sql), params)
    return [
        {
            "id": row.cod or row.nombre,
            "label": f"{row.nombre}" + (f" ({row.mpio})" if row.mpio else ""),
            "value": row.nombre,
            "nombre": row.nombre,
            "cod_mpio": row.cod_mpio,
            "cod_dpto": row.cod_dpto,
            "macro": row.macro,
            "cod_resguardo": row.cod_resguardo,
            "resguardo": row.resguardo,
            "pueblo": row.pueblo,
        }
        for row in r
    ]
