"""Reglas de negocio del auth-service.

Aquí vive todo lo que el tablero exigió sobre seguridad. La capa de routers
solo traduce HTTP; las decisiones se toman en este archivo.
"""
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from barmoe_common.auditoria import Auditoria, registrar
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
def _ip_excedida(db: Session, ip: str | None) -> bool:
    """OBS-02: demasiados logins fallidos desde la misma IP, sin importar el usuario."""
    if not ip or config.MAX_INTENTOS_POR_IP <= 0:
        return False
    desde = ahora_utc() - timedelta(minutes=config.VENTANA_IP_MINUTOS)
    fallidos = db.scalar(
        select(func.count()).select_from(Auditoria).where(
            Auditoria.accion == "LOGIN", Auditoria.resultado == "FALLIDO",
            Auditoria.ip == ip, Auditoria.fecha >= desde,
        )
    )
    return fallidos >= config.MAX_INTENTOS_POR_IP


def _vencio_bloqueo_temporal(usuario: Usuario) -> bool:
    return (usuario.bloqueado and usuario.bloqueado_hasta is not None
            and _aware(usuario.bloqueado_hasta) <= ahora_utc())


def login(
    db: Session, usuario_str: str, password: str, ip: str | None = None,
    request_id: str | None = None,
) -> tuple[str, datetime, Usuario]:
    ctx = {"ip": ip, "request_id": request_id}

    if _ip_excedida(db, ip):
        registrar(db, accion="LOGIN", usuario=usuario_str, resultado="BLOQUEADO",
                  detalle="demasiados intentos fallidos desde esta IP", **ctx)
        db.commit()
        raise ErrorApp(
            "DEMASIADOS_INTENTOS",
            f"Demasiados intentos fallidos desde este equipo. Espere {config.VENTANA_IP_MINUTOS} minutos.",
            429,
        )

    usuario = buscar_por_usuario(db, usuario_str)

    # Mensaje genérico a propósito: no revelamos si el usuario existe (OWASP).
    if usuario is None:
        registrar(db, accion="LOGIN", usuario=usuario_str, resultado="FALLIDO",
                  detalle="usuario inexistente", **ctx)
        db.commit()
        raise ErrorApp("CREDENCIALES_INVALIDAS", "Usuario o contraseña incorrectos.", 401)

    if _vencio_bloqueo_temporal(usuario):
        usuario.bloqueado = False
        usuario.bloqueado_hasta = None
        usuario.intentos_fallidos = 0
        registrar(db, accion="DESBLOQUEO_AUTOMATICO", usuario_id=usuario.id, usuario=usuario.usuario,
                  sede_id=usuario.sede_id, detalle=f"venció el bloqueo de {config.BLOQUEO_MINUTOS} min",
                  **ctx)

    if usuario.bloqueado:
        registrar(db, accion="LOGIN", usuario_id=usuario.id, usuario=usuario.usuario,
                  sede_id=usuario.sede_id, resultado="BLOQUEADO", **ctx)
        db.commit()
        mensaje = "La cuenta está bloqueada por intentos fallidos. Contacte al administrador."
        if usuario.bloqueado_hasta is not None:
            mensaje += f" Se desbloqueará sola en {config.BLOQUEO_MINUTOS} minutos como máximo."
        raise ErrorApp("USUARIO_BLOQUEADO", mensaje, 423)

    if usuario.estado != "ACTIVO":
        registrar(db, accion="LOGIN", usuario_id=usuario.id, usuario=usuario.usuario,
                  sede_id=usuario.sede_id, resultado="INACTIVO", **ctx)
        db.commit()
        raise ErrorApp("USUARIO_INACTIVO", "El usuario se encuentra inactivo.", 403)

    if not verificar_password(password, usuario.password_hash):
        # RNF-09 · bloqueo por reintentos
        usuario.intentos_fallidos += 1
        motivo = "password incorrecta"
        if usuario.intentos_fallidos >= config.MAX_INTENTOS_LOGIN:
            usuario.bloqueado = True
            if config.BLOQUEO_MINUTOS > 0:
                usuario.bloqueado_hasta = ahora_utc() + timedelta(minutes=config.BLOQUEO_MINUTOS)
            motivo = f"bloqueado tras {usuario.intentos_fallidos} intentos"
        registrar(db, accion="LOGIN", usuario_id=usuario.id, usuario=usuario.usuario,
                  sede_id=usuario.sede_id, resultado="FALLIDO", detalle=motivo, **ctx)
        db.commit()
        raise ErrorApp("CREDENCIALES_INVALIDAS", "Usuario o contraseña incorrectos.", 401)

    # RNF-10 · sesión única
    activas = [s for s in sesiones_activas(db, usuario.id) if not esta_inactiva(s)]
    vencidas = [s for s in sesiones_activas(db, usuario.id) if esta_inactiva(s)]
    for sesion in vencidas:
        cerrar_sesion(db, sesion, "INACTIVIDAD")

    if activas and not config.PERMITIR_MULTISESION:
        registrar(db, accion="LOGIN", usuario_id=usuario.id, usuario=usuario.usuario,
                  sede_id=usuario.sede_id, resultado="RECHAZADO", detalle="ya tiene una sesión activa",
                  **ctx)
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
              sede_id=usuario.sede_id, resultado="OK", **ctx)
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
    usuario = db.get(Usuario, usuario_id)
    if usuario is None or usuario.estado != "ACTIVO":
        cerrar_sesion(db, sesion, "USUARIO_INACTIVO")
        db.commit()
        raise ErrorApp("USUARIO_INACTIVO", "El usuario no está habilitado.", 403)
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


