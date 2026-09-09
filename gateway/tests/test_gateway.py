"""Pruebas del gateway.

Los microservicios se sustituyen por un transporte simulado de httpx, así estas
pruebas corren sin Docker y sin levantar auth ni parametrización de verdad.
"""
import os

os.environ["JWT_SECRET"] = "secreto-de-pruebas"

import httpx  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.config import config  # noqa: E402
from app.main import app  # noqa: E402

TOKEN = {"Authorization": "Bearer token-de-prueba"}


def _transporte(sesion_valida: bool = True) -> httpx.MockTransport:
    def responder(peticion: httpx.Request) -> httpx.Response:
        ruta = peticion.url.path
        if ruta == "/auth/validar-sesion":
            if sesion_valida:
                return httpx.Response(200, json={
                    "usuario_id": 1, "usuario": "admin", "perfil": "ADMINISTRADOR",
                    "sede_id": None, "segundos_inactivo": 1.0,
                })
            return httpx.Response(401, json={
                "error": {"codigo": "SESION_EXPIRADA", "mensaje": "Sesión cerrada por inactividad."}
            })
        if ruta == "/health":
            return httpx.Response(200, json={"estado": "ok"})
        if ruta == "/auth/login":
            return httpx.Response(200, json={"access_token": "abc", "token_type": "bearer"})
        if ruta == "/sedes":
            return httpx.Response(200, json=[{"id": 1, "nombre": "Bar de Moe · Centro"}])
        return httpx.Response(404, json={"error": {"codigo": "NO_ENCONTRADO", "mensaje": ruta}})

    return httpx.MockTransport(responder)


@pytest.fixture()
def cliente():
    with TestClient(app) as c:
        c.app.state.http = httpx.AsyncClient(transport=_transporte(True))
        yield c


@pytest.fixture()
def cliente_sesion_vencida():
    with TestClient(app) as c:
        c.app.state.http = httpx.AsyncClient(transport=_transporte(False))
        yield c


def test_health_agrega_el_estado_de_los_servicios(cliente):
    cuerpo = cliente.get("/health").json()
    assert cuerpo["estado"] == "ok"
    assert cuerpo["servicios"] == {"auth": "ok", "parametrizacion": "ok"}


def test_el_login_es_publico(cliente):
    respuesta = cliente.post("/api/auth/auth/login", json={"usuario": "admin", "password": "x"})
    assert respuesta.status_code == 200
    assert respuesta.json()["token_type"] == "bearer"


def test_una_ruta_protegida_sin_token_es_rechazada(cliente):
    respuesta = cliente.get("/api/parametrizacion/sedes")
    assert respuesta.status_code == 401
    assert respuesta.json()["error"]["codigo"] == "NO_AUTENTICADO"


def test_una_ruta_protegida_con_sesion_valida_se_enruta(cliente):
    respuesta = cliente.get("/api/parametrizacion/sedes", headers=TOKEN)
    assert respuesta.status_code == 200
    assert respuesta.json()[0]["nombre"] == "Bar de Moe · Centro"


def test_rnf03_el_gateway_propaga_la_expiracion_por_inactividad(cliente_sesion_vencida):
    respuesta = cliente_sesion_vencida.get("/api/parametrizacion/sedes", headers=TOKEN)
    assert respuesta.status_code == 401
    assert respuesta.json()["error"]["codigo"] == "SESION_EXPIRADA"


def test_un_servicio_desconocido_da_404(cliente):
    respuesta = cliente.get("/api/inventario/existencias", headers=TOKEN)
    assert respuesta.status_code == 404
    assert respuesta.json()["error"]["codigo"] == "SERVICIO_DESCONOCIDO"


def test_se_propaga_el_request_id(cliente):
    respuesta = cliente.get("/health", headers={"X-Request-Id": "abc-123"})
    assert respuesta.headers["X-Request-Id"] == "abc-123"


def test_config_apunta_a_los_dos_servicios():
    assert "auth-service" in config.AUTH_URL
    assert "parametrizacion-service" in config.PARAMETRIZACION_URL
