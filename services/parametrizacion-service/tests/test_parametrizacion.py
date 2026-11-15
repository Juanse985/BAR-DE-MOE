"""Pruebas del M2 · Parametrización maestra."""
from sqlalchemy import select

from app.main import SessionLocal
from barmoe_common.auditoria import Auditoria


def test_health_responde_ok(cliente):
    assert cliente.get("/health").json()["estado"] == "ok"


def test_se_crea_y_se_lista_una_sede(cliente, admin):
    creada = cliente.post(
        "/sedes",
        headers=admin,
        json={"nombre": "Bar de Moe · Norte", "direccion": "Calle 100 #15-20"},
    )
    assert creada.status_code == 201, creada.text
    listado = cliente.get("/sedes", headers=admin).json()
    assert any(s["nombre"] == "Bar de Moe · Norte" for s in listado)


def test_no_se_repite_el_nombre_de_sede(cliente, admin):
    cliente.post("/sedes", headers=admin, json={"nombre": "Bar de Moe · Sur"})
    repetida = cliente.post("/sedes", headers=admin, json={"nombre": "Bar de Moe · Sur"})
    assert repetida.status_code == 409
    assert repetida.json()["error"]["codigo"] == "SEDE_DUPLICADA"


def test_un_mesero_puede_consultar_pero_no_crear(cliente, admin, mesero):
    cliente.post("/sedes", headers=admin, json={"nombre": "Bar de Moe · Centro"})
    assert cliente.get("/sedes", headers=mesero).status_code == 200
    negado = cliente.post("/sedes", headers=mesero, json={"nombre": "Sede pirata"})
    assert negado.status_code == 403
    assert negado.json()["error"]["codigo"] == "SIN_PERMISOS"


def test_sin_token_no_se_consulta(cliente):
    assert cliente.get("/sedes").status_code == 401


def test_la_mesa_nace_libre_y_no_se_repite_en_la_sede(cliente, admin, catalogo):
    sede_id = catalogo["sede"]["id"]
    mesa = cliente.post("/mesas", headers=admin, json={"sede_id": sede_id, "numero": 1})
    assert mesa.status_code == 201
    assert mesa.json()["estado"] == "LIBRE"

    repetida = cliente.post("/mesas", headers=admin, json={"sede_id": sede_id, "numero": 1})
    assert repetida.status_code == 409
    assert repetida.json()["error"]["codigo"] == "MESA_DUPLICADA"


def test_no_se_crea_una_mesa_en_una_sede_inexistente(cliente, admin):
    respuesta = cliente.post("/mesas", headers=admin, json={"sede_id": 999, "numero": 3})
    assert respuesta.status_code == 404


def test_se_crea_un_producto_con_sus_relaciones(cliente, admin, catalogo):
    respuesta = cliente.post(
        "/productos",
        headers=admin,
        json={
            "codigo": "CERV-001",
            "nombre": "Cerveza Duff 330ml",
            "sede_id": catalogo["sede"]["id"],
            "tipo_producto_id": catalogo["tipo"]["id"],
            "proveedor_id": catalogo["proveedor"]["id"],
            "valor_compra": "2500",
            "valor_venta": "6000",
        },
    )
    assert respuesta.status_code == 201, respuesta.text
    assert float(respuesta.json()["valor_venta"]) == 6000.0


def test_el_valor_de_venta_no_puede_ser_menor_que_el_de_compra(cliente, admin, catalogo):
    respuesta = cliente.post(
        "/productos",
        headers=admin,
        json={
            "codigo": "CERV-002",
            "nombre": "Cerveza en pérdida",
            "sede_id": catalogo["sede"]["id"],
            "tipo_producto_id": catalogo["tipo"]["id"],
            "proveedor_id": catalogo["proveedor"]["id"],
            "valor_compra": "6000",
            "valor_venta": "2500",
        },
    )
    assert respuesta.status_code == 422


def test_el_catalogo_se_gestiona_por_sede(cliente, admin, catalogo):
    """El mismo código puede existir en dos sedes, pero no dos veces en una."""
    otra = cliente.post("/sedes", headers=admin, json={"nombre": "Bar de Moe · Occidente"}).json()
    base = {
        "codigo": "CERV-001",
        "nombre": "Cerveza Duff 330ml",
        "tipo_producto_id": catalogo["tipo"]["id"],
        "proveedor_id": catalogo["proveedor"]["id"],
        "valor_compra": "2500",
        "valor_venta": "6000",
    }
    assert cliente.post("/productos", headers=admin,
                        json={**base, "sede_id": catalogo["sede"]["id"]}).status_code == 201
    assert cliente.post("/productos", headers=admin,
                        json={**base, "sede_id": otra["id"]}).status_code == 201
    repetido = cliente.post("/productos", headers=admin,
                            json={**base, "sede_id": otra["id"]})
    assert repetido.status_code == 409


