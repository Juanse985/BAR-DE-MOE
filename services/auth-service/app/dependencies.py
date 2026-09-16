from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, RolEnum
from app.security import decodificar_token
from app.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    from app.servicio import registrar_auditoria  # import local para evitar ciclo

    credenciales_invalidas = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar la sesión",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decodificar_token(token)
    if payload is None:
        raise credenciales_invalidas

    username = payload.get("sub")
    jti = payload.get("jti")
    if username is None or jti is None:
        raise credenciales_invalidas

    user = db.query(User).filter(User.username == username).first()
    if user is None or not user.activo:
        raise credenciales_invalidas

    # HU-003: sesión única por usuario -> el jti del token debe coincidir con la
    # sesión activa guardada en la BD. Si alguien inició sesión después, este token muere.
    # Si PERMITIR_MULTISESION=true, se omite esta validación y varios tokens pueden convivir.
    if not settings.permitir_multisesion and user.session_id != jti:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="La sesión fue cerrada porque se inició sesión en otro dispositivo",
        )

    # HU-004: cierre de sesión por inactividad
    if user.ultima_actividad:
        limite = user.ultima_actividad + timedelta(seconds=settings.inactivity_timeout_seconds)
        if datetime.utcnow() > limite:
            user.session_id = None
            db.commit()
            registrar_auditoria(db, user, "SESION_EXPIRADA_INACTIVIDAD", "Cierre automático por inactividad")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Sesión cerrada por inactividad, inicia sesión nuevamente",
            )

    user.ultima_actividad = datetime.utcnow()
    db.commit()
    return user


def get_admin_user(user: User = Depends(get_current_user)) -> User:
    if user.rol != RolEnum.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Requiere privilegios de administrador")
    return user
