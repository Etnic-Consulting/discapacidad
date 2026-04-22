from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.auth import Usuario
from app.schemas.auth import LoginRequest, TokenResponse, UserOut
from app.services.auth import authenticate_user, create_session, get_current_user, revoke_token

router = APIRouter()
bearer_scheme = HTTPBearer(auto_error=False)


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, payload.username, payload.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales invalidas")
    session = await create_session(db, user)
    return TokenResponse(
        access_token=session.token,
        expires_at=session.expires_at,
        user=UserOut.model_validate(user),
    )


@router.post("/logout")
async def logout(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    if creds is not None:
        await revoke_token(db, creds.credentials)
    return {"status": "ok"}


@router.get("/me", response_model=UserOut)
async def me(current: Usuario = Depends(get_current_user)):
    return UserOut.model_validate(current)
