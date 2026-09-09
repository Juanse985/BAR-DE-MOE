"""Emisión y validación de JWT."""
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import jwt


def crear_token(
    *,
    usuario_id: int,
    usuario: str,
    perfil: str,
    sede_id: int | None,
    secreto: str,
    algoritmo: str = "HS256",
    expira_minutos: int = 60,
) -> tuple[str, str, datetime]:
    """Devuelve (token, jti, fecha_expiracion)."""
    ahora = datetime.now(UTC)
    expira = ahora + timedelta(minutes=expira_minutos)
    jti = str(uuid4())
    payload = {
        "sub": str(usuario_id),
        "usr": usuario,
        "perfil": perfil,
        "sede_id": sede_id,
        "jti": jti,
        "iat": int(ahora.timestamp()),
        "exp": int(expira.timestamp()),
    }
    return jwt.encode(payload, secreto, algorithm=algoritmo), jti, expira


def decodificar_token(token: str, secreto: str, algoritmo: str = "HS256") -> dict[str, Any]:
    """Lanza jwt.PyJWTError si el token es inválido o está vencido."""
    return jwt.decode(token, secreto, algorithms=[algoritmo])
