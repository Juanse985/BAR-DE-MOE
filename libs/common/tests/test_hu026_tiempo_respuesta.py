"""HU-026 · RNF-02 — Tiempo de respuesta máximo de dos segundos.

El middleware mide cada respuesta, la expone en X-Tiempo-Ms y marca y registra
en el log las que superan el SLA. La config de prueba usa un SLA de 0,2 s para
poder forzar el caso sin hacer esperar al CI.
"""
import logging

from .conftest import firmar


def test_rnf02_toda_respuesta_trae_x_tiempo_ms(cliente):
    respuesta = cliente.get("/health")
    assert respuesta.status_code == 200
    assert float(respuesta.headers["X-Tiempo-Ms"]) >= 0


def test_rnf02_una_respuesta_rapida_no_se_marca(cliente):
    respuesta = cliente.get("/health")
    assert "X-SLA-Excedido" not in respuesta.headers


def test_rnf02_una_respuesta_lenta_se_marca_y_se_registra_en_el_log(cliente, caplog):
    with caplog.at_level(logging.WARNING, logger="barmoe"):
        respuesta = cliente.get("/lento")
    assert respuesta.headers["X-SLA-Excedido"] == "true"
    assert float(respuesta.headers["X-Tiempo-Ms"]) >= 200
    assert any("SLA excedido: GET /lento" in r.getMessage() for r in caplog.records)


def test_rnf02_tambien_se_mide_en_los_errores(cliente):
    assert "X-Tiempo-Ms" in cliente.get("/solo-admin").headers  # 401
    assert "X-Tiempo-Ms" in cliente.get("/no-existe").headers    # 404


def test_el_request_id_se_genera_o_se_respeta(cliente):
    generado = cliente.get("/health").headers["X-Request-Id"]
    assert len(generado) == 36
    assert cliente.get("/health", headers={"X-Request-Id": "mio"}).headers["X-Request-Id"] == "mio"


def test_cors_expone_las_cabeceras_de_trazabilidad(cliente):
    respuesta = cliente.get("/health", headers={"Origin": "http://localhost:5173"})
    expuestas = respuesta.headers["access-control-expose-headers"]
    for cabecera in ("X-Request-Id", "X-Tiempo-Ms", "X-SLA-Excedido"):
        assert cabecera in expuestas


def test_cors_no_acepta_origenes_desconocidos(cliente):
    respuesta = cliente.get("/health", headers={"Origin": "http://sitio-malicioso.com"})
    assert "access-control-allow-origin" not in respuesta.headers


def test_health_informa_servicio_y_entorno(cliente):
    esperado = {"estado": "ok", "servicio": "servicio-de-prueba", "entorno": "dev"}
    assert cliente.get("/health").json() == esperado


def test_una_operacion_autorizada_responde_dentro_del_sla(cliente):
    respuesta = cliente.get("/solo-admin", headers=firmar())
    assert float(respuesta.headers["X-Tiempo-Ms"]) < 2000
