from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, func, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base, relationship

from app.models.auth import Base, SCHEMA  # reuse same Base


class RespuestaFormulario(Base):
    __tablename__ = "respuestas_formulario"
    __table_args__ = (
        Index("ix_respuestas_pueblo", "cod_pueblo"),
        Index("ix_respuestas_mpio", "cod_mpio"),
        Index("ix_respuestas_fecha", "fecha_envio"),
        {"schema": SCHEMA},
    )

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey(f"{SCHEMA}.usuarios.id", ondelete="RESTRICT"), nullable=False)
    cod_pueblo = Column(String(10), index=True)
    cod_dpto = Column(String(5))
    cod_mpio = Column(String(10))
    nombre_comunidad = Column(String(200))
    documento_persona = Column(String(40))
    fecha_envio = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    # Full form payload: territorio, identificacion, demografia, capacidades, salud, etc.
    datos = Column(JSONB, nullable=False)
    cpli_consentimiento = Column(String(10), nullable=False, default="no")
    notas = Column(Text)

    usuario = relationship("Usuario")
