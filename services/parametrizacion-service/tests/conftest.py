"""Configuración de pruebas del parametrizacion-service.

Este servicio no emite tokens: los valida. Por eso las pruebas firman un JWT
con el mismo secreto, igual que haría el auth-service en producción.
"""
import os
import tempfile
from pathlib import Path

TMP = Path(tempfile.mkdtemp(prefix="param-test-"))
os.environ["DATABASE_URL"] = f"sqlite:///{TMP / 'param_test.db'}"
os.environ["JWT_SECRET"] = "secreto-de-pruebas"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.config import config  # noqa: E402
from app.main import SessionLocal, app  # noqa: E402
from barmoe_common.db import Base  # noqa: E402
from barmoe_common.tokens import crear_token  # noqa: E402


def _encabezado(usuario_id: int, usuario: str, perfil: str, sede_id: int | None = 1) -> dict:
    token, _, _ = crear_token(
        usuario_id=usuario_id,
        usuario=usuario,
        perfil=perfil,
        sede_id=sede_id,
        secreto=config.JWT_SECRET,
        algoritmo=config.JWT_ALGORITMO,
        expira_minutos=30,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def cliente():
    Base.metadata.drop_all(bind=SessionLocal.engine)
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def admin() -> dict:
    return _encabezado(1, "admin", "ADMINISTRADOR", None)


@pytest.fixture()
def mesero() -> dict:
    return _encabezado(2, "mszyslak", "MESERO", 1)


@pytest.fixture()
def catalogo(cliente, admin) -> dict:
    """Crea una sede, un tipo y un proveedor para las pruebas de producto."""
    sede = cliente.post("/sedes", headers=admin, json={"nombre": "Bar de Moe · Centro"}).json()
    tipo = cliente.post("/tipos-producto", headers=admin, json={"nombre": "Cerveza"}).json()
    proveedor = cliente.post(
        "/proveedores", headers=admin, json={"nit": "900123456-1", "nombre": "Distribuidora Duff"}
    ).json()
    return {"sede": sede, "tipo": tipo, "proveedor": proveedor}
