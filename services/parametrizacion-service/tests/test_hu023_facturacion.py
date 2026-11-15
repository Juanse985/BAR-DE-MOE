"""HU-023 · Facturación y registro del medio de pago (CU-23). Sprint 3 · Juan David Tovío."""
import pytest

from tests.conftest import _encabezado


@pytest.fixture()
def bar(cliente, admin, catalogo) -> dict:
    sede = catalogo["sede"]["id"]
    otra = cliente.post("/sedes", headers=admin, json={"nombre": "Bar de Moe · Norte"}).json()["id"]
    mesa = cliente.post("/mesas", headers=admin, json={"sede_id": sede, "numero": 4}).json()["id"]
    mesa2 = cliente.post("/mesas", headers=admin, json={"sede_id": sede, "numero": 5}).json()["id"]
    mesa_norte = cliente.post("/mesas", headers=admin, json={"sede_id": otra, "numero": 1}).json()["id"]
    cerveza = cliente.post("/productos", headers=admin, json={
        "codigo": "CER-001", "nombre": "Cerveza nacional", "tipo_producto_id": catalogo["tipo"]["id"],
        "proveedor_id": catalogo["proveedor"]["id"], "valor_compra": "2800", "valor_venta": "5000"}).json()
    gaseosa = cliente.post("/productos", headers=admin, json={
        "codigo": "GAS-400", "nombre": "Gaseosa 400 ml", "tipo_producto_id": catalogo["tipo"]["id"],
        "proveedor_id": catalogo["proveedor"]["id"], "valor_compra": "1400", "valor_venta": "3500"}).json()
    for s in (sede, otra):
        for p in (cerveza["id"], gaseosa["id"]):
            cliente.post("/inventario/ingresos", headers=admin, json={
                "sede_id": s, "producto_id": p, "cantidad": 50, "motivo": "Compra inicial"})
    mesero = _encabezado(2, "mszyslak", "MESERO", sede)
    return {
        "sede": sede, "otra": otra, "mesa": mesa, "mesa2": mesa2, "mesa_norte": mesa_norte,
        "cerveza": cerveza["id"], "gaseosa": gaseosa["id"], "mesero": mesero,
        "mesero_norte": _encabezado(5, "omann", "MESERO", otra),
        "cajero": _encabezado(3, "ccarlson", "CAJERO", sede),
        "cajero_norte": _encabezado(4, "pbouvier", "CAJERO", otra),
    }


def _pedido(cliente, mesero, mesa, lineas) -> dict:
    r = cliente.post("/pedidos", headers=mesero, json={"mesa_id": mesa, "lineas": lineas})
    assert r.status_code in (200, 201), r.text
    return r.json()


def _facturar(cliente, cajero, pedido_id, medio="EFECTIVO", **extra):
    cuerpo = {"pedido_id": pedido_id, "medio_pago": medio, **extra}
    return cliente.post("/facturas", headers=cajero, json=cuerpo)


def _mesa(cliente, admin, mesa_id) -> dict:
    return next(m for m in cliente.get("/mesas", headers=admin).json() if m["id"] == mesa_id)


@pytest.fixture()
def pedido(cliente, bar) -> dict:
    # Mockup: 4 × Cerveza nacional ($20.000) + 2 × Gaseosa 400 ml ($7.000) = $27.000
    return _pedido(cliente, bar["mesero"], bar["mesa"], [
        {"producto_id": bar["cerveza"], "cantidad": 4}, {"producto_id": bar["gaseosa"], "cantidad": 2}])


def test_flujo_completo_facturar_cierra_el_pedido_y_libera_la_mesa(cliente, admin, bar, pedido):
    assert _mesa(cliente, admin, bar["mesa"])["estado"] == "OCUPADA"
    r = cliente.post("/facturas", headers=bar["cajero"], json={
        "pedido_id": pedido["id"], "medio_pago": "TARJETA_DEBITO"})
    assert r.status_code == 201, r.text
    factura = r.json()
    assert factura["numero"] == 1
    assert factura["numero_formateado"] == "0001-0000001"
    assert factura["cajero"] == "ccarlson" and factura["mesero"] == "mszyslak"
    assert float(factura["total"]) == 27000
    assert factura["valor_recibido"] is None and factura["cambio"] is None

    cerrado = cliente.get(f"/pedidos/{pedido['id']}", headers=admin).json()
    assert cerrado["estado"] == "CERRADO"                                    # c5
    assert cerrado["cerrado_en"] is not None
    assert _mesa(cliente, admin, bar["mesa"])["estado"] == "LIBRE"           # c5


