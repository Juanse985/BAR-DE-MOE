#!/usr/bin/env python3
"""Prueba de humo de punta a punta contra la plataforma levantada.

Recorre el flujo que se muestra en la Sprint Review, siempre por el gateway:

    health → login → segunda sesión rechazada → crear sede, tipo, proveedor y
    producto → consultar → mesero sin permisos → logout → token inservible

En cada paso verifica el código HTTP esperado y que el tiempo de respuesta
esté bajo los 2 segundos (RNF-02, cabecera X-Tiempo-Ms y reloj del cliente).

Uso:
    python scripts/prueba_humo.py
    python scripts/prueba_humo.py --base-url http://localhost:8000 --evidencia docs/evidencias

Variables de entorno: BASE_URL, ADMIN_USUARIO, ADMIN_PASSWORD,
MESERO_USUARIO, MESERO_PASSWORD (por defecto los del seed).

Sale con código 0 si todo pasa y 1 si algún paso falla.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

import httpx

SLA_MS = 2000.0


@dataclass
class Paso:
    numero: int
    nombre: str
    requisito: str
    esperado: str
    obtenido: str = ""
    tiempo_servidor_ms: float | None = None
    tiempo_cliente_ms: float = 0.0
    estado: str = "PENDIENTE"  # OK · FALLO · OMITIDO
    nota: str = ""


@dataclass
class Resultado:
    base_url: str
    inicio: str
    pasos: list[Paso] = field(default_factory=list)

    @property
    def aprobado(self) -> bool:
        return all(p.estado != "FALLO" for p in self.pasos)


class PruebaHumo:
    def __init__(self, base_url: str, admin: tuple[str, str], mesero: tuple[str, str]):
        self.http = httpx.Client(base_url=base_url, timeout=15.0)
        self.admin = admin
        self.mesero = mesero
        self.r = Resultado(base_url=base_url, inicio=datetime.now().isoformat(timespec="seconds"))
        self.token: str | None = None
        self.sufijo = datetime.now().strftime("%Y%m%d%H%M%S")

    # --------------------------------------------------------------- utilidades
    @property
    def h(self) -> dict:
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    def paso(self, nombre: str, requisito: str, esperado: int | tuple[int, ...], metodo: str, ruta: str,
             *, headers: dict | None = None, json_: dict | None = None, params: dict | None = None,
             validar=None) -> httpx.Response | None:
        esperados = esperado if isinstance(esperado, tuple) else (esperado,)
        p = Paso(len(self.r.pasos) + 1, nombre, requisito, " o ".join(map(str, esperados)))
        self.r.pasos.append(p)
        inicio = time.perf_counter()
        try:
            resp = self.http.request(metodo, ruta, headers=headers, json=json_, params=params)
        except httpx.HTTPError as exc:
            p.estado, p.obtenido, p.nota = "FALLO", "sin respuesta", str(exc)
            self._imprimir(p)
            return None
        p.tiempo_cliente_ms = (time.perf_counter() - inicio) * 1000
        p.obtenido = str(resp.status_code)
        if "X-Tiempo-Ms" in resp.headers:
            p.tiempo_servidor_ms = float(resp.headers["X-Tiempo-Ms"])

        problemas = []
        if resp.status_code not in esperados:
            problemas.append(f"código {resp.status_code}: {resp.text[:160]}")
        if p.tiempo_servidor_ms is None:
            problemas.append("falta la cabecera X-Tiempo-Ms")
        elif p.tiempo_servidor_ms > SLA_MS:
            problemas.append(f"servidor tardó {p.tiempo_servidor_ms:.0f} ms (> {SLA_MS:.0f})")
        if p.tiempo_cliente_ms > SLA_MS:
            problemas.append(f"cliente esperó {p.tiempo_cliente_ms:.0f} ms (> {SLA_MS:.0f})")
        if not problemas and validar is not None:
            try:
                validar(resp)
            except AssertionError as exc:
                problemas.append(str(exc) or "validación del contenido falló")
        p.estado = "FALLO" if problemas else "OK"
        p.nota = "; ".join(problemas)
        self._imprimir(p)
        return resp

    def omitir(self, nombre: str, requisito: str, motivo: str) -> None:
        p = Paso(len(self.r.pasos) + 1, nombre, requisito, "-", estado="OMITIDO", nota=motivo)
        self.r.pasos.append(p)
        self._imprimir(p)

    @staticmethod
    def _imprimir(p: Paso) -> None:
        marca = {"OK": "✓", "FALLO": "✗", "OMITIDO": "·"}.get(p.estado, "?")
        tiempo = f"{p.tiempo_servidor_ms:7.1f} ms" if p.tiempo_servidor_ms is not None else "     -    "
        print(f" {marca} {p.numero:>2}. {p.nombre:<48} {p.obtenido:>4}  {tiempo}  {p.nota}")

    # ------------------------------------------------------------------- flujo
    def ejecutar(self) -> Resultado:
        print(f"Prueba de humo contra {self.r.base_url}\n")

        def plataforma_sana(resp):
            cuerpo = resp.json()
            assert cuerpo.get("estado") == "ok", f"estado de la plataforma: {cuerpo}"

        salud = self.paso("Plataforma disponible (/health)", "Despliegue", 200, "GET", "/health",
                          validar=plataforma_sana)
        if salud is None:
            return self.r

        usuario, password = self.admin
        login = self.paso("Login del administrador", "HU-001 · RNF-05", 200, "POST",
                          "/api/auth/auth/login", json_={"usuario": usuario, "password": password})
        if login is None or login.status_code != 200:
            if login is not None and login.status_code == 409:
                self.r.pasos[-1].nota += " · ya hay una sesión abierta: haga logout o espere 3 minutos"
            return self.r
        self.token = login.json()["access_token"]

        def trae_codigo(codigo):
            def _validar(resp):
                assert resp.json()["error"]["codigo"] == codigo, f"se esperaba {codigo}"
            return _validar

        self.paso("Segunda sesión del mismo usuario rechazada", "HU-003 · RNF-10", 409, "POST",
                  "/api/auth/auth/login", json_={"usuario": usuario, "password": password},
                  validar=trae_codigo("SESION_ACTIVA"))

        self.paso("Datos del usuario en sesión (/auth/me)", "HU-001", 200, "GET", "/api/auth/auth/me",
                  headers=self.h)

        sede = self.paso("Crear sede", "HU-017 · RNF-12", 201, "POST", "/api/parametrizacion/sedes",
                         headers=self.h, json_={"nombre": f"QA Humo {self.sufijo}",
                                                "direccion": "Av. Siempreviva 742"})
        tipo = self.paso("Crear tipo de producto", "HU-019", 201, "POST",
                         "/api/parametrizacion/tipos-producto", headers=self.h,
                         json_={"nombre": f"QA Tipo {self.sufijo}"})
        proveedor = self.paso("Crear proveedor", "HU-019", 201, "POST", "/api/parametrizacion/proveedores",
                              headers=self.h, json_={"nit": f"QA{self.sufijo}", "nombre": "QA Proveedor"})

        if all(x is not None and x.status_code == 201 for x in (sede, tipo, proveedor)):
            sede_id = sede.json()["id"]
            codigo = f"QA-{self.sufijo[-6:]}"
            self.paso("Crear producto en la sede", "HU-020", 201, "POST", "/api/parametrizacion/productos",
                      headers=self.h, json_={
                          "codigo": codigo, "nombre": "Cerveza Duff QA", "sede_id": sede_id,
                          "tipo_producto_id": tipo.json()["id"], "proveedor_id": proveedor.json()["id"],
                          "valor_compra": "2500", "valor_venta": "6000"})
            self.paso("Crear mesa en la sede", "HU-018", 201, "POST", "/api/parametrizacion/mesas",
                      headers=self.h, json_={"sede_id": sede_id, "numero": 1, "capacidad": 4})

            def contiene_producto(resp):
                codigos = [p["codigo"] for p in resp.json()]
                assert codigos == [codigo], f"el catálogo de la sede devolvió {codigos}"

            self.paso("Consultar catálogo filtrado por sede", "HU-020", 200, "GET",
                      "/api/parametrizacion/productos", headers=self.h, params={"sede_id": sede_id},
                      validar=contiene_producto)
            self.paso("Consultar la sede creada", "HU-017", 200, "GET",
                      f"/api/parametrizacion/sedes/{sede_id}", headers=self.h)
        else:
            self.omitir("Crear producto / mesa y consultar", "HU-018 · HU-020",
                        "no se pudieron crear sede, tipo o proveedor")

        self.paso("Ruta protegida sin token", "HU-028 · C-1", 401, "GET", "/api/parametrizacion/sedes",
                  validar=trae_codigo("NO_AUTENTICADO"))
        self.paso("Token falsificado", "HU-028 · C-1", 401, "GET", "/api/parametrizacion/sedes",
                  headers={"Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.e30.firma-falsa"})

        self._mesero_sin_permisos()

        self.paso("Logout del administrador", "HU-004", 200, "POST", "/api/auth/auth/logout", headers=self.h)
        self.paso("El token cerrado ya no sirve", "HU-004 · C-4", 401, "GET",
                  "/api/parametrizacion/sedes", headers=self.h, validar=trae_codigo("SESION_CERRADA"))
        return self.r

    def _mesero_sin_permisos(self) -> None:
        usuario, password = self.mesero
        try:
            resp = self.http.post("/api/auth/auth/login", json={"usuario": usuario, "password": password})
        except httpx.HTTPError as exc:
            self.omitir("Mesero no puede crear sedes", "HU-028 · C-1", f"login del mesero falló: {exc}")
            return
        if resp.status_code != 200:
            self.omitir("Mesero no puede crear sedes", "HU-028 · C-1",
                        f"no se pudo entrar como '{usuario}' ({resp.status_code}); ¿se corrió el seed?")
            return
        h = {"Authorization": f"Bearer {resp.json()['access_token']}"}
        self.paso("Mesero no puede crear sedes", "HU-028 · C-1", 403, "POST", "/api/parametrizacion/sedes",
                  headers=h, json_={"nombre": f"Sede pirata {self.sufijo}"})
        self.paso("Mesero no puede administrar usuarios", "HU-028 · C-1", 403, "GET", "/api/auth/usuarios",
                  headers=h)
        self.http.post("/api/auth/auth/logout", headers=h)


# --------------------------------------------------------------------- salida
def guardar_evidencia(r: Resultado, carpeta: Path) -> Path:
    carpeta.mkdir(parents=True, exist_ok=True)
    (carpeta / "prueba-humo.json").write_text(
        json.dumps({"base_url": r.base_url, "inicio": r.inicio, "aprobado": r.aprobado,
                    "pasos": [asdict(p) for p in r.pasos]}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    lineas = [
        "# Evidencia · prueba de humo de punta a punta",
        "",
        f"- **Fecha:** {r.inicio}",
        f"- **Plataforma:** `{r.base_url}`",
        f"- **Resultado:** {'✅ APROBADA' if r.aprobado else '❌ CON FALLOS'}",
        f"- **SLA verificado en cada paso:** {SLA_MS:.0f} ms (RNF-02)",
        "",
        "| # | Paso | Requisito | Esperado | Obtenido | Servidor (ms) | Cliente (ms) | Estado | Nota |",
        "|---|---|---|---|---|---:|---:|---|---|",
    ]
    for p in r.pasos:
        servidor = f"{p.tiempo_servidor_ms:.1f}" if p.tiempo_servidor_ms is not None else "-"
        lineas.append(f"| {p.numero} | {p.nombre} | {p.requisito} | {p.esperado} | {p.obtenido or '-'} | "
                      f"{servidor} | {p.tiempo_cliente_ms:.1f} | {p.estado} | {p.nota.replace('|', '/')} |")
    destino = carpeta / "prueba-humo.md"
    destino.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    return destino


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--base-url", default=os.environ.get("BASE_URL", "http://localhost:8000"))
    parser.add_argument("--evidencia", type=Path, default=None,
                        help="carpeta donde dejar prueba-humo.md y .json (ej. docs/evidencias)")
    args = parser.parse_args()

    prueba = PruebaHumo(
        args.base_url,
        admin=(os.environ.get("ADMIN_USUARIO", "admin"), os.environ.get("ADMIN_PASSWORD", "Admin2026")),
        mesero=(os.environ.get("MESERO_USUARIO", "bgumble"), os.environ.get("MESERO_PASSWORD", "Mesero2026")),
    )
    resultado = prueba.ejecutar()

    ok = sum(p.estado == "OK" for p in resultado.pasos)
    fallos = sum(p.estado == "FALLO" for p in resultado.pasos)
    omitidos = sum(p.estado == "OMITIDO" for p in resultado.pasos)
    print(f"\n{ok} OK · {fallos} fallos · {omitidos} omitidos → "
          f"{'APROBADA' if resultado.aprobado and resultado.pasos else 'NO APROBADA'}")
    if args.evidencia:
        print(f"Evidencia: {guardar_evidencia(resultado, args.evidencia)}")
    return 0 if resultado.aprobado and len(resultado.pasos) > 2 else 1


if __name__ == "__main__":
    sys.exit(main())
