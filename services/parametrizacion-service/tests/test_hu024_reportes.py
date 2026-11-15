"""HU-024 · Reporte de ventas y ganancia por rol y sede. Sprint 4 · Juan David Tovío."""
from datetime import UTC, date, datetime
from decimal import Decimal
from io import BytesIO

import pytest
from openpyxl import load_workbook
from sqlalchemy import update

from app import reportes
from app.main import SessionLocal
from app.models import Factura
from tests.conftest import _encabezado

XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _mover_factura(numero: int, momento: datetime) -> None:
    """Las pruebas fijan la fecha de emisión para no depender del reloj."""
    with SessionLocal() as db:
        db.execute(update(Factura).where(Factura.numero == numero).values(emitida_en=momento))
        db.commit()


@pytest.fixture()
def ventas(cliente, admin, catalogo) -> dict:
    """Dos sedes con ventas en dos días distintos (hora de Bogotá)."""
    centro = catalogo["sede"]["id"]
    norte = cliente.post("/sedes", headers=admin, json={"nombre": "Bar de Moe · Norte"}).json()["id"]
    mesas = {s: cliente.post("/mesas", headers=admin, json={"sede_id": s, "numero": 1}).json()["id"]
             for s in (centro, norte)}

    def producto(codigo, nombre, compra, venta) -> int:
        return cliente.post("/productos", headers=admin, json={
            "codigo": codigo, "nombre": nombre, "tipo_producto_id": catalogo["tipo"]["id"],
            "proveedor_id": catalogo["proveedor"]["id"], "valor_compra": compra, "valor_venta": venta,
        }).json()["id"]

    cerveza = producto("CER-001", "Cerveza nacional", "2800", "5000")
    picada = producto("PIC-001", "Picada mixta", "12000", "28000")
    for s in (centro, norte):
        for p in (cerveza, picada):
            cliente.post("/inventario/ingresos", headers=admin, json={
                "sede_id": s, "producto_id": p, "cantidad": 200, "motivo": "Compra inicial"})

    meseros = {centro: _encabezado(2, "mszyslak", "MESERO", centro),
               norte: _encabezado(5, "omann", "MESERO", norte)}
    cajeros = {centro: _encabezado(3, "ccarlson", "CAJERO", centro),
               norte: _encabezado(4, "pbouvier", "CAJERO", norte)}

    def vender(sede, lineas, momento):
        pedido = cliente.post("/pedidos", headers=meseros[sede], json={"mesa_id": mesas[sede], "lineas": [
            {"producto_id": p, "cantidad": c} for p, c in lineas]}).json()
        factura = cliente.post("/facturas", headers=cajeros[sede], json={
            "pedido_id": pedido["id"], "medio_pago": "EFECTIVO"}).json()
        _mover_factura(factura["numero"], momento)

    # 12/03 en Bogotá. Las 23:30 de Bogotá son las 04:30 UTC del día siguiente.
    vender(centro, [(cerveza, 100), (picada, 2)], datetime(2026, 3, 12, 15, 0, tzinfo=UTC))
    vender(centro, [(cerveza, 28), (picada, 20)], datetime(2026, 3, 13, 4, 30, tzinfo=UTC))
    vender(norte, [(cerveza, 10)], datetime(2026, 3, 12, 20, 0, tzinfo=UTC))
    # 13/03 en Bogotá
    vender(norte, [(picada, 5)], datetime(2026, 3, 13, 18, 0, tzinfo=UTC))
    return {"centro": centro, "norte": norte, "cajero_centro": cajeros[centro],
            "cajero_norte": cajeros[norte], "mesero": meseros[centro]}


def _filas(r) -> list[dict]:
    assert r.status_code == 200, r.text
    return r.json()["filas"]


def test_c5_c6_columnas_y_ganancia_del_mockup(cliente, admin, ventas):
    filas = _filas(cliente.get(f"/reportes/ventas?desde=2026-03-12&hasta=2026-03-12&sedes={ventas['centro']}",
                               headers=admin))
    assert set(filas[0]) == {"fecha", "codigo", "nombre", "cantidad", "valor_compra", "valor_venta",
                             "ganancia", "sede_id", "sede"}                                    # c5
    por_codigo = {f["codigo"]: f for f in filas}
    cerveza, picada = por_codigo["CER-001"], por_codigo["PIC-001"]
    # Mockup: 128 cervezas a $2.800 / $5.000 → $281.600; 22 picadas a $12.000 / $28.000 → $352.000
    assert cerveza["cantidad"] == 128 and float(cerveza["ganancia"]) == 281600                # c6
    assert picada["cantidad"] == 22 and float(picada["ganancia"]) == 352000
    assert cerveza["fecha"] == "2026-03-12"
    assert cerveza["sede"] == "Bar de Moe · Centro"


