from typing import List, Optional

from fastapi import FastAPI, Depends, Request
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.dependencies import get_current_user, get_admin_user
from app import schemas, servicio
from app.models import User, RolEnum
from app.config import settings

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Auth Service", version="1.0.0")


@app.on_event("startup")
def crear_admin_inicial():
    """Si no existe ningún admin, crea uno con las credenciales de config.py."""
    from app.security import hash_password

    db = next(get_db())
    existe_admin = db.query(User).filter(User.rol == RolEnum.admin).first()
    if not existe_admin:
        admin = User(
            username=settings.default_admin_username,
            email=settings.default_admin_email,
            hashed_password=hash_password(settings.default_admin_password),
            rol=RolEnum.admin,
        )
        db.add(admin)
        db.commit()
    db.close()


def get_client_ip(request: Request) -> Optional[str]:
    return request.client.host if request.client else None


@app.get("/health", tags=["Salud"])
def health(db: Session = Depends(get_db)):
    """Usado por el HEALTHCHECK del Dockerfile. Verifica que la app y la BD respondan."""
    from sqlalchemy import text

    db.execute(text("SELECT 1"))
    return {"status": "ok"}


# ---------------- AUTH: HU-001, HU-002, HU-003, HU-004 ----------------

@app.post("/auth/login", response_model=schemas.TokenRespuesta, tags=["Auth"])
def login(datos: schemas.LoginRequest, request: Request, db: Session = Depends(get_db)):
    return servicio.autenticar_usuario(db, datos.username, datos.password, get_client_ip(request))


@app.post("/auth/logout", tags=["Auth"])
def logout(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    servicio.cerrar_sesion(db, user, get_client_ip(request))
    return {"mensaje": "Sesión cerrada correctamente"}


@app.get("/auth/me", response_model=schemas.UsuarioRespuesta, tags=["Auth"])
def perfil_propio(user: User = Depends(get_current_user)):
    return user


# ---------------- HU-005: cambio de password propio ----------------

@app.patch("/users/me/password", tags=["Usuarios"])
def cambiar_mi_password(
    datos: schemas.CambioPasswordPropio,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    servicio.cambiar_password_propio(db, user, datos)
    return {"mensaje": "Contraseña actualizada correctamente"}


# ---------------- HU-007: gestión de usuarios (CRUD, solo admin) ----------------

@app.post("/users", response_model=schemas.UsuarioRespuesta, status_code=201, tags=["Usuarios"])
def crear_usuario(
    datos: schemas.UsuarioCrear,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    return servicio.crear_usuario(db, datos, admin)


@app.get("/users", response_model=List[schemas.UsuarioRespuesta], tags=["Usuarios"])
def listar_usuarios(admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    return servicio.listar_usuarios(db)


@app.get("/users/{user_id}", response_model=schemas.UsuarioRespuesta, tags=["Usuarios"])
def obtener_usuario(user_id: int, admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    return servicio.obtener_usuario(db, user_id)


@app.put("/users/{user_id}", response_model=schemas.UsuarioRespuesta, tags=["Usuarios"])
def actualizar_usuario(
    user_id: int,
    datos: schemas.UsuarioActualizar,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    return servicio.actualizar_usuario(db, user_id, datos, admin)


@app.delete("/users/{user_id}", status_code=204, tags=["Usuarios"])
def eliminar_usuario(user_id: int, admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    # Solo un admin llega aquí gracias a get_admin_user -> cumple "solo el admin borra usuarios"
    servicio.eliminar_usuario(db, user_id, admin)


# ---------------- HU-006: restablecer password (admin) ----------------

@app.post("/users/{user_id}/reset-password", tags=["Usuarios"])
def resetear_password(
    user_id: int,
    datos: schemas.ResetPasswordAdmin,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    servicio.resetear_password_admin(db, user_id, datos, admin)
    return {"mensaje": "Contraseña restablecida correctamente"}


# ---------------- HU-008: consulta de auditoría (solo admin) ----------------

@app.get("/audit", response_model=List[schemas.AuditoriaRespuesta], tags=["Auditoría"])
def consultar_auditoria(
    usuario_id: Optional[int] = None,
    accion: Optional[str] = None,
    limite: int = 100,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    return servicio.consultar_auditoria(db, usuario_id, accion, limite)
