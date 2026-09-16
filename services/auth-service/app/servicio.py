from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import User, Auditoria, RolEnum
from app.security import hash_password, verify_password, crear_access_token, nuevo_session_id
from app.config import settings
from app import schemas


def registrar_auditoria(db: Session, usuario: Optional[User], accion: str, detalle: str = None, ip: str = None):
    entrada = Auditoria(
        usuario_id=usuario.id if usuario else None,
        username=usuario.username if usuario else None,
        accion=accion,
        detalle=detalle,
        ip=ip,
    )
    db.add(entrada)
    db.commit()


# ---------- HU-001 / HU-002: login + bloqueo por intentos fallidos ----------

def autenticar_usuario(db: Session, username: str, password: str, ip: str = None) -> schemas.TokenRespuesta:
    user = db.query(User).filter(User.username == username).first()

    if user is None:
        registrar_auditoria(db, None, "LOGIN_FALLIDO", f"Usuario inexistente: {username}", ip)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")

    if user.bloqueado_hasta and user.bloqueado_hasta > datetime.utcnow():
        registrar_auditoria(db, user, "LOGIN_BLOQUEADO", "Intento de acceso a cuenta bloqueada", ip)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Cuenta bloqueada hasta {user.bloqueado_hasta.isoformat()}",
        )

    if not user.activo:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cuenta inactiva")

    if not verify_password(password, user.hashed_password):
        user.intentos_fallidos += 1
        detalle = f"Intento {user.intentos_fallidos}/{settings.max_failed_attempts}"

        if user.intentos_fallidos >= settings.max_failed_attempts:
            user.bloqueado_hasta = datetime.utcnow() + timedelta(minutes=settings.lockout_minutes)
            db.commit()
            registrar_auditoria(db, user, "CUENTA_BLOQUEADA", "Se alcanzó el máximo de intentos fallidos", ip)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Cuenta bloqueada por {settings.lockout_minutes} minutos tras superar los intentos permitidos",
            )

        db.commit()
        registrar_auditoria(db, user, "LOGIN_FALLIDO", detalle, ip)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")

    # login correcto -> resetea intentos y abre sesión única (HU-003)
    user.intentos_fallidos = 0
    user.bloqueado_hasta = None
    session_id = nuevo_session_id()
    user.session_id = session_id
    user.ultima_actividad = datetime.utcnow()
    db.commit()

    token = crear_access_token(user.username, session_id)
    registrar_auditoria(db, user, "LOGIN_EXITOSO", None, ip)

    return schemas.TokenRespuesta(access_token=token, expira_en_minutos=settings.access_token_expire_minutes)


def cerrar_sesion(db: Session, user: User, ip: str = None):
    user.session_id = None
    db.commit()
    registrar_auditoria(db, user, "LOGOUT", None, ip)


# ---------- HU-007: gestión de usuarios (CRUD) ----------

def crear_usuario(db: Session, datos: schemas.UsuarioCrear, creado_por: User) -> User:
    if db.query(User).filter(User.username == datos.username).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El nombre de usuario ya existe")
    if db.query(User).filter(User.email == datos.email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El correo ya está registrado")

    nuevo = User(
        username=datos.username,
        email=datos.email,
        hashed_password=hash_password(datos.password),
        rol=datos.rol,
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    registrar_auditoria(db, creado_por, "USUARIO_CREADO", f"Usuario creado: {nuevo.username} (rol={nuevo.rol.value})")
    return nuevo


def listar_usuarios(db: Session) -> List[User]:
    return db.query(User).all()


def obtener_usuario(db: Session, user_id: int) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return user


def actualizar_usuario(db: Session, user_id: int, datos: schemas.UsuarioActualizar, actualizado_por: User) -> User:
    user = obtener_usuario(db, user_id)
    if datos.email is not None:
        user.email = datos.email
    if datos.rol is not None:
        user.rol = datos.rol
    if datos.activo is not None:
        user.activo = datos.activo
    db.commit()
    db.refresh(user)
    registrar_auditoria(db, actualizado_por, "USUARIO_ACTUALIZADO", f"Usuario actualizado: {user.username}")
    return user


def eliminar_usuario(db: Session, user_id: int, eliminado_por: User):
    # Solo el admin llega aquí (se controla en la ruta con get_admin_user)
    user = obtener_usuario(db, user_id)
    if user.id == eliminado_por.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No puede eliminar su propia cuenta")
    username = user.username
    db.delete(user)
    db.commit()
    registrar_auditoria(db, eliminado_por, "USUARIO_ELIMINADO", f"Usuario eliminado: {username}")


# ---------- HU-005 / HU-006: contraseñas ----------

def cambiar_password_propio(db: Session, user: User, datos: schemas.CambioPasswordPropio):
    if not verify_password(datos.password_actual, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="La contraseña actual es incorrecta")
    user.hashed_password = hash_password(datos.password_nueva)
    db.commit()
    registrar_auditoria(db, user, "CAMBIO_PASSWORD_PROPIO", None)


def resetear_password_admin(db: Session, user_id: int, datos: schemas.ResetPasswordAdmin, admin: User):
    user = obtener_usuario(db, user_id)
    user.hashed_password = hash_password(datos.password_nueva)
    user.intentos_fallidos = 0
    user.bloqueado_hasta = None
    user.session_id = None  # fuerza a que el usuario vuelva a iniciar sesión
    db.commit()
    registrar_auditoria(db, admin, "RESET_PASSWORD_ADMIN", f"Contraseña restablecida para: {user.username}")


# ---------- HU-008: auditoría ----------

def consultar_auditoria(
    db: Session, usuario_id: Optional[int] = None, accion: Optional[str] = None, limite: int = 100
) -> List[Auditoria]:
    query = db.query(Auditoria)
    if usuario_id is not None:
        query = query.filter(Auditoria.usuario_id == usuario_id)
    if accion is not None:
        query = query.filter(Auditoria.accion == accion)
    return query.order_by(Auditoria.fecha.desc()).limit(limite).all()