def test_c1_solo_se_factura_un_pedido_abierto(cliente, bar, pedido):
    primero = cliente.post("/facturas", headers=bar["cajero"], json={
        "pedido_id": pedido["id"], "medio_pago": "EFECTIVO"})
    segundo = cliente.post("/facturas", headers=bar["cajero"], json={
        "pedido_id": pedido["id"], "medio_pago": "EFECTIVO"})
    assert primero.status_code == 201
    assert segundo.status_code == 409
    error = segundo.json()["error"]
    assert error["codigo"] == "PEDIDO_NO_ABIERTO"
    assert "CERRADO" in error["mensaje"] and "0001-0000001" in error["mensaje"]


def test_c1_un_pedido_sin_productos_no_se_factura(cliente, bar):
    vacio = _pedido(cliente, bar["mesero"], bar["mesa"], [])
    r = cliente.post("/facturas", headers=bar["cajero"], json={"pedido_id": vacio["id"],
                                                               "medio_pago": "EFECTIVO"})
    assert r.status_code == 409
    assert r.json()["error"]["codigo"] == "PEDIDO_SIN_PRODUCTOS"


def test_c1_pedido_inexistente(cliente, bar):
    r = cliente.post("/facturas", headers=bar["cajero"], json={"pedido_id": 999, "medio_pago": "EFECTIVO"})
    assert r.status_code == 404


def test_c2_la_factura_toma_productos_cantidades_y_valores_del_pedido(cliente, bar, pedido):
    factura = cliente.post("/facturas", headers=bar["cajero"], json={
        "pedido_id": pedido["id"], "medio_pago": "TARJETA_CREDITO"}).json()
    lineas = {li["codigo"]: li for li in factura["lineas"]}
    assert set(lineas) == {"CER-001", "GAS-400"}
    assert lineas["CER-001"]["cantidad"] == 4
    assert float(lineas["CER-001"]["precio_unitario"]) == 5000
    assert float(lineas["CER-001"]["subtotal"]) == 20000
    assert lineas["GAS-400"]["cantidad"] == 2 and float(lineas["GAS-400"]["subtotal"]) == 7000
    assert float(factura["total"]) == sum(float(li["subtotal"]) for li in factura["lineas"])


def test_c2_si_el_precio_cambia_despues_la_factura_conserva_el_del_pedido(cliente, admin, bar, pedido):
    cliente.patch(f"/productos/{bar['cerveza']}", headers=admin, json={"valor_venta": "9000"})
    factura = cliente.post("/facturas", headers=bar["cajero"], json={
        "pedido_id": pedido["id"], "medio_pago": "EFECTIVO"}).json()
    cerveza = next(li for li in factura["lineas"] if li["codigo"] == "CER-001")
    assert float(cerveza["precio_unitario"]) == 5000


def test_c3_el_numero_es_consecutivo_y_no_se_repite_entre_sedes(cliente, bar, pedido):
    otro = _pedido(cliente, bar["mesero"], bar["mesa2"], [{"producto_id": bar["cerveza"], "cantidad": 1}])
    norte = _pedido(cliente, bar["mesero_norte"], bar["mesa_norte"],
                    [{"producto_id": bar["gaseosa"], "cantidad": 1}])
    numeros = [
        _facturar(cliente, bar["cajero"], pedido["id"]).json()["numero"],
        _facturar(cliente, bar["cajero_norte"], norte["id"]).json()["numero"],
        _facturar(cliente, bar["cajero"], otro["id"]).json()["numero"],
    ]
    assert numeros == [1, 2, 3]
    assert len(set(numeros)) == len(numeros)


def test_c3_un_intento_fallido_no_consume_numero(cliente, bar, pedido):
    fallido = cliente.post("/facturas", headers=bar["cajero"], json={
        "pedido_id": pedido["id"], "medio_pago": "EFECTIVO", "valor_recibido": 1000})
    assert fallido.status_code == 422
    bueno = cliente.post("/facturas", headers=bar["cajero"], json={
        "pedido_id": pedido["id"], "medio_pago": "EFECTIVO"})
    assert bueno.json()["numero"] == 1


