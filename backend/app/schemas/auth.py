from datetime import datetime
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=80)
    password: str = Field(..., min_length=3, max_length=200)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    user: "UserOut"


class UserOut(BaseModel):
    id: int
    username: str
    nombre: str
    email: str | None = None
    rol: str
    pueblo_asignado: str | None = None

    model_config = {"from_attributes": True}


TokenResponse.model_rebuild()
