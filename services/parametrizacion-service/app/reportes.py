"""M6 Reportería · HU-024 (Juan David Tovío Montes).

Lógica pura del reporte de ventas y ganancia: no toca la base de datos ni
FastAPI, para poder probarla sola. `main.py` trae las líneas facturadas y
este módulo las agrupa, las ordena (algoritmo 6, merge sort) y las exporta.

Reglas del tablero:
- c5 Columnas: fecha, código, nombre, cantidad vendida, valor de compra,
  valor de venta, ganancia y sede.
- c6 ganancia = (valor de venta - valor de compra) x cantidad vendida.
- c7 El Excel sale de las MISMAS filas que ve el usuario en pantalla.
"""
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta, timezone
from decimal import Decimal
from io import BytesIO

from . import algoritmos

# Colombia no tiene horario de verano: UTC-5 todo el año. Se usa un desfase
# fijo para no depender de que la imagen de Docker traiga la base tzdata.
ZONA_BAR = timezone(timedelta(hours=-5), "America/Bogota")

ORDENES = ("fecha", "ganancia", "cantidad")
MAXIMO_DIAS = 366

COLUMNAS = ("Fecha", "Código", "Producto", "Cantidad vendida", "Valor de compra",
            "Valor de venta", "Ganancia", "Sede")


@dataclass(frozen=True)
class LineaVendida:
    """Una línea de factura tal como sale de la base de datos."""

    emitida_en: datetime
    sede_id: int
    sede: str
    producto_id: int
    codigo: str
    nombre: str
    cantidad: int
    valor_compra: Decimal
    valor_venta: Decimal


@dataclass
class Fila:
    fecha: date
    codigo: str
    nombre: str
    cantidad: int
    valor_compra: Decimal
    valor_venta: Decimal
    ganancia: Decimal
    sede_id: int
    sede: str


def fecha_local(momento: datetime) -> date:
    """La fecha del bar (Bogotá). SQLite devuelve fechas sin zona: se asumen UTC."""
    if momento.tzinfo is None:
        momento = momento.replace(tzinfo=UTC)
    return momento.astimezone(ZONA_BAR).date()


def rango_utc(desde: date, hasta: date) -> tuple[datetime, datetime]:
    """[desde 00:00, hasta+1 00:00) en hora de Bogotá, convertido a UTC para la consulta."""
    inicio = datetime.combine(desde, datetime.min.time(), tzinfo=ZONA_BAR)
    fin = datetime.combine(hasta + timedelta(days=1), datetime.min.time(), tzinfo=ZONA_BAR)
    return inicio.astimezone(UTC), fin.astimezone(UTC)


def hoy_local() -> date:
    return datetime.now(ZONA_BAR).date()


def agrupar(lineas: Iterable[LineaVendida]) -> list[Fila]:
    """Suma la cantidad por día, sede, producto y precios.

    Si el precio de un producto cambió en el mismo día, salen dos filas: así
    la ganancia de cada una sigue siendo (venta - compra) x cantidad (c6).
    """
    grupos: dict[tuple, Fila] = {}
    for linea in lineas:
        compra, venta = Decimal(linea.valor_compra), Decimal(linea.valor_venta)
        clave = (fecha_local(linea.emitida_en), linea.sede_id, linea.producto_id, compra, venta)
        fila = grupos.get(clave)
        if fila is None:
            fila = grupos[clave] = Fila(fecha=clave[0], codigo=linea.codigo, nombre=linea.nombre,
                                        cantidad=0, valor_compra=compra, valor_venta=venta,
                                        ganancia=Decimal(0), sede_id=linea.sede_id, sede=linea.sede)
        fila.cantidad += linea.cantidad
    for fila in grupos.values():
        fila.ganancia = (fila.valor_venta - fila.valor_compra) * fila.cantidad  # c6
    return list(grupos.values())