def test_c1_el_filtro_de_fechas_usa_la_hora_de_bogota(cliente, admin, ventas):
    dia_13 = _filas(cliente.get("/reportes/ventas?desde=2026-03-13&hasta=2026-03-13", headers=admin))
    assert [(f["sede"], f["codigo"], f["cantidad"]) for f in dia_13] == [("Bar de Moe · Norte", "PIC-001", 5)]
    fuera = _filas(cliente.get("/reportes/ventas?desde=2026-04-01&hasta=2026-04-30", headers=admin))
    assert fuera == []


def test_c2_el_administrador_ve_todas_consolidadas(cliente, admin, ventas):
    r = cliente.get("/reportes/ventas?desde=2026-03-12&hasta=2026-03-13", headers=admin).json()
    assert r["sedes"] is None and r["sede_fija"] is False
    assert {f["sede_id"] for f in r["filas"]} == {ventas["centro"], ventas["norte"]}
    assert r["total_cantidad"] == 128 + 22 + 10 + 5
    esperada = 128 * 2200 + 22 * 16000 + 10 * 2200 + 5 * 16000
    assert float(r["total_ganancia"]) == esperada
    totales = {t["sede_id"]: t for t in r["totales_por_sede"]}
    assert float(totales[ventas["norte"]]["ganancia"]) == 10 * 2200 + 5 * 16000


def test_c2_el_administrador_filtra_una_o_varias_sedes(cliente, admin, ventas):
    rango = "desde=2026-03-12&hasta=2026-03-13"
    solo_norte = _filas(cliente.get(f"/reportes/ventas?{rango}&sedes={ventas['norte']}", headers=admin))
    assert {f["sede_id"] for f in solo_norte} == {ventas["norte"]}
    ambas = cliente.get(f"/reportes/ventas?desde=2026-03-12&hasta=2026-03-13&sedes={ventas['norte']},"
                        f"{ventas['centro']}", headers=admin).json()
    assert ambas["sedes"] == sorted([ventas["norte"], ventas["centro"]])
    assert len(ambas["filas"]) == 4


def test_c2_sede_inexistente_o_lista_mal_escrita(cliente, admin, ventas):
    assert cliente.get("/reportes/ventas?sedes=999", headers=admin).status_code == 404
    r = cliente.get("/reportes/ventas?sedes=1,abc", headers=admin)
    assert r.status_code == 422 and r.json()["error"]["codigo"] == "SEDES_INVALIDAS"


def test_c3_el_cajero_solo_ve_su_sede(cliente, ventas):
    rango = "desde=2026-03-12&hasta=2026-03-13"
    r = cliente.get(f"/reportes/ventas?{rango}", headers=ventas["cajero_norte"]).json()
    assert r["sedes"] == [ventas["norte"]] and r["sede_fija"] is True
    assert {f["sede_id"] for f in r["filas"]} == {ventas["norte"]}


def test_c3_el_cajero_no_puede_cambiar_el_filtro_de_sede(cliente, ventas):
    otra = cliente.get(f"/reportes/ventas?sedes={ventas['centro']}", headers=ventas["cajero_norte"])
    mezcla = cliente.get(f"/reportes/ventas?sedes={ventas['norte']},{ventas['centro']}",
                         headers=ventas["cajero_norte"])
    excel = cliente.get(f"/reportes/ventas/excel?sedes={ventas['centro']}", headers=ventas["cajero_norte"])
    for r in (otra, mezcla, excel):
        assert r.status_code == 403
        assert r.json()["error"]["codigo"] == "SEDE_NO_AUTORIZADA"
    propia = cliente.get(f"/reportes/ventas?sedes={ventas['norte']}", headers=ventas["cajero_norte"])
    assert propia.status_code == 200


def test_c4_el_mesero_no_tiene_acceso_aunque_llame_la_direccion(cliente, ventas):
    for ruta in ("/reportes/ventas", "/reportes/ventas/excel",
                 "/reportes/ventas?desde=2026-03-12&hasta=2026-03-13"):
        r = cliente.get(ruta, headers=ventas["mesero"])
        assert r.status_code == 403
        assert r.json()["error"]["codigo"] == "SIN_PERMISOS"


