"""auth-service — M1 Seguridad y gestión de usuarios.

Cubre del tablero: campos del usuario, tres perfiles, cifrado de contraseñas,
bloqueo por reintentos, sesión única, inactividad de 3 minutos, cambio de
contraseña por administrador y por usuario, y trazabilidad de cada acción.
"""
from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, FastAPI, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from barmoe_common.app import crear_app
from barmoe_common.db import Base, crear_session_factory, dependencia_db
from barmoe_common.deps import UsuarioActual, construir_autenticacion
from barmoe_common.errors import ErrorApp

from . import servicio
from .config import config
from .models import Usuario
from .schemas import (
    CambioPassword,
    LoginEntrada,
    LoginSalida,
    RestablecerPassword,
    SesionValidada,
    UsuarioActualizar,
    UsuarioCrear,
    UsuarioSalida,
)

SessionLocal = crear_session_factory(config.DATABASE_URL)
get_db = dependencia_db(SessionLocal)
usuario_token, requiere_perfil = construir_autenticacion(config.JWT_SECRET, config.JWT_ALGORITMO)

@asynccontextmanager
async def ciclo_de_vida(_: FastAPI):
    """Crea las tablas y siembra el administrador inicial al arrancar."""
    Base.metadata.create_all(bind=SessionLocal.engine)
    with SessionLocal() as db:
        servicio.asegurar_admin_inicial(db)
    yield


app = crear_app(
    config,
    titulo="Bar de Moe · auth-service",
    descripcion="M1 · Seguridad y gestión de usuarios. DATHEON S.A.S.",
    lifespan=ciclo_de_vida,
)


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def usuario_db(
    token: UsuarioActual = Depends(usuario_token),
    db: Session = Depends(get_db),
) -> Usuario:
    """Convierte el token en la fila real del usuario."""
    usuario = db.get(Usuario, token.id)
    if usuario is None or usuario.estado != "ACTIVO":
        raise ErrorApp("USUARIO_INACTIVO", "El usuario no está habilitado.", 403)
    return usuario


# =====================================================================  AUTH
auth = APIRouter(prefix="/auth", tags=["autenticación"])


@auth.post("/login", response_model=LoginSalida, summary="Iniciar sesión")
def login(datos: LoginEntrada, request: Request, db: Session = Depends(get_db)):
    token, expira, usuario = servicio.login(db, datos.usuario, datos.password, _ip(request))
    return LoginSalida(
        access_token=token,
        expira_en=expira,
        inactividad_segundos=config.INACTIVIDAD_SEGUNDOS,
        usuario=UsuarioSalida.model_validate(usuario),
    )


@auth.post("/logout", summary="Cerrar sesión")
def logout(token: UsuarioActual = Depends(usuario_token), db: Session = Depends(get_db)):
    servicio.logout(db, token.jti)
    return {"mensaje": "Sesión cerrada."}


@auth.post("/validar-sesion", response_model=SesionValidada,
           summary="Validar sesión (uso interno del gateway)")
def validar_sesion(token: UsuarioActual = Depends(usuario_token), db: Session = Depends(get_db)):
    _, segundos_inactivo = servicio.validar_sesion(db, token.jti, token.id)
    return SesionValidada(
        usuario_id=token.id,
        usuario=token.usuario,
        perfil=token.perfil,
        sede_id=token.sede_id,
        segundos_inactivo=round(segundos_inactivo, 2),
    )


@auth.get("/me", response_model=UsuarioSalida, summary="Datos del usuario en sesión")
def me(usuario: Usuario = Depends(usuario_db)):
    return usuario


@auth.post("/cambiar-password", summary="Cambiar la propia contraseña")
def cambiar_password(
    datos: CambioPassword,
    usuario: Usuario = Depends(usuario_db),
    db: Session = Depends(get_db),
):
    servicio.cambiar_password(db, usuario, datos.password_actual, datos.password_nueva)
    return {"mensaje": "Contraseña actualizada."}


# =================================================================  USUARIOS
usuarios = APIRouter(prefix="/usuarios", tags=["usuarios"])
solo_admin = requiere_perfil("ADMINISTRADOR")


@usuarios.post("", response_model=UsuarioSalida, status_code=201, summary="Crear usuario")
def crear(
    datos: UsuarioCrear,
    _: UsuarioActual = Depends(solo_admin),
    admin: Usuario = Depends(usuario_db),
    db: Session = Depends(get_db),
):
    return servicio.crear_usuario(db, datos, admin)


@usuarios.get("", response_model=list[UsuarioSalida], summary="Listar usuarios")
def listar(
    _: UsuarioActual = Depends(solo_admin),
    db: Session = Depends(get_db),
    sede_id: int | None = None,
    perfil: str | None = None,
):
    consulta = select(Usuario)
    if sede_id is not None:
        consulta = consulta.where(Usuario.sede_id == sede_id)
    if perfil:
        consulta = consulta.where(Usuario.perfil == perfil)
    return list(db.scalars(consulta.order_by(Usuario.nombre)))


@usuarios.get("/{usuario_id}", response_model=UsuarioSalida, summary="Consultar usuario")
def obtener(usuario_id: int, _: UsuarioActual = Depends(solo_admin), db: Session = Depends(get_db)):
    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise ErrorApp("NO_ENCONTRADO", "El usuario no existe.", 404)
    return usuario


@usuarios.patch("/{usuario_id}", response_model=UsuarioSalida, summary="Actualizar usuario")
def actualizar(
    usuario_id: int,
    datos: UsuarioActualizar,
    _: UsuarioActual = Depends(solo_admin),
    db: Session = Depends(get_db),
):
    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise ErrorApp("NO_ENCONTRADO", "El usuario no existe.", 404)
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(usuario, campo, valor)
    db.commit()
    db.refresh(usuario)
    return usuario


@usuarios.post("/{usuario_id}/restablecer-password", summary="Restablecer contraseña (admin)")
def restablecer(
    usuario_id: int,
    datos: RestablecerPassword,
    _: UsuarioActual = Depends(solo_admin),
    admin: Usuario = Depends(usuario_db),
    db: Session = Depends(get_db),
):
    objetivo = db.get(Usuario, usuario_id)
    if objetivo is None:
        raise ErrorApp("NO_ENCONTRADO", "El usuario no existe.", 404)
    servicio.restablecer_password(db, admin, objetivo, datos.password_nueva)
    return {"mensaje": "Contraseña restablecida. El usuario deberá cambiarla al ingresar."}


@usuarios.post("/{usuario_id}/desbloquear", summary="Desbloquear usuario (admin)")
def desbloquear(
    usuario_id: int,
    _: UsuarioActual = Depends(solo_admin),
    admin: Usuario = Depends(usuario_db),
    db: Session = Depends(get_db),
):
    objetivo = db.get(Usuario, usuario_id)
    if objetivo is None:
        raise ErrorApp("NO_ENCONTRADO", "El usuario no existe.", 404)
    servicio.desbloquear(db, admin, objetivo)
    return {"mensaje": "Usuario desbloqueado."}


app.include_router(auth)
app.include_router(usuarios)
