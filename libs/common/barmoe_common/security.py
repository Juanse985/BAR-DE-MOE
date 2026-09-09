"""Cifrado de contraseñas — RNF-08.

Nunca se guarda la contraseña en texto plano: solo el hash bcrypt con sal.
"""
import bcrypt

RONDAS = 12


def hashear_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(RONDAS)).decode("utf-8")


def verificar_password(password: str, hash_guardado: str) -> bool:
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
