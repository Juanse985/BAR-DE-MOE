"""HU-026 · RNF-02 — Tiempo de respuesta máximo de dos segundos.

Mide en proceso las operaciones más usadas del M2 y exige que el percentil 95
quede por debajo del SLA. La medición contra el despliegue real la hace
`scripts/medir_rnf02.py`.
"""
import statistics

import pytest

SLA_MS = 2000.0


def _ms(respuesta) -> float:
    return float(respuesta.headers["X-Tiempo-Ms"])


def _p95(valores: list[float]) -> float:
    return statistics.quantiles(valores, n=20, method="inclusive")[-1]


@pytest.fixture()
def carga(cliente, admin, catalogo):
    sede = catalogo["sede"]["id"]
    for numero in range(1, 21):
        cliente.post("/mesas", headers=admin, json={"sede_id": sede, "numero": numero})
    for i in range(30):
        cliente.post("/productos", headers=admin, json={
            "codigo": f"P-{i:03d}", "nombre": f"Producto {i}", "sede_id": sede,
            "tipo_producto_id": catalogo["tipo"]["id"], "proveedor_id": catalogo["proveedor"]["id"],
            "valor_compra": "1000", "valor_venta": "2000",
        })
    return sede


@pytest.mark.parametrize("ruta", ["/sedes", "/mesas?sede_id={sede}", "/productos?sede_id={sede}",
                                  "/tipos-producto", "/proveedores"])
def test_rnf02_el_p95_de_las_consultas_esta_bajo_dos_segundos(cliente, mesero, carga, ruta):
    tiempos = []
    for _ in range(25):
        respuesta = cliente.get(ruta.format(sede=carga), headers=mesero)
        assert respuesta.status_code == 200
        tiempos.append(_ms(respuesta))
    assert _p95(tiempos) < SLA_MS
    assert max(tiempos) < SLA_MS


def test_rnf02_las_escrituras_responden_bajo_dos_segundos(cliente, admin, catalogo):
    respuestas = [
        cliente.post("/sedes", headers=admin, json={"nombre": "Bar de Moe · Norte"}),
        cliente.post("/mesas", headers=admin, json={"sede_id": catalogo["sede"]["id"], "numero": 99}),
        cliente.patch(f"/sedes/{catalogo['sede']['id']}", headers=admin, json={"telefono": "123"}),
    ]
    for respuesta in respuestas:
        assert respuesta.status_code in (200, 201)
        assert _ms(respuesta) < SLA_MS
        assert "X-SLA-Excedido" not in respuesta.headers


def test_rnf02_los_errores_tambien_traen_la_medicion(cliente, mesero):
    assert _ms(cliente.post("/sedes", headers=mesero, json={"nombre": "Sin permiso"})) < SLA_MS
    assert _ms(cliente.get("/sedes/999", headers=mesero)) < SLA_MS
