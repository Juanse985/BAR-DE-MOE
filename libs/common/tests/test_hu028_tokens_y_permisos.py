"""HU-028 · control C-1 (control de acceso) y errores uniformes.

Estas pruebas atacan las dependencias de autorización con tokens vencidos,
falsificados, sin firma y con perfiles no autorizados.
"""
from datetime import UTC, datetime, timedelta

import jwt
import pytest

from barmoe_common.tokens import crear_token, decodificar_token

from .conftest import SECRETO, firmar


def _codigo(respuesta) -> str:
    return respuesta.json()["error"]["codigo"]


def test_el_token_lleva_usuario_perfil_y_sede():
    token, jti, expira = crear_token(usuario_id=5, usuario="carl", perfil="CAJERO",
                                     sede_id=2, secreto=SECRETO, expira_minutos=10)
    datos = decodificar_token(token, SECRETO)
    assert datos["sub"] == "5"
    assert datos["usr"] == "carl"
    assert datos["perfil"] == "CAJERO"
    assert datos["sede_id"] == 2
    assert datos["jti"] == jti
    assert expira > datetime.now(UTC)


def test_c1_el_administrador_entra(cliente):
    respuesta = cliente.get("/solo-admin", headers=firmar("ADMINISTRADOR", None))
    assert respuesta.status_code == 200
    assert respuesta.json() == {"usuario": "moe", "sede_id": None}


@pytest.mark.parametrize("perfil", ["CAJERO", "MESERO", "INVENTADO"])
def test_c1_otros_perfiles_reciben_403(cliente, perfil):
    respuesta = cliente.get("/solo-admin", headers=firmar(perfil))
    assert respuesta.status_code == 403
    assert _codigo(respuesta) == "SIN_PERMISOS"


def test_c1_sin_cabecera_authorization(cliente):
    respuesta = cliente.get("/solo-admin")
    assert respuesta.status_code == 401
    assert _codigo(respuesta) == "NO_AUTENTICADO"


@pytest.mark.parametrize("cabecera", ["token-suelto", "Basic YWRtaW46QWRtaW4yMDI2", "Bearer"])
def test_c1_cabeceras_mal_formadas(cliente, cabecera):
    respuesta = cliente.get("/solo-admin", headers={"Authorization": cabecera})
    assert respuesta.status_code == 401


def test_c1_token_firmado_con_otro_secreto(cliente):
    respuesta = cliente.get("/solo-admin", headers=firmar(secreto="secreto-del-atacante"))
    assert respuesta.status_code == 401
    assert _codigo(respuesta) == "TOKEN_INVALIDO"


def test_c1_token_vencido(cliente):
    respuesta = cliente.get("/solo-admin", headers=firmar(expira_minutos=-1))
    assert respuesta.status_code == 401
    assert _codigo(respuesta) == "SESION_EXPIRADA"


def test_c1_token_sin_firma_alg_none_es_rechazado(cliente):
    ahora = datetime.now(UTC)
    carga = {"sub": "1", "usr": "admin", "perfil": "ADMINISTRADOR", "sede_id": None, "jti": "x",
             "iat": int(ahora.timestamp()), "exp": int((ahora + timedelta(minutes=5)).timestamp())}
    sin_firma = jwt.encode(carga, key=None, algorithm="none")
    respuesta = cliente.get("/solo-admin", headers={"Authorization": f"Bearer {sin_firma}"})
    assert respuesta.status_code == 401


def test_c1_token_con_perfil_alterado_a_mano_es_rechazado(cliente):
    """Cambiar MESERO por ADMINISTRADOR en el payload rompe la firma."""
    import base64
    import json

    token = firmar("MESERO")["Authorization"].split(" ")[1]
    cabecera, carga, firma = token.split(".")
    datos = json.loads(base64.urlsafe_b64decode(carga + "=="))
    datos["perfil"] = "ADMINISTRADOR"
    nueva = base64.urlsafe_b64encode(json.dumps(datos).encode()).decode().rstrip("=")
    respuesta = cliente.get("/solo-admin", headers={"Authorization": f"Bearer {cabecera}.{nueva}.{firma}"})
    assert respuesta.status_code == 401


def test_los_errores_de_negocio_usan_la_envoltura_unica(cliente):
    respuesta = cliente.get("/error-negocio")
    assert respuesta.status_code == 409
    assert respuesta.json() == {"error": {"codigo": "REGLA_ROTA", "mensaje": "Una regla de negocio falló."}}


def test_c3_los_datos_invalidos_se_rechazan_con_422_y_detalle(cliente):
    respuesta = cliente.get("/con-parametro", params={"numero": "1 OR 1=1"})
    assert respuesta.status_code == 422
    error = respuesta.json()["error"]
    assert error["codigo"] == "DATOS_INVALIDOS"
    assert error["detalle"][0]["campo"] == "numero"


def test_una_ruta_inexistente_responde_404_con_la_envoltura(cliente):
    respuesta = cliente.get("/no-existe")
    assert respuesta.status_code == 404
    assert _codigo(respuesta) == "NO_ENCONTRADO"


def test_un_metodo_no_permitido_usa_la_envoltura(cliente):
    respuesta = cliente.delete("/health")
    assert respuesta.status_code == 405
    assert _codigo(respuesta) == "ERROR"
