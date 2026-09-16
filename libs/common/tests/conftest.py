"""Pruebas de la librería común (barmoe_common).

Se arma una app mínima con `crear_app`, igual que hacen los microservicios,
para probar lo transversal sin depender de ningún servicio en particular:
X-Request-Id, SLA de 2 segundos, errores uniformes, JWT, cifrado y auditoría.
"""
import tempfile
import time
from pathlib import Path

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy import select

from barmoe_common.app import crear_app
from barmoe_common.auditoria import Auditoria
from barmoe_common.config import ConfigBase
from barmoe_common.db import Base, crear_session_factory, dependencia_db
from barmoe_common.deps import UsuarioActual, construir_autenticacion
from barmoe_common.errors import ErrorApp
from barmoe_common.tokens import crear_token

SECRETO = "secreto-de-pruebas-common"


class ConfigPrueba(ConfigBase):
    APP_NAME: str = "servicio-de-prueba"
    JWT_SECRET: str = SECRETO
    SLA_SEGUNDOS: float = 0.2


def firmar(perfil: str = "ADMINISTRADOR", sede_id: int | None = 1, *, usuario_id: int = 7,
           usuario: str = "moe", secreto: str = SECRETO, expira_minutos: int = 30) -> dict:
    token, _, _ = crear_token(usuario_id=usuario_id, usuario=usuario, perfil=perfil,
                              sede_id=sede_id, secreto=secreto, expira_minutos=expira_minutos)
    return {"Authorization": f"Bearer {token}"}


def construir(auditar: bool = True):
    tmp = Path(tempfile.mkdtemp(prefix="common-test-"))
    fabrica = crear_session_factory(f"sqlite:///{tmp / 'common.db'}")
    Base.metadata.create_all(bind=fabrica.engine)
    config = ConfigPrueba()
    app = crear_app(config, titulo="prueba", descripcion="prueba",
                    auditar_rechazos=fabrica if auditar else None)
    get_db = dependencia_db(fabrica)
    usuario_actual, requiere_perfil = construir_autenticacion(SECRETO)

    @app.get("/lento")
    def lento():
        time.sleep(0.3)  # supera el SLA de 0.2 s de esta config
        return {"ok": True}

    @app.get("/solo-admin")
    def solo_admin(u: UsuarioActual = Depends(requiere_perfil("ADMINISTRADOR"))):
        return {"usuario": u.usuario, "sede_id": u.sede_id}

    @app.get("/error-negocio")
    def error_negocio():
        raise ErrorApp("REGLA_ROTA", "Una regla de negocio falló.", 409)

    @app.get("/con-parametro")
    def con_parametro(numero: int):
        return {"numero": numero}

    @app.get("/auditorias")
    def auditorias(db=Depends(get_db)):
        return [
            {"accion": a.accion, "usuario": a.usuario, "sede_id": a.sede_id, "resultado": a.resultado,
             "ip": a.ip, "request_id": a.request_id, "detalle": a.detalle}
            for a in db.scalars(select(Auditoria).order_by(Auditoria.id))
        ]

    return app, fabrica


@pytest.fixture()
def app_y_fabrica():
    return construir(auditar=True)


@pytest.fixture()
def cliente(app_y_fabrica):
    app, _ = app_y_fabrica
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def fabrica(app_y_fabrica):
    return app_y_fabrica[1]
