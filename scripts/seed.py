#!/usr/bin/env python3
"""Carga datos de ejemplo del Bar de Moe a través del gateway.

Uso:
    python scripts/seed.py                       # contra http://localhost:8000
    BASE_URL=http://otro:8000 python scripts/seed.py

Es la base de la demo de la Sprint Review. Está intencionalmente escrito contra
la API pública y no contra la base de datos: así el seed también sirve como
prueba de humo del flujo completo.

Se puede correr varias veces: lo que ya existe se reporta como "ya existía" y
no se duplica. Termina con código 1 si algo falló de verdad.

Usuarios que deja creados (uno por perfil en cada sede):

    Centro  mszyslak / Cerveza2026 (ADMINISTRADOR) · ccarlson / Cajero2026 · bgumble / Mesero2026
    Norte   lleonard / Cajero2026 (CAJERO)          · sgumble  / Mesero2026 (MESERO)
"""
import os
import sys

import httpx

BASE = os.environ.get("BASE_URL", "http://localhost:8000")
USUARIO = os.environ.get("ADMIN_USUARIO", "admin")
PASSWORD = os.environ.get("ADMIN_PASSWORD", "Admin2026")

SEDES = [
    {"nombre": "Bar de Moe · Centro", "direccion": "Av. Siempreviva 742", "telefono": "6011234567"},
    {"nombre": "Bar de Moe · Norte", "direccion": "Calle 100 #15-20", "telefono": "6017654321"},
]
TIPOS = [
    {"nombre": "Cerveza", "descripcion": "Cervezas nacionales e importadas"},
    {"nombre": "Licor", "descripcion": "Destilados y cócteles"},
    {"nombre": "Snack", "descripcion": "Pasabocas y picadas"},
]
PROVEEDORES = [
    {"nit": "900123456-1", "nombre": "Distribuidora Duff",
     "contacto": "H. Simpson", "telefono": "3001112233"},
    {"nit": "900654321-2", "nombre": "Licores del Valle",
     "contacto": "B. Gumble", "telefono": "3004445566"},
]
PRODUCTOS = [
    ("CERV-001", "Cerveza Duff 330ml", "Cerveza", "Distribuidora Duff", "2500", "6000"),
    ("CERV-002", "Cerveza Duff 750ml", "Cerveza", "Distribuidora Duff", "5000", "12000"),
    ("LIC-001", "Aguardiente botella", "Licor", "Licores del Valle", "28000", "65000"),
    ("SNK-001", "Picada personal", "Snack", "Distribuidora Duff", "8000", "18000"),
]
MESAS_POR_SEDE = 10
USUARIOS = [
    {"cedula": "1032456789", "nombre": "Moe Szyslak", "perfil": "ADMINISTRADOR",
     "usuario": "mszyslak", "password": "Cerveza2026", "sede": "Bar de Moe · Centro"},
    {"cedula": "1099887766", "nombre": "Barney Gumble", "perfil": "MESERO",
     "usuario": "bgumble", "password": "Mesero2026", "sede": "Bar de Moe · Centro"},
    {"cedula": "1011223344", "nombre": "Carl Carlson", "perfil": "CAJERO",
     "usuario": "ccarlson", "password": "Cajero2026", "sede": "Bar de Moe · Centro"},
    {"cedula": "1022334455", "nombre": "Lenny Leonard", "perfil": "CAJERO",
     "usuario": "lleonard", "password": "Cajero2026", "sede": "Bar de Moe · Norte"},
    {"cedula": "1033445566", "nombre": "Sam Gumble", "perfil": "MESERO",
     "usuario": "sgumble", "password": "Mesero2026", "sede": "Bar de Moe · Norte"},
]


