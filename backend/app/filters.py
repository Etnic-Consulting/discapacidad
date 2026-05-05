"""B01/B02 · Helper para filtros geográficos cascada.

Resuelve el ámbito (lista de mpios, dptos, pueblos) según los filtros
macro/dpto/mpio/pueblo/resguardo que envíe el frontend, y devuelve
WHERE clauses + parámetros listos para queries SQL.

Filtros son combinables y NO excluyentes:
- macro restringe el universo a sus dptos/mpios
- dpto refina a mpios del dpto
- mpio refina más a un mpio específico
- pueblo cruza con pueblos presentes en el ámbito
- resguardo el filtro más específico
"""
from __future__ import annotations

from dataclasses import dataclass, field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class FiltroGeografico:
    """Resultado de resolver los filtros del request."""
    cod_macro: str | None = None
    cod_dpto: str | None = None
    cod_mpio: str | None = None
    cod_pueblo: str | None = None
    cod_resguardo: str | None = None

    # Listas resueltas
    mpios: list[str] = field(default_factory=list)
    """Lista de cod_mpio del ámbito (vacía = sin restricción geográfica)."""

    dptos: list[str] = field(default_factory=list)
    """Lista de cod_dpto del ámbito."""

    @property
    def aplica_geo(self) -> bool:
        """True si hay alguna restricción geográfica activa."""
        return any([
            self.cod_macro, self.cod_dpto, self.cod_mpio,
            self.cod_resguardo,
        ])

    @property
    def scope_label(self) -> str:
        """Etiqueta de ámbito para logs/headers."""
        parts = []
        if self.cod_macro:
            parts.append(f"macro={self.cod_macro}")
        if self.cod_dpto:
            parts.append(f"dpto={self.cod_dpto}")
        if self.cod_mpio:
            parts.append(f"mpio={self.cod_mpio}")
        if self.cod_pueblo:
            parts.append(f"pueblo={self.cod_pueblo}")
        if self.cod_resguardo:
            parts.append(f"resguardo={self.cod_resguardo}")
        return " · ".join(parts) or "nacional"


async def resolver_filtros(
    db: AsyncSession,
    cod_macro: str | None = None,
    cod_dpto: str | None = None,
    cod_mpio: str | None = None,
    cod_pueblo: str | None = None,
    cod_resguardo: str | None = None,
) -> FiltroGeografico:
    """Resuelve los filtros recibidos en lista de cod_mpio y cod_dpto.

    Precedencia (más específico gana):
    1. cod_resguardo → resguardo específico (mpios derivados de smt_geo.resguardos)
    2. cod_mpio → un solo mpio
    3. cod_dpto → todos los mpios del dpto
    4. cod_macro → todos los mpios de la macrorregión

    cod_pueblo NO restringe el ámbito geográfico, solo filtra por pueblo
    dentro del ámbito.
    """
    f = FiltroGeografico(
        cod_macro=cod_macro,
        cod_dpto=cod_dpto,
        cod_mpio=cod_mpio,
        cod_pueblo=cod_pueblo,
        cod_resguardo=cod_resguardo,
    )

    if cod_resguardo:
        r = await db.execute(
            text("SELECT DISTINCT mpio_cdpmp FROM smt_geo.resguardos WHERE ccdgo_terr = :r"),
            {"r": cod_resguardo},
        )
        f.mpios = [x[0] for x in r.fetchall()]
        f.dptos = list({m[:2] for m in f.mpios})
        return f

    if cod_mpio:
        f.mpios = [cod_mpio]
        f.dptos = [cod_mpio[:2]]
        return f

    if cod_dpto:
        r = await db.execute(
            text("SELECT cod_mpio FROM geo.municipios WHERE cod_dpto = :d ORDER BY cod_mpio"),
            {"d": cod_dpto},
        )
        f.mpios = [x[0] for x in r.fetchall()]
        f.dptos = [cod_dpto]
        return f

    if cod_macro:
        # Fuente canónica: geo.macro_dptos (mapeo oficial ONIC desde Departamentos.gpkg)
        # Resolver TODOS los mpios de los dptos asignados a la macro · cobertura completa
        # incluso para dptos sin resguardos titulados pero con población indígena.
        r = await db.execute(
            text("""
                SELECT m.cod_mpio
                FROM geo.municipios m
                JOIN geo.macro_dptos md ON m.cod_dpto = md.cod_dpto
                WHERE UPPER(TRIM(md.macro)) = UPPER(TRIM(:m))
                ORDER BY m.cod_mpio
            """),
            {"m": cod_macro},
        )
        f.mpios = [x[0] for x in r.fetchall()]
        # Dptos canónicos · NO derivados de los mpios (incluye dptos sin mpios poblados)
        r2 = await db.execute(
            text("""
                SELECT cod_dpto FROM geo.macro_dptos
                WHERE UPPER(TRIM(macro)) = UPPER(TRIM(:m))
                ORDER BY cod_dpto
            """),
            {"m": cod_macro},
        )
        f.dptos = [x[0] for x in r2.fetchall()]
        return f

    return f


def where_mpios(filtro: FiltroGeografico, columna: str = "cod_mpio") -> tuple[str, dict]:
    """Construye una cláusula WHERE para filtrar por mpios del ámbito.

    Returns (clause_str, params_dict). Si no hay filtro geográfico, retorna ("", {}).
    """
    if not filtro.aplica_geo or not filtro.mpios:
        return "", {}
    return f"AND {columna} = ANY(:_filter_mpios)", {"_filter_mpios": filtro.mpios}


def where_dptos(filtro: FiltroGeografico, columna: str = "cod_dpto") -> tuple[str, dict]:
    """Construye WHERE clause para filtrar por dptos del ámbito."""
    if not filtro.aplica_geo or not filtro.dptos:
        return "", {}
    return f"AND {columna} = ANY(:_filter_dptos)", {"_filter_dptos": filtro.dptos}


def where_pueblo(filtro: FiltroGeografico, columna: str = "cod_pueblo") -> tuple[str, dict]:
    """WHERE para filtrar por pueblo específico."""
    if not filtro.cod_pueblo:
        return "", {}
    return f"AND {columna} = :_filter_pueblo", {"_filter_pueblo": filtro.cod_pueblo}
