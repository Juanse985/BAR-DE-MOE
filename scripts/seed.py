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

Usuarios que deja creados (deben cambiar la contraseña al primer ingreso):

    Todas las sedes  mszyslak / Cerveza2026 (ADMINISTRADOR)
    Galerías         ccarlson / Cajero2026 (CAJERO)  · bgumble / Mesero2026 (MESERO)
    Modelia          lleonard / Cajero2026 (CAJERO)  · sgumble / Mesero2026 (MESERO)
    Zona T           pbouvier / Cajero2026 (CAJERO)  · omann   / Mesero2026 (MESERO)
"""
import os
import sys

import httpx

BASE = os.environ.get("BASE_URL", "http://localhost:8000")
USUARIO = os.environ.get("ADMIN_USUARIO", "admin")
PASSWORD = os.environ.get("ADMIN_PASSWORD", "Admin2026")

# Las tres sedes del Bar de Moe en Bogotá.
GALERIAS, MODELIA, ZONA_T = "Galerías", "Modelia", "Zona T"
SEDES = [
    {"nombre": GALERIAS, "direccion": "Galerías, Bogotá"},
    {"nombre": MODELIA, "direccion": "Modelia, Bogotá"},
    {"nombre": ZONA_T, "direccion": "Zona T, Bogotá"},
]
TIPOS = [
    {"nombre": "Cerveza nacional", "descripcion": "Cervezas de marcas colombianas"},
    {"nombre": "Cerveza artesanal", "descripcion": "Cervezas artesanales colombianas"},
    {"nombre": "Cerveza internacional", "descripcion": "Marcas internacionales que se venden en Colombia"},
]
# Los NIT son de ejemplo: se reemplazan por los reales al parametrizar el bar.
PROVEEDORES = [
    {"nit": "900000001-1", "nombre": "Bavaria", "contacto": "Asesor comercial", "telefono": "3000000001"},
    {"nit": "900000002-2", "nombre": "Central Cervecera de Colombia",
     "contacto": "Asesor comercial", "telefono": "3000000002"},
    {"nit": "900000003-3", "nombre": "Bogotá Beer Company", "contacto": "Asesor comercial",
     "telefono": "3000000003"},
]
# Catálogo mínimo de cervezas. Precios en pesos colombianos, de ejemplo.
# Sprint 2: cada producto se crea una vez y queda en las tres sedes; lo que
# cambia por sede es la existencia.
EXISTENCIA_INICIAL = 48
PRODUCTOS = [
    # (código, nombre, tipo, proveedor, valor de compra, valor de venta)
    ("CERV-001", "Águila 330 ml", "Cerveza nacional", "Bavaria", "2200", "6000"),
    ("CERV-002", "Águila Light 330 ml", "Cerveza nacional", "Bavaria", "2300", "6000"),
    ("CERV-003", "Poker 330 ml", "Cerveza nacional", "Bavaria", "2200", "6000"),
    ("CERV-004", "Costeña 330 ml", "Cerveza nacional", "Bavaria", "2000", "5500"),
    ("CERV-005", "Pilsen 330 ml", "Cerveza nacional", "Bavaria", "2200", "6000"),
    ("CERV-006", "Club Colombia Dorada 330 ml", "Cerveza nacional", "Bavaria", "2800", "7500"),
    ("CERV-007", "Andina 330 ml", "Cerveza nacional", "Central Cervecera de Colombia", "2000", "5500"),
    ("ART-001", "BBC Cajicá Honey Ale 330 ml", "Cerveza artesanal", "Bogotá Beer Company", "5000", "12000"),
    ("ART-002", "BBC Chapinero Porter 330 ml", "Cerveza artesanal", "Bogotá Beer Company", "5000", "12000"),
    ("INT-001", "Corona 355 ml", "Cerveza internacional", "Bavaria", "4000", "10000"),
    ("INT-002", "Heineken 330 ml", "Cerveza internacional", "Central Cervecera de Colombia", "3500", "9000"),
]
MESAS_POR_SEDE = 10
# Un cajero y un mesero por sede: cada uno solo ve la información de su sede.
USUARIOS = [
    {"cedula": "1032456789", "nombre": "Moe Szyslak", "perfil": "ADMINISTRADOR",
     "usuario": "mszyslak", "password": "Cerveza2026", "sede": None},
    {"cedula": "1011223344", "nombre": "Carl Carlson", "perfil": "CAJERO",
     "usuario": "ccarlson", "password": "Cajero2026", "sede": GALERIAS},
    {"cedula": "1099887766", "nombre": "Barney Gumble", "perfil": "MESERO",
     "usuario": "bgumble", "password": "Mesero2026", "sede": GALERIAS},
    {"cedula": "1022334455", "nombre": "Lenny Leonard", "perfil": "CAJERO",
     "usuario": "lleonard", "password": "Cajero2026", "sede": MODELIA},
    {"cedula": "1033445566", "nombre": "Sam Gumble", "perfil": "MESERO",
     "usuario": "sgumble", "password": "Mesero2026", "sede": MODELIA},
    {"cedula": "1044556677", "nombre": "Patty Bouvier", "perfil": "CAJERO",
     "usuario": "pbouvier", "password": "Cajero2026", "sede": ZONA_T},
    {"cedula": "1055667788", "nombre": "Otto Mann", "perfil": "MESERO",
     "usuario": "omann", "password": "Mesero2026", "sede": ZONA_T},
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

    print("→ Productos (uno solo para todas las sedes)")
    for codigo, nombre, tipo, proveedor, compra, venta in PRODUCTOS:
        crear("/api/parametrizacion/productos", {
            "codigo": codigo, "nombre": nombre,
            "tipo_producto_id": tipos[tipo], "proveedor_id": proveedores[proveedor],
            "valor_compra": compra, "valor_venta": venta,
        }, codigo)

    print(f"→ Inventario inicial ({EXISTENCIA_INICIAL} unidades por producto y sede)")
    for s in SEDES:
        sede_id = sedes[s["nombre"]]
        filas = cliente.get("/api/parametrizacion/inventario", headers=h, params={"sede_id": sede_id}).json()
        cargados = 0
        for fila in filas:
            if fila["existencia"] == 0:
                r = cliente.post("/api/parametrizacion/inventario/ingresos", headers=h, json={
                    "sede_id": sede_id, "producto_id": fila["producto_id"],
                    "cantidad": EXISTENCIA_INICIAL, "motivo": "Initial stock (seed)"})
                if r.status_code == 201:
                    cargados += 1
                else:
                    conteo["errores"] += 1
                    print(f"  ! {fila['codigo']} en {s['nombre']} -> {r.status_code} {r.text}")
        print(f"  + {cargados} productos con existencia en {s['nombre']}")

    print("→ Usuarios (un cajero y un mesero por sede)")
    for u in USUARIOS:
        datos = {k: v for k, v in u.items() if k != "sede"}
        sede_id = sedes[u["sede"]] if u["sede"] else None
        crear("/api/auth/usuarios", {**datos, "sede_id": sede_id},
              f"{u['usuario']} ({u['perfil']}, {u['sede'] or 'todas las sedes'})")

    cliente.post("/api/auth/auth/logout", headers=h)
    print(f"✓ Sesión cerrada. {conteo['creados']} registros nuevos, "
          f"{conteo['existentes']} ya existían, {conteo['errores']} errores.")
    return 1 if conteo["errores"] else 0


if __name__ == "__main__":
    sys.exit(main())