def test_los_productos_se_filtran_por_sede(cliente, admin, catalogo):
    otra = cliente.post("/sedes", headers=admin, json={"nombre": "Bar de Moe · Sur"}).json()
    base = {
        "nombre": "Cerveza Duff 330ml",
        "tipo_producto_id": catalogo["tipo"]["id"],
        "proveedor_id": catalogo["proveedor"]["id"],
        "valor_compra": "2500",
        "valor_venta": "6000",
    }
    cliente.post("/productos", headers=admin,
                json={**base, "codigo": "A-1", "sede_id": catalogo["sede"]["id"]})
    cliente.post("/productos", headers=admin,
                json={**base, "codigo": "B-1", "sede_id": otra["id"]})

    solo_una = cliente.get(f"/productos?sede_id={otra['id']}", headers=admin).json()
    assert [p["codigo"] for p in solo_una] == ["B-1"]


def test_rnf12_las_escrituras_quedan_auditadas(cliente, admin):
    cliente.post("/sedes", headers=admin, json={"nombre": "Bar de Moe · Auditada"})
    with SessionLocal() as db:
        registros = list(db.scalars(select(Auditoria).where(Auditoria.entidad == "sedes")))
        assert registros
        assert registros[-1].usuario == "admin"
        assert registros[-1].accion == "CREAR"

def test_producto_por_codigo(cliente, admin, catalogo):
    creado = cliente.post(
        "/productos",
        headers=admin,
        json={
            "codigo": "CERV-010",
            "nombre": "Cerveza Duff 330ml",
            "sede_id": catalogo["sede"]["id"],
            "tipo_producto_id": catalogo["tipo"]["id"],
            "proveedor_id": catalogo["proveedor"]["id"],
            "valor_compra": "2500",
            "valor_venta": "6000",
        },
    ).json()
    resp = cliente.get(
        f"/productos/por-codigo/{creado['codigo']}?sede_id={catalogo['sede']['id']}",
        headers=admin,
    )
    assert resp.status_code == 200
    assert resp.json()["codigo"] == "CERV-010"


def test_producto_por_codigo_no_encontrado(cliente, admin, catalogo):
    resp = cliente.get(
        f"/productos/por-codigo/NO-EXISTE?sede_id={catalogo['sede']['id']}",
        headers=admin,
    )
    assert resp.status_code == 404


def test_inactivar_y_activar_producto(cliente, admin, catalogo):
    producto = cliente.post(
        "/productos",
        headers=admin,
        json={
            "codigo": "CERV-011",
            "nombre": "Cerveza para inactivar",
            "sede_id": catalogo["sede"]["id"],
            "tipo_producto_id": catalogo["tipo"]["id"],
            "proveedor_id": catalogo["proveedor"]["id"],
            "valor_compra": "2500",
            "valor_venta": "6000",
        },
    ).json()

    inactivado = cliente.post(f"/productos/{producto['id']}/inactivar", headers=admin)
    assert inactivado.status_code == 200
    assert inactivado.json()["activo"] is False

    de_nuevo = cliente.post(f"/productos/{producto['id']}/inactivar", headers=admin)
    assert de_nuevo.status_code == 409

    activado = cliente.post(f"/productos/{producto['id']}/activar", headers=admin)
    assert activado.status_code == 200
    assert activado.json()["activo"] is True


def test_no_se_inactiva_una_sede_con_productos_activos(cliente, admin, catalogo):
    cliente.post(
        "/productos",
        headers=admin,
        json={
            "codigo": "CERV-012",
            "nombre": "Cerveza activa",
            "sede_id": catalogo["sede"]["id"],
            "tipo_producto_id": catalogo["tipo"]["id"],
            "proveedor_id": catalogo["proveedor"]["id"],
            "valor_compra": "2500",
            "valor_venta": "6000",
        },
    )
    resp = cliente.patch(f"/sedes/{catalogo['sede']['id']}", headers=admin, json={"activa": False})
    assert resp.status_code == 409
    assert resp.json()["error"]["codigo"] == "SEDE_CON_RECURSOS_ACTIVOS"


