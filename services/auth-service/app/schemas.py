"""Contratos de entrada y salida del auth-service."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Perfil = Literal["ADMINISTRADOR", "CAJERO", "MESERO"]
Estado = Literal["ACTIVO", "INACTIVO"]


# ---------- Usuarios ----------
class UsuarioCrear(BaseModel):
    cedula: str = Field(min_length=5, max_length=20, examples=["1032456789"])
    nombre: str = Field(min_length=3, max_length=120, examples=["Moe Szyslak"])
    sede_id: int | None = Field(default=None, examples=[1])
    perfil: Perfil = Field(examples=["MESERO"])
    usuario: str = Field(min_length=4, max_length=60, examples=["mszyslak"])
    password: str = Field(min_length=8, max_length=72, examples=["Cerveza2026"])


class UsuarioActualizar(BaseModel):
    nombre: str | None = Field(default=None, min_length=3, max_length=120)
    sede_id: int | None = None
    perfil: Perfil | None = None
    estado: Estado | None = None


class UsuarioSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cedula: str
    nombre: str
    sede_id: int | None
    perfil: Perfil
    usuario: str
    estado: Estado
    bloqueado: bool
    debe_cambiar_password: bool
    creado_en: datetime


# ---------- Autenticación ----------
class LoginEntrada(BaseModel):
    usuario: str = Field(examples=["admin"])
    password: str = Field(examples=["Admin2026"])


class LoginSalida(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expira_en: datetime
    inactividad_segundos: int
    usuario: UsuarioSalida


class CambioPassword(BaseModel):
    password_actual: str
    password_nueva: str = Field(min_length=8, max_length=72)


class RestablecerPassword(BaseModel):
    password_nueva: str = Field(min_length=8, max_length=72)


class SesionValidada(BaseModel):
    usuario_id: int
    usuario: str
    perfil: Perfil
    sede_id: int | None
    segundos_inactivo: float
