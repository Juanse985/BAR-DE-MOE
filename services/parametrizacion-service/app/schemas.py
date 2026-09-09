"""Contratos del parametrizacion-service."""
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

EstadoMesa = Literal["LIBRE", "OCUPADA"]


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
    sede_id: int
    tipo_producto_id: int
    proveedor_id: int
    valor_compra: Decimal = Field(ge=0, examples=["2500"])
    valor_venta: Decimal = Field(ge=0, examples=["6000"])

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
    activo: bool | None = None


class ProductoSalida(Base):
    id: int
    codigo: str
    nombre: str
    sede_id: int
    tipo_producto_id: int
    proveedor_id: int
    valor_compra: Decimal
    valor_venta: Decimal
    activo: bool
