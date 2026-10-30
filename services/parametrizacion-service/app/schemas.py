"""Contratos del parametrizacion-service."""
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

EstadoMesa = Literal["LIBRE", "OCUPADA"]
EstadoPedido = Literal["ABIERTO", "CERRADO"]


class Base(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Actualizar(BaseModel):
    """H-01: un campo que no se puede editar responde 422 en vez de ignorarse en silencio."""

    model_config = ConfigDict(extra="forbid")


def _motivo_obligatorio(valor: str) -> str:
    valor = (valor or "").strip()
    if len(valor) < 3:
        raise ValueError("A reason is required (at least 3 characters).")
    return valor


# ---------------------------------------------------------------- Sedes
class SedeCrear(BaseModel):
    nombre: str = Field(min_length=3, max_length=120, examples=["Bar de Moe · Centro"])
    direccion: str | None = Field(default=None, max_length=200)
    telefono: str | None = Field(default=None, max_length=30)


class SedeActualizar(Actualizar):
    nombre: str | None = Field(default=None, min_length=3, max_length=120)
    direccion: str | None = None
    telefono: str | None = None
    activa: bool | None = None


class SedeSalida(Base):
    id: int
    nombre: str
    direccion: str | None
    telefono: str | None
    activa: bool


# ---------------------------------------------------------------- Mesas
class MesaCrear(BaseModel):
    sede_id: int
    numero: int = Field(gt=0, examples=[1])
    capacidad: int = Field(default=4, gt=0, le=30)


class MesaActualizar(Actualizar):
    capacidad: int | None = Field(default=None, gt=0, le=30)
    estado: EstadoMesa | None = None
    activa: bool | None = None


class MesaSalida(Base):
    id: int
    sede_id: int
    numero: int
    capacidad: int
    estado: EstadoMesa
    activa: bool


# ------------------------------------------------------- Tipos de producto
class TipoProductoCrear(BaseModel):
    nombre: str = Field(min_length=2, max_length=80, examples=["Cerveza"])
    descripcion: str | None = Field(default=None, max_length=200)


class TipoProductoActualizar(Actualizar):
    nombre: str | None = Field(default=None, min_length=2, max_length=80)
    descripcion: str | None = None
    activo: bool | None = None


class TipoProductoSalida(Base):
    id: int
    nombre: str
    descripcion: str | None
    activo: bool


# ---------------------------------------------------------- Proveedores
class ProveedorCrear(BaseModel):
    nit: str = Field(min_length=5, max_length=20, examples=["900123456-1"])
    nombre: str = Field(min_length=3, max_length=120, examples=["Distribuidora Duff"])
    contacto: str | None = Field(default=None, max_length=120)
    telefono: str | None = Field(default=None, max_length=30)


class ProveedorActualizar(Actualizar):
    nombre: str | None = Field(default=None, min_length=3, max_length=120)
    contacto: str | None = None
    telefono: str | None = None
    activo: bool | None = None


class ProveedorSalida(Base):
    id: int
    nit: str
    nombre: str
    contacto: str | None
    telefono: str | None
    activo: bool


# ------------------------------------------------------------- Productos
class ProductoCrear(BaseModel):
    """El producto se crea una vez y queda en el inventario de TODAS las sedes activas.

    `sede_id` ya no se pide. Si un cliente viejo lo manda, se ignora para no
    romper la pantalla mientras Felipe la actualiza.
    """

    codigo: str = Field(min_length=2, max_length=30, examples=["CERV-001"])
    nombre: str = Field(min_length=3, max_length=120, examples=["Cerveza Duff 330ml"])
    tipo_producto_id: int
    proveedor_id: int
    valor_compra: Decimal = Field(ge=0, examples=["2500"])
    valor_venta: Decimal = Field(ge=0, examples=["6000"])
    stock_minimo: int = Field(default=5, ge=0, le=100_000)

    @field_validator("codigo")
    @classmethod
    def codigo_en_mayusculas(cls, valor: str) -> str:
        return valor.strip().upper()

    @model_validator(mode="after")
    def venta_mayor_que_compra(self):
        # El reporte de M6 calcula la ganancia como venta - compra: vender por
        # debajo del costo dejaría márgenes negativos sin que nadie se entere.
        if self.valor_venta < self.valor_compra:
            raise ValueError(
                f"Sale price ({self.valor_venta}) cannot be lower than purchase price "
                f"({self.valor_compra})."
            )
        return self


class ProductoActualizar(Actualizar):
    nombre: str | None = Field(default=None, min_length=3, max_length=120)
    tipo_producto_id: int | None = None
    proveedor_id: int | None = None
    valor_compra: Decimal | None = Field(default=None, ge=0)
    valor_venta: Decimal | None = Field(default=None, ge=0)


class ProductoSalida(Base):
    """Datos globales del producto. Si se consulta con sede, trae su existencia ahí."""

    id: int
    codigo: str
    nombre: str
    tipo_producto_id: int
    proveedor_id: int
    valor_compra: Decimal
    valor_venta: Decimal
    activo: bool
    sede_id: int | None = None
    existencia: int | None = None
    activo_en_sede: bool | None = None


class ProductoCargaError(BaseModel):
    fila: int
    mensaje: str


class ProductoCargaResultado(BaseModel):
    creados: int
    errores: list[ProductoCargaError]


# ------------------------------------------------------- Inventario (M3)
class InventarioSalida(BaseModel):
    producto_id: int
    codigo: str
    nombre: str
    tipo_producto: str
    sede_id: int
    existencia: int
    stock_minimo: int
    agotado: bool
    bajo_minimo: bool
    activo: bool


class IngresoInventario(BaseModel):
    """CU-15: suma existencia. HU-021 criterio 2: cantidad y motivo obligatorios."""

    sede_id: int
    producto_id: int
    cantidad: int = Field(gt=0, le=100_000)
    motivo: str = Field(max_length=200, examples=["Purchase from Bavaria, invoice 1234"])

    _motivo = field_validator("motivo")(_motivo_obligatorio)


class AjusteInventario(BaseModel):
    """CU-16: corrige la existencia. `cantidad` con signo: -3 resta tres, +2 suma dos."""

    sede_id: int
    producto_id: int
    cantidad: int = Field(ge=-100_000, le=100_000, examples=[-3])
    motivo: str = Field(max_length=200, examples=["Physical count: 3 broken bottles"])
    stock_minimo: int | None = Field(default=None, ge=0, le=100_000)

    _motivo = field_validator("motivo")(_motivo_obligatorio)

    @field_validator("cantidad")
    @classmethod
    def distinta_de_cero(cls, valor: int) -> int:
        if valor == 0:
            raise ValueError("The adjustment quantity cannot be 0.")
        return valor


class MovimientoSalida(Base):
    id: int
    producto_id: int
    sede_id: int
    tipo: str
    cantidad: int
    existencia_anterior: int
    existencia_resultante: int
    motivo: str
    usuario: str | None
    pedido_id: int | None
    creado_en: datetime


class ConciliacionSalida(BaseModel):
    """Algoritmo 4: la existencia guardada debe ser igual a la suma de sus movimientos."""

    producto_id: int
    sede_id: int
    movimientos: int
    existencia_registrada: int
    existencia_iterativa: int
    existencia_recursiva: int | None
    cuadra: bool
    mensaje: str


class LoteSugerido(BaseModel):
    producto_id: int
    codigo: str
    nombre: str
    existencia: int
    unidades: int
    costo: int
    ganancia_esperada: int


class SugerenciaCompraSalida(BaseModel):
    """Algoritmos 1, 2 y 3: mochila con el presupuesto como capacidad."""

    sede_id: int
    presupuesto: int
    metodo: str
    escala_mcd: int
    costo_total: int
    ganancia_esperada: int
    sobrante: int
    lotes: list[LoteSugerido]
    descartados: list[LoteSugerido]


# ---------------------------------------------------------- Pedidos (M4)
class LineaCrear(BaseModel):
    producto_id: int
    cantidad: int = Field(gt=0, le=500)


class PedidoAbrir(BaseModel):
    """CU-20: se abre sobre una mesa; opcionalmente con los primeros productos."""

    mesa_id: int
    lineas: list[LineaCrear] = Field(default_factory=list, max_length=100)


class LineasAgregar(BaseModel):
    """CU-21: todas las líneas entran o ninguna (una sola transacción, CU-18)."""

    lineas: list[LineaCrear] = Field(min_length=1, max_length=100)


class LineaSalida(Base):
    id: int
    producto_id: int
    codigo: str
    nombre: str
    cantidad: int
    precio_unitario: Decimal
    subtotal: Decimal


class PedidoSalida(Base):
    id: int
    sede_id: int
    mesa_id: int
    mesero_id: int
    mesero: str
    estado: EstadoPedido
    total: Decimal
    creado_en: datetime
    cerrado_en: datetime | None
    lineas: list[LineaSalida]


class CambioSalida(BaseModel):
    """Algoritmo 5 (voraz): vueltas en billetes y monedas colombianos."""

    pedido_id: int
    total: int
    pagado: int
    cambio: int
    piezas: list[dict]
    total_piezas: int
