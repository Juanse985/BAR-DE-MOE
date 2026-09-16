"""HU-008 — router común de consulta de la auditoría (`router_consulta`)."""
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from barmoe_common.auditoria import Auditoria, contexto_http, registrar, router_consulta
from barmoe_common.db import dependencia_db
from barmoe_common.deps import construir_autenticacion

from .conftest import SECRETO, construir, firmar


@pytest.fixture()
def app_con_auditoria():
    app, fabrica = construir(auditar=False)
    _, requiere_perfil = construir_autenticacion(SECRETO)
    app.include_router(router_consulta(dependencia_db(fabrica), requiere_perfil("ADMINISTRADOR")))
    base = datetime(2026, 9, 1, 12, 0, tzinfo=UTC)
    with fabrica() as db:
        for i in range(6):
            fila = registrar(db, accion="CREAR" if i % 2 else "LOGIN", usuario=f"u{i % 3}",
                             usuario_id=i % 3, sede_id=1 + i % 2, resultado="OK" if i < 5 else "FALLIDO")
            fila.fecha = base + timedelta(days=i)
        db.commit()
    with TestClient(app) as c:
        yield c


ADMIN = firmar("ADMINISTRADOR", None)


def test_ordena_del_mas_reciente_al_mas_antiguo(app_con_auditoria):
    filas = app_con_auditoria.get("/auditoria", headers=ADMIN).json()
    assert [f["fecha"][:10] for f in filas] == [f"2026-09-0{d}" for d in range(6, 0, -1)]


@pytest.mark.parametrize(("params", "esperados"), [
    ({"usuario": "u1"}, 2),
    ({"usuario_id": 2}, 2),
    ({"sede_id": 2}, 3),
    ({"accion": "crear"}, 3),
    ({"resultado": "fallido"}, 1),
    ({"desde": "2026-09-03T00:00:00", "hasta": "2026-09-04T23:59:59"}, 2),
    ({"desde": "2026-09-05T00:00:00-05:00"}, 2),
])
def test_filtros(app_con_auditoria, params, esperados):
    respuesta = app_con_auditoria.get("/auditoria", headers=ADMIN, params=params)
    assert len(respuesta.json()) == esperados
    assert respuesta.headers["X-Total-Count"] == str(esperados)


def test_paginacion_y_total(app_con_auditoria):
    respuesta = app_con_auditoria.get("/auditoria", headers=ADMIN, params={"tamano": 4, "pagina": 2})
    assert len(respuesta.json()) == 2
    assert respuesta.headers["X-Total-Count"] == "6"


def test_rango_invertido(app_con_auditoria):
    params = {"desde": "2026-09-05T00:00:00", "hasta": "2026-09-01T00:00:00"}
    assert app_con_auditoria.get("/auditoria", headers=ADMIN, params=params).status_code == 422


@pytest.mark.parametrize("perfil", ["CAJERO", "MESERO"])
def test_solo_el_administrador(app_con_auditoria, perfil):
    assert app_con_auditoria.get("/auditoria", headers=firmar(perfil)).status_code == 403
    assert app_con_auditoria.get("/auditoria").status_code == 401


def test_no_hay_rutas_para_modificar(app_con_auditoria):
    for metodo in ("POST", "PUT", "PATCH", "DELETE"):
        assert app_con_auditoria.request(metodo, "/auditoria", headers=ADMIN).status_code == 405


def test_contexto_http_junta_ip_y_request_id():
    class _R:
        headers = {"x-forwarded-for": "9.9.9.9", "x-request-id": "abc"}
        client = None

        class state:  # noqa: N801
            request_id = None

    assert contexto_http(_R()) == {"ip": "9.9.9.9", "request_id": "abc"}
    assert Auditoria.__tablename__ == "auditoria"
