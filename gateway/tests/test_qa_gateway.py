"""Pruebas de QA del gateway: HU-025 (trazabilidad), HU-026 (SLA) y HU-028 (C-1/C-4).

Se usa un transporte simulado que además GUARDA lo que el gateway le envía a
cada servicio, para poder verificar qué cabeceras viajan y cuáles no.
"""
import os

os.environ.setdefault("JWT_SECRET", "secreto-de-pruebas")

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app

TOKEN = {"Authorization": "Bearer token-de-prueba"}


class ServiciosFalsos:
    def __init__(self, sesion: int = 200, cuerpo_no_json: bool = False, caido: bool = False):
        self.sesion = sesion
        self.cuerpo_no_json = cuerpo_no_json
        self.caido = caido
        self.recibidas: list[httpx.Request] = []

    def __call__(self, peticion: httpx.Request) -> httpx.Response:
        self.recibidas.append(peticion)
        ruta = peticion.url.path
        if ruta == "/auth/validar-sesion":
            if self.sesion == 200:
                return httpx.Response(200, json={"usuario_id": 1, "usuario": "admin",
                                                 "perfil": "ADMINISTRADOR", "sede_id": None,
                                                 "segundos_inactivo": 1.0})
            codigos = {401: "SESION_CERRADA", 409: "SESION_ACTIVA"}
            return httpx.Response(self.sesion, json={"error": {"codigo": codigos.get(self.sesion, "X"),
                                                               "mensaje": "rechazada"}})
        if self.caido:
            raise httpx.ConnectError("servicio caído")
        if self.cuerpo_no_json:
            return httpx.Response(502, text="<html>Bad Gateway</html>")
        return httpx.Response(200, json={"ruta": ruta, "query": str(peticion.url.query, "utf-8")})

    def a(self, ruta: str) -> list[httpx.Request]:
        return [p for p in self.recibidas if p.url.path == ruta]


def _cliente(servicios: ServiciosFalsos):
    c = TestClient(app)
    c.__enter__()
    c.app.state.http = httpx.AsyncClient(transport=httpx.MockTransport(servicios))
    return c


@pytest.fixture()
def servicios():
    return ServiciosFalsos()


@pytest.fixture()
def cliente(servicios):
    c = _cliente(servicios)
    yield c
    c.__exit__(None, None, None)


# ------------------------------------------------------------ HU-025 · trazabilidad
def test_hu025_el_mismo_request_id_llega_a_auth_y_al_servicio_destino(cliente, servicios):
    respuesta = cliente.get("/api/parametrizacion/sedes", headers={**TOKEN, "X-Request-Id": "req-777"})
    assert respuesta.headers["X-Request-Id"] == "req-777"
    assert servicios.a("/auth/validar-sesion")[0].headers["X-Request-Id"] == "req-777"
    assert servicios.a("/sedes")[0].headers["X-Request-Id"] == "req-777"


def test_hu025_si_el_cliente_no_manda_request_id_el_gateway_lo_genera(cliente, servicios):
    respuesta = cliente.get("/api/parametrizacion/sedes", headers=TOKEN)
    generado = respuesta.headers["X-Request-Id"]
    assert len(generado) == 36
    assert servicios.a("/sedes")[0].headers["X-Request-Id"] == generado


@pytest.mark.xfail(strict=True, reason="DEF-07: detrás del gateway se guarda la IP del gateway y no la del "
                                       "cliente (falta reenviar y usar X-Forwarded-For)")
def test_hu025_el_gateway_reenvia_la_ip_del_cliente(cliente, servicios):
    cliente.post("/api/auth/auth/login", json={"usuario": "admin", "password": "x"})
    assert "x-forwarded-for" in servicios.a("/auth/login")[0].headers


# ------------------------------------------------------------ HU-026 · SLA
def test_hu026_el_gateway_mide_su_propio_tiempo(cliente):
    respuesta = cliente.get("/api/parametrizacion/sedes", headers=TOKEN)
    assert float(respuesta.headers["X-Tiempo-Ms"]) < 2000


