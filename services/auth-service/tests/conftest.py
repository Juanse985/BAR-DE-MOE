"""Configuración de pruebas del auth-service.

Las pruebas corren sobre SQLite en un archivo temporal: no necesitan Docker
ni Postgres, así el CI y los portátiles del equipo van rápido.
"""
import os
import tempfile
from pathlib import Path

TMP = Path(tempfile.mkdtemp(prefix="auth-test-"))
os.environ["DATABASE_URL"] = f"sqlite:///{TMP / 'auth_test.db'}"
os.environ["JWT_SECRET"] = "secreto-de-pruebas"
os.environ["MAX_INTENTOS_LOGIN"] = "3"
os.environ["INACTIVIDAD_SEGUNDOS"] = "180"
os.environ["ADMIN_USUARIO"] = "admin"
os.environ["ADMIN_PASSWORD"] = "Admin2026"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.config import config  # noqa: E402
from app.main import SessionLocal, app  # noqa: E402
from barmoe_common.db import Base  # noqa: E402


@pytest.fixture()
def cliente():
    Base.metadata.drop_all(bind=SessionLocal.engine)
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def token_admin(cliente):
    respuesta = cliente.post(
        "/auth/login",
        json={"usuario": config.ADMIN_USUARIO, "password": config.ADMIN_PASSWORD},
    )
    assert respuesta.status_code == 200, respuesta.text
    return respuesta.json()["access_token"]


@pytest.fixture()
def encabezado_admin(token_admin):
    return {"Authorization": f"Bearer {token_admin}"}
