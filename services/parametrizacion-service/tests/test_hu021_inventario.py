"""HU-021 · Control de inventario por sede (CU-15, CU-16, CU-17, CU-32)."""
import pytest
from sqlalchemy import select

from app.main import SessionLocal
from app.models import MovimientoInventario
from tests.conftest import _encabezado


@pytest.fixture()
def dos_sedes(cliente, admin, catalogo) -> dict:
    otra = cliente.post("/sedes", headers=admin, json={"nombre": "Bar de Moe · Norte"}).json()
    producto = cliente.post("/productos", headers=admin, json={
        "codigo": "CERV-001", "nombre": "Cerveza nacional", "tipo_producto_id": catalogo["tipo"]["id"],
        "proveedor_id": catalogo["proveedor"]["id"], "valor_compra": "2500", "valor_venta": "5000",
        "stock_minimo": 5,
    }).json()
    return {"centro": catalogo["sede"]["id"], "norte": otra["id"], "producto": producto["id"]}


def _ingreso(cliente, admin, sede, producto, cantidad, motivo="Compra al proveedor"):
    return cliente.post("/inventario/ingresos", headers=admin, json={
        "sede_id": sede, "producto_id": producto, "cantidad": cantidad, "motivo": motivo})


def _existencia(cliente, admin, sede, producto) -> int:
    filas = cliente.get(f"/inventario?sede_id={sede}", headers=admin).json()
    return next(f["existencia"] for f in filas if f["producto_id"] == producto)


def test_c1_cada_sede_tiene_su_propia_existencia(cliente, admin, dos_sedes):
    r = _ingreso(cliente, admin, dos_sedes["centro"], dos_sedes["producto"], 60)
    assert r.status_code == 201, r.text
    assert r.json()["existencia"] == 60
    assert _existencia(cliente, admin, dos_sedes["centro"], dos_sedes["producto"]) == 60
    assert _existencia(cliente, admin, dos_sedes["norte"], dos_sedes["producto"]) == 0


def test_c2_el_ingreso_exige_cantidad_positiva_y_motivo(cliente, admin, dos_sedes):
    sin_motivo = cliente.post("/inventario/ingresos", headers=admin, json={
        "sede_id": dos_sedes["centro"], "producto_id": dos_sedes["producto"], "cantidad": 5, "motivo": " "})
    assert sin_motivo.status_code == 422
    assert "reason is required" in sin_motivo.json()["error"]["mensaje"]

    cero = _ingreso(cliente, admin, dos_sedes["centro"], dos_sedes["producto"], 0)
    assert cero.status_code == 422
    assert "cantidad" in cero.json()["error"]["mensaje"]


def test_c2_el_ajuste_exige_motivo(cliente, admin, dos_sedes):
    r = cliente.post("/inventario/ajustes", headers=admin, json={
        "sede_id": dos_sedes["centro"], "producto_id": dos_sedes["producto"], "cantidad": -1})
    assert r.status_code == 422
    assert "motivo" in r.json()["error"]["mensaje"]


def test_c3_un_ajuste_no_deja_la_existencia_en_negativo(cliente, admin, dos_sedes):
    _ingreso(cliente, admin, dos_sedes["centro"], dos_sedes["producto"], 5)
    r = cliente.post("/inventario/ajustes", headers=admin, json={
        "sede_id": dos_sedes["centro"], "producto_id": dos_sedes["producto"], "cantidad": -8,
        "motivo": "Conteo físico"})
    assert r.status_code == 409
    error = r.json()["error"]
    assert error["codigo"] == "EXISTENCIA_NEGATIVA"
    assert "5" in error["mensaje"] and "-3" in error["mensaje"]  # el mensaje dice el motivo
    assert _existencia(cliente, admin, dos_sedes["centro"], dos_sedes["producto"]) == 5


