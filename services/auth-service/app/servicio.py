"""Reglas de negocio del auth-service.

Aquí vive todo lo que el tablero exigió sobre seguridad. La capa de routers
solo traduce HTTP; las decisiones se toman en este archivo.
"""
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from barmoe_common.auditoria import registrar
from barmoe_common.errors import ErrorApp
from barmoe_common.security import hashear_password, password_es_valida, verificar_password
from barmoe_common.tokens import crear_token

from .config import config
from .models import Sesion, Usuario, ahora_utc


def _aware(fecha: datetime) -> datetime:
    """SQLite devuelve datetimes sin zona; los normalizamos a UTC."""
    return fecha if fecha.tzinfo else fecha.replace(tzinfo=UTC)


def buscar_por_usuario(db: Session, usuario: str) -> Usuario | None:
    return db.scalar(select(Usuario).where(Usuario.usuario == usuario))


def sesiones_activas(db: Session, usuario_id: int) -> list[Sesion]:
    return list(db.scalars(select(Sesion).where(Sesion.usuario_id == usuario_id, Sesion.activa.is_(True))))


def cerrar_sesion(db: Session, sesion: Sesion, motivo: str) -> None:
    sesion.activa = False
    sesion.cerrada_en = ahora_utc()
    sesion.motivo_cierre = motivo


def esta_inactiva(sesion: Sesion) -> bool:
    """RNF-03: más de INACTIVIDAD_SEGUNDOS sin actividad cierra la sesión."""
    transcurrido = (ahora_utc() - _aware(sesion.ultima_actividad)).total_seconds()
    return transcurrido > config.INACTIVIDAD_SEGUNDOS


# ------------------------------------------------------------------ login
def login(
    db: Session, usuario_str: str, password: str, ip: str | None = None
) -> tuple[str, datetime, Usuario]:
    usuario = buscar_por_usuario(db, usuario_str)

    # Mensaje genérico a propósito: no revelamos si el usuario existe (OWASP).
    if usuario is None:
        registrar(db, accion="LOGIN", usuario=usuario_str, resultado="FALLIDO", ip=ip,
                  detalle="usuario inexistente")
        db.commit()
        raise ErrorApp("CREDENCIALES_INVALIDAS", "Usuario o contraseña incorrectos.", 401)

    if usuario.bloqueado:
        registrar(db, accion="LOGIN", usuario_id=usuario.id, usuario=usuario.usuario,
                  sede_id=usuario.sede_id, resultado="BLOQUEADO", ip=ip)
        db.commit()
        raise ErrorApp(
            "USUARIO_BLOQUEADO",
            "La cuenta está bloqueada por intentos fallidos. Contacte al administrador.",
            423,
        )

    if usuario.estado != "ACTIVO":
        registrar(db, accion="LOGIN", usuario_id=usuario.id, usuario=usuario.usuario,
                  sede_id=usuario.sede_id, resultado="INACTIVO", ip=ip)
        db.commit()
        raise ErrorApp("USUARIO_INACTIVO", "El usuario se encuentra inactivo.", 403)

    if not verificar_password(password, usuario.password_hash):
        # RNF-09 · bloqueo por reintentos
        usuario.intentos_fallidos += 1
        motivo = "password incorrecta"
        if usuario.intentos_fallidos >= config.MAX_INTENTOS_LOGIN:
            usuario.bloqueado = True
            motivo = f"bloqueado tras {usuario.intentos_fallidos} intentos"
        registrar(db, accion="LOGIN", usuario_id=usuario.id, usuario=usuario.usuario,
                  sede_id=usuario.sede_id, resultado="FALLIDO", ip=ip, detalle=motivo)
        db.commit()
        raise ErrorApp("CREDENCIALES_INVALIDAS", "Usuario o contraseña incorrectos.", 401)

    # RNF-10 · sesión única
    activas = [s for s in sesiones_activas(db, usuario.id) if not esta_inactiva(s)]
    vencidas = [s for s in sesiones_activas(db, usuario.id) if esta_inactiva(s)]
    for s in vencidas:
        cerrar_sesion(db, s, "INACTIVIDAD")

    if activas and not config.PERMITIR_MULTISESION:
        db.commit()
        raise ErrorApp(
            "SESION_ACTIVA",
            "Este usuario ya tiene una sesión abierta. Ciérrela antes de volver a entrar.",
            409,
        )

    token, jti, expira = crear_token(
        usuario_id=usuario.id,
        usuario=usuario.usuario,
        perfil=usuario.perfil,
        sede_id=usuario.sede_id,
        secreto=config.JWT_SECRET,
        algoritmo=config.JWT_ALGORITMO,
        expira_minutos=config.JWT_EXPIRA_MINUTOS,
    )

    usuario.intentos_fallidos = 0
    db.add(Sesion(jti=jti, usuario_id=usuario.id, ip=ip))
    registrar(db, accion="LOGIN", usuario_id=usuario.id, usuario=usuario.usuario,
              sede_id=usuario.sede_id, resultado="OK", ip=ip)
    db.commit()
    return token, expira, usuario


