"""Modelo de datos del parametrizacion-service — M2, M3 y M4 del tablero.

Entidades: sedes, mesas, tipos de producto, proveedores, productos,
inventario por sede, movimientos de inventario y pedidos.

Sprint 2 (corrección del docente): el producto se crea UNA vez y queda para
todas las sedes; lo que depende de cada sede es el inventario
(`inventario_sede`). Inventario y pedidos viven en este servicio porque
descontar la existencia y registrar el pedido deben ocurrir en una sola
transacción (CU-18), y eso no se garantiza entre dos bases de datos.
"""
from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from barmoe_common.auditoria import Auditoria  # noqa: F401  (crea la tabla auditoria)
from barmoe_common.db import Base


def ahora_utc() -> datetime:
    return datetime.now(UTC)


ESTADOS_MESA = ("LIBRE", "OCUPADA")
ESTADOS_PEDIDO = ("ABIERTO", "CERRADO")  # HU-022 criterio 7
TIPOS_MOVIMIENTO = ("INGRESO", "AJUSTE", "VENTA")  # CU-32


class Sede(Base):
    __tablename__ = "sedes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    direccion: Mapped[str] = mapped_column(String(200), nullable=True)
    telefono: Mapped[str] = mapped_column(String(30), nullable=True)
    activa: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    creada_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora_utc)

    mesas: Mapped[list["Mesa"]] = relationship(back_populates="sede", cascade="all, delete-orphan")


class Mesa(Base):
    """Estado LIBRE/OCUPADA vive aquí; las transiciones son del Sprint 2 (M4)."""

    __tablename__ = "mesas"
    __table_args__ = (UniqueConstraint("sede_id", "numero", name="uq_mesa_por_sede"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sede_id: Mapped[int] = mapped_column(ForeignKey("sedes.id"), index=True)
    numero: Mapped[int] = mapped_column(Integer)
    capacidad: Mapped[int] = mapped_column(Integer, default=4)
    estado: Mapped[str] = mapped_column(String(10), default="LIBRE", index=True)
    activa: Mapped[bool] = mapped_column(Boolean, default=True)

    sede: Mapped[Sede] = relationship(back_populates="mesas")


class TipoProducto(Base):
    __tablename__ = "tipos_producto"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    descripcion: Mapped[str] = mapped_column(String(200), nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)


class Proveedor(Base):
    __tablename__ = "proveedores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nit: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    nombre: Mapped[str] = mapped_column(String(120), index=True)
    contacto: Mapped[str] = mapped_column(String(120), nullable=True)
    telefono: Mapped[str] = mapped_column(String(30), nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)


class Producto(Base):
    """Producto único para todas las sedes. El código no se repite (HU-020 v2.1)."""

    __tablename__ = "productos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    codigo: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    nombre: Mapped[str] = mapped_column(String(120), index=True)
    tipo_producto_id: Mapped[int] = mapped_column(ForeignKey("tipos_producto.id"), index=True)
    proveedor_id: Mapped[int] = mapped_column(ForeignKey("proveedores.id"), index=True)
    valor_compra: Mapped[float] = mapped_column(Numeric(12, 2))
    valor_venta: Mapped[float] = mapped_column(Numeric(12, 2))
    activo: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora_utc)

    tipo: Mapped[TipoProducto] = relationship()
    proveedor: Mapped[Proveedor] = relationship()


class InventarioSede(Base):
    """Existencia de un producto en una sede (HU-021 criterio 1).

    `activo` dice si el producto se vende en esa sede (columna "En la sede"
    del mockup de HU-020): inactivarlo aquí no afecta a las demás sedes.
    """

    __tablename__ = "inventario_sede"
    __table_args__ = (
        UniqueConstraint("producto_id", "sede_id", name="uq_inventario_producto_sede"),
        CheckConstraint("existencia >= 0", name="ck_existencia_no_negativa"),  # HU-021 criterio 3
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id"), index=True)
    sede_id: Mapped[int] = mapped_column(ForeignKey("sedes.id"), index=True)
    existencia: Mapped[int] = mapped_column(Integer, default=0)
    stock_minimo: Mapped[int] = mapped_column(Integer, default=5)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    actualizado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora_utc,
                                                     onupdate=ahora_utc)

    producto: Mapped[Producto] = relationship()
    sede: Mapped[Sede] = relationship()


class MovimientoInventario(Base):
    """Histórico inmutable de la existencia (HU-021 criterio 6, CU-32).

    `cantidad` lleva signo: +ingreso, -venta, ±ajuste. Nunca se edita ni se
    borra; una corrección se hace con otro ajuste.
    """

    __tablename__ = "movimientos_inventario"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id"), index=True)
    sede_id: Mapped[int] = mapped_column(ForeignKey("sedes.id"), index=True)
    tipo: Mapped[str] = mapped_column(String(10))
    cantidad: Mapped[int] = mapped_column(Integer)
    existencia_anterior: Mapped[int] = mapped_column(Integer)
    existencia_resultante: Mapped[int] = mapped_column(Integer)
    motivo: Mapped[str] = mapped_column(String(200))
    usuario_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    usuario: Mapped[str | None] = mapped_column(String(60), nullable=True)
    pedido_id: Mapped[int | None] = mapped_column(ForeignKey("pedidos.id"), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora_utc, index=True)


class Pedido(Base):
    """Pedido de una mesa (HU-022). Un solo pedido ABIERTO por mesa."""

    __tablename__ = "pedidos"
    __table_args__ = (
        # HU-022 criterio 3: la base de datos también impide dos pedidos abiertos en la misma mesa.
        Index("uq_un_pedido_abierto_por_mesa", "mesa_id", unique=True,
              sqlite_where=text("estado = 'ABIERTO'"), postgresql_where=text("estado = 'ABIERTO'")),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sede_id: Mapped[int] = mapped_column(ForeignKey("sedes.id"), index=True)
    mesa_id: Mapped[int] = mapped_column(ForeignKey("mesas.id"), index=True)
    mesero_id: Mapped[int] = mapped_column(Integer)
    mesero: Mapped[str] = mapped_column(String(60))
    estado: Mapped[str] = mapped_column(String(10), default="ABIERTO", index=True)
    total: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora_utc)
    cerrado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    mesa: Mapped[Mesa] = relationship()
    lineas: Mapped[list["PedidoLinea"]] = relationship(
        back_populates="pedido", cascade="all, delete-orphan", order_by="PedidoLinea.id"
    )


class PedidoLinea(Base):
    """Producto registrado en un pedido, con el precio de venta del momento."""

    __tablename__ = "pedido_lineas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pedido_id: Mapped[int] = mapped_column(ForeignKey("pedidos.id"), index=True)
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id"))
    codigo: Mapped[str] = mapped_column(String(30))
    nombre: Mapped[str] = mapped_column(String(120))
    cantidad: Mapped[int] = mapped_column(Integer)
    precio_unitario: Mapped[float] = mapped_column(Numeric(12, 2))
    subtotal: Mapped[float] = mapped_column(Numeric(12, 2))
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora_utc)

    pedido: Mapped[Pedido] = relationship(back_populates="lineas")
