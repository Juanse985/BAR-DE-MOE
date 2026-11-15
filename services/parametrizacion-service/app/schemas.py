"""Contratos del parametrizacion-service."""
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

EstadoMesa = Literal["LIBRE", "OCUPADA"]
TipoMovimientoInventario = Literal["ENTRADA", "SALIDA", "AJUSTE"]
EstadoPedido = Literal["ABIERTO", "ENTREGADO", "CERRADO", "CANCELADO"]
MedioPago = Literal[
    "EFECTIVO",
    "TARJETA_CREDITO",
    "TARJETA_DEBITO",
    "TARJETA",
    "TRANSFERENCIA",
    "MIXTO",
]


class Base(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------- Sedes
class SedeCrear(BaseModel):
    nombre: str = Field(min_length=3, max_length=120, examples=["Bar de Moe · Centro"])
    direccion: str | None = Field(default=None, max_length=200)
    telefono: str | None = Field(default=None, max_length=30)


class SedeActualizar(BaseModel):
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


class MesaActualizar(BaseModel):
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


class TipoProductoActualizar(BaseModel):
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


class ProveedorActualizar(BaseModel):
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
    codigo: str = Field(min_length=2, max_length=30, examples=["CERV-001"])
    nombre: str = Field(min_length=3, max_length=120, examples=["Cerveza Duff 330ml"])
    sede_id: int | None = None
    tipo_producto_id: int
    proveedor_id: int
    valor_compra: Decimal = Field(ge=0, examples=["2500"])
    valor_venta: Decimal = Field(ge=0, examples=["6000"])
    stock: int = Field(default=24, ge=0)
    stock_minimo: int = Field(default=5, ge=0)

    @model_validator(mode="after")
    def venta_mayor_que_compra(self):
        # El reporte de M6 calcula la ganancia como venta - compra: vender por
        # debajo del costo dejaría márgenes negativos sin que nadie se entere.
        if self.valor_venta < self.valor_compra:
            raise ValueError("El valor de venta no puede ser menor que el valor de compra.")
        return self


class ProductoActualizar(BaseModel):
    nombre: str | None = Field(default=None, min_length=3, max_length=120)
    tipo_producto_id: int | None = None
    proveedor_id: int | None = None
    valor_compra: Decimal | None = Field(default=None, ge=0)
    valor_venta: Decimal | None = Field(default=None, ge=0)
    stock: int | None = Field(default=None, ge=0)
    stock_minimo: int | None = Field(default=None, ge=0)


class ProductoSalida(Base):
    id: int
    codigo: str
    nombre: str
    sede_id: int
    tipo_producto_id: int
    proveedor_id: int
    valor_compra: Decimal
    valor_venta: Decimal
    stock: int = 24
    stock_minimo: int = 5
    activo: bool


class ProductoCargaError(BaseModel):
    fila: int
    mensaje: str


class ProductoCargaResultado(BaseModel):
    creados: int
    errores: list[ProductoCargaError]


# ------------------------------------------- Sprint 2: Inventario y Pedidos
class InventarioAjuste(BaseModel):
    tipo: TipoMovimientoInventario = "ENTRADA"
    cantidad: int = Field(ge=0)
    stock_minimo: int | None = Field(default=None, ge=0)
    motivo: str | None = Field(default=None, max_length=150)


class MesaEstadoActualizar(BaseModel):
    estado: EstadoMesa


class PedidoItemCrear(BaseModel):
    producto_id: int
    cantidad: int = Field(gt=0, le=500)


class PedidoCrear(BaseModel):
    mesa_id: int
    mesero_nombre: str | None = Field(default=None, max_length=120)
    observaciones: str | None = Field(default=None, max_length=250)
    items: list[PedidoItemCrear] = Field(min_length=1)


class PedidoEstadoActualizar(BaseModel):
    estado: EstadoPedido


class PedidoDetalleSalida(Base):
    id: int
    producto_id: int
    codigo_producto: str
    nombre_producto: str
    cantidad: int
    precio_unitario: Decimal
    subtotal: Decimal


class PedidoSalida(Base):
    id: int
    sede_id: int
    mesa_id: int
    usuario_id: int | None
    mesero: str
    estado: EstadoPedido
    observaciones: str | None
    total: Decimal
    creado_en: datetime
    detalles: list[PedidoDetalleSalida] = []


# ------------------------------------------- Sprint 3: Facturación y Pagos
class FacturaCrear(BaseModel):
    pedido_id: int
    medio_pago: MedioPago = "EFECTIVO"
    propina: Decimal = Field(default=Decimal("0"), ge=0)
    monto_recibido: Decimal | None = Field(default=None, ge=0)
    cliente_nombre: str = Field(default="Consumidor Final", max_length=120)
    cliente_documento: str = Field(default="222222222222", max_length=40)
    cajero_nombre: str | None = Field(default=None, max_length=120)
    observaciones: str | None = Field(default=None, max_length=250)


class FacturaSalida(Base):
    id: int
    numero_factura: str
    pedido_id: int
    sede_id: int
    mesa_id: int
    cajero: str
    cliente_nombre: str
    cliente_documento: str
    medio_pago: MedioPago
    subtotal: Decimal
    impuesto: Decimal
    propina: Decimal
    total: Decimal
    monto_recibido: Decimal
    cambio: Decimal
    observaciones: str | None
    creado_en: datetime
    detalles: list[PedidoDetalleSalida] = []


# ------------------------------------------- Sprint 4: Reportería (M6 · HU-016 & HU-024)
class ReporteResumenSalida(BaseModel):
    total_facturas: int
    unidades_vendidas: int
    subtotal_ventas: Decimal
    impuestos: Decimal
    propinas: Decimal
    total_facturado: Decimal
    costo_total: Decimal
    ganancia_neta: Decimal
    margen_porcentaje: float


class ReportePorSedeItem(BaseModel):
    sede_id: int
    sede_nombre: str
    total_facturas: int
    unidades_vendidas: int
    subtotal_ventas: Decimal
    total_facturado: Decimal
    costo_total: Decimal
    ganancia_neta: Decimal
    margen_porcentaje: float


class ReportePorMedioPagoItem(BaseModel):
    medio_pago: str
    total_facturas: int
    subtotal_ventas: Decimal
    propinas: Decimal
    total_facturado: Decimal


class ReportePorRolItem(BaseModel):
    rol: str
    responsable: str
    sede_id: int
    sede_nombre: str
    operaciones: int
    subtotal_ventas: Decimal
    ganancia_generada: Decimal


class ReportePorProductoItem(BaseModel):
    codigo: str
    nombre: str
    sede_id: int
    sede_nombre: str
    unidades_vendidas: int
    valor_compra_unitario: Decimal
    valor_venta_unitario: Decimal
    costo_total: Decimal
    subtotal_ventas: Decimal
    ganancia_neta: Decimal
    margen_porcentaje: float


class ReporteVentasSalida(BaseModel):
    perfil_consultante: str
    sede_filtrada: int | None
    resumen: ReporteResumenSalida
    por_sede: list[ReportePorSedeItem] = []
    por_medio_pago: list[ReportePorMedioPagoItem] = []
    por_rol: list[ReportePorRolItem] = []
    por_producto: list[ReportePorProductoItem] = []
    facturas: list[FacturaSalida] = []
