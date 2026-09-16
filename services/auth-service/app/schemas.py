from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.models import RolEnum


class UsuarioBase(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr


class UsuarioCrear(UsuarioBase):
    password: str = Field(min_length=8)
    rol: RolEnum = RolEnum.usuario


class UsuarioActualizar(BaseModel):
    email: Optional[EmailStr] = None
    rol: Optional[RolEnum] = None
    activo: Optional[bool] = None


class UsuarioRespuesta(UsuarioBase):
    id: int
    rol: RolEnum
    activo: bool
    creado_en: datetime

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenRespuesta(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expira_en_minutos: int


class CambioPasswordPropio(BaseModel):
    password_actual: str
    password_nueva: str = Field(min_length=8)


class ResetPasswordAdmin(BaseModel):
    password_nueva: str = Field(min_length=8)


class AuditoriaRespuesta(BaseModel):
    id: int
    usuario_id: Optional[int]
    username: Optional[str]
    accion: str
    detalle: Optional[str]
    ip: Optional[str]
    fecha: datetime

    class Config:
        from_attributes = True
