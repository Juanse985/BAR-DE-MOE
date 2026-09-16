#!/usr/bin/env python3
"""Medición del RNF-02 (HU-026): ninguna transacción puede pasar de 2 segundos.

Lanza N peticiones por operación contra el gateway, calcula promedio, p50, p95
y máximo, y FALLA (código de salida 1) si el p95 de alguna operación supera el
límite. Es la evidencia de desempeño que se muestra en la Sprint Review.

Uso:
    python scripts/medir_rnf02.py                        # 50 peticiones por operación
    python scripts/medir_rnf02.py -n 200 -c 8            # 200 por operación, 8 en paralelo
    python scripts/medir_rnf02.py --evidencia docs/evidencias

Se mide el tiempo que ve el cliente (reloj propio, incluye red y gateway) y el
que reporta el servidor en X-Tiempo-Ms. El criterio de aprobación usa el del
cliente, que es el que siente el mesero.

Variables de entorno: BASE_URL, ADMIN_USUARIO, ADMIN_PASSWORD.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import httpx

LIMITE_MS = 2000.0


@dataclass
class Medicion:
    operacion: str
    cliente_ms: list[float] = field(default_factory=list)
    servidor_ms: list[float] = field(default_factory=list)
    errores: int = 0
    sla_excedido: int = 0
    candado: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def anotar(self, cliente_ms: float | None, respuesta: httpx.Response | None) -> None:
        with self.candado:
            if cliente_ms is None or respuesta is None:
                self.errores += 1
                return
            self.cliente_ms.append(cliente_ms)
            if "X-Tiempo-Ms" in respuesta.headers:
                self.servidor_ms.append(float(respuesta.headers["X-Tiempo-Ms"]))
            if respuesta.headers.get("X-SLA-Excedido") == "true":
                self.sla_excedido += 1
            if respuesta.status_code >= 400:
                self.errores += 1

    @staticmethod
    def percentil(valores: list[float], p: float) -> float:
        """Percentil por rango más cercano (el que se explica en clase)."""
        if not valores:
            return math.nan
        ordenados = sorted(valores)
        rango = max(1, math.ceil(p / 100 * len(ordenados)))
        return ordenados[rango - 1]

    def resumen(self) -> dict:
        c = self.cliente_ms
        return {
            "operacion": self.operacion,
            "n": len(c),
            "errores": self.errores,
            "promedio_ms": round(statistics.fmean(c), 1) if c else None,
            "p50_ms": round(self.percentil(c, 50), 1) if c else None,
            "p95_ms": round(self.percentil(c, 95), 1) if c else None,
            "max_ms": round(max(c), 1) if c else None,
            "p95_servidor_ms": round(self.percentil(self.servidor_ms, 95), 1) if self.servidor_ms else None,
            "sla_excedido": self.sla_excedido,
            "cumple": bool(c) and self.percentil(c, 95) <= LIMITE_MS and self.errores == 0,
        }


def _medir(http: httpx.Client, medicion: Medicion, metodo: str, ruta: str, **kwargs) -> httpx.Response | None:
    inicio = time.perf_counter()
    try:
        resp = http.request(metodo, ruta, **kwargs)
    except httpx.HTTPError:
        medicion.anotar(None, None)
        return None
    medicion.anotar((time.perf_counter() - inicio) * 1000, resp)
    return resp


def medir(base_url: str, n: int, concurrencia: int, n_login: int, usuario: str, password: str,
          ambiente: str = "local") -> dict:
    http = httpx.Client(base_url=base_url, timeout=15.0,
                        limits=httpx.Limits(max_connections=concurrencia + 2))

    # 1. Login / logout. Se mide en serie porque la sesión es única (RNF-10).
    login = Medicion("Login (bcrypt 12 rondas)")
    token = None
    for i in range(n_login):
        resp = _medir(http, login, "POST", "/api/auth/auth/login",
                      json={"usuario": usuario, "password": password})
        if resp is None or resp.status_code != 200:
            detalle = resp.text[:200] if resp is not None else "sin respuesta"
            raise SystemExit(f"✗ No se pudo iniciar sesión como '{usuario}': {detalle}")
        token = resp.json()["access_token"]
        if i < n_login - 1:
            http.post("/api/auth/auth/logout", headers={"Authorization": f"Bearer {token}"})
    if token is None:  # n_login == 0
        resp = http.post("/api/auth/auth/login", json={"usuario": usuario, "password": password})
        if resp.status_code != 200:
            raise SystemExit(f"✗ No se pudo iniciar sesión como '{usuario}': {resp.text[:200]}")
        token = resp.json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}

    try:
        sedes = http.get("/api/parametrizacion/sedes", headers=h).json()
        sede_id = sedes[0]["id"] if sedes else None

        operaciones = [
            ("Estado de la plataforma", "GET", "/health", {}),
            ("Usuario en sesión (auth/me)", "GET", "/api/auth/auth/me", {"headers": h}),
            ("Listar sedes", "GET", "/api/parametrizacion/sedes", {"headers": h}),
            ("Listar mesas de la sede", "GET", "/api/parametrizacion/mesas",
             {"headers": h, "params": {"sede_id": sede_id} if sede_id else {}}),
            ("Catálogo de la sede", "GET", "/api/parametrizacion/productos",
             {"headers": h, "params": {"sede_id": sede_id} if sede_id else {}}),
            ("Listar tipos de producto", "GET", "/api/parametrizacion/tipos-producto", {"headers": h}),
            ("Listar proveedores", "GET", "/api/parametrizacion/proveedores", {"headers": h}),
            ("Listar usuarios", "GET", "/api/auth/usuarios", {"headers": h}),
        ]
        mediciones = [login] if n_login else []
        with ThreadPoolExecutor(max_workers=concurrencia) as pool:
            for nombre, metodo, ruta, kwargs in operaciones:
                m = Medicion(nombre)
                tareas = [pool.submit(_medir, http, m, metodo, ruta, **kwargs) for _ in range(n)]
                for tarea in tareas:
                    tarea.result()
                mediciones.append(m)
                r = m.resumen()
                print(f"  {'✓' if r['cumple'] else '✗'} {nombre:<32} p95 {r['p95_ms']:>8.1f} ms · "
                      f"máx {r['max_ms']:>8.1f} ms · errores {r['errores']}")
    finally:
        http.post("/api/auth/auth/logout", headers=h)

    resumenes = [m.resumen() for m in mediciones]
    return {
        "fecha": datetime.now().isoformat(timespec="seconds"),
        "base_url": base_url,
        "ambiente": ambiente,
        "limite_ms": LIMITE_MS,
        "peticiones_por_operacion": n,
        "concurrencia": concurrencia,
        "operaciones": resumenes,
        "aprobado": all(r["cumple"] for r in resumenes),
    }


def guardar(resultado: dict, carpeta: Path) -> Path:
    carpeta.mkdir(parents=True, exist_ok=True)
    (carpeta / "rnf02-tiempo-respuesta.json").write_text(
        json.dumps(resultado, indent=2, ensure_ascii=False), encoding="utf-8")
    lineas = [
        "# Evidencia · RNF-02 tiempo de respuesta (HU-026)",
        "",
        f"- **Fecha:** {resultado['fecha']}",
        f"- **Plataforma:** `{resultado['base_url']}` · ambiente: {resultado.get('ambiente', '-')}",
        f"- **Carga:** {resultado['peticiones_por_operacion']} peticiones por operación, "
        f"{resultado['concurrencia']} en paralelo",
        f"- **Criterio:** p95 del tiempo visto por el cliente ≤ {resultado['limite_ms']:.0f} ms "
        "y cero errores",
        f"- **Resultado:** {'✅ CUMPLE' if resultado['aprobado'] else '❌ NO CUMPLE'}",
        "",
        "| Operación | n | Promedio (ms) | p50 (ms) | p95 (ms) | Máx (ms) | p95 servidor (ms) "
        "| SLA excedido | Errores | Cumple |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for r in resultado["operaciones"]:
        lineas.append(
            f"| {r['operacion']} | {r['n']} | {r['promedio_ms']} | {r['p50_ms']} | **{r['p95_ms']}** | "
            f"{r['max_ms']} | {r['p95_servidor_ms']} | {r['sla_excedido']} | {r['errores']} | "
            f"{'✅' if r['cumple'] else '❌'} |"
        )
    lineas += [
        "",
        "> El login incluye el cálculo de bcrypt con 12 rondas (RNF-08); es la operación más costosa",
        "> a propósito, y aun así debe quedar bajo el límite.",
    ]
    destino = carpeta / "rnf02-tiempo-respuesta.md"
    destino.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    return destino


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--base-url", default=os.environ.get("BASE_URL", "http://localhost:8000"))
    parser.add_argument("-n", "--peticiones", type=int, default=50, help="peticiones por operación")
    parser.add_argument("-c", "--concurrencia", type=int, default=4, help="peticiones en paralelo")
    parser.add_argument("--logins", type=int, default=10, help="ciclos de login/logout a medir")
    parser.add_argument("--evidencia", type=Path, default=None, help="carpeta para el .md y el .json")
    parser.add_argument("--ambiente", default=os.environ.get("AMBIENTE", "local"),
                        help="texto que describe dónde se midió (ej. 'docker compose, portátil de Juan')")
    args = parser.parse_args()

    print(f"Midiendo RNF-02 contra {args.base_url} "
          f"({args.peticiones} peticiones por operación, {args.concurrencia} en paralelo)")
    resultado = medir(args.base_url, args.peticiones, args.concurrencia, args.logins,
                      os.environ.get("ADMIN_USUARIO", "admin"), os.environ.get("ADMIN_PASSWORD", "Admin2026"),
                      args.ambiente)
    if args.logins:
        login = resultado["operaciones"][0]
        marca = "✓" if login["cumple"] else "✗"
        print(f"  {marca} {login['operacion']:<32} p95 {login['p95_ms']:>8.1f} ms · "
              f"máx {login['max_ms']:>8.1f} ms · errores {login['errores']}")
    print(f"\nRNF-02: {'CUMPLE' if resultado['aprobado'] else 'NO CUMPLE'} (p95 ≤ {LIMITE_MS:.0f} ms)")
    if args.evidencia:
        print(f"Evidencia: {guardar(resultado, args.evidencia)}")
    return 0 if resultado["aprobado"] else 1


if __name__ == "__main__":
    sys.exit(main())