def test_c7_el_excel_tiene_exactamente_las_filas_de_la_pantalla(cliente, ventas):
    params = "desde=2026-03-12&hasta=2026-03-13"
    pantalla = _filas(cliente.get(f"/reportes/ventas?{params}", headers=ventas["cajero_centro"]))
    r = cliente.get(f"/reportes/ventas/excel?{params}", headers=ventas["cajero_centro"])
    assert r.status_code == 200
    assert r.headers["content-type"].startswith(XLSX)
    assert 'filename="reporte-ventas_2026-03-12_2026-03-13.xlsx"' in r.headers["content-disposition"]
    assert r.headers["x-total-count"] == str(len(pantalla))

    hoja = load_workbook(BytesIO(r.content)).active
    filas = list(hoja.iter_rows(values_only=True))
    encabezado = filas.index(reportes.COLUMNAS)
    datos = [f for f in filas[encabezado + 1:] if f[0] != "TOTAL"]
    assert len(datos) == len(pantalla)
    for excel, json_ in zip(datos, pantalla, strict=True):
        assert excel[0].date().isoformat() == json_["fecha"]
        assert (excel[1], excel[2], excel[3]) == (json_["codigo"], json_["nombre"], json_["cantidad"])
        assert excel[6] == float(json_["ganancia"])
        assert excel[7] == json_["sede"]
    assert all(f[7] == "Bar de Moe · Centro" for f in datos)  # nada de la otra sede


def test_c7_exportar_queda_en_la_auditoria(cliente, admin, ventas):
    cliente.get("/reportes/ventas/excel?desde=2026-03-12&hasta=2026-03-13", headers=ventas["cajero_centro"])
    registro = cliente.get("/auditoria?accion=EXPORTAR_REPORTE", headers=admin).json()
    assert len(registro) == 1
    assert registro[0]["usuario"] == "ccarlson" and "Centro" in registro[0]["detalle"]


def test_orden_por_ganancia_con_merge_sort(cliente, admin, ventas):
    filas = _filas(cliente.get("/reportes/ventas?desde=2026-03-12&hasta=2026-03-13&orden=ganancia",
                               headers=admin))
    ganancias = [float(f["ganancia"]) for f in filas]
    assert ganancias == sorted(ganancias, reverse=True)
    assert cliente.get("/reportes/ventas?orden=precio", headers=admin).status_code == 422


def test_rango_de_fechas_invalido(cliente, admin, ventas):
    al_reves = cliente.get("/reportes/ventas?desde=2026-03-13&hasta=2026-03-12", headers=admin)
    largo = cliente.get("/reportes/ventas?desde=2024-01-01&hasta=2026-03-12", headers=admin)
    for r in (al_reves, largo):
        assert r.status_code == 422 and r.json()["error"]["codigo"] == "RANGO_INVALIDO"


def test_sin_fechas_el_reporte_es_de_hoy(cliente, admin, ventas):
    r = cliente.get("/reportes/ventas", headers=admin).json()
    assert r["desde"] == r["hasta"] == reportes.hoy_local().isoformat()


def test_el_reporte_no_cambia_si_despues_se_edita_el_precio(cliente, admin, catalogo, ventas):
    antes = cliente.get("/reportes/ventas?desde=2026-03-12&hasta=2026-03-13", headers=admin).json()
    producto = next(p for p in cliente.get("/productos", headers=admin).json() if p["codigo"] == "CER-001")
    cliente.patch(f"/productos/{producto['id']}", headers=admin, json={"valor_compra": "4000"})
    despues = cliente.get("/reportes/ventas?desde=2026-03-12&hasta=2026-03-13", headers=admin).json()
    assert antes["total_ganancia"] == despues["total_ganancia"]


# ----------------------------------------------------- lógica pura (reportes.py)
def _linea(momento, cantidad, compra="1000", venta="3000", producto=1, sede=1):
    return reportes.LineaVendida(emitida_en=momento, sede_id=sede, sede=f"Sede {sede}", producto_id=producto,
                                 codigo=f"P-{producto}", nombre=f"Producto {producto}", cantidad=cantidad,
                                 valor_compra=Decimal(compra), valor_venta=Decimal(venta))


def test_agrupar_suma_por_dia_y_separa_si_cambia_el_precio():
    dia = datetime(2026, 3, 12, 15, tzinfo=UTC)
    filas = reportes.agrupar([_linea(dia, 2), _linea(dia, 3), _linea(dia, 1, venta="3500")])
    assert sorted((f.cantidad, f.ganancia) for f in filas) == [(1, Decimal(2500)), (5, Decimal(10000))]


def test_fecha_local_con_y_sin_zona():
    assert reportes.fecha_local(datetime(2026, 3, 13, 4, 30, tzinfo=UTC)) == date(2026, 3, 12)
    assert reportes.fecha_local(datetime(2026, 3, 13, 4, 30)) == date(2026, 3, 12)  # SQLite: sin zona


