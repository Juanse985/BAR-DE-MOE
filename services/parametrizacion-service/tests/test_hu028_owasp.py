"""HU-028 · RNF-11 — Controles C-1 (acceso) y C-3 (inyección) en el M2."""
import pytest
from sqlalchemy import inspect

from app.main import SessionLocal

from .conftest import _encabezado

ESCRITURAS = [
    ("POST", "/sedes", {"nombre": "Sede pirata"}),
    ("PATCH", "/sedes/{sede}", {"nombre": "Renombrada"}),
    ("POST", "/mesas", {"sede_id": "{sede}", "numero": 50}),
    ("PATCH", "/mesas/{mesa}", {"capacidad": 10}),
    ("POST", "/tipos-producto", {"nombre": "Pirata"}),
    ("PATCH", "/tipos-producto/{tipo}", {"nombre": "Otro"}),
    ("POST", "/proveedores", {"nit": "900111222", "nombre": "Pirata"}),
    ("PATCH", "/proveedores/{proveedor}", {"nombre": "Otro"}),
    ("POST", "/productos", {"codigo": "PIR-1", "nombre": "Pirata", "sede_id": "{sede}",
                            "tipo_producto_id": "{tipo}", "proveedor_id": "{proveedor}",
                            "valor_compra": "1", "valor_venta": "2"}),
    ("PATCH", "/productos/{producto}", {"valor_venta": "1"}),
]


@pytest.fixture()
def ids(cliente, admin, catalogo) -> dict:
    sede = catalogo["sede"]["id"]
    mesa = cliente.post("/mesas", headers=admin, json={"sede_id": sede, "numero": 1}).json()
    producto = cliente.post("/productos", headers=admin, json={
        "codigo": "CERV-001", "nombre": "Duff", "sede_id": sede,
        "tipo_producto_id": catalogo["tipo"]["id"], "proveedor_id": catalogo["proveedor"]["id"],
        "valor_compra": "2500", "valor_venta": "6000",
    }).json()
    return {"sede": sede, "mesa": mesa["id"], "tipo": catalogo["tipo"]["id"],
            "proveedor": catalogo["proveedor"]["id"], "producto": producto["id"]}


def _rellenar(valor, ids):
    if isinstance(valor, dict):
        return {k: _rellenar(v, ids) for k, v in valor.items()}
    if isinstance(valor, str) and valor.startswith("{"):
        return ids[valor.strip("{}")]
    return valor


# ------------------------------------------------------------------- C-1
@pytest.mark.parametrize("perfil", ["CAJERO", "MESERO"])
@pytest.mark.parametrize(("metodo", "ruta", "cuerpo"), ESCRITURAS)
def test_c1_solo_el_administrador_parametriza(cliente, ids, perfil, metodo, ruta, cuerpo):
    h = _encabezado(5, "operario", perfil, ids["sede"])
    respuesta = cliente.request(metodo, ruta.format(**ids), headers=h, json=_rellenar(cuerpo, ids))
    assert respuesta.status_code == 403, respuesta.text
    assert respuesta.json()["error"]["codigo"] == "SIN_PERMISOS"


def test_c1_un_rechazo_no_modifica_nada(cliente, admin, ids):
    h = _encabezado(5, "barney", "MESERO", ids["sede"])
    cliente.patch(f"/productos/{ids['producto']}", headers=h, json={"valor_venta": "1"})
    producto = cliente.get(f"/productos/{ids['producto']}", headers=admin).json()
    assert float(producto["valor_venta"]) == 6000


@pytest.mark.parametrize("cabecera", [
    {},
    {"Authorization": "Bearer inventado"},
    {"X-Perfil": "ADMINISTRADOR"},                 # cabeceras sueltas no dan permisos
    {"X-Usuario-Id": "1", "X-Sede-Id": "1"},
])
def test_c1_sin_token_valido_no_hay_acceso(cliente, cabecera):
    assert cliente.get("/sedes", headers=cabecera).status_code == 401
    assert cliente.post("/sedes", headers=cabecera, json={"nombre": "Pirata"}).status_code == 401


# DEF-06 corregido en la integración del Sprint 1.
@pytest.mark.parametrize("ruta", ["/productos?sede_id={otra}", "/mesas?sede_id={otra}"])
def test_c1_un_operario_no_ve_datos_de_otra_sede(cliente, admin, ids, ruta):
    otra = cliente.post("/sedes", headers=admin, json={"nombre": "Bar de Moe · Norte"}).json()["id"]
    cliente.post("/mesas", headers=admin, json={"sede_id": otra, "numero": 1})
    cliente.post("/productos", headers=admin, json={
        "codigo": "NORTE-1", "nombre": "Solo Norte", "sede_id": otra,
        "tipo_producto_id": ids["tipo"], "proveedor_id": ids["proveedor"],
        "valor_compra": "1", "valor_venta": "2",
    })
    mesero_centro = _encabezado(5, "barney", "MESERO", ids["sede"])
    respuesta = cliente.get(ruta.format(otra=otra), headers=mesero_centro)
    assert respuesta.status_code == 403
    assert respuesta.json()["error"]["codigo"] == "SEDE_NO_AUTORIZADA"


