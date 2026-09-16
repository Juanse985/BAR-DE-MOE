"""auth-service — M1 Seguridad y gestión de usuarios.

Cubre del tablero: campos del usuario, tres perfiles, cifrado de contraseñas,
bloqueo por reintentos, sesión única, inactividad de 3 minutos, cambio de
contraseña por administrador y por usuario, y trazabilidad de cada acción.
"""
from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, FastAPI, Query, Request, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from barmoe_common.app import crear_app
from barmoe_common.auditoria import contexto_http, router_consulta
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
    auditar_rechazos=SessionLocal,  # DEF-05 · C-1: los 401/403 quedan en la auditoría
)


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
    token, expira, usuario = servicio.login(db, datos.usuario, datos.password, **contexto_http(request))
    return LoginSalida(
        access_token=token,
        expira_en=expira,
        inactividad_segundos=config.INACTIVIDAD_SEGUNDOS,
        usuario=UsuarioSalida.model_validate(usuario),
    )


@auth.post("/logout", summary="Cerrar sesión")
def logout(request: Request, token: UsuarioActual = Depends(usuario_token), db: Session = Depends(get_db)):
    servicio.logout(db, token.jti, **contexto_http(request))
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
    request: Request,
    usuario: Usuario = Depends(usuario_db),
    db: Session = Depends(get_db),
):
    servicio.cambiar_password(db, usuario, datos.password_actual, datos.password_nueva,
                              **contexto_http(request))
    return {"mensaje": "Contraseña actualizada."}


# =================================================================  USUARIOS
def _objetivo(db: Session, usuario_id: int) -> Usuario:
    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise ErrorApp("NO_ENCONTRADO", "El usuario no existe.", 404)
    return usuario


usuarios = APIRouter(prefix="/usuarios", tags=["usuarios"])
solo_admin = requiere_perfil("ADMINISTRADOR")


@usuarios.post("", response_model=UsuarioSalida, status_code=201, summary="Crear usuario")
def crear(
    datos: UsuarioCrear,
    request: Request,
    _: UsuarioActual = Depends(solo_admin),
    admin: Usuario = Depends(usuario_db),
    db: Session = Depends(get_db),
):
    return servicio.crear_usuario(db, datos, admin, **contexto_http(request))


@usuarios.get("", response_model=list[UsuarioSalida], summary="Listar usuarios (paginado)")
def listar(
    response: Response,
    _: UsuarioActual = Depends(solo_admin),
    db: Session = Depends(get_db),
    sede_id: int | None = None,
    perfil: str | None = None,
    estado: str | None = None,
    pagina: int = Query(default=1, ge=1),
    tamano: int = Query(default=100, ge=1, le=500),
):
    """HU-007 criterio 4: filtros por sede y perfil, y resultado paginado.

    Sigue devolviendo una lista (así el frontend no cambia); el total va en
    la cabecera `X-Total-Count`.
    """
    filtros = []
    if sede_id is not None:
        filtros.append(Usuario.sede_id == sede_id)
    if perfil:
        filtros.append(Usuario.perfil == perfil.upper())
    if estado:
        filtros.append(Usuario.estado == estado.upper())
    response.headers["X-Total-Count"] = str(
        db.scalar(select(func.count()).select_from(Usuario).where(*filtros))
    )
    consulta = (select(Usuario).where(*filtros).order_by(Usuario.nombre, Usuario.id)
                .offset((pagina - 1) * tamano).limit(tamano))
    return list(db.scalars(consulta))


@usuarios.get("/{usuario_id}", response_model=UsuarioSalida, summary="Consultar usuario")
def obtener(usuario_id: int, _: UsuarioActual = Depends(solo_admin), db: Session = Depends(get_db)):
    return _objetivo(db, usuario_id)


@usuarios.patch("/{usuario_id}", response_model=UsuarioSalida, summary="Actualizar usuario")
def actualizar(
    usuario_id: int,
    datos: UsuarioActualizar,
    request: Request,
    _: UsuarioActual = Depends(solo_admin),
    admin: Usuario = Depends(usuario_db),
    db: Session = Depends(get_db),
):
    objetivo = _objetivo(db, usuario_id)
    return servicio.actualizar_usuario(db, admin, objetivo, datos.model_dump(exclude_unset=True),
                                       **contexto_http(request))


@usuarios.post("/{usuario_id}/inactivar", response_model=UsuarioSalida, summary="Inactivar usuario")
def inactivar(
    usuario_id: int,
    request: Request,
    _: UsuarioActual = Depends(solo_admin),
    admin: Usuario = Depends(usuario_db),
    db: Session = Depends(get_db),
):
    """Reemplaza el DELETE de Angel: el usuario no se borra, se inactiva (HU-007 criterio 5)."""
    objetivo = _objetivo(db, usuario_id)
    if objetivo.estado == "INACTIVO":
        raise ErrorApp("USUARIO_YA_INACTIVO", "El usuario ya está inactivo.", 409)
    return servicio.actualizar_usuario(db, admin, objetivo, {"estado": "INACTIVO"},
                                       accion="INACTIVAR_USUARIO", **contexto_http(request))


@usuarios.post("/{usuario_id}/activar", response_model=UsuarioSalida, summary="Activar usuario")
def activar(
    usuario_id: int,
    request: Request,
    _: UsuarioActual = Depends(solo_admin),
    admin: Usuario = Depends(usuario_db),
    db: Session = Depends(get_db),
):
    objetivo = _objetivo(db, usuario_id)
    if objetivo.estado == "ACTIVO":
        raise ErrorApp("USUARIO_YA_ACTIVO", "El usuario ya está activo.", 409)
    return servicio.actualizar_usuario(db, admin, objetivo, {"estado": "ACTIVO"},
                                       accion="ACTIVAR_USUARIO", **contexto_http(request))


@usuarios.post("/{usuario_id}/restablecer-password", summary="Restablecer contraseña (admin)")
def restablecer(
    usuario_id: int,
    datos: RestablecerPassword,
    request: Request,
    _: UsuarioActual = Depends(solo_admin),
    admin: Usuario = Depends(usuario_db),
    db: Session = Depends(get_db),
):
    objetivo = _objetivo(db, usuario_id)
    servicio.restablecer_password(db, admin, objetivo, datos.password_nueva, **contexto_http(request))
    return {"mensaje": "Contraseña restablecida. El usuario deberá cambiarla al ingresar."}


@usuarios.post("/{usuario_id}/desbloquear", summary="Desbloquear usuario (admin)")
def desbloquear(
    usuario_id: int,
    request: Request,
    _: UsuarioActual = Depends(solo_admin),
    admin: Usuario = Depends(usuario_db),
    db: Session = Depends(get_db),
):
    objetivo = _objetivo(db, usuario_id)
    servicio.desbloquear(db, admin, objetivo, **contexto_http(request))
    return {"mensaje": "Usuario desbloqueado."}


app.include_router(auth)
app.include_router(usuarios)
# HU-008 (aporte de Angel): GET /auditoria, solo ADMINISTRADOR, paginado y de solo lectura.
app.include_router(router_consulta(get_db, solo_admin))