def test_rango_utc_cubre_el_dia_completo_en_bogota():
    inicio, fin = reportes.rango_utc(date(2026, 3, 12), date(2026, 3, 12))
    assert inicio == datetime(2026, 3, 12, 5, tzinfo=UTC)
    assert fin == datetime(2026, 3, 13, 5, tzinfo=UTC)


def test_excel_vacio_igual_se_genera():
    contenido = reportes.a_excel([], desde=date(2026, 3, 1), hasta=date(2026, 3, 2), alcance="todas",
                                 usuario="admin")
    filas = list(load_workbook(BytesIO(contenido)).active.iter_rows(values_only=True))
    encabezado = filas.index(reportes.COLUMNAS)
    assert filas[encabezado + 1][0] == "TOTAL"


# ------------------------------------------------ Filtros de la propuesta (M6): producto y tipo
# Agregados en la integración de los Sprints 3 y 4 (QA): la propuesta comercial pide filtrar
# por rango de fechas, sede, producto y tipo de producto.
RANGO = "desde=2026-03-12&hasta=2026-03-13"


def _producto_id(cliente, admin, codigo: str) -> int:
    return next(p["id"] for p in cliente.get("/productos", headers=admin).json() if p["codigo"] == codigo)


def test_m6_filtro_por_producto(cliente, admin, ventas):
    cerveza = _producto_id(cliente, admin, "CER-001")
    r = cliente.get(f"/reportes/ventas?{RANGO}&producto_id={cerveza}", headers=admin).json()
    assert {f["codigo"] for f in r["filas"]} == {"CER-001"}
    assert r["total_cantidad"] == 128 + 10 and r["producto_id"] == cerveza


def test_m6_filtro_por_tipo_de_producto(cliente, admin, catalogo, ventas):
    comida = cliente.post("/tipos-producto", headers=admin, json={"nombre": "Comida QA"}).json()["id"]
    picada = _producto_id(cliente, admin, "PIC-001")
    cliente.patch(f"/productos/{picada}", headers=admin, json={"tipo_producto_id": comida})
    filas = _filas(cliente.get(f"/reportes/ventas?{RANGO}&tipo_producto_id={comida}", headers=admin))
    assert {f["codigo"] for f in filas} == {"PIC-001"}
    assert sum(f["cantidad"] for f in filas) == 22 + 5
    otro = _filas(cliente.get(f"/reportes/ventas?{RANGO}&tipo_producto_id={catalogo['tipo']['id']}",
                              headers=admin))
    assert {f["codigo"] for f in otro} == {"CER-001"}


def test_m6_el_cajero_filtra_por_producto_sin_salir_de_su_sede(cliente, admin, ventas):
    picada = _producto_id(cliente, admin, "PIC-001")
    r = cliente.get(f"/reportes/ventas?{RANGO}&producto_id={picada}", headers=ventas["cajero_norte"]).json()
    assert r["sede_fija"] is True
    filas = [(f["sede_id"], f["codigo"], f["cantidad"]) for f in r["filas"]]
    assert filas == [(ventas["norte"], "PIC-001", 5)]


def test_m6_el_excel_respeta_los_mismos_filtros(cliente, admin, ventas):
    cerveza = _producto_id(cliente, admin, "CER-001")
    r = cliente.get(f"/reportes/ventas/excel?{RANGO}&producto_id={cerveza}", headers=admin)
    assert r.status_code == 200
    hoja = load_workbook(BytesIO(r.content)).active
    codigos = {c.value for c in hoja["B"] if c.value not in (None, "CÓD. PRODUCTO", "Código", "CÓD.")}
    assert "PIC-001" not in codigos and "CER-001" in codigos


@pytest.mark.parametrize("malicioso", ["1 OR 1=1", "1;DROP TABLE facturas", "' OR ''='", "-1"])
def test_c3_owasp_inyeccion_en_los_filtros_del_reporte(cliente, admin, ventas, malicioso):
    """C-3: cadenas de inyección en los filtros del reporte se rechazan por tipo (422)."""
    for campo in ("producto_id", "tipo_producto_id"):
        r = cliente.get(f"/reportes/ventas?{RANGO}&{campo}={malicioso}", headers=admin)
        assert r.status_code == 422, (campo, malicioso, r.text)
    r = cliente.get(f"/reportes/ventas?{RANGO}&sedes={malicioso}", headers=admin)
    assert r.status_code in (403, 404, 422), r.text   # rechazada, nunca ejecutada
    # Las facturas siguen ahí: nada alteró la consulta.
    assert len(_filas(cliente.get(f"/reportes/ventas?{RANGO}", headers=admin))) > 0