def test_c6_cada_movimiento_queda_con_usuario_sede_fecha_y_motivo(cliente, admin, dos_sedes):
    _ingreso(cliente, admin, dos_sedes["centro"], dos_sedes["producto"], 60)
    cliente.post("/inventario/ajustes", headers=admin, json={
        "sede_id": dos_sedes["centro"], "producto_id": dos_sedes["producto"], "cantidad": -8,
        "motivo": "Botellas rotas"})
    movimientos = cliente.get("/inventario/movimientos", headers=admin, params={
        "sede_id": dos_sedes["centro"], "producto_id": dos_sedes["producto"]}).json()
    assert [(m["tipo"], m["cantidad"], m["existencia_resultante"]) for m in movimientos] == [
        ("AJUSTE", -8, 52), ("INGRESO", 60, 60)]
    assert all(m["usuario"] == "admin" and m["creado_en"] and m["motivo"] for m in movimientos)
    with SessionLocal() as db:
        assert {m.sede_id for m in db.scalars(select(MovimientoInventario))} == {dos_sedes["centro"]}


def test_cu17_el_mesero_solo_ve_el_inventario_de_su_sede(cliente, admin, dos_sedes):
    mesero = _encabezado(7, "lenny", "MESERO", dos_sedes["centro"])
    assert cliente.get("/inventario", headers=mesero).status_code == 200
    otra = cliente.get(f"/inventario?sede_id={dos_sedes['norte']}", headers=mesero)
    assert otra.status_code == 403
    assert cliente.post("/inventario/ingresos", headers=mesero, json={
        "sede_id": dos_sedes["centro"], "producto_id": dos_sedes["producto"], "cantidad": 1,
        "motivo": "No debería"}).status_code == 403


def test_cu17_los_agotados_se_marcan(cliente, admin, dos_sedes):
    fila = cliente.get(f"/inventario?sede_id={dos_sedes['norte']}", headers=admin).json()[0]
    assert fila["agotado"] is True and fila["bajo_minimo"] is True


def test_conciliacion_iterativa_y_recursiva_cuadran(cliente, admin, dos_sedes):
    _ingreso(cliente, admin, dos_sedes["centro"], dos_sedes["producto"], 60)
    cliente.post("/inventario/ajustes", headers=admin, json={
        "sede_id": dos_sedes["centro"], "producto_id": dos_sedes["producto"], "cantidad": -8,
        "motivo": "Conteo"})
    r = cliente.get("/inventario/conciliacion", headers=admin, params={
        "sede_id": dos_sedes["centro"], "producto_id": dos_sedes["producto"]}).json()
    assert r["cuadra"] is True
    assert r["existencia_registrada"] == r["existencia_iterativa"] == r["existencia_recursiva"] == 52


def test_sugerencia_de_compra_respeta_el_presupuesto(cliente, admin, catalogo):
    sede = catalogo["sede"]["id"]
    for codigo, compra, venta in (("P-A", "1000", "3000"), ("P-B", "2000", "3000"), ("P-C", "1500", "4500")):
        cliente.post("/productos", headers=admin, json={
            "codigo": codigo, "nombre": f"Producto {codigo}", "tipo_producto_id": catalogo["tipo"]["id"],
            "proveedor_id": catalogo["proveedor"]["id"], "valor_compra": compra, "valor_venta": venta,
            "stock_minimo": 5})
    # Cada lote repone 10 unidades: A cuesta 10.000, B 20.000 y C 15.000.
    r = cliente.get("/inventario/sugerencia-compra", headers=admin,
                    params={"sede_id": sede, "presupuesto": 25_000})
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    assert cuerpo["metodo"] == "PROGRAMACION_DINAMICA"
    assert cuerpo["escala_mcd"] == 5_000
    assert sorted(lote["codigo"] for lote in cuerpo["lotes"]) == ["P-A", "P-C"]
    assert cuerpo["costo_total"] == 25_000 and cuerpo["ganancia_esperada"] == 50_000
    assert [d["codigo"] for d in cuerpo["descartados"]] == ["P-B"]


def test_inactivar_en_sede_bloquea_el_ingreso(cliente, admin, dos_sedes):
    cliente.post(f"/inventario/sedes/{dos_sedes['norte']}/productos/{dos_sedes['producto']}/inactivar",
                 headers=admin)
    r = _ingreso(cliente, admin, dos_sedes["norte"], dos_sedes["producto"], 3)
    assert r.status_code == 409
    assert r.json()["error"]["codigo"] == "PRODUCTO_INACTIVO_EN_SEDE"
    de_nuevo = cliente.post(
        f"/inventario/sedes/{dos_sedes['norte']}/productos/{dos_sedes['producto']}/inactivar", headers=admin)
    assert de_nuevo.status_code == 409
    assert "is already inactive" in de_nuevo.json()["error"]["mensaje"]