def ordenar(filas: list[Fila], orden: str) -> list[Fila]:
    """Algoritmo 6 (merge sort, estable).

    - fecha:    fecha ascendente; dentro del día, por sede y por código.
    - ganancia: de la que más deja a la que menos; a igual ganancia, por fecha.
    - cantidad: de la más vendida a la menos; a igual cantidad, por fecha.
    """
    base = algoritmos.ordenar_mezcla(filas, clave=lambda f: (f.fecha, f.sede, f.codigo))
    if orden == "ganancia":
        return algoritmos.ordenar_mezcla(base, clave=lambda f: f.ganancia, descendente=True)
    if orden == "cantidad":
        return algoritmos.ordenar_mezcla(base, clave=lambda f: f.cantidad, descendente=True)
    return base


def totales_por_sede(filas: list[Fila]) -> list[dict]:
    totales: dict[int, dict] = {}
    for fila in filas:
        t = totales.setdefault(fila.sede_id, {"sede_id": fila.sede_id, "sede": fila.sede, "cantidad": 0,
                                              "ventas": Decimal(0), "ganancia": Decimal(0)})
        t["cantidad"] += fila.cantidad
        t["ventas"] += fila.valor_venta * fila.cantidad
        t["ganancia"] += fila.ganancia
    return algoritmos.ordenar_mezcla(list(totales.values()), clave=lambda t: t["sede"])


def a_excel(filas: list[Fila], *, desde: date, hasta: date, alcance: str, usuario: str) -> bytes:
    """c7: el archivo lleva exactamente las filas recibidas, ni una más.

    Se importa openpyxl aquí adentro para que el resto del servicio arranque
    aunque la librería no esté instalada en una máquina de desarrollo.
    """
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter

    libro = Workbook()
    hoja = libro.active
    hoja.title = "Ventas"

    hoja.append(["Bar de Moe · Reporte de ventas y ganancia (HU-024)"])
    hoja.append([f"Desde {desde.isoformat()} hasta {hasta.isoformat()} · Sedes: {alcance}"])
    hoja.append([f"Generado por {usuario} el {datetime.now(ZONA_BAR):%Y-%m-%d %H:%M} (hora de Bogotá)"])
    hoja.append([])
    hoja["A1"].font = Font(bold=True, size=14)

    hoja.append(list(COLUMNAS))
    fila_encabezado = hoja.max_row
    relleno = PatternFill("solid", fgColor="1F3864")
    for celda in hoja[fila_encabezado]:
        celda.font = Font(bold=True, color="FFFFFF")
        celda.fill = relleno
        celda.alignment = Alignment(horizontal="center")

    for f in filas:
        hoja.append([f.fecha, f.codigo, f.nombre, f.cantidad, float(f.valor_compra),
                     float(f.valor_venta), float(f.ganancia), f.sede])

    primera, ultima = fila_encabezado + 1, hoja.max_row
    for n in range(primera, ultima + 1):
        hoja.cell(n, 1).number_format = "yyyy-mm-dd"
        for col in (5, 6, 7):
            hoja.cell(n, col).number_format = '"$"#,##0'

    total = ultima + 1
    hoja.cell(total, 1, "TOTAL").font = Font(bold=True)
    if filas:
        hoja.cell(total, 4, f"=SUM(D{primera}:D{ultima})")
        hoja.cell(total, 7, f"=SUM(G{primera}:G{ultima})")
    else:
        hoja.cell(total, 4, 0)
        hoja.cell(total, 7, 0)
    hoja.cell(total, 4).font = Font(bold=True)
    hoja.cell(total, 7).font = Font(bold=True)
    hoja.cell(total, 7).number_format = '"$"#,##0'

    for i, ancho in enumerate((12, 12, 32, 16, 16, 16, 16, 26), start=1):
        hoja.column_dimensions[get_column_letter(i)].width = ancho
    hoja.freeze_panes = hoja.cell(primera, 1)

    salida = BytesIO()
    libro.save(salida)
    return salida.getvalue()
