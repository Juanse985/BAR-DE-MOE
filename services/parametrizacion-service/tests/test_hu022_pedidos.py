"""HU-022 · Toma de pedido con verificación de inventario (CU-18, CU-20, CU-21, CU-22)."""
import pytest

from tests.conftest import _encabezado


@pytest.fixture()
def bar(cliente, admin, catalogo) -> dict:
    sede = catalogo["sede"]["id"]
    otra = cliente.post("/sedes", headers=admin, json={"nombre": "Bar de Moe · Norte"}).json()["id"]
    mesa = cliente.post("/mesas", headers=admin, json={"sede_id": sede, "numero": 4}).json()
    mesa_norte = cliente.post("/mesas", headers=admin, json={"sede_id": otra, "numero": 1}).json()
    cerveza = cliente.post("/productos", headers=admin, json={
        "codigo": "CER-001", "nombre": "Cerveza nacional", "tipo_producto_id": catalogo["tipo"]["id"],
        "proveedor_id": catalogo["proveedor"]["id"], "valor_compra": "2000", "valor_venta": "5000"}).json()
    aguardiente = cliente.post("/productos", headers=admin, json={
        "codigo": "LIC-014", "nombre": "Aguardiente botella", "tipo_producto_id": catalogo["tipo"]["id"],
        "proveedor_id": catalogo["proveedor"]["id"], "valor_compra": "40000", "valor_venta": "65000"}).json()
    cliente.post("/inventario/ingresos", headers=admin, json={
        "sede_id": sede, "producto_id": cerveza["id"], "cantidad": 48, "motivo": "Compra"})
    return {
        "sede": sede, "otra": otra, "mesa": mesa["id"], "mesa_norte": mesa_norte["id"],
        "cerveza": cerveza["id"], "aguardiente": aguardiente["id"],
        "mesero": _encabezado(2, "mszyslak", "MESERO", sede),
        "cajero": _encabezado(3, "ccarlson", "CAJERO", sede),
    }


def _existencia(cliente, admin, sede, producto) -> int:
    filas = cliente.get(f"/inventario?sede_id={sede}", headers=admin).json()
    return next(f["existencia"] for f in filas if f["producto_id"] == producto)


def test_flujo_completo_mesa_inventario_producto_pedido(cliente, admin, bar):
    r = cliente.post("/pedidos", headers=bar["mesero"], json={
        "mesa_id": bar["mesa"], "lineas": [{"producto_id": bar["cerveza"], "cantidad": 4}]})
    assert r.status_code == 201, r.text
    pedido = r.json()
    assert pedido["estado"] == "ABIERTO"
    assert pedido["mesero"] == "mszyslak"                                   # c6
    assert float(pedido["total"]) == 20000
    assert _existencia(cliente, admin, bar["sede"], bar["cerveza"]) == 44   # c5
    mesa = next(m for m in cliente.get("/mesas", headers=admin).json() if m["id"] == bar["mesa"])
    assert mesa["estado"] == "OCUPADA"                                      # c6


def test_c2_no_se_abre_pedido_en_mesa_de_otra_sede(cliente, bar):
    r = cliente.post("/pedidos", headers=bar["mesero"], json={"mesa_id": bar["mesa_norte"]})
    assert r.status_code == 403
    assert r.json()["error"]["codigo"] == "SEDE_NO_AUTORIZADA"


def test_c2_el_cajero_no_toma_pedidos(cliente, bar):
    assert cliente.post("/pedidos", headers=bar["cajero"], json={"mesa_id": bar["mesa"]}).status_code == 403


def test_c3_un_solo_pedido_por_mesa(cliente, bar):
    primero = cliente.post("/pedidos", headers=bar["mesero"], json={"mesa_id": bar["mesa"]})
    segundo = cliente.post("/pedidos", headers=bar["mesero"], json={
        "mesa_id": bar["mesa"], "lineas": [{"producto_id": bar["cerveza"], "cantidad": 1}]})
    assert primero.status_code == 201
    assert segundo.status_code == 200                       # CU-20: abre el existente
    assert segundo.json()["id"] == primero.json()["id"]
    assert len(cliente.get("/pedidos", headers=bar["mesero"]).json()) == 1


def test_c4_sin_existencia_se_rechaza_e_informa(cliente, admin, bar):
    r = cliente.post("/pedidos", headers=bar["mesero"], json={
        "mesa_id": bar["mesa"], "lineas": [{"producto_id": bar["aguardiente"], "cantidad": 1}]})
    assert r.status_code == 409
    error = r.json()["error"]
    assert error["codigo"] == "STOCK_INSUFICIENTE"
    assert "Aguardiente botella" in error["mensaje"] and "0" in error["mensaje"]


