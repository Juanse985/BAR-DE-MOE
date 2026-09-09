"""Modelo de datos del parametrizacion-service — M2 del tablero.

Entidades: sedes, mesas, tipos de producto, proveedores y productos.
El catálogo de productos se gestiona POR SEDE, tal como quedó en el tablero.
"""
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from barmoe_common.auditoria import Auditoria  # noqa: F401  (crea la tabla auditoria)
from barmoe_common.db import Base


def ahora_utc() -> datetime:
    return datetime.now(UTC)


ESTADOS_MESA = ("LIBRE", "OCUPADA")


class Sede(Base):
    __tablename__ = "sedes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    direccion: Mapped[str | None] = mapped_column(String(200))
    telefono: Mapped[str | None] = mapped_column(String(30))
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
    descripcion: Mapped[str | None] = mapped_column(String(200))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)


class Proveedor(Base):
    __tablename__ = "proveedores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nit: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    nombre: Mapped[str] = mapped_column(String(120), index=True)
    contacto: Mapped[str | None] = mapped_column(String(120))
    telefono: Mapped[str | None] = mapped_column(String(30))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)


class Producto(Base):
    """Catálogo por sede: el mismo código puede existir en varias sedes."""

    __tablename__ = "productos"
    __table_args__ = (UniqueConstraint("sede_id", "codigo", name="uq_producto_por_sede"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    codigo: Mapped[str] = mapped_column(String(30), index=True)
    nombre: Mapped[str] = mapped_column(String(120), index=True)
    sede_id: Mapped[int] = mapped_column(ForeignKey("sedes.id"), index=True)
    tipo_producto_id: Mapped[int] = mapped_column(ForeignKey("tipos_producto.id"), index=True)
    proveedor_id: Mapped[int] = mapped_column(ForeignKey("proveedores.id"), index=True)
    valor_compra: Mapped[float] = mapped_column(Numeric(12, 2))
    valor_venta: Mapped[float] = mapped_column(Numeric(12, 2))
    activo: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora_utc)

    sede: Mapped[Sede] = relationship()
    tipo: Mapped[TipoProducto] = relationship()
    proveedor: Mapped[Proveedor] = relationship()
