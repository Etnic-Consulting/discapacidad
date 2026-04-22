from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


class RespuestaCreate(BaseModel):
    cod_pueblo: str | None = Field(None, max_length=10)
    cod_dpto: str | None = Field(None, max_length=5)
    cod_mpio: str | None = Field(None, max_length=10)
    nombre_comunidad: str | None = Field(None, max_length=200)
    documento_persona: str | None = Field(None, max_length=40)
    datos: dict[str, Any]
    cpli_consentimiento: str = Field(default="no", pattern=r"^(si|no)$")
    notas: str | None = None


class RespuestaOut(BaseModel):
    id: int
    usuario_id: int
    cod_pueblo: str | None
    cod_dpto: str | None
    cod_mpio: str | None
    nombre_comunidad: str | None
    documento_persona: str | None
    fecha_envio: datetime
    cpli_consentimiento: str
    notas: str | None
    datos: dict[str, Any]

    model_config = {"from_attributes": True}


class RespuestaListItem(BaseModel):
    id: int
    cod_pueblo: str | None
    nombre_comunidad: str | None
    documento_persona: str | None
    fecha_envio: datetime
    cpli_consentimiento: str

    model_config = {"from_attributes": True}


class RespuestaStats(BaseModel):
    total: int
    por_pueblo: list[dict[str, Any]]
    ultimos_7d: int