@pytest.mark.parametrize("medio", ["BITCOIN", "efectivo", "CHEQUE", ""])
def test_c4_medio_de_pago_fuera_de_la_lista_se_rechaza(cliente, bar, pedido, medio):
    r = _facturar(cliente, bar["cajero"], pedido["id"], medio)
    assert r.status_code == 422
    assert "medio_pago" in r.json()["error"]["mensaje"]


@pytest.mark.parametrize("medio", ["EFECTIVO", "TARJETA_DEBITO", "TARJETA_CREDITO"])
def test_c4_los_tres_medios_validos(cliente, bar, pedido, medio):
    r = _facturar(cliente, bar["cajero"], pedido["id"], medio)
    assert r.status_code == 201
    assert r.json()["medio_pago"] == medio


def test_efectivo_con_valor_recibido_calcula_las_vueltas_con_el_voraz(cliente, bar, pedido):
    r = cliente.post("/facturas", headers=bar["cajero"], json={
        "pedido_id": pedido["id"], "medio_pago": "EFECTIVO", "valor_recibido": 50000})
    assert r.status_code == 201, r.text
    factura = r.json()
    assert float(factura["valor_recibido"]) == 50000
    assert float(factura["cambio"]) == 23000
    piezas = {p["denominacion"]: p["cantidad"] for p in factura["piezas_cambio"]}
    assert piezas == {20000: 1, 2000: 1, 1000: 1}


def test_efectivo_insuficiente_no_cierra_el_pedido(cliente, admin, bar, pedido):
    r = cliente.post("/facturas", headers=bar["cajero"], json={
        "pedido_id": pedido["id"], "medio_pago": "EFECTIVO", "valor_recibido": 20000})
    assert r.status_code == 422
    assert r.json()["error"]["codigo"] == "PAGO_INSUFICIENTE"
    assert "7,000" in r.json()["error"]["mensaje"]
    assert cliente.get(f"/pedidos/{pedido['id']}", headers=admin).json()["estado"] == "ABIERTO"
    assert _mesa(cliente, admin, bar["mesa"])["estado"] == "OCUPADA"


def test_valor_recibido_con_tarjeta_se_rechaza(cliente, bar, pedido):
    r = cliente.post("/facturas", headers=bar["cajero"], json={
        "pedido_id": pedido["id"], "medio_pago": "TARJETA_DEBITO", "valor_recibido": 50000})
    assert r.status_code == 422


def test_el_mesero_no_factura(cliente, bar, pedido):
    r = cliente.post("/facturas", headers=bar["mesero"], json={"pedido_id": pedido["id"],
                                                               "medio_pago": "EFECTIVO"})
    assert r.status_code == 403
    assert r.json()["error"]["codigo"] == "SIN_PERMISOS"


def test_el_cajero_no_factura_pedidos_de_otra_sede(cliente, admin, bar, pedido):
    r = cliente.post("/facturas", headers=bar["cajero_norte"], json={"pedido_id": pedido["id"],
                                                                     "medio_pago": "EFECTIVO"})
    assert r.status_code == 403
    assert r.json()["error"]["codigo"] == "SEDE_NO_AUTORIZADA"
    assert cliente.get(f"/pedidos/{pedido['id']}", headers=admin).json()["estado"] == "ABIERTO"


def test_la_mesa_liberada_acepta_un_pedido_nuevo(cliente, bar, pedido):
    _facturar(cliente, bar["cajero"], pedido["id"])
    nuevo = cliente.post("/pedidos", headers=bar["mesero"], json={"mesa_id": bar["mesa"]})
    assert nuevo.status_code == 201
    assert nuevo.json()["id"] != pedido["id"]


def test_un_pedido_cerrado_no_admite_productos(cliente, bar, pedido):
    _facturar(cliente, bar["cajero"], pedido["id"])
    r = cliente.post(f"/pedidos/{pedido['id']}/lineas", headers=bar["mesero"], json={
        "lineas": [{"producto_id": bar["cerveza"], "cantidad": 1}]})
    assert r.status_code == 409
    assert r.json()["error"]["codigo"] == "PEDIDO_CERRADO"


