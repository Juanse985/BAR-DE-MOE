"""HU-025 · RNF-12 — Trazabilidad en el parametrizacion-service.

Toda escritura del M2 debe decir quién la hizo, desde qué sede y cuándo.
"""
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.main import SessionLocal
from barmoe_common.auditoria import Auditoria

from .conftest import _encabezado


def _auditorias(**filtros) -> list[Auditoria]:
    with SessionLocal() as db:
        return list(db.scalars(select(Auditoria).filter_by(**filtros).order_by(Auditoria.id)))


def test_hu025_crear_cada_entidad_deja_su_registro(cliente, admin, catalogo):
    mesa = cliente.post("/mesas", headers=admin, json={"sede_id": catalogo["sede"]["id"], "numero": 1}).json()
    producto = cliente.post("/productos", headers=admin, json={
        "codigo": "CERV-001", "nombre": "Duff", "sede_id": catalogo["sede"]["id"],
        "tipo_producto_id": catalogo["tipo"]["id"], "proveedor_id": catalogo["proveedor"]["id"],
        "valor_compra": "2500", "valor_venta": "6000",
    }).json()

    esperadas = {
        ("sedes", str(catalogo["sede"]["id"])),
        ("tipos_producto", str(catalogo["tipo"]["id"])),
        ("proveedores", str(catalogo["proveedor"]["id"])),
        ("mesas", str(mesa["id"])),
        ("productos", str(producto["id"])),
    }
    registradas = {(a.entidad, a.entidad_id) for a in _auditorias(accion="CREAR")}
    assert esperadas <= registradas


def test_hu025_el_registro_trae_usuario_sede_y_fecha(cliente):
    admin_sede_2 = _encabezado(9, "moe", "ADMINISTRADOR", 2)
    antes = datetime.now(UTC) - timedelta(seconds=1)
    cliente.post("/sedes", headers=admin_sede_2, json={"nombre": "Bar de Moe · Sur"})

    fila = _auditorias(accion="CREAR", entidad="sedes")[-1]
    assert (fila.usuario_id, fila.usuario, fila.sede_id, fila.resultado) == (9, "moe", 2, "OK")
    fecha = fila.fecha if fila.fecha.tzinfo else fila.fecha.replace(tzinfo=UTC)
    assert antes <= fecha <= datetime.now(UTC) + timedelta(seconds=1)


@pytest.mark.parametrize(("ruta", "cambio"), [
    ("/sedes/{sede}", {"telefono": "6019999999"}),
    ("/tipos-producto/{tipo}", {"descripcion": "Nacionales"}),
    ("/proveedores/{proveedor}", {"contacto": "Homero"}),
])
def test_hu025_las_actualizaciones_registran_los_campos_cambiados(cliente, admin, catalogo, ruta, cambio):
    ids = {k: v["id"] for k, v in catalogo.items()}
    respuesta = cliente.patch(ruta.format(**ids), headers=admin, json=cambio)
    assert respuesta.status_code == 200
    fila = _auditorias(accion="ACTUALIZAR")[-1]
    assert fila.detalle == ", ".join(cambio.keys())
    assert fila.usuario == "admin"


def test_hu025_las_consultas_no_llenan_la_auditoria(cliente, admin, mesero, catalogo):
    total = len(_auditorias())
    cliente.get("/sedes", headers=mesero)
    cliente.get("/productos", headers=admin)
    assert len(_auditorias()) == total


def test_hu025_un_error_de_negocio_no_deja_registro_ok(cliente, admin, catalogo):
    total = len(_auditorias(resultado="OK"))
    cliente.post("/sedes", headers=admin, json={"nombre": catalogo["sede"]["nombre"]})  # duplicada
    assert len(_auditorias(resultado="OK")) == total


# DEF-05 corregido en la integración del Sprint 1.
def test_hu025_un_intento_rechazado_queda_registrado(cliente, mesero):
    cliente.post("/sedes", headers=mesero, json={"nombre": "Sede pirata"})
    fila = _auditorias(accion="ACCESO_DENEGADO")[-1]
    assert (fila.usuario, fila.sede_id, fila.detalle) == ("mszyslak", 1, "POST /sedes -> 403")


def test_hu025_otra_sede_rechazada_tambien_queda_registrada(cliente, mesero):
    cliente.get("/mesas", headers=mesero, params={"sede_id": 99})
    assert _auditorias(accion="ACCESO_DENEGADO")[-1].detalle == "GET /mesas -> 403"


def test_hu025_la_escritura_guarda_ip_real_y_request_id(cliente, admin):
    """DEF-07 y DEF-08 corregidos en el parametrizacion-service."""
    cliente.post("/sedes", headers={**admin, "X-Forwarded-For": "181.60.10.20", "X-Request-Id": "req-9"},
                 json={"nombre": "Bar de Moe · Oeste"})
    fila = _auditorias(accion="CREAR", entidad="sedes")[-1]
    assert (fila.ip, fila.request_id) == ("181.60.10.20", "req-9")


def test_hu008_el_administrador_consulta_la_auditoria_del_servicio(cliente, admin, mesero, catalogo):
    assert cliente.get("/auditoria", headers=mesero).status_code == 403
    filas = cliente.get("/auditoria", headers=admin, params={"accion": "CREAR"}).json()
    assert {f["entidad"] for f in filas} == {"sedes", "tipos_producto", "proveedores"}