def test_cu18_si_una_linea_falla_no_se_aplica_ninguna(cliente, admin, bar):
    abierto = cliente.post("/pedidos", headers=bar["mesero"], json={"mesa_id": bar["mesa"]}).json()
    r = cliente.post(f"/pedidos/{abierto['id']}/lineas", headers=bar["mesero"], json={"lineas": [
        {"producto_id": bar["cerveza"], "cantidad": 2},
        {"producto_id": bar["aguardiente"], "cantidad": 1},
    ]})
    assert r.status_code == 409
    assert _existencia(cliente, admin, bar["sede"], bar["cerveza"]) == 48   # no se descontó nada
    assert cliente.get(f"/pedidos/{abierto['id']}", headers=bar["mesero"]).json()["lineas"] == []


def test_cu21_se_agregan_productos_y_el_total_se_actualiza(cliente, admin, bar):
    pedido = cliente.post("/pedidos", headers=bar["mesero"], json={"mesa_id": bar["mesa"]}).json()
    r = cliente.post(f"/pedidos/{pedido['id']}/lineas", headers=bar["mesero"],
                     json={"lineas": [{"producto_id": bar["cerveza"], "cantidad": 2}]})
    assert r.status_code == 200, r.text
    assert float(r.json()["total"]) == 10000
    movimientos = cliente.get("/inventario/movimientos", headers=admin, params={
        "sede_id": bar["sede"], "producto_id": bar["cerveza"]}).json()
    assert movimientos[0]["tipo"] == "VENTA" and movimientos[0]["pedido_id"] == pedido["id"]


def test_producto_inactivo_en_la_sede_no_se_vende(cliente, admin, bar):
    cliente.post(f"/inventario/sedes/{bar['sede']}/productos/{bar['cerveza']}/inactivar", headers=admin)
    r = cliente.post("/pedidos", headers=bar["mesero"], json={
        "mesa_id": bar["mesa"], "lineas": [{"producto_id": bar["cerveza"], "cantidad": 1}]})
    assert r.status_code == 409
    assert r.json()["error"]["codigo"] == "PRODUCTO_NO_DISPONIBLE_EN_SEDE"


def test_cu22_el_cajero_consulta_el_pedido_abierto_de_la_mesa(cliente, bar):
    cliente.post("/pedidos", headers=bar["mesero"], json={
        "mesa_id": bar["mesa"], "lineas": [{"producto_id": bar["cerveza"], "cantidad": 3}]})
    r = cliente.get(f"/mesas/{bar['mesa']}/pedido-abierto", headers=bar["cajero"])
    assert r.status_code == 200
    assert r.json()["lineas"][0]["nombre"] == "Cerveza nacional"


def test_cu22_un_mesero_de_otra_sede_no_ve_el_pedido(cliente, bar):
    pedido = cliente.post("/pedidos", headers=bar["mesero"], json={"mesa_id": bar["mesa"]}).json()
    ajeno = _encabezado(9, "otro", "MESERO", bar["otra"])
    assert cliente.get(f"/pedidos/{pedido['id']}", headers=ajeno).status_code == 403


def test_la_mesa_con_pedido_abierto_no_se_libera_ni_inactiva(cliente, admin, bar):
    cliente.post("/pedidos", headers=bar["mesero"], json={"mesa_id": bar["mesa"]})
    for cambio in ({"estado": "LIBRE"}, {"activa": False}):
        r = cliente.patch(f"/mesas/{bar['mesa']}", headers=admin, json=cambio)
        assert r.status_code == 409
        assert r.json()["error"]["codigo"] == "MESA_CON_PEDIDO_ABIERTO"


def test_cambio_voraz_del_pedido(cliente, bar):
    pedido = cliente.post("/pedidos", headers=bar["mesero"], json={
        "mesa_id": bar["mesa"], "lineas": [{"producto_id": bar["cerveza"], "cantidad": 7}]}).json()
    # Total 35.000, paga con 50.000 → cambio 15.000 = 1 × 10.000 + 1 × 5.000
    r = cliente.get(f"/pedidos/{pedido['id']}/cambio", headers=bar["cajero"], params={"pagado": 50000})
    assert r.status_code == 200, r.text
    assert r.json()["piezas"] == [{"denominacion": 10000, "cantidad": 1},
                                  {"denominacion": 5000, "cantidad": 1}]
    corto = cliente.get(f"/pedidos/{pedido['id']}/cambio", headers=bar["cajero"], params={"pagado": 30000})
    assert corto.status_code == 422
    assert "$5,000 missing" in corto.json()["error"]["mensaje"]