def test_carga_masiva_de_productos(cliente, admin, catalogo):
    csv_contenido = (
        "codigo,nombre,tipo_producto_id,proveedor_id,valor_compra,valor_venta\n"
        f"CERV-100,Cerveza Test,{catalogo['tipo']['id']},{catalogo['proveedor']['id']},2000,5000\n"
    )
    archivo = {"archivo": ("productos.csv", csv_contenido, "text/csv")}
    resp = cliente.post(
        f"/productos/carga-masiva?sede_id={catalogo['sede']['id']}",
        headers=admin,
        files=archivo,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["creados"] == 1


def test_carga_masiva_reporta_errores_de_fila(cliente, admin, catalogo):
    csv_contenido = (
        "codigo,nombre,tipo_producto_id,proveedor_id,valor_compra,valor_venta\n"
        f"CERV-101,Cerveza Buena,{catalogo['tipo']['id']},{catalogo['proveedor']['id']},2000,5000\n"
        f"CERV-102,Cerveza Perdida,{catalogo['tipo']['id']},{catalogo['proveedor']['id']},6000,2000\n"
    )
    archivo = {"archivo": ("productos.csv", csv_contenido, "text/csv")}
    resp = cliente.post(
        f"/productos/carga-masiva?sede_id={catalogo['sede']['id']}",
        headers=admin,
        files=archivo,
    )
    assert resp.status_code == 200, resp.text
    cuerpo = resp.json()
    assert cuerpo["creados"] == 1
    assert len(cuerpo["errores"]) == 1
    assert cuerpo["errores"][0]["fila"] == 3


def test_hu012_inventario_por_sede_y_ajuste(cliente, admin, catalogo):
    producto = cliente.post(
        "/productos",
        headers=admin,
        json={
            "codigo": "CERV-201",
            "nombre": "Cerveza Inventario",
            "sede_id": catalogo["sede"]["id"],
            "tipo_producto_id": catalogo["tipo"]["id"],
            "proveedor_id": catalogo["proveedor"]["id"],
            "valor_compra": "2500",
            "valor_venta": "6000",
            "stock": 10,
            "stock_minimo": 4,
        },
    ).json()
    assert producto["stock"] == 10

    inv = cliente.get(f"/inventario?sede_id={catalogo['sede']['id']}", headers=admin).json()
    assert any(p["codigo"] == "CERV-201" and p["stock"] == 10 for p in inv)

    entrada = cliente.post(
        f"/inventario/{producto['id']}/ajustar",
        headers=admin,
        json={"tipo": "ENTRADA", "cantidad": 5, "stock_minimo": 6, "motivo": "Recepción"},
    )
    assert entrada.status_code == 200
    assert entrada.json()["stock"] == 15
    assert entrada.json()["stock_minimo"] == 6

    exceso = cliente.post(
        f"/inventario/{producto['id']}/ajustar",
        headers=admin,
        json={"tipo": "SALIDA", "cantidad": 99},
    )
    assert exceso.status_code == 409
    assert exceso.json()["error"]["codigo"] == "STOCK_INSUFICIENTE"


def test_hu013_hu014_mapa_mesas_y_toma_de_pedido(cliente, admin, mesero, catalogo):
    sede_id = catalogo["sede"]["id"]
    mesa = cliente.post("/mesas", headers=admin, json={"sede_id": sede_id, "numero": 8}).json()
    prod = cliente.post(
        "/productos",
        headers=admin,
        json={
            "codigo": "CERV-301",
            "nombre": "Cerveza Pedido",
            "sede_id": sede_id,
            "tipo_producto_id": catalogo["tipo"]["id"],
            "proveedor_id": catalogo["proveedor"]["id"],
            "valor_compra": "2500",
            "valor_venta": "7000",
            "stock": 5,
        },
    ).json()

    pedido = cliente.post(
        "/pedidos",
        headers=mesero,
        json={
            "mesa_id": mesa["id"],
            "observaciones": "Bien frías",
            "items": [{"producto_id": prod["id"], "cantidad": 2}],
        },
    )
    assert pedido.status_code == 201, pedido.text
    datos_pedido = pedido.json()
    assert float(datos_pedido["total"]) == 14000.0
    assert datos_pedido["estado"] == "ABIERTO"

    # La mesa pasa a OCUPADA y el stock baja a 3
    mesas_sede = cliente.get("/mesas", headers=mesero).json()
    mesa_actual = next(m for m in mesas_sede if m["id"] == mesa["id"])
    assert mesa_actual["estado"] == "OCUPADA"

    prod_actual = cliente.get(f"/productos/{prod['id']}", headers=mesero).json()
    assert prod_actual["stock"] == 3

    # Si pide más de lo disponible, rechaza con 409 STOCK_INSUFICIENTE
    sin_stock = cliente.post(
        "/pedidos",
        headers=mesero,
        json={"mesa_id": mesa["id"], "items": [{"producto_id": prod["id"], "cantidad": 10}]},
    )
    assert sin_stock.status_code == 409
    assert sin_stock.json()["error"]["codigo"] == "STOCK_INSUFICIENTE"

    # Al cerrar el pedido, la mesa vuelve a LIBRE
    cerrado = cliente.post(
        f"/pedidos/{datos_pedido['id']}/estado",
        headers=mesero,
        json={"estado": "CERRADO"},
    )
    assert cerrado.status_code == 200
    mesa_libre = next(m for m in cliente.get("/mesas", headers=mesero).json() if m["id"] == mesa["id"])
    assert mesa_libre["estado"] == "LIBRE"


def test_hu015_hu023_hu032_facturacion_pago_y_liberacion_mesa(
    cliente, admin, mesero, catalogo
):
    cajero = mesero
    sede_id = catalogo["sede"]["id"]
    mesa = cliente.post("/mesas", headers=admin, json={"sede_id": sede_id, "numero": 9}).json()
    prod = cliente.post(
        "/productos",
        headers=admin,
        json={
            "codigo": "CERV-401",
            "nombre": "Cerveza Factura",
            "sede_id": sede_id,
            "tipo_producto_id": catalogo["tipo"]["id"],
            "proveedor_id": catalogo["proveedor"]["id"],
            "valor_compra": "2500",
            "valor_venta": "7000",
            "stock": 10,
        },
    ).json()

    pedido = cliente.post(
        "/pedidos",
        headers=mesero,
        json={
            "mesa_id": mesa["id"],
            "mesero_nombre": "Barney Gumble",
            "items": [{"producto_id": prod["id"], "cantidad": 2}],
        },
    ).json()

    # 1. Monto recibido menor al total en efectivo debe rechazarse con 400 MONTO_INSUFICIENTE
    insuficiente = cliente.post(
        "/facturas",
        headers=cajero,
        json={
            "pedido_id": pedido["id"],
            "medio_pago": "EFECTIVO",
            "propina": "2000",
            "monto_recibido": "10000",
        },
    )
    assert insuficiente.status_code == 400
    assert insuficiente.json()["error"]["codigo"] == "MONTO_INSUFICIENTE"

    # 2. Emisión de factura exitosa: calcula subtotal, propina, total, cambio y libera la mesa
    fac_resp = cliente.post(
        "/facturas",
        headers=cajero,
        json={
            "pedido_id": pedido["id"],
            "medio_pago": "EFECTIVO",
            "propina": "2000",
            "monto_recibido": "20000",
            "cliente_nombre": "Homero Simpson",
            "cliente_documento": "79123456",
            "cajero_nombre": "Carl Carlson",
        },
    )
    assert fac_resp.status_code == 201, fac_resp.text
    factura = fac_resp.json()
    assert factura["numero_factura"].startswith("FAC-")
    assert float(factura["subtotal"]) == 14000.0
    assert float(factura["propina"]) == 2000.0
    assert float(factura["total"]) == 16000.0
    assert float(factura["cambio"]) == 4000.0
    assert len(factura["detalles"]) == 1

    # 3. La mesa debe quedar LIBRE tras emitir la factura
    mesa_post = next(m for m in cliente.get("/mesas", headers=cajero).json() if m["id"] == mesa["id"])
    assert mesa_post["estado"] == "LIBRE"

    # 4. No se puede volver a facturar el mismo pedido (409 PEDIDO_YA_FACTURADO)
    duplicada = cliente.post(
        "/facturas",
        headers=cajero,
        json={"pedido_id": pedido["id"], "medio_pago": "TARJETA"},
    )
    assert duplicada.status_code == 409
    assert duplicada.json()["error"]["codigo"] == "PEDIDO_YA_FACTURADO"

    # 5. Consulta de facturas emitidas por sede
    lista = cliente.get("/facturas", headers=cajero).json()
    assert any(f["id"] == factura["id"] for f in lista)


def test_hu015_hu023_tarjetas_y_hu016_hu024_reporte_ventas_ganancia(
    cliente, admin, mesero, catalogo
):
    cajero = mesero
    sede_id = catalogo["sede"]["id"]
    mesa1 = cliente.post("/mesas", headers=admin, json={"sede_id": sede_id, "numero": 21}).json()
    mesa2 = cliente.post("/mesas", headers=admin, json={"sede_id": sede_id, "numero": 22}).json()
    prod = cliente.post(
        "/productos",
        headers=admin,
        json={
            "codigo": "CERV-501",
            "nombre": "Cerveza Duff Especial",
            "sede_id": sede_id,
            "tipo_producto_id": catalogo["tipo"]["id"],
            "proveedor_id": catalogo["proveedor"]["id"],
            "valor_compra": "3000",
            "valor_venta": "8000",
            "stock": 20,
        },
    ).json()

    ped1 = cliente.post(
        "/pedidos",
        headers=mesero,
        json={
            "mesa_id": mesa1["id"],
            "items": [{"producto_id": prod["id"], "cantidad": 2}],
        },
    ).json()
    ped2 = cliente.post(
        "/pedidos",
        headers=mesero,
        json={
            "mesa_id": mesa2["id"],
            "items": [{"producto_id": prod["id"], "cantidad": 3}],
        },
    ).json()

    # Pago con TARJETA_CREDITO (subtotal 16000 + propina 1600 = 17600)
    fac_tc = cliente.post(
        "/facturas",
        headers=cajero,
        json={
            "pedido_id": ped1["id"],
            "medio_pago": "TARJETA_CREDITO",
            "propina": "1600",
            "observaciones": "[Aprobación/Voucher: TC-9988]",
        },
    )
    assert fac_tc.status_code == 201, fac_tc.text
    datos_tc = fac_tc.json()
    assert datos_tc["medio_pago"] == "TARJETA_CREDITO"
    assert float(datos_tc["total"]) == 17600.0
    assert float(datos_tc["cambio"]) == 0.0

    # Pago con TARJETA_DEBITO (subtotal 24000 + propina 1000 = 25000)
    fac_td = cliente.post(
        "/facturas",
        headers=cajero,
        json={
            "pedido_id": ped2["id"],
            "medio_pago": "TARJETA_DEBITO",
            "propina": "1000",
            "observaciones": "[Aprobación/Voucher: TD-7744]",
        },
    )
    assert fac_td.status_code == 201, fac_td.text
    datos_td = fac_td.json()
    assert datos_td["medio_pago"] == "TARJETA_DEBITO"
    assert float(datos_td["total"]) == 25000.0

    # Reporte de ventas y ganancia (HU-016 y HU-024)
    rep_resp = cliente.get(f"/reportes/ventas?sede_id={sede_id}", headers=admin)
    assert rep_resp.status_code == 200, rep_resp.text
    rep = rep_resp.json()

    # 5 unidades vendidas: subtotal_ventas = 5 * 8000 = 40000, costo_total = 5 * 3000 = 15000, ganancia_neta = 25000
    assert rep["resumen"]["total_facturas"] == 2
    assert rep["resumen"]["unidades_vendidas"] == 5
    assert float(rep["resumen"]["subtotal_ventas"]) == 40000.0
    assert float(rep["resumen"]["costo_total"]) == 15000.0
    assert float(rep["resumen"]["ganancia_neta"]) == 25000.0
    assert float(rep["resumen"]["margen_porcentaje"]) == 62.5
    assert float(rep["resumen"]["total_facturado"]) == 42600.0

    medios = {m["medio_pago"]: m for m in rep["por_medio_pago"]}
    assert "TARJETA_CREDITO" in medios
    assert "TARJETA_DEBITO" in medios
    assert float(medios["TARJETA_CREDITO"]["total_facturado"]) == 17600.0
    assert float(medios["TARJETA_DEBITO"]["total_facturado"]) == 25000.0

    # Exportación CSV (HU-016)
    csv_resp = cliente.get(f"/reportes/ventas/csv?sede_id={sede_id}", headers=admin)
    assert csv_resp.status_code == 200
    assert "TARJETA_CREDITO" in csv_resp.text
    assert "TARJETA_DEBITO" in csv_resp.text
    assert "Cerveza Duff Especial" in csv_resp.text
