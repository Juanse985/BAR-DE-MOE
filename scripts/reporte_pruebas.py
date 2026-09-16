#!/usr/bin/env python3
"""Reporte consolidado de pruebas para la Sprint Review.

Corre pytest con cobertura en los cuatro componentes, junta los resultados y
escribe `docs/evidencias/reporte-pruebas.md`. Si existen las evidencias de la
prueba de humo y del RNF-02, las resume también.

Uso:
    python scripts/reporte_pruebas.py            # desde la raíz del repositorio
    make reporte
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
EVIDENCIAS = RAIZ / "docs" / "evidencias"
UMBRAL_COBERTURA = 70

COMPONENTES = [
    ("libs/common", "barmoe_common", "Librería común"),
    ("services/auth-service", "app", "auth-service (M1)"),
    ("services/parametrizacion-service", "app", "parametrizacion-service (M2)"),
    ("gateway", "app", "API Gateway"),
]

# Qué requisito cubre cada prueba, según su archivo o su nombre.
REQUISITOS = [
    (r"hu025|rnf12", "HU-025 · RNF-12 Trazabilidad"),
    (r"hu026|rnf02", "HU-026 · RNF-02 Tiempo de respuesta"),
    (r"hu027|rnf08", "HU-027 · RNF-08 Cifrado"),
    (r"test_c1_|rnf05", "HU-028 · C-1 Control de acceso"),
    (r"test_c3_", "HU-028 · C-3 Inyección"),
    (r"test_c4_|rnf03|rnf09|rnf10", "HU-028 · C-4 Autenticación"),
    (r"rnf07", "RNF-07 Gestión de contraseñas"),
]


def correr(carpeta: str, paquete: str, tmp: Path) -> dict:
    junit = tmp / f"{paquete}-{carpeta.replace('/', '_')}.xml"
    cobertura = tmp / f"cov-{carpeta.replace('/', '_')}.json"
    comando = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-W", "ignore",
               f"--junitxml={junit}", f"--cov={paquete}", f"--cov-report=json:{cobertura}"]
    proceso = subprocess.run(comando, cwd=RAIZ / carpeta, capture_output=True, text=True)

    casos = []
    if junit.exists():
        for caso in ET.parse(junit).getroot().iter("testcase"):
            estado, detalle = "OK", ""
            for hijo in caso:
                if hijo.tag == "failure" or hijo.tag == "error":
                    estado, detalle = "FALLO", (hijo.get("message") or "")[:200]
                elif hijo.tag == "skipped":
                    mensaje = hijo.get("message") or ""
                    if hijo.get("type") == "pytest.xfail" or "xfail" in mensaje.lower():
                        estado = "DEFECTO_ABIERTO"
                        detalle = re.sub(r"^.*?(DEF-\d+)", r"\1", mensaje)
                    else:
                        estado, detalle = "OMITIDA", mensaje
            casos.append({"nombre": caso.get("name"), "archivo": caso.get("classname", ""),
                          "estado": estado, "detalle": detalle})

    porcentaje = None
    if cobertura.exists():
        porcentaje = json.loads(cobertura.read_text())["totals"]["percent_covered"]
    return {"codigo": proceso.returncode, "casos": casos, "cobertura": porcentaje,
            "salida": proceso.stdout[-1500:] + proceso.stderr[-1500:]}


def requisito_de(caso: dict) -> str | None:
    texto = f"{caso['archivo']} {caso['nombre']}".lower()
    for patron, requisito in REQUISITOS:
        if re.search(patron, texto):
            return requisito
    return None


def main() -> int:
    EVIDENCIAS.mkdir(parents=True, exist_ok=True)
    resultados = {}
    with tempfile.TemporaryDirectory() as tmp:
        for carpeta, paquete, nombre in COMPONENTES:
            print(f"→ {nombre} ...", flush=True)
            resultados[nombre] = correr(carpeta, paquete, Path(tmp))

    todos = [c for r in resultados.values() for c in r["casos"]]
    total = Counter(c["estado"] for c in todos)
    hay_fallos = any(r["codigo"] not in (0,) for r in resultados.values()) or total["FALLO"] > 0
    bajo_umbral = [n for n, r in resultados.items() if (r["cobertura"] or 0) < UMBRAL_COBERTURA]

    lineas = [
        "# Reporte de pruebas · Sprint 1",
        "",
        f"Generado el {datetime.now():%Y-%m-%d %H:%M} con `python scripts/reporte_pruebas.py`.",
        "",
        "## Resumen",
        "",
        f"- **Pruebas ejecutadas:** {len(todos)}",
        f"- **En verde:** {total['OK']}",
        f"- **Fallidas:** {total['FALLO']}",
        f"- **Defectos abiertos documentados (xfail):** {total['DEFECTO_ABIERTO']}",
        f"- **Umbral de cobertura acordado:** {UMBRAL_COBERTURA} %",
        f"- **Veredicto:** {'❌ HAY FALLOS' if hay_fallos or bajo_umbral else '✅ SUITE EN VERDE'}",
        "",
        "| Componente | Pruebas | Verde | Fallidas | Defectos abiertos | Cobertura |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for nombre, r in resultados.items():
        c = Counter(x["estado"] for x in r["casos"])
        cob = f"{r['cobertura']:.1f} %" if r["cobertura"] is not None else "-"
        marca = "" if (r["cobertura"] or 0) >= UMBRAL_COBERTURA else " ⚠️"
        lineas.append(f"| {nombre} | {len(r['casos'])} | {c['OK']} | {c['FALLO']} | "
                      f"{c['DEFECTO_ABIERTO']} | {cob}{marca} |")

    lineas += ["", "## Cobertura por requisito", "",
               "| Requisito | Pruebas en verde | Defectos abiertos |", "|---|---:|---:|"]
    por_req: dict[str, Counter] = {}
    for caso in todos:
        req = requisito_de(caso)
        if req:
            por_req.setdefault(req, Counter())[caso["estado"]] += 1
    for _, req in REQUISITOS:
        if req in por_req:
            lineas.append(f"| {req} | {por_req[req]['OK']} | {por_req[req]['DEFECTO_ABIERTO']} |")

    abiertos = sorted({c["detalle"] for c in todos if c["estado"] == "DEFECTO_ABIERTO"})
    if abiertos:
        lineas += ["", "## Defectos abiertos", "",
                   "Cada uno tiene una prueba marcada `xfail(strict=True)`: cuando se corrija, la prueba",
                   "pasará a verde y pytest obligará a quitar la marca. Detalle y responsable en",
                   "`docs/07-informe-qa-sprint-1.md`.", ""]
        lineas += [f"- {d}" for d in abiertos]

    fallidas = [c for c in todos if c["estado"] == "FALLO"]
    if fallidas:
        lineas += ["", "## Pruebas fallidas", ""]
        lineas += [f"- `{c['archivo']}::{c['nombre']}` — {c['detalle']}" for c in fallidas]

    humo = EVIDENCIAS / "prueba-humo.json"
    rnf02 = EVIDENCIAS / "rnf02-tiempo-respuesta.json"
    if humo.exists() or rnf02.exists():
        lineas += ["", "## Evidencias contra la plataforma levantada", ""]
    if humo.exists():
        h = json.loads(humo.read_text(encoding="utf-8"))
        ok = sum(p["estado"] == "OK" for p in h["pasos"])
        lineas.append(f"- **Prueba de humo** ({h['inicio']}): {ok}/{len(h['pasos'])} pasos OK → "
                      f"{'✅ aprobada' if h['aprobado'] else '❌ con fallos'} · detalle en `prueba-humo.md`")
    if rnf02.exists():
        m = json.loads(rnf02.read_text(encoding="utf-8"))
        peor = max(m["operaciones"], key=lambda o: o["p95_ms"] or 0)
        lineas.append(f"- **RNF-02** ({m['fecha']}): {'✅ cumple' if m['aprobado'] else '❌ no cumple'}; "
                      f"el p95 más alto fue {peor['p95_ms']} ms en «{peor['operacion']}» "
                      f"· detalle en `rnf02-tiempo-respuesta.md`")

    destino = EVIDENCIAS / "reporte-pruebas.md"
    destino.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print(f"\n{len(todos)} pruebas · {total['OK']} verdes · {total['FALLO']} fallidas · "
          f"{total['DEFECTO_ABIERTO']} defectos abiertos")
    print(f"Reporte: {destino.relative_to(RAIZ)}")
    for nombre, r in resultados.items():
        if r["codigo"] != 0:
            print(f"\n--- {nombre} (código {r['codigo']}) ---\n{r['salida']}")
    return 1 if hay_fallos or bajo_umbral else 0


if __name__ == "__main__":
    sys.exit(main())
