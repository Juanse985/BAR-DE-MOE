"""Endpoints /algoritmos: los algoritmos de la asignatura sobre los datos reales del bar."""
import pytest

from tests.conftest import _encabezado


@pytest.fixture()
def bar(cliente, admin, catalogo) -> dict:
    sede = catalogo["sede"]["id"]
    otra = cliente.post("/sedes", headers=admin, json={"nombre": "Bar de Moe · Norte"}).json()["id"]
    productos = {}
    for codigo, nombre, compra, venta, existencia in [
        ("CER-003", "Poker", "2000", "5000", 12),
        ("CER-001", "Águila", "2200", "5500", 48),
        ("LIC-014", "Aguardiente media", "18000", "30000", 2),
        ("PIC-001", "Picada mixta", "12000", "28000", 5),
        ("GAS-400", "Gaseosa", "1400", "3500", 0),
    ]:
        p = cliente.post("/productos", headers=admin, json={
            "codigo": codigo, "nombre": nombre, "tipo_producto_id": catalogo["tipo"]["id"],
            "proveedor_id": catalogo["proveedor"]["id"], "valor_compra": compra, "valor_venta": venta}).json()
        productos[codigo] = p["id"]
        if existencia:
            cliente.post("/inventario/ingresos", headers=admin, json={
                "sede_id": sede, "producto_id": p["id"], "cantidad": existencia, "motivo": "Compra"})
    return {"sede": sede, "otra": otra, "productos": productos,
            "mesero": _encabezado(2, "mszyslak", "MESERO", sede)}


def test_catalogo_de_algoritmos(cliente, admin):
    catalogo = cliente.get("/algoritmos", headers=admin).json()
    tecnicas = " ".join(a["tecnica"] for a in catalogo)
    for tecnica in ("voraz", "recursivo", "iterativo", "programación dinámica", "backtracking",
                    "ordenamiento", "divide y vencerás"):
        assert tecnica in tecnicas


@pytest.mark.parametrize("metodo", ["burbuja", "insercion", "seleccion", "quicksort", "mezcla"])
def test_ordenar_inventario_con_cada_metodo(cliente, admin, bar, metodo):
    r = cliente.get(f"/algoritmos/ordenar-inventario?sede_id={bar['sede']}&metodo={metodo}"
                    "&campo=existencia&descendente=true", headers=admin)
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    assert [f["existencia"] for f in cuerpo["filas"]] == [48, 12, 5, 2, 0]
    assert cuerpo["metodo"] == metodo and cuerpo["n"] == 5 and cuerpo["comparaciones"] > 0
    assert len(cuerpo["comparativa"]) == 5
    assert all(c["mismo_orden"] for c in cuerpo["comparativa"])


def test_ordenar_por_nombre_y_por_ganancia(cliente, admin, bar):
    por_nombre = cliente.get(f"/algoritmos/ordenar-inventario?sede_id={bar['sede']}&campo=nombre",
                             headers=admin).json()
    assert por_nombre["filas"][0]["nombre"] == "Aguardiente media"
    ruta = (f"/algoritmos/ordenar-inventario?sede_id={bar['sede']}"
            "&campo=ganancia_unitaria&descendente=true&comparar=false")
    por_ganancia = cliente.get(ruta, headers=admin).json()
    assert por_ganancia["filas"][0]["codigo"] == "PIC-001"            # 28.000 - 12.000
    assert por_ganancia["comparativa"] == []


def test_ordenar_metodo_invalido_y_sede_ajena(cliente, admin, bar):
    assert cliente.get("/algoritmos/ordenar-inventario?metodo=shell", headers=admin).status_code == 422
    r = cliente.get(f"/algoritmos/ordenar-inventario?sede_id={bar['otra']}", headers=bar["mesero"])
    assert r.status_code == 403


@pytest.mark.parametrize("modo", ["iterativa", "recursiva"])
def test_busqueda_binaria_de_producto(cliente, admin, bar, modo):
    r = cliente.get(f"/algoritmos/buscar-producto?codigo=pic-001&modo={modo}", headers=admin).json()
    assert r["encontrado"] and r["producto"]["nombre"] == "Picada mixta"
    assert len(r["pasos"]) <= r["maximo_teorico"]
    assert r["pasos"][-1]["decision"] == "ENCONTRADO"
    faltante = cliente.get(f"/algoritmos/buscar-producto?codigo=XXX-999&modo={modo}", headers=admin).json()
    assert faltante["encontrado"] is False and faltante["producto"] is None


@pytest.mark.parametrize("modo", ["recursivo", "iterativo"])
def test_hanoi(cliente, admin, modo):
    r = cliente.get(f"/algoritmos/hanoi?discos=4&modo={modo}", headers=admin).json()
    assert r["total_movimientos"] == 15 and r["verificado"] and r["coincide_con_el_otro_modo"]
    assert r["estado_final"]["C"] == [4, 3, 2, 1]
    assert r["movimientos"][0] == {"numero": 1, "canasta": 1, "desde": "A", "hacia": "B"}


def test_hanoi_limites(cliente, admin):
    assert cliente.get("/algoritmos/hanoi?discos=0", headers=admin).status_code == 422
    assert cliente.get("/algoritmos/hanoi?discos=13", headers=admin).status_code == 422


def test_combo_backtracking_contra_voraz(cliente, admin, bar):
    # $33.000: el voraz toma el aguardiente (30.000) y se queda corto; backtracking: 1 picada + 1 Poker
    r = cliente.get(f"/algoritmos/combo?sede_id={bar['sede']}&monto=33000", headers=admin).json()
    assert r["backtracking"]["encontrado"] and r["backtracking"]["total"] == 33000
    assert {c["nombre"] for c in r["backtracking"]["combo"]} == {"Picada mixta", "Poker"}
    assert r["voraz"]["encontrado"] is False and r["voraz"]["faltante"] > 0
    assert "greedy is not always optimal" in r["conclusion"]


def test_combo_ignora_productos_sin_existencia_y_respeta_la_sede(cliente, admin, bar):
    r = cliente.get(f"/algoritmos/combo?sede_id={bar['sede']}&monto=3500", headers=admin).json()
    assert r["backtracking"]["encontrado"] is False          # la gaseosa no tiene existencia
    assert r["productos_considerados"] == 4
    assert cliente.get("/algoritmos/combo?monto=10000", headers=admin).status_code == 422
    assert cliente.get(f"/algoritmos/combo?sede_id={bar['otra']}&monto=10000",
                       headers=bar["mesero"]).status_code == 403


def test_mcd_y_cambio(cliente, admin):
    mcd = cliente.get("/algoritmos/mcd?a=252&b=105", headers=admin).json()
    assert mcd["iterativo"] == mcd["recursivo"] == 21 and len(mcd["pasos"]) == 3
    cambio = cliente.get("/algoritmos/cambio?monto=23000", headers=admin).json()
    assert {p["denominacion"]: p["cantidad"] for p in cambio["piezas"]} == {20000: 1, 2000: 1, 1000: 1}
    assert cliente.get("/algoritmos/cambio?monto=30", headers=admin).status_code == 422


def test_sin_token_no_hay_acceso(cliente):
    assert cliente.get("/algoritmos/hanoi").status_code == 401


def test_el_catalogo_trae_los_12_algoritmos_numerados(cliente, admin):
    catalogo = cliente.get("/algoritmos", headers=admin).json()
    assert [a["numero"] for a in catalogo] == list(range(1, 13))
    rutas = " ".join(a["ruta"] for a in catalogo)
    assert "/mesas/ruta-entrega" in rutas and "/pedidos/cola-barra" in rutas
