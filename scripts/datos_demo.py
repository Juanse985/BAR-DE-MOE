#!/usr/bin/env python3
"""Completa los datos de ejemplo del Bar de Moe para la demo (correr DESPUÉS de seed.py).

seed.py deja sedes, mesas, cervezas con 48 unidades y usuarios. Este script agrega:

- tipos de producto: aguardiente, ron, whisky, bebidas sin alcohol y comida;
- proveedores de licores, bebidas y pasabocas;
- 14 productos más (licores, bebidas, pasabocas), que quedan en las tres sedes;
- existencias distintas por sede, con algunos productos bajo el mínimo y uno agotado
  por sede, para que se vean las alertas;
- movimientos de inventario: compras y ajustes por conteo físico;
- pedidos abiertos tomados por el mesero de cada sede (mesas ocupadas y ventas
  descontadas del inventario);
- Sprints 3 y 4 (HU-032, MVP): pedidos ya cobrados por el cajero de cada sede, con
  factura en efectivo, débito y crédito, para que la consulta de facturas y el reporte
  de ventas y ganancia tengan datos del día.

Todo pasa por el gateway, igual que seed.py. Los productos se pueden volver a crear sin
duplicarse; el inventario y los pedidos solo se cargan la primera vez.

Uso (con la plataforma levantada):
    docker cp scripts/datos_demo.py barmoe-gateway:/tmp/datos_demo.py
    docker exec barmoe-gateway python /tmp/datos_demo.py

Variables: BASE_URL, ADMIN_USUARIO, ADMIN_PASSWORD, MESERO_PASSWORD, CAJERO_PASSWORD.
"""
import os
import sys

import httpx

BASE = os.environ.get("BASE_URL", "http://localhost:8000")
USUARIO = os.environ.get("ADMIN_USUARIO", "admin")
PASSWORD = os.environ.get("ADMIN_PASSWORD", "Admin2026")
MESERO_PASSWORD = os.environ.get("MESERO_PASSWORD", "Mesero2026")
CAJERO_PASSWORD = os.environ.get("CAJERO_PASSWORD", "Cajero2026")
API = "/api/parametrizacion"

GALERIAS, MODELIA, ZONA_T = "Galerías", "Modelia", "Zona T"

TIPOS = [
    {"nombre": "Aguardiente", "descripcion": "Aguardientes colombianos"},
    {"nombre": "Ron", "descripcion": "Rones colombianos"},
    {"nombre": "Whisky", "descripcion": "Whisky importado"},
    {"nombre": "Bebida sin alcohol", "descripcion": "Gaseosas, agua y jugos"},
    {"nombre": "Comida y pasabocas", "descripcion": "Picadas y pasabocas de paquete"},
]
# Nombres y NIT de ejemplo: se reemplazan por los reales al parametrizar el bar.
PROVEEDORES = [
    {"nit": "900000004-4", "nombre": "Distribuidora de Licores Andina", "contacto": "Asesor comercial",
     "telefono": "3000000004"},
    {"nit": "900000005-5", "nombre": "Bebidas y Aguas Bogotá", "contacto": "Asesor comercial",
     "telefono": "3000000005"},
    {"nit": "900000006-6", "nombre": "Pasabocas Capital", "contacto": "Asesor comercial",
     "telefono": "3000000006"},
]
LICORES, BEBIDAS, PASABOCAS = (p["nombre"] for p in PROVEEDORES)
PRODUCTOS = [
    # (código, nombre, tipo, proveedor, compra, venta, stock mínimo)
    ("LIC-001", "Aguardiente Antioqueño sin azúcar 375 ml", "Aguardiente", LICORES, "28000", "55000", 3),
    ("LIC-002", "Aguardiente Néctar Club 375 ml", "Aguardiente", LICORES, "25000", "50000", 3),
    ("LIC-003", "Ron Viejo de Caldas 3 años 375 ml", "Ron", LICORES, "30000", "60000", 3),
    ("LIC-004", "Ron Medellín Añejo 375 ml", "Ron", LICORES, "29000", "58000", 3),
    ("LIC-005", "Whisky Old Parr 12 años 750 ml", "Whisky", LICORES, "150000", "290000", 2),
    ("LIC-006", "Whisky Buchanan's 12 años 750 ml", "Whisky", LICORES, "140000", "270000", 2),
    ("BEB-001", "Coca-Cola 350 ml", "Bebida sin alcohol", BEBIDAS, "1800", "5000", 6),
    ("BEB-002", "Agua Cristal 600 ml", "Bebida sin alcohol", BEBIDAS, "1200", "4000", 6),
    ("BEB-003", "Soda Bretaña 300 ml", "Bebida sin alcohol", BEBIDAS, "1500", "4500", 6),
    ("BEB-004", "Jugo Hit mango 500 ml", "Bebida sin alcohol", BEBIDAS, "1800", "5000", 6),
    ("COM-001", "Papas fritas de paquete 45 g", "Comida y pasabocas", PASABOCAS, "1500", "4500", 5),
    ("COM-002", "Maní salado 50 g", "Comida y pasabocas", PASABOCAS, "1200", "4000", 5),
    ("COM-003", "Chicharrones de paquete 40 g", "Comida y pasabocas", PASABOCAS, "1600", "4500", 5),
    ("COM-004", "Picada para dos personas", "Comida y pasabocas", PASABOCAS, "18000", "42000", 2),
]

