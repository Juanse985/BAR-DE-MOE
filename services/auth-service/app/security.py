import uuid
from datetime import datetime, timedelta
from typing import Optional

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    # Recorta la contraseña a 72 bytes para evitar el fallo de bcrypt/passlib
    pwd_bytes = password.encode('utf-8')[:72]
    return pwd_context.hash(pwd_bytes.decode('utf-8', errors='ignore'))


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def crear_access_token(username: str, session_id: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": username, "jti": session_id, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decodificar_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError:
        return None


def nuevo_session_id() -> str:
    return uuid.uuid4().hex