@pytest.mark.parametrize("perfil", ["CAJERO", "MESERO"])
def test_c1_sin_filtro_el_operario_solo_recibe_su_sede(cliente, admin, ids, perfil):
    otra = cliente.post("/sedes", headers=admin, json={"nombre": "Bar de Moe · Norte"}).json()["id"]
    cliente.post("/mesas", headers=admin, json={"sede_id": otra, "numero": 7})
    h = _encabezado(5, "operario", perfil, ids["sede"])
    assert {m["sede_id"] for m in cliente.get("/mesas", headers=h).json()} == {ids["sede"]}
    assert {p["sede_id"] for p in cliente.get("/productos", headers=h).json()} == {ids["sede"]}
    assert [s["id"] for s in cliente.get("/sedes", headers=h).json()] == [ids["sede"]]
    assert cliente.get(f"/sedes/{otra}", headers=h).status_code == 403
    # El administrador sí ve todas las sedes.
    assert {m["sede_id"] for m in cliente.get("/mesas", headers=admin).json()} == {ids["sede"], otra}


def test_c1_un_operario_no_abre_un_producto_de_otra_sede(cliente, admin, ids):
    otra = cliente.post("/sedes", headers=admin, json={"nombre": "Bar de Moe · Sur"}).json()["id"]
    ajeno = cliente.post("/productos", headers=admin, json={
        "codigo": "SUR-1", "nombre": "Solo Sur", "sede_id": otra, "tipo_producto_id": ids["tipo"],
        "proveedor_id": ids["proveedor"], "valor_compra": "1", "valor_venta": "2",
    }).json()
    h = _encabezado(5, "barney", "MESERO", ids["sede"])
    assert cliente.get(f"/productos/{ajeno['id']}", headers=h).status_code == 403
    assert cliente.get("/productos/por-codigo/SUR-1", headers=h, params={"sede_id": otra}).status_code == 403
    assert cliente.get("/productos/por-codigo/CERV-001", headers=h,
                       params={"sede_id": ids["sede"]}).status_code == 200
    assert cliente.get(f"/productos/{ids['producto']}", headers=h).status_code == 200


def test_c1_un_operario_sin_sede_no_consulta_nada(cliente, ids):
    h = _encabezado(5, "huerfano", "CAJERO", None)
    respuesta = cliente.get("/mesas", headers=h)
    assert respuesta.status_code == 403
    assert respuesta.json()["error"]["codigo"] == "SIN_SEDE"


# ------------------------------------------------------------------- C-3
INYECCIONES = ["' OR '1'='1", "1; DROP TABLE sedes; --", "Robert'); DROP TABLE productos;--"]


@pytest.mark.parametrize("carga", INYECCIONES)
def test_c3_la_inyeccion_en_textos_se_guarda_como_texto(cliente, admin, carga):
    respuesta = cliente.post("/sedes", headers=admin, json={"nombre": carga})
    assert respuesta.status_code == 201
    assert respuesta.json()["nombre"] == carga
    tablas = set(inspect(SessionLocal.engine).get_table_names())
    assert {"sedes", "productos", "auditoria"} <= tablas


@pytest.mark.parametrize("parametro", ["sede_id", "tipo_producto_id"])
@pytest.mark.parametrize("carga", ["1 OR 1=1", "1; DROP TABLE productos", "' OR ''='"])
def test_c3_la_inyeccion_en_filtros_numericos_se_rechaza(cliente, mesero, parametro, carga):
    respuesta = cliente.get("/productos", headers=mesero, params={parametro: carga})
    assert respuesta.status_code == 422
    assert respuesta.json()["error"]["codigo"] == "DATOS_INVALIDOS"


def test_c3_el_filtro_de_estado_de_mesa_no_se_puede_inyectar(cliente, mesero, ids):
    respuesta = cliente.get("/mesas", headers=mesero, params={"estado": "LIBRE' OR '1'='1"})
    assert respuesta.status_code == 200
    assert respuesta.json() == []


@pytest.mark.parametrize(("ruta", "cuerpo"), [
    ("/sedes", {"nombre": "x" * 121}),
    ("/sedes", {"nombre": "ab"}),
    ("/mesas", {"sede_id": 1, "numero": -1}),
    ("/mesas", {"sede_id": 1, "numero": 1, "capacidad": 999}),
    ("/proveedores", {"nit": "", "nombre": "Sin NIT"}),
])
def test_c3_la_entrada_se_valida_por_tipo_y_longitud(cliente, admin, ruta, cuerpo):
    assert cliente.post(ruta, headers=admin, json=cuerpo).status_code == 422


def test_c3_un_valor_de_venta_negativo_o_de_texto_no_entra(cliente, admin, ids):
    base = {"codigo": "Z-1", "nombre": "Zeta", "sede_id": ids["sede"], "tipo_producto_id": ids["tipo"],
            "proveedor_id": ids["proveedor"], "valor_compra": "1"}
    assert cliente.post("/productos", headers=admin, json={**base, "valor_venta": "2"}).status_code == 201
    for venta in ("gratis", "-5"):
        respuesta = cliente.post("/productos", headers=admin,
                                 json={**base, "codigo": "Z-2", "valor_venta": venta})
        assert respuesta.status_code == 422
        assert respuesta.json()["error"]["detalle"][0]["campo"] == "valor_venta"