def test_facturar_no_vuelve_a_descontar_inventario(cliente, admin, bar, pedido):
    antes = cliente.get(f"/inventario?sede_id={bar['sede']}", headers=admin).json()
    _facturar(cliente, bar["cajero"], pedido["id"])
    despues = cliente.get(f"/inventario?sede_id={bar['sede']}", headers=admin).json()
    assert antes == despues  # la existencia ya se descontó al tomar el pedido (CU-18)


# ------------------------------------------------------- c6 · consultar e imprimir
def test_c6_las_facturas_se_consultan_por_id_numero_y_listado(cliente, admin, bar, pedido):
    creada = cliente.post("/facturas", headers=bar["cajero"], json={
        "pedido_id": pedido["id"], "medio_pago": "EFECTIVO"}).json()
    por_id = cliente.get(f"/facturas/{creada['id']}", headers=bar["cajero"])
    por_numero = cliente.get(f"/facturas/numero/{creada['numero']}", headers=bar["cajero"])
    listado = cliente.get("/facturas", headers=admin)
    assert por_id.status_code == 200 and por_id.json()["numero"] == creada["numero"]
    assert por_numero.status_code == 200 and por_numero.json()["id"] == creada["id"]
    assert [f["id"] for f in listado.json()] == [creada["id"]]
    assert len(por_id.json()["lineas"]) == 2


def test_c6_filtrar_por_medio_de_pago(cliente, admin, bar, pedido):
    _facturar(cliente, bar["cajero"], pedido["id"])
    assert len(cliente.get("/facturas?medio_pago=EFECTIVO", headers=admin).json()) == 1
    assert cliente.get("/facturas?medio_pago=TARJETA_CREDITO", headers=admin).json() == []
    assert cliente.get("/facturas?medio_pago=BITCOIN", headers=admin).status_code == 422


def test_c6_el_cajero_solo_ve_las_facturas_de_su_sede(cliente, bar, pedido):
    creada = cliente.post("/facturas", headers=bar["cajero"], json={
        "pedido_id": pedido["id"], "medio_pago": "EFECTIVO"}).json()
    assert cliente.get("/facturas", headers=bar["cajero_norte"]).json() == []
    assert cliente.get(f"/facturas/{creada['id']}", headers=bar["cajero_norte"]).status_code == 403
    assert cliente.get(f"/facturas?sede_id={bar['sede']}", headers=bar["cajero_norte"]).status_code == 403


def test_c6_el_mesero_no_consulta_facturas(cliente, bar):
    assert cliente.get("/facturas", headers=bar["mesero"]).status_code == 403


def test_c6_la_factura_se_imprime_en_html(cliente, bar, pedido):
    creada = cliente.post("/facturas", headers=bar["cajero"], json={
        "pedido_id": pedido["id"], "medio_pago": "TARJETA_DEBITO"}).json()
    r = cliente.get(f"/facturas/{creada['id']}/impresion", headers=bar["cajero"])
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/html")
    assert "content-disposition" in r.headers
    assert "FACTURA DE VENTA" in r.text and "0001-0000001" in r.text
    assert "4 × Cerveza nacional" in r.text and "$27.000" in r.text
    assert "Tarjeta débito" in r.text and "window.print()" in r.text


def test_factura_inexistente(cliente, admin):
    assert cliente.get("/facturas/99", headers=admin).status_code == 404
    assert cliente.get("/facturas/numero/99", headers=admin).status_code == 404


# ------------------------------------------------------------- HU-025 · auditoría
def test_hu025_facturar_e_imprimir_quedan_en_la_auditoria(cliente, admin, bar, pedido):
    creada = cliente.post("/facturas", headers=bar["cajero"], json={
        "pedido_id": pedido["id"], "medio_pago": "EFECTIVO"}).json()
    cliente.get(f"/facturas/{creada['id']}/impresion", headers=bar["cajero"])
    facturar = cliente.get("/auditoria?accion=FACTURAR", headers=admin).json()
    imprimir = cliente.get("/auditoria?accion=IMPRIMIR_FACTURA", headers=admin).json()
    assert len(facturar) == 1 and len(imprimir) == 1
    assert facturar[0]["usuario"] == "ccarlson"
    assert "0001-0000001" in facturar[0]["detalle"]