# ------------------------------------------------------- validación sesión
def validar_sesion(db: Session, jti: str, usuario_id: int) -> tuple[Sesion, float]:
    """Usada por el gateway en cada request. Refresca la ventana de inactividad.

    Devuelve la sesión y los segundos que llevaba inactiva ANTES del refresco.
    """
    sesion = db.get(Sesion, jti)
    if sesion is None or not sesion.activa:
        raise ErrorApp("SESION_CERRADA", "La sesión no está activa.", 401)
    if sesion.usuario_id != usuario_id:
        raise ErrorApp("TOKEN_INVALIDO", "El token no corresponde a la sesión.", 401)
    if esta_inactiva(sesion):
        cerrar_sesion(db, sesion, "INACTIVIDAD")
        db.commit()
        raise ErrorApp(
            "SESION_EXPIRADA",
            f"Sesión cerrada por inactividad de más de {config.INACTIVIDAD_SEGUNDOS} segundos.",
            401,
        )
    inactivo = (ahora_utc() - _aware(sesion.ultima_actividad)).total_seconds()
    sesion.ultima_actividad = ahora_utc()
    db.commit()
    return sesion, inactivo


def logout(db: Session, jti: str) -> None:
    sesion = db.get(Sesion, jti)
    if sesion and sesion.activa:
        cerrar_sesion(db, sesion, "LOGOUT")
        registrar(db, accion="LOGOUT", usuario_id=sesion.usuario_id, resultado="OK")
        db.commit()


# ------------------------------------------------------------- contraseñas
def _validar_reglas(password: str) -> None:
    ok, mensaje = password_es_valida(password)
    if not ok:
        raise ErrorApp("PASSWORD_DEBIL", mensaje, 422)


def cambiar_password(db: Session, usuario: Usuario, actual: str, nueva: str) -> None:
    """RNF-07 · el propio usuario cambia su contraseña."""
    if not verificar_password(actual, usuario.password_hash):
        raise ErrorApp("CREDENCIALES_INVALIDAS", "La contraseña actual no es correcta.", 401)
    if verificar_password(nueva, usuario.password_hash):
        raise ErrorApp("PASSWORD_REPETIDA", "La nueva contraseña debe ser distinta de la actual.", 422)
    _validar_reglas(nueva)
    usuario.password_hash = hashear_password(nueva)
    usuario.debe_cambiar_password = False
    registrar(db, accion="CAMBIO_PASSWORD", usuario_id=usuario.id, usuario=usuario.usuario,
              sede_id=usuario.sede_id, resultado="OK")
    db.commit()


def restablecer_password(db: Session, admin: Usuario, objetivo: Usuario, nueva: str) -> None:
    """RNF-07 · el administrador restablece la contraseña de otro usuario."""
    _validar_reglas(nueva)
    objetivo.password_hash = hashear_password(nueva)
    objetivo.debe_cambiar_password = True
    objetivo.intentos_fallidos = 0
    objetivo.bloqueado = False
    for s in sesiones_activas(db, objetivo.id):
        cerrar_sesion(db, s, "RESTABLECIMIENTO")
    registrar(db, accion="RESTABLECER_PASSWORD", usuario_id=admin.id, usuario=admin.usuario,
              entidad="usuarios", entidad_id=objetivo.id, resultado="OK")
    db.commit()


def desbloquear(db: Session, admin: Usuario, objetivo: Usuario) -> None:
    objetivo.bloqueado = False
    objetivo.intentos_fallidos = 0
    registrar(db, accion="DESBLOQUEAR_USUARIO", usuario_id=admin.id, usuario=admin.usuario,
              entidad="usuarios", entidad_id=objetivo.id, resultado="OK")
    db.commit()


# ---------------------------------------------------------------- usuarios
def crear_usuario(db: Session, datos, admin: Usuario | None = None) -> Usuario:
    if db.scalar(select(Usuario).where(Usuario.usuario == datos.usuario)):
        raise ErrorApp("USUARIO_DUPLICADO", f"Ya existe el usuario '{datos.usuario}'.", 409)
    if db.scalar(select(Usuario).where(Usuario.cedula == datos.cedula)):
        raise ErrorApp("CEDULA_DUPLICADA", f"Ya existe un usuario con la cédula {datos.cedula}.", 409)
    _validar_reglas(datos.password)

    usuario = Usuario(
        cedula=datos.cedula,
        nombre=datos.nombre,
        sede_id=datos.sede_id,
        perfil=datos.perfil,
        usuario=datos.usuario,
        password_hash=hashear_password(datos.password),
        estado="ACTIVO",
    )
    db.add(usuario)
    db.flush()
    registrar(db, accion="CREAR_USUARIO",
              usuario_id=admin.id if admin else None,
              usuario=admin.usuario if admin else "sistema",
              entidad="usuarios", entidad_id=usuario.id, resultado="OK")
    db.commit()
    db.refresh(usuario)
    return usuario


def asegurar_admin_inicial(db: Session) -> None:
    """Crea el administrador por defecto si la tabla está vacía."""
    if db.scalar(select(Usuario).limit(1)):
        return
    usuario = Usuario(
        cedula=config.ADMIN_CEDULA,
        nombre=config.ADMIN_NOMBRE,
        sede_id=None,
        perfil="ADMINISTRADOR",
        usuario=config.ADMIN_USUARIO,
        password_hash=hashear_password(config.ADMIN_PASSWORD),
        estado="ACTIVO",
        debe_cambiar_password=True,
    )
    db.add(usuario)
    registrar(db, accion="BOOTSTRAP_ADMIN", usuario="sistema", resultado="OK",
              detalle="administrador inicial creado")
    db.commit()
