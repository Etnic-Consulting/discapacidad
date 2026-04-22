import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.auth import Usuario, SesionToken

TOKEN_LIFETIME_HOURS = 12
bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    if salt is None:
        salt = secrets.token_hex(16)
    digest = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return digest, salt


def verify_password(password: str, password_hash: str, salt: str) -> bool:
    digest, _ = hash_password(password, salt)
    return secrets.compare_digest(digest, password_hash)


def generate_token() -> str:
    return secrets.token_urlsafe(48)


async def authenticate_user(db: AsyncSession, username: str, password: str) -> Usuario | None:
    result = await db.execute(select(Usuario).where(Usuario.username == username, Usuario.activo.is_(True)))
    user = result.scalar_one_or_none()
    if user is None:
        return None
    if not verify_password(password, user.password_hash, user.salt):
        return None
    return user


async def create_session(db: AsyncSession, user: Usuario) -> SesionToken:
    token = generate_token()
    expires = datetime.now(timezone.utc) + timedelta(hours=TOKEN_LIFETIME_HOURS)
    session = SesionToken(token=token, usuario_id=user.id, expires_at=expires)
    db.add(session)
    user.last_login = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(session)
    return session


async def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Usuario:
    if creds is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token requerido")
    result = await db.execute(
        select(SesionToken).where(SesionToken.token == creds.credentials, SesionToken.revoked.is_(False))
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalido")
    expires_at = session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expirado")
    user_result = await db.execute(select(Usuario).where(Usuario.id == session.usuario_id, Usuario.activo.is_(True)))
    user = user_result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario inactivo")
    return user


async def revoke_token(db: AsyncSession, token: str) -> None:
    result = await db.execute(select(SesionToken).where(SesionToken.token == token))
    session = result.scalar_one_or_none()
    if session is not None:
        session.revoked = True
        await db.commit()