# Existencia de los productos nuevos en cada sede. 0 = agotado; por debajo del mínimo = alerta.
EXISTENCIAS = {
    "LIC-001": {GALERIAS: 18, MODELIA: 12, ZONA_T: 20},
    "LIC-002": {GALERIAS: 10, MODELIA: 8, ZONA_T: 2},     # Zona T bajo el mínimo
    "LIC-003": {GALERIAS: 12, MODELIA: 10, ZONA_T: 14},
    "LIC-004": {GALERIAS: 8, MODELIA: 1, ZONA_T: 9},      # Modelia bajo el mínimo
    "LIC-005": {GALERIAS: 4, MODELIA: 3, ZONA_T: 6},
    "LIC-006": {GALERIAS: 3, MODELIA: 0, ZONA_T: 5},      # Modelia agotado
    "BEB-001": {GALERIAS: 48, MODELIA: 36, ZONA_T: 60},
    "BEB-002": {GALERIAS: 40, MODELIA: 30, ZONA_T: 48},
    "BEB-003": {GALERIAS: 24, MODELIA: 4, ZONA_T: 30},    # Modelia bajo el mínimo
    "BEB-004": {GALERIAS: 0, MODELIA: 20, ZONA_T: 24},    # Galerías agotado
    "COM-001": {GALERIAS: 30, MODELIA: 24, ZONA_T: 36},
    "COM-002": {GALERIAS: 30, MODELIA: 20, ZONA_T: 3},    # Zona T bajo el mínimo
    "COM-003": {GALERIAS: 20, MODELIA: 15, ZONA_T: 0},    # Zona T agotado
    "COM-004": {GALERIAS: 6, MODELIA: 4, ZONA_T: 8},
}
COMPRA = {LICORES: "Compra Distribuidora de Licores Andina, factura ",
          BEBIDAS: "Compra Bebidas y Aguas Bogotá, factura ", PASABOCAS: "Compra Pasabocas Capital, factura "}

# Ajustes por conteo físico sobre las cervezas que dejó el seed (48 unidades).
AJUSTES = [
    (GALERIAS, "CERV-001", -2, "Conteo físico: 2 botellas rotas en la nevera"),
    (MODELIA, "INT-001", -1, "Conteo físico: 1 unidad vencida"),
    (ZONA_T, "ART-002", -3, "Conteo físico: faltante en la bodega"),
]

# Pedidos abiertos que toma el mesero de cada sede: (mesa, [(código, cantidad), ...]).
MESEROS = {GALERIAS: "bgumble", MODELIA: "sgumble", ZONA_T: "omann"}
PEDIDOS = {
    GALERIAS: [(2, [("CERV-001", 6), ("COM-001", 2)]),
               (5, [("LIC-001", 1), ("BEB-002", 2), ("COM-004", 1)]),
               (7, [("ART-001", 4), ("CERV-006", 2)])],
    MODELIA: [(1, [("CERV-003", 4), ("COM-002", 2)]),
              (4, [("LIC-003", 1), ("BEB-001", 3)])],
    ZONA_T: [(3, [("INT-002", 6), ("COM-001", 3)]),
             (6, [("LIC-005", 1), ("BEB-003", 4)]),
             (9, [("CERV-004", 5), ("CERV-007", 5), ("COM-004", 1)])],
}

