"""HU-025 · RNF-12 — Trazabilidad de las transacciones (librería común)."""
from datetime import UTC, datetime, timedelta

from starlette.datastructures import Headers

from barmoe_common.auditoria import Auditoria, ip_cliente, registrar, registrar_rechazo, request_id_de

from .conftest import firmar


class _Cliente:
    host = "10.0.0.5"


class _Estado:
    request_id = None


class _RequestFalso:
    def __init__(self, cabeceras: dict | None = None, request_id: str | None = None, con_cliente=True):
        self.headers = Headers(cabeceras or {})
        self.client = _Cliente() if con_cliente else None
        self.state = _Estado()
        self.state.request_id = request_id


def test_rnf12_registrar_guarda_quien_donde_y_cuando(fabrica):
    antes = datetime.now(UTC) - timedelta(seconds=1)
    with fabrica() as db:
        fila = registrar(db, accion="CREAR", usuario_id=7, usuario="moe", sede_id=2,
                         entidad="sedes", entidad_id=15, ip="10.0.0.9", request_id="abc-123")
        db.commit()
        guardada = db.get(Auditoria, fila.id)
    assert guardada.usuario_id == 7
    assert guardada.usuario == "moe"
    assert guardada.sede_id == 2
    assert guardada.entidad_id == "15"  # siempre texto, sirva para cualquier llave
    assert guardada.resultado == "OK"
    assert guardada.request_id == "abc-123"
    fecha = guardada.fecha if guardada.fecha.tzinfo else guardada.fecha.replace(tzinfo=UTC)
    assert fecha >= antes


def test_registrar_no_hace_commit_por_su_cuenta(fabrica):
    with fabrica() as db:
        registrar(db, accion="SIN_COMMIT")
        db.rollback()
        assert db.query(Auditoria).filter_by(accion="SIN_COMMIT").count() == 0


def test_registrar_rechazo_arma_el_detalle(fabrica):
    with fabrica() as db:
        fila = registrar_rechazo(db, metodo="POST", ruta="/sedes", status=403,
                                 codigo="SIN_PERMISOS", usuario="barney", sede_id=1)
        db.commit()
    assert fila.accion == "ACCESO_DENEGADO"
    assert fila.resultado == "RECHAZADO"
    assert fila.detalle == "POST /sedes -> 403 SIN_PERMISOS"


def test_la_ip_real_sale_de_x_forwarded_for():
    request = _RequestFalso({"x-forwarded-for": "181.50.1.2, 172.18.0.4"})
    assert ip_cliente(request) == "181.50.1.2"


def test_sin_x_forwarded_for_se_usa_la_ip_de_la_conexion():
    assert ip_cliente(_RequestFalso()) == "10.0.0.5"
    assert ip_cliente(_RequestFalso(con_cliente=False)) is None


def test_request_id_sale_del_estado_o_de_la_cabecera():
    assert request_id_de(_RequestFalso(request_id="desde-state")) == "desde-state"
    assert request_id_de(_RequestFalso({"x-request-id": "desde-cabecera"})) == "desde-cabecera"
    assert request_id_de(_RequestFalso()) is None


def test_c1_un_perfil_no_autorizado_queda_en_la_auditoria(cliente):
    respuesta = cliente.get("/solo-admin", headers={**firmar("MESERO", 3, usuario="barney"),
                                                     "X-Request-Id": "req-mesero-1",
                                                     "X-Forwarded-For": "190.1.1.1"})
    assert respuesta.status_code == 403

    rechazos = [a for a in cliente.get("/auditorias").json() if a["accion"] == "ACCESO_DENEGADO"]
    assert len(rechazos) == 1
    rechazo = rechazos[0]
    assert rechazo["usuario"] == "barney"
    assert rechazo["sede_id"] == 3
    assert rechazo["resultado"] == "RECHAZADO"
    assert rechazo["ip"] == "190.1.1.1"
    assert rechazo["request_id"] == "req-mesero-1"
    assert rechazo["detalle"] == "GET /solo-admin -> 403"


def test_c1_sin_token_tambien_queda_registrado_pero_sin_usuario(cliente):
    assert cliente.get("/solo-admin").status_code == 401
    rechazo = [a for a in cliente.get("/auditorias").json() if a["accion"] == "ACCESO_DENEGADO"][0]
    assert rechazo["usuario"] is None
    assert rechazo["detalle"] == "GET /solo-admin -> 401"


def test_c1_un_token_falsificado_no_aporta_identidad_a_la_auditoria(cliente):
    falso = firmar("ADMINISTRADOR", 1, usuario="impostor", secreto="otro-secreto")
    assert cliente.get("/solo-admin", headers=falso).status_code == 401
    rechazo = [a for a in cliente.get("/auditorias").json() if a["accion"] == "ACCESO_DENEGADO"][0]
    assert rechazo["usuario"] is None  # no se cree lo que dice un token sin firma válida


def test_las_operaciones_permitidas_no_generan_rechazos(cliente):
    assert cliente.get("/solo-admin", headers=firmar("ADMINISTRADOR")).status_code == 200
    assert not [a for a in cliente.get("/auditorias").json() if a["accion"] == "ACCESO_DENEGADO"]


def test_si_la_auditoria_falla_la_respuesta_no_se_cae():
    """Una base caída no puede convertir un 403 en un 500."""
    from fastapi.testclient import TestClient

    from .conftest import construir

    app, fabrica = construir(auditar=True)
    fabrica.engine.dispose()
    from barmoe_common.db import Base

    Base.metadata.drop_all(bind=fabrica.engine)  # la tabla auditoria ya no existe
    with TestClient(app) as c:
        assert c.get("/solo-admin").status_code == 401


def test_sin_activar_la_opcion_no_se_auditan_rechazos():
    from fastapi.testclient import TestClient

    from .conftest import construir

    app, fabrica = construir(auditar=False)
    with TestClient(app) as c:
        assert c.get("/solo-admin").status_code == 401
    with fabrica() as db:
        assert db.query(Auditoria).count() == 0
