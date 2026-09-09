#!/usr/bin/env python3
"""Carga datos de ejemplo del Bar de Moe a través del gateway.

Uso:
    python scripts/seed.py                       # contra http://localhost:8000
    BASE_URL=http://otro:8000 python scripts/seed.py

Es la base de la demo de la Sprint Review. Está intencionalmente escrito contra
la API pública y no contra la base de datos: así el seed también sirve como
prueba de humo del flujo completo.
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
USUARIOS = [
    {"cedula": "1032456789", "nombre": "Moe Szyslak", "perfil": "ADMINISTRADOR",
     "usuario": "mszyslak", "password": "Cerveza2026"},
    {"cedula": "1099887766", "nombre": "Barney Gumble", "perfil": "MESERO",
     "usuario": "bgumble", "password": "Mesero2026"},
    {"cedula": "1011223344", "nombre": "Carl Carlson", "perfil": "CAJERO",
     "usuario": "ccarlson", "password": "Cajero2026"},
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
    if login.status_code != 200:
        print(f"✗ No se pudo autenticar: {login.status_code} {login.text}")
        return 1

    token = login.json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}
    print(f"✓ Autenticado como {USUARIO}")

    def crear(ruta: str, datos: dict, etiqueta: str):
        r = cliente.post(ruta, headers=h, json=datos)
        if r.status_code == 201:
            print(f"  + {etiqueta}")
            return r.json()
        if r.status_code == 409:
            print(f"  · {etiqueta} (ya existía)")
            return None
        print(f"  ! {etiqueta} -> {r.status_code} {r.text}")
        return None

    print("→ Sedes")
    for s in SEDES:
        crear("/api/parametrizacion/sedes", s, s["nombre"])
    sedes = {s["nombre"]: s["id"] for s in cliente.get("/api/parametrizacion/sedes", headers=h).json()}

    print("→ Mesas (10 por sede)")
    for nombre, sede_id in sedes.items():
        for numero in range(1, 11):
            cliente.post("/api/parametrizacion/mesas", headers=h,
                         json={"sede_id": sede_id, "numero": numero, "capacidad": 4})
        print(f"  + 10 mesas en {nombre}")

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
    for sede_nombre, sede_id in sedes.items():
        for codigo, nombre, tipo, proveedor, compra, venta in PRODUCTOS:
            crear("/api/parametrizacion/productos", {
                "codigo": codigo, "nombre": nombre, "sede_id": sede_id,
                "tipo_producto_id": tipos[tipo], "proveedor_id": proveedores[proveedor],
                "valor_compra": compra, "valor_venta": venta,
            }, f"{codigo} en {sede_nombre}")

    print("→ Usuarios (uno por perfil)")
    sede_centro = sedes.get("Bar de Moe · Centro")
    for u in USUARIOS:
        crear("/api/auth/usuarios", {**u, "sede_id": sede_centro}, f"{u['usuario']} ({u['perfil']})")

    cliente.post("/api/auth/auth/logout", headers=h)
    print("✓ Sesión cerrada. Datos de ejemplo cargados.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
