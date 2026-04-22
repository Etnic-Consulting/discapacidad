from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, func
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base(metadata=None)

SCHEMA = "smt"


class Usuario(Base):
    __tablename__ = "usuarios"
    __table_args__ = {"schema": SCHEMA}

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(80), unique=True, nullable=False, index=True)
    password_hash = Column(String(128), nullable=False)
    salt = Column(String(32), nullable=False)
    nombre = Column(String(200), nullable=False)
    email = Column(String(200))
    rol = Column(String(40), nullable=False, default="dinamizador")
    pueblo_asignado = Column(String(10))
    activo = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True))


class SesionToken(Base):
    __tablename__ = "sesion_tokens"
    __table_args__ = {"schema": SCHEMA}

    id = Column(Integer, primary_key=True)
    token = Column(String(64), unique=True, nullable=False, index=True)
    usuario_id = Column(Integer, ForeignKey(f"{SCHEMA}.usuarios.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked = Column(Boolean, nullable=False, default=False)

    usuario = relationship("Usuario")