def logout(db: Session, jti: str, **ctx) -> None:
    sesion = db.get(Sesion, jti)
    if sesion and sesion.activa:
        cerrar_sesion(db, sesion, "LOGOUT")
        usuario = db.get(Usuario, sesion.usuario_id)
        # DEF-03: el logout ahora dice quién salió y de qué sede.
        registrar(db, accion="LOGOUT", usuario_id=sesion.usuario_id,
                  usuario=usuario.usuario if usuario else None,
                  sede_id=usuario.sede_id if usuario else None, resultado="OK", **ctx)
        db.commit()


# ------------------------------------------------------------- contraseñas
def _validar_reglas(password: str) -> None:
    ok, mensaje = password_es_valida(password)
    if not ok:
        raise ErrorApp("PASSWORD_DEBIL", mensaje, 422)


def cambiar_password(db: Session, usuario: Usuario, actual: str, nueva: str, **ctx) -> None:
    """RNF-07 · el propio usuario cambia su contraseña."""
    if not verificar_password(actual, usuario.password_hash):
        raise ErrorApp("CREDENCIALES_INVALIDAS", "La contraseña actual no es correcta.", 401)
    if verificar_password(nueva, usuario.password_hash):
        raise ErrorApp("PASSWORD_REPETIDA", "La nueva contraseña debe ser distinta de la actual.", 422)
    _validar_reglas(nueva)
    usuario.password_hash = hashear_password(nueva)
    usuario.debe_cambiar_password = False
    registrar(db, accion="CAMBIO_PASSWORD", usuario_id=usuario.id, usuario=usuario.usuario,
              sede_id=usuario.sede_id, resultado="OK", **ctx)
    db.commit()


def restablecer_password(db: Session, admin: Usuario, objetivo: Usuario, nueva: str, **ctx) -> None:
    """RNF-07 · el administrador restablece la contraseña de otro usuario."""
    _validar_reglas(nueva)
    objetivo.password_hash = hashear_password(nueva)
    objetivo.debe_cambiar_password = True
    objetivo.intentos_fallidos = 0
    objetivo.bloqueado = False
    objetivo.bloqueado_hasta = None
    for sesion in sesiones_activas(db, objetivo.id):
        cerrar_sesion(db, sesion, "RESTABLECIMIENTO")
    registrar(db, accion="RESTABLECER_PASSWORD", usuario_id=admin.id, usuario=admin.usuario,
              sede_id=admin.sede_id, entidad="usuarios", entidad_id=objetivo.id, resultado="OK",
              detalle=f"a {objetivo.usuario}", **ctx)
    db.commit()


def desbloquear(db: Session, admin: Usuario, objetivo: Usuario, **ctx) -> None:
    objetivo.bloqueado = False
    objetivo.bloqueado_hasta = None
    objetivo.intentos_fallidos = 0
    registrar(db, accion="DESBLOQUEAR_USUARIO", usuario_id=admin.id, usuario=admin.usuario,
              sede_id=admin.sede_id, entidad="usuarios", entidad_id=objetivo.id, resultado="OK",
              detalle=f"a {objetivo.usuario}", **ctx)
    db.commit()


# ---------------------------------------------------------------- usuarios
def crear_usuario(db: Session, datos, admin: Usuario | None = None, **ctx) -> Usuario:
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
        debe_cambiar_password=True,
    )
    db.add(usuario)
    db.flush()
    registrar(db, accion="CREAR_USUARIO",
              usuario_id=admin.id if admin else None,
              usuario=admin.usuario if admin else "sistema",
              sede_id=admin.sede_id if admin else None,
              entidad="usuarios", entidad_id=usuario.id, resultado="OK",
              detalle=f"{usuario.usuario} ({usuario.perfil})", **ctx)
    db.commit()
    db.refresh(usuario)
    return usuario


def actualizar_usuario(db: Session, admin: Usuario, objetivo: Usuario, cambios: dict,
                       accion: str = "ACTUALIZAR_USUARIO", **ctx) -> Usuario:
    """HU-007: editar, activar o inactivar. DEF-02: ahora queda en la auditoría."""
    quita_admin = cambios.get("perfil", "ADMINISTRADOR") != "ADMINISTRADOR"
    if objetivo.id == admin.id and (cambios.get("estado") == "INACTIVO" or quita_admin):
        # Aporte de Angel: nadie se quita el acceso a sí mismo por error.
        raise ErrorApp("OPERACION_SOBRE_SI_MISMO",
                       "No puede inactivar su propia cuenta ni quitarse el perfil de administrador.", 409)
    for campo, valor in cambios.items():
        setattr(objetivo, campo, valor)
    if cambios.get("estado") == "INACTIVO":
        # Arreglo de Felipe (DEF-04): un usuario inactivo pierde sus sesiones.
        for sesion in sesiones_activas(db, objetivo.id):
            cerrar_sesion(db, sesion, "USUARIO_INACTIVO")
    registrar(db, accion=accion, usuario_id=admin.id, usuario=admin.usuario, sede_id=admin.sede_id,
              entidad="usuarios", entidad_id=objetivo.id, resultado="OK",
              detalle=", ".join(f"{k}={v}" for k, v in cambios.items()) or "sin cambios", **ctx)
    db.commit()
    db.refresh(objetivo)
    return objetivo


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