def test_hu026_health_responde_rapido_aun_con_un_servicio_caido():
    c = _cliente(ServiciosFalsos(caido=True))
    try:
        respuesta = c.get("/health")
    finally:
        c.__exit__(None, None, None)
    assert respuesta.status_code == 200
    assert float(respuesta.headers["X-Tiempo-Ms"]) < 2000


# ------------------------------------------------------------ HU-028 · C-1 / C-4
def test_c1_solo_viajan_las_cabeceras_permitidas(cliente, servicios):
    cliente.get("/api/parametrizacion/sedes", headers={
        **TOKEN, "X-Perfil": "ADMINISTRADOR", "X-Sede-Id": "1", "Cookie": "sesion=robada",
    })
    enviadas = {k.lower() for k in servicios.a("/sedes")[0].headers}
    assert "authorization" in enviadas
    assert not {"x-perfil", "x-sede-id", "cookie"} & enviadas


@pytest.mark.parametrize("ruta", [
    "/api/parametrizacion/sedes",
    "/api/auth/usuarios",
    "/api/auth/auth/me",
    "/api/auth/auth/validar-sesion",
])
def test_c1_ninguna_ruta_privada_se_enruta_sin_token(cliente, servicios, ruta):
    assert cliente.get(ruta).status_code == 401
    assert servicios.recibidas == []


def test_c1_la_lista_de_rutas_publicas_es_minima():
    from app.main import PUBLICAS

    assert PUBLICAS == {"/api/auth/auth/login", "/api/auth/health", "/api/parametrizacion/health"}


def test_c1_no_se_puede_escapar_del_prefijo_con_rutas_raras(cliente, servicios):
    respuesta = cliente.get("/api/auth/auth/login/../../usuarios")
    assert respuesta.status_code in (401, 404)
    assert not servicios.a("/usuarios")


@pytest.mark.parametrize("estado", [401, 409])
def test_c4_si_auth_rechaza_la_sesion_el_gateway_no_enruta(estado):
    servicios = ServiciosFalsos(sesion=estado)
    c = _cliente(servicios)
    try:
        respuesta = c.get("/api/parametrizacion/sedes", headers=TOKEN)
    finally:
        c.__exit__(None, None, None)
    assert respuesta.status_code == estado
    assert not servicios.a("/sedes")


def test_c4_si_auth_esta_caido_se_niega_el_acceso():
    c = TestClient(app)
    c.__enter__()

    def caido(_):
        raise httpx.ConnectError("auth caído")

    c.app.state.http = httpx.AsyncClient(transport=httpx.MockTransport(caido))
    try:
        respuesta = c.get("/api/parametrizacion/sedes", headers=TOKEN)
    finally:
        c.__exit__(None, None, None)
    assert respuesta.status_code == 503
    assert respuesta.json()["error"]["codigo"] == "AUTH_NO_DISPONIBLE"


def test_un_servicio_destino_caido_da_503_y_no_500():
    c = _cliente(ServiciosFalsos(caido=True))
    try:
        respuesta = c.get("/api/parametrizacion/sedes", headers=TOKEN)
    finally:
        c.__exit__(None, None, None)
    assert respuesta.status_code == 503
    assert respuesta.json()["error"]["codigo"] == "SERVICIO_NO_DISPONIBLE"


def test_los_parametros_de_consulta_se_reenvian(cliente):
    cuerpo = cliente.get("/api/parametrizacion/productos", headers=TOKEN, params={"sede_id": 2}).json()
    assert cuerpo == {"ruta": "/productos", "query": "sede_id=2"}


@pytest.mark.xfail(strict=True, raises=Exception,
                   reason="DEF-09: si un servicio responde algo que no es JSON el gateway se cae con 500")
def test_una_respuesta_no_json_no_tumba_el_gateway():
    c = _cliente(ServiciosFalsos(cuerpo_no_json=True))
    try:
        respuesta = c.get("/api/parametrizacion/sedes", headers=TOKEN)
    finally:
        c.__exit__(None, None, None)
    assert respuesta.status_code == 502
