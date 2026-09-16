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