#!/usr/bin/env python3
"""Evidencia de los 7 algoritmos de Diseño de Algoritmos, corriendo en la plataforma.

Arma un escenario propio para no tocar los datos de la demo:

    sede "QA Algoritmos <fecha>" (recibe todo el catálogo con existencia 0)
    → 9 mesas (mapa 3×3) → ingreso de 3 cervezas → pedidos en las mesas 9, 1, 8 y 3

y después llama, por el gateway, a cada endpoint que usa un algoritmo. Deja el
resultado en `docs/evidencias/algoritmos.md`.

Uso:
    python scripts/evidencia_algoritmos.py --evidencia docs/evidencias
Variables de entorno: BASE_URL, ADMIN_USUARIO, ADMIN_PASSWORD.
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

import httpx

API = "/api/parametrizacion"
MESAS_CON_PEDIDO = (9, 1, 8, 3)     # en el orden en que llegan las comandas
PRESUPUESTO = 120_000


def pesos(valor) -> str:
    return f"${int(float(valor)):,}".replace(",", ".")


class Escenario:
    def __init__(self, base_url: str, usuario: str, password: str):
        self.http = httpx.Client(base_url=base_url, timeout=15.0)
        resp = self.http.post("/api/auth/auth/login", json={"usuario": usuario, "password": password})
        if resp.status_code != 200:
            raise SystemExit(f"No se pudo entrar como {usuario}: {resp.status_code} {resp.text[:200]}")
        self.h = {"Authorization": f"Bearer {resp.json()['access_token']}"}

    def get(self, ruta: str, **params):
        resp = self.http.get(API + ruta, headers=self.h, params=params)
        resp.raise_for_status()
        return resp.json()

    def post(self, ruta: str, cuerpo: dict):
        resp = self.http.post(API + ruta, headers=self.h, json=cuerpo)
        if resp.status_code >= 400:
            raise SystemExit(f"POST {ruta} → {resp.status_code}: {resp.text[:300]}")
        return resp.json()

    def cerrar(self) -> None:
        self.http.post("/api/auth/auth/logout", headers=self.h)


def armar(e: Escenario) -> dict:
    sello = datetime.now().strftime("%Y%m%d%H%M%S")
    sede = e.post("/sedes", {"nombre": f"QA Algoritmos {sello}", "direccion": "Evidencia Sprint 2"})["id"]
    mesas = {n: e.post("/mesas", {"sede_id": sede, "numero": n, "capacidad": 4})["id"] for n in range(1, 10)}
    productos = [p for p in e.get("/productos", sede_id=sede) if p["activo"]]
    productos.sort(key=lambda p: p["codigo"])
    vendidos = productos[:3]
    for p in vendidos:
        e.post("/inventario/ingresos", {"sede_id": sede, "producto_id": p["id"], "cantidad": 24,
                                        "motivo": "Compra para la evidencia de algoritmos"})
    pedidos = []
    for i, numero in enumerate(MESAS_CON_PEDIDO):
        p = vendidos[i % len(vendidos)]
        pedidos.append(e.post("/pedidos", {"mesa_id": mesas[numero],
                                           "lineas": [{"producto_id": p["id"], "cantidad": 2 + i}]}))
    return {"sede": sede, "nombre": f"QA Algoritmos {sello}", "vendido": vendidos[0], "pedido": pedidos[0]}


def escribir(e: Escenario, datos: dict, carpeta: Path) -> Path:
    sede, vendido, pedido = datos["sede"], datos["vendido"], datos["pedido"]
    mochila = e.get("/inventario/sugerencia-compra", sede_id=sede, presupuesto=PRESUPUESTO)
    conciliacion = e.get("/inventario/conciliacion", sede_id=sede, producto_id=vendido["id"])
    pagado = (int(float(pedido["total"])) // 50_000 + 1) * 50_000
    cambio = e.get(f"/pedidos/{pedido['id']}/cambio", pagado=pagado)
    ruta = e.get("/mesas/ruta-entrega", sede_id=sede)
    cola = e.get("/pedidos/cola-barra", sede_id=sede)

    L = ["# Evidencia · los 7 algoritmos funcionando en la plataforma", "",
         f"- **Fecha:** {datetime.now().isoformat(timespec='seconds')}",
         f"- **Plataforma:** `{e.http.base_url}` (todo por el gateway)",
         f"- **Escenario:** sede `{datos['nombre']}` con 9 mesas (mapa 3×3), 3 cervezas con 24 unidades y "
         f"pedidos en las mesas {', '.join(map(str, MESAS_CON_PEDIDO))}, en ese orden.",
         "- **Se regenera con:** `python scripts/evidencia_algoritmos.py --evidencia docs/evidencias`", "",
         "## 1, 2 y 3 · Sugerencia de compra (mochila 0/1 + MCD + voraz de respaldo)", "",
         f"`GET /inventario/sugerencia-compra?presupuesto={PRESUPUESTO}` · método **{mochila['metodo']}** · "
         f"MCD usado para reducir la tabla: **{mochila['escala_mcd']:,}**".replace(",", "."), "",
         f"Presupuesto {pesos(mochila['presupuesto'])} → se gastan {pesos(mochila['costo_total'])} y se "
         f"espera ganar {pesos(mochila['ganancia_esperada'])} (sobran {pesos(mochila['sobrante'])}).", "",
         "| Lote | Unidades | Costo (volumen) | Ganancia (beneficio) | ¿Entra? |", "|---|---:|---:|---:|---|"]
    for lote, entra in [(x, "✅") for x in mochila["lotes"]] + [(x, "—") for x in mochila["descartados"]]:
        L.append(f"| {lote['nombre']} | {lote['unidades']} | {pesos(lote['costo'])} | "
                 f"{pesos(lote['ganancia_esperada'])} | {entra} |")

    L += ["", "## 4 · Conciliación de existencia (iterativa y recursiva)", "",
          f"`GET /inventario/conciliacion` de **{vendido['nombre']}**: {conciliacion['movimientos']} "
          f"movimientos · existencia guardada **{conciliacion['existencia_registrada']}** · iterativa "
          f"**{conciliacion['existencia_iterativa']}** · recursiva "
          f"**{conciliacion['existencia_recursiva']}** → "
          f"{'✅ cuadra' if conciliacion['cuadra'] else '❌ no cuadra'}.", "",
          "## 5 · Vueltas con billetes y monedas (voraz)", "",
          f"`GET /pedidos/{pedido['id']}/cambio?pagado={pagado}`: total {pesos(cambio['total'])}, "
          f"vueltas **{pesos(cambio['cambio'])}** en {cambio['total_piezas']} piezas:", ""]
    L += [f"- {p['cantidad']} × {pesos(p['denominacion'])}" for p in cambio["piezas"]]

    L += ["", "## 6 · Ruta del mesero (recorrido voraz en un grafo, conjuntos C y S)", "",
          "`GET /mesas/ruta-entrega` · la barra está arriba del mapa; "
          "el costo es la distancia en casillas.", "",
          f"- **C** (candidatos) = {{{', '.join(ruta['candidatos'])}}}",
          f"- **S** (solución, en orden) = {' → '.join(ruta['ruta'])}",
          f"- Distancia total: **{ruta['distancia_total']}** casillas (en orden de número serían "
          f"{ruta['distancia_en_orden_de_numero']})", "",
          "| Paso | Nodo actual | Opciones (distancia) | Elegido |", "|---|---|---|---|"]
    for i, p in enumerate(ruta["pasos"], 1):
        opciones = ", ".join(f"{p['desde']}→{k}={v}" for k, v in p["opciones"].items())
        L.append(f"| {i} | {p['desde']} | {opciones} | **{p['elegido']}** ({p['distancia']}) |")

    L += ["", "## 7 · Cola de la barra (cadena lexicográficamente menor)", "",
          "`GET /pedidos/cola-barra` · clave de cada comanda = "
          "(distancia de la mesa a la barra, número de mesa).",
          "", "| Llega la comanda de | Clave | Va al | Cola resultante (mesas) |", "|---|---|---|---|"]
    for p in cola["pasos"]:
        c = p["comanda"]
        L.append(f"| Mesa {c['mesa']} (pedido #{c['pedido_id']}) | ({c['distancia_a_barra']}, {c['mesa']}) | "
                 f"{p['posicion']} | {' · '.join(map(str, p['cola']))} |")
    L += ["", f"Orden de despacho: **{' → '.join('Mesa ' + str(c['mesa']) for c in cola['cola'])}**", ""]

    carpeta.mkdir(parents=True, exist_ok=True)
    destino = carpeta / "algoritmos.md"
    destino.write_text("\n".join(L), encoding="utf-8")
    return destino


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base-url", default=os.environ.get("BASE_URL", "http://localhost:8000"))
    parser.add_argument("--evidencia", type=Path, default=Path("docs/evidencias"))
    args = parser.parse_args()
    e = Escenario(args.base_url, os.environ.get("ADMIN_USUARIO", "admin"),
                  os.environ.get("ADMIN_PASSWORD", "Admin2026"))
    try:
        destino = escribir(e, armar(e), args.evidencia)
    finally:
        e.cerrar()
    print(f"Evidencia: {destino}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