# Pedidos que se toman y se cobran enseguida (HU-023): (mesa, líneas, medio de pago, valor recibido).
CAJEROS = {GALERIAS: "ccarlson", MODELIA: "lleonard", ZONA_T: "pbouvier"}
COBRADOS = {
    GALERIAS: [(1, [("CERV-002", 4), ("COM-002", 1)], "EFECTIVO", 50000),
               (3, [("LIC-003", 1), ("BEB-001", 2)], "TARJETA_CREDITO", None)],
    MODELIA: [(2, [("CERV-005", 6)], "EFECTIVO", 40000),
              (6, [("ART-002", 2), ("COM-004", 1)], "TARJETA_DEBITO", None)],
    ZONA_T: [(1, [("INT-001", 3), ("BEB-002", 1)], "TARJETA_DEBITO", None),
             (4, [("LIC-002", 1), ("CERV-001", 4), ("COM-001", 2)], "EFECTIVO", 100000)],
}


def main() -> int:
    http = httpx.Client(base_url=BASE, timeout=15.0)
    print(f"→ Conectando a {BASE}")
    if http.get("/health").status_code != 200:
        print("✗ El gateway no responde. ¿Levantaste 'docker compose up -d'?")
        return 1

    login = http.post("/api/auth/auth/login", json={"usuario": USUARIO, "password": PASSWORD})
    if login.status_code != 200:
        print(f"✗ No se pudo entrar como '{USUARIO}' ({login.status_code}): {login.text[:200]}")
        print("  Si cambiaste la clave, pásala con -e ADMIN_PASSWORD=...")
        print("  o entra con otro administrador con -e ADMIN_USUARIO=...")
        print("  Si dice sesión activa, cierra sesión en el navegador o espera 3 minutos.")
        return 1
    h = {"Authorization": f"Bearer {login.json()['access_token']}"}
    print(f"✓ Autenticado como {USUARIO}")
    conteo = {"creados": 0, "existentes": 0, "errores": 0}

    def crear(ruta, datos, etiqueta):
        r = http.post(API + ruta, headers=h, json=datos)
        if r.status_code == 201:
            conteo["creados"] += 1
            print(f"  + {etiqueta}")
            return r.json()
        if r.status_code == 409:
            conteo["existentes"] += 1
            print(f"  · {etiqueta} (ya existía)")
            return None
        conteo["errores"] += 1
        print(f"  ! {etiqueta} -> {r.status_code} {r.text[:200]}")
        return None

    try:
        sedes = {s["nombre"]: s["id"] for s in http.get(API + "/sedes", headers=h).json()}
        faltan = [s for s in (GALERIAS, MODELIA, ZONA_T) if s not in sedes]
        if faltan:
            print(f"✗ Faltan las sedes {faltan}. Corre primero scripts/seed.py.")
            return 1

        ya_cargado = any(p["codigo"] == "LIC-001" for p in http.get(API + "/productos", headers=h).json())

        print("→ Tipos de producto")
        for t in TIPOS:
            crear("/tipos-producto", t, t["nombre"])
        tipos = {t["nombre"]: t["id"] for t in http.get(API + "/tipos-producto", headers=h).json()}

        print("→ Proveedores")
        for p in PROVEEDORES:
            crear("/proveedores", p, p["nombre"])
        proveedores = {p["nombre"]: p["id"] for p in http.get(API + "/proveedores", headers=h).json()}

        print("→ Productos (quedan en las tres sedes)")
        for codigo, nombre, tipo, prov, compra, venta, minimo in PRODUCTOS:
            crear("/productos", {"codigo": codigo, "nombre": nombre, "tipo_producto_id": tipos[tipo],
                                 "proveedor_id": proveedores[prov], "valor_compra": compra,
                                 "valor_venta": venta, "stock_minimo": minimo}, f"{codigo} · {nombre}")

        if ya_cargado:
            print("· El inventario y los pedidos de la demo ya estaban cargados: no se repiten.")
        else:
            productos = {p["codigo"]: p for p in http.get(API + "/productos", headers=h).json()}
            prov_de = {codigo: prov for codigo, _, _, prov, *_ in PRODUCTOS}

            print("→ Compras de los productos nuevos (existencia distinta por sede)")
            factura = 4100
            for codigo, por_sede in EXISTENCIAS.items():
                for sede, cantidad in por_sede.items():
                    if cantidad <= 0:
                        continue
                    factura += 1
                    r = http.post(API + "/inventario/ingresos", headers=h, json={
                        "sede_id": sedes[sede], "producto_id": productos[codigo]["id"], "cantidad": cantidad,
                        "motivo": COMPRA[prov_de[codigo]] + str(factura)})
                    if r.status_code == 201:
                        conteo["creados"] += 1
                    else:
                        conteo["errores"] += 1
                        print(f"  ! ingreso {codigo} en {sede} -> {r.status_code} {r.text[:160]}")
            print(f"  + {factura - 4100} compras registradas")

            print("→ Ajustes por conteo físico")
            for sede, codigo, cantidad, motivo in AJUSTES:
                r = http.post(API + "/inventario/ajustes", headers=h, json={
                    "sede_id": sedes[sede], "producto_id": productos[codigo]["id"], "cantidad": cantidad,
                    "motivo": motivo})
                ok = r.status_code == 201
                conteo["creados" if ok else "errores"] += 1
                print(f"  {'+' if ok else '!'} {sede} · {codigo} {cantidad:+d} · {motivo}"
                      + ("" if ok else f" -> {r.status_code} {r.text[:120]}"))

            print("→ Pedidos (los toma el mesero) y facturas (las emite el cajero de cada sede)")
            for sede, pedidos in PEDIDOS.items():
                mesero = MESEROS[sede]
                lm = http.post("/api/auth/auth/login", json={"usuario": mesero, "password": MESERO_PASSWORD})
                if lm.status_code != 200:
                    print(f"  ! No se pudo entrar como {mesero} ({lm.status_code}): se omiten sus pedidos. "
                          "Si cambió la clave, pásala con -e MESERO_PASSWORD=...")
                    conteo["errores"] += 1
                    continue
                hm = {"Authorization": f"Bearer {lm.json()['access_token']}"}
                mesas = {m["numero"]: m["id"] for m in http.get(API + "/mesas", headers=hm).json()}
                for numero, lineas in pedidos:
                    r = http.post(API + "/pedidos", headers=hm, json={
                        "mesa_id": mesas[numero],
                        "lineas": [{"producto_id": productos[c]["id"], "cantidad": n} for c, n in lineas]})
                    if r.status_code in (200, 201):
                        conteo["creados"] += 1
                        p = r.json()
                        print(f"  + {sede} · mesa {numero} · pedido #{p['id']} · ${int(float(p['total'])):,}"
                              .replace(",", "."))
                    else:
                        conteo["errores"] += 1
                        print(f"  ! {sede} · mesa {numero} -> {r.status_code} {r.text[:160]}")
                # Pedidos que el cajero cobra de una vez (Sprints 3 y 4).
                cobrados = []
                for numero, lineas, medio, recibido in COBRADOS[sede]:
                    r = http.post(API + "/pedidos", headers=hm, json={
                        "mesa_id": mesas[numero],
                        "lineas": [{"producto_id": productos[c]["id"], "cantidad": n} for c, n in lineas]})
                    if r.status_code in (200, 201):
                        cobrados.append((numero, r.json()["id"], medio, recibido))
                    else:
                        conteo["errores"] += 1
                        print(f"  ! {sede} · mesa {numero} (para cobrar) -> {r.status_code} {r.text[:160]}")
                http.post("/api/auth/auth/logout", headers=hm)

                cajero = CAJEROS[sede]
                lc = http.post("/api/auth/auth/login", json={"usuario": cajero, "password": CAJERO_PASSWORD})
                if lc.status_code != 200:
                    print(f"  ! No se pudo entrar como {cajero} ({lc.status_code}): no se cobran sus "
                          "pedidos. Si cambió la clave, pásala con -e CAJERO_PASSWORD=...")
                    conteo["errores"] += 1
                    continue
                hc = {"Authorization": f"Bearer {lc.json()['access_token']}"}
                for numero, pedido_id, medio, recibido in cobrados:
                    cuerpo = {"pedido_id": pedido_id, "medio_pago": medio}
                    if recibido is not None:
                        cuerpo["valor_recibido"] = recibido
                    r = http.post(API + "/facturas", headers=hc, json=cuerpo)
                    if r.status_code == 201:
                        conteo["creados"] += 1
                        f = r.json()
                        cambio = f["cambio"]
                        vueltas = f" · vueltas ${int(float(cambio)):,}" if cambio is not None else ""
                        print(f"  + {sede} · mesa {numero} · factura {f['numero_formateado']} · {medio} · "
                              f"${int(float(f['total'])):,}{vueltas}".replace(",", "."))
                    else:
                        conteo["errores"] += 1
                        print(f"  ! factura {sede} · mesa {numero} -> {r.status_code} {r.text[:160]}")
                http.post("/api/auth/auth/logout", headers=hc)
    finally:
        http.post("/api/auth/auth/logout", headers=h)

    print(f"✓ Listo. {conteo['creados']} registros nuevos, {conteo['existentes']} ya existían, "
          f"{conteo['errores']} errores.")
    return 1 if conteo["errores"] else 0


if __name__ == "__main__":
    sys.exit(main())
