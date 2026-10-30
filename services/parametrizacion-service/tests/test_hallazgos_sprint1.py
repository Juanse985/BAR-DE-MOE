"""Hallazgos de docs/05-contratos.md §9 que pasaron al Sprint 2 (H-01, H-02, H-03, H-04, H-10)."""


def _producto(cliente, admin, catalogo, codigo="CERV-001"):
    return cliente.post("/productos", headers=admin, json={
        "codigo": codigo, "nombre": "Cerveza Duff", "tipo_producto_id": catalogo["tipo"]["id"],
        "proveedor_id": catalogo["proveedor"]["id"], "valor_compra": "2500", "valor_venta": "6000"}).json()


def test_h01_un_campo_que_no_se_edita_responde_422_con_el_campo(cliente, admin, catalogo):
    mesa = cliente.post("/mesas", headers=admin, json={"sede_id": catalogo["sede"]["id"], "numero": 1}).json()
    r = cliente.patch(f"/mesas/{mesa['id']}", headers=admin, json={"numero": 9})
    assert r.status_code == 422
    assert "numero" in r.json()["error"]["mensaje"]


def test_h02_editar_producto_con_tipo_inexistente_da_404_y_no_500(cliente, admin, catalogo):
    producto = _producto(cliente, admin, catalogo)
    r = cliente.patch(f"/productos/{producto['id']}", headers=admin, json={"tipo_producto_id": 999})
    assert r.status_code == 404
    assert r.json()["error"]["mensaje"] == "There is no product type with id 999."


def test_h03_no_se_renombra_una_sede_a_un_nombre_existente(cliente, admin, catalogo):
    otra = cliente.post("/sedes", headers=admin, json={"nombre": "Bar de Moe · Sur"}).json()
    r = cliente.patch(f"/sedes/{otra['id']}", headers=admin, json={"nombre": catalogo["sede"]["nombre"]})
    assert r.status_code == 409
    assert r.json()["error"]["codigo"] == "SEDE_DUPLICADA"


def test_h03_no_se_renombra_un_tipo_a_un_nombre_existente(cliente, admin, catalogo):
    otro = cliente.post("/tipos-producto", headers=admin, json={"nombre": "Licor"}).json()
    r = cliente.patch(f"/tipos-producto/{otro['id']}", headers=admin, json={"nombre": "Cerveza"})
    assert r.status_code == 409
    assert r.json()["error"]["codigo"] == "TIPO_DUPLICADO"


def test_h04_no_se_asigna_un_proveedor_inactivo(cliente, admin, catalogo):
    inactivo = cliente.post("/proveedores", headers=admin,
                            json={"nit": "800111222-3", "nombre": "Viejo"}).json()
    cliente.patch(f"/proveedores/{inactivo['id']}", headers=admin, json={"activo": False})
    r = cliente.post("/productos", headers=admin, json={
        "codigo": "X-1", "nombre": "Producto X", "tipo_producto_id": catalogo["tipo"]["id"],
        "proveedor_id": inactivo["id"], "valor_compra": "1", "valor_venta": "2"})
    assert r.status_code == 409
    assert r.json()["error"]["mensaje"] == "Supplier 'Viejo' is inactive and cannot be assigned."


def test_h10_no_se_crea_una_mesa_en_una_sede_inactiva(cliente, admin):
    sede = cliente.post("/sedes", headers=admin, json={"nombre": "Sede cerrada"}).json()
    cliente.patch(f"/sedes/{sede['id']}", headers=admin, json={"activa": False})
    r = cliente.post("/mesas", headers=admin, json={"sede_id": sede["id"], "numero": 1})
    assert r.status_code == 409
    assert r.json()["error"]["codigo"] == "SEDE_INACTIVA"


def test_mensaje_de_validacion_dice_campo_y_motivo(cliente, admin):
    r = cliente.post("/mesas", headers=admin, json={"numero": -1})
    error = r.json()["error"]
    assert r.status_code == 422
    assert "sede_id" in error["mensaje"] and "numero" in error["mensaje"]
    assert error["mensaje"] != "The submitted data is not valid."
