"""Dependencias de autorización reutilizables por los microservicios.

El gateway ya validó la sesión (inactividad y sesión única) antes de enrutar,
pero cada servicio vuelve a validar la FIRMA del token: defensa en profundidad.
Ningún servicio confía solamente en cabeceras inyectadas.
"""
from dataclasses import dataclass

import jwt
from fastapi import Depends, Header

from .errors import ErrorApp
from .tokens import decodificar_token


@dataclass(frozen=True)
class UsuarioActual:
    id: int
    usuario: str
    perfil: str
    sede_id: int | None
    jti: str


PERFILES = ("ADMINISTRADOR", "CAJERO", "MESERO")  # RNF-05: tres perfiles


def construir_autenticacion(secreto: str, algoritmo: str = "HS256"):
    """Fabrica las dependencias `usuario_actual` y `requiere_perfil`."""

    def usuario_actual(authorization: str | None = Header(default=None)) -> UsuarioActual:
        if not authorization or not authorization.lower().startswith("bearer "):
            raise ErrorApp("NO_AUTENTICADO", "Falta el token de acceso.", 401)
        token = authorization.split(" ", 1)[1].strip()
        try:
            datos = decodificar_token(token, secreto, algoritmo)
        except jwt.ExpiredSignatureError as exc:
            raise ErrorApp("SESION_EXPIRADA", "La sesión expiró. Inicie sesión de nuevo.", 401) from exc
        except jwt.PyJWTError as exc:
            raise ErrorApp("TOKEN_INVALIDO", "El token de acceso no es válido.", 401) from exc
        return UsuarioActual(
            id=int(datos["sub"]),
            usuario=datos["usr"],
            perfil=datos["perfil"],
            sede_id=datos.get("sede_id"),
            jti=datos["jti"],
        )

    def requiere_perfil(*perfiles: str):
        def _verificar(usuario: UsuarioActual = Depends(usuario_actual)) -> UsuarioActual:
            if usuario.perfil not in perfiles:
                raise ErrorApp(
                    "SIN_PERMISOS",
                    f"El perfil {usuario.perfil} no puede ejecutar esta operación.",
                    403,
                )
            return usuario

        return _verificar

    return usuario_actual, requiere_perfil