def main() -> int:
    cliente = httpx.Client(base_url=BASE, timeout=15.0)

    print(f"→ Conectando a {BASE}")
    salud = cliente.get("/health")
    if salud.status_code != 200:
        print("✗ El gateway no responde. ¿Levantaste 'docker compose up'?")
        return 1
    print(f"  estado: {salud.json()['estado']}")

    login = cliente.post("/api/auth/auth/login", json={"usuario": USUARIO, "password": PASSWORD})
    if login.status_code == 409:
        print("✗ Ya hay una sesión abierta para ese usuario (RNF-10).")
        print("  Hacé logout o esperá 3 minutos a que caduque por inactividad.")
        return 1
    if login.status_code == 423:
        print("✗ La cuenta del administrador está bloqueada por reintentos (RNF-09).")
        return 1
    if login.status_code != 200:
        print(f"✗ No se pudo autenticar: {login.status_code} {login.text}")
        return 1

    token = login.json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}
    print(f"✓ Autenticado como {USUARIO}")

    conteo = {"creados": 0, "existentes": 0, "errores": 0}

    def crear(ruta: str, datos: dict, etiqueta: str, silencioso: bool = False):
        r = cliente.post(ruta, headers=h, json=datos)
        if r.status_code == 201:
            conteo["creados"] += 1
            if not silencioso:
                print(f"  + {etiqueta}")
            return r.json()
        if r.status_code == 409:
            conteo["existentes"] += 1
            if not silencioso:
                print(f"  · {etiqueta} (ya existía)")
            return None
        conteo["errores"] += 1
        print(f"  ! {etiqueta} -> {r.status_code} {r.text}")
        return None

    print("→ Sedes")
    for s in SEDES:
        crear("/api/parametrizacion/sedes", s, s["nombre"])
    sedes = {s["nombre"]: s["id"] for s in cliente.get("/api/parametrizacion/sedes", headers=h).json()}

    print(f"→ Mesas ({MESAS_POR_SEDE} por sede)")
    for s in SEDES:
        sede_id = sedes[s["nombre"]]
        antes = conteo["creados"]
        for numero in range(1, MESAS_POR_SEDE + 1):
            crear("/api/parametrizacion/mesas", {"sede_id": sede_id, "numero": numero, "capacidad": 4},
                  f"mesa {numero}", silencioso=True)
        print(f"  + {conteo['creados'] - antes} mesas nuevas en {s['nombre']}")

    print("→ Tipos de producto")
    for t in TIPOS:
        crear("/api/parametrizacion/tipos-producto", t, t["nombre"])
    respuesta_tipos = cliente.get("/api/parametrizacion/tipos-producto", headers=h).json()
    tipos = {t["nombre"]: t["id"] for t in respuesta_tipos}

    print("→ Proveedores")
    for p in PROVEEDORES:
        crear("/api/parametrizacion/proveedores", p, p["nombre"])
    respuesta_prov = cliente.get("/api/parametrizacion/proveedores", headers=h).json()
    proveedores = {p["nombre"]: p["id"] for p in respuesta_prov}

    print("→ Productos (catálogo por sede)")
    for s in SEDES:
        sede_nombre, sede_id = s["nombre"], sedes[s["nombre"]]
        for codigo, nombre, tipo, proveedor, compra, venta in PRODUCTOS:
            crear("/api/parametrizacion/productos", {
                "codigo": codigo, "nombre": nombre, "sede_id": sede_id,
                "tipo_producto_id": tipos[tipo], "proveedor_id": proveedores[proveedor],
                "valor_compra": compra, "valor_venta": venta,
            }, f"{codigo} en {sede_nombre}")

    print("→ Usuarios (uno por perfil en cada sede)")
    for u in USUARIOS:
        datos = {k: v for k, v in u.items() if k != "sede"}
        crear("/api/auth/usuarios", {**datos, "sede_id": sedes[u["sede"]]},
              f"{u['usuario']} ({u['perfil']}, {u['sede']})")

    cliente.post("/api/auth/auth/logout", headers=h)
    print(f"✓ Sesión cerrada. {conteo['creados']} registros nuevos, "
          f"{conteo['existentes']} ya existían, {conteo['errores']} errores.")
    return 1 if conteo["errores"] else 0


if __name__ == "__main__":
    sys.exit(main())
