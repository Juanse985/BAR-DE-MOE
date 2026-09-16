"""Cifrado de contraseñas — RNF-08.

Nunca se guarda la contraseña en texto plano: solo el hash bcrypt con sal.
"""
import re

import bcrypt

RONDAS = 12

# $2a$/$2b$/$2y$ + costo de dos dígitos + 53 caracteres (22 de sal + 31 de hash)
_FORMATO_BCRYPT = re.compile(r"\$2[aby]\$\d{2}\$[./A-Za-z0-9]{53}")


def hashear_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(RONDAS)).decode("utf-8")


def verificar_password(password: str, hash_guardado: str) -> bool:
    # bcrypt (Rust) entra en pánico — no lanza ValueError — si el hash está
    # truncado o mal formado. Un pánico no se puede capturar como Exception,
    # así que el formato se valida antes de llamarlo (hallazgo QA, HU-027).
    if not isinstance(hash_guardado, str) or not _FORMATO_BCRYPT.fullmatch(hash_guardado):
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hash_guardado.encode("utf-8"))
    except (ValueError, TypeError):
        return False


REGLAS_PASSWORD = (
    "Mínimo 8 caracteres, con al menos una mayúscula, una minúscula y un número."
)


def password_es_valida(password: str) -> tuple[bool, str]:
    if len(password) < 8:
        return False, REGLAS_PASSWORD
    if not any(c.isupper() for c in password):
        return False, REGLAS_PASSWORD
    if not any(c.islower() for c in password):
        return False, REGLAS_PASSWORD
    if not any(c.isdigit() for c in password):
        return False, REGLAS_PASSWORD
    return True, ""
