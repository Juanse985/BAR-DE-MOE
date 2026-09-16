"""parametrizacion-service — M2 Parametrización maestra.

Sedes, mesas, tipos de producto, proveedores y productos. Solo el perfil
ADMINISTRADOR puede escribir; cualquier perfil autenticado puede consultar.
Toda escritura queda registrada en la tabla de auditoría (RNF-12).
"""
from contextlib import asynccontextmanager
import csv
from io import StringIO

from fastapi import File, UploadFile

from fastapi import APIRouter, Depends, FastAPI
from sqlalchemy import select
from sqlalchemy.orm import Session

from barmoe_common.app import crear_app
from barmoe_common.auditoria import registrar
from barmoe_common.db import Base, crear_session_factory, dependencia_db
from barmoe_common.deps import UsuarioActual, construir_autenticacion
from barmoe_common.errors import ErrorApp

from .config import config
from .models import Mesa, Producto, Proveedor, Sede, TipoProducto
from .schemas import (
    MesaActualizar,
    MesaCrear,
    MesaSalida,
    ProductoActualizar,
    ProductoCargaError,
    ProductoCargaResultado,
    ProductoCrear,
    ProductoSalida,
    ProveedorActualizar,
    ProveedorCrear,
    ProveedorSalida,
    SedeActualizar,
    SedeCrear,
    SedeSalida,
    TipoProductoActualizar,
    TipoProductoCrear,
    TipoProductoSalida,
)

SessionLocal = crear_session_factory(config.DATABASE_URL)
get_db = dependencia_db(SessionLocal)
usuario_actual, requiere_perfil = construir_autenticacion(config.JWT_SECRET, config.JWT_ALGORITMO)
solo_admin = requiere_perfil("ADMINISTRADOR")


@asynccontextmanager
async def ciclo_de_vida(_: FastAPI):
    Base.metadata.create_all(bind=SessionLocal.engine)
    yield


app = crear_app(
    config,
    titulo="Bar de Moe · parametrizacion-service",
    descripcion="M2 · Parametrización maestra. DATHEON S.A.S.",
    lifespan=ciclo_de_vida,
)


# --------------------------------------------------------------- utilidades
def obtener_o_404(db: Session, modelo, entidad_id: int, etiqueta: str):
    fila = db.get(modelo, entidad_id)
    if fila is None:
        raise ErrorApp("NO_ENCONTRADO", f"No existe {etiqueta} con id {entidad_id}.", 404)
    return fila


def guardar(db: Session, fila, *, accion: str, entidad: str, usuario: UsuarioActual):
    db.add(fila)
    db.flush()
    registrar(db, accion=accion, entidad=entidad, entidad_id=fila.id,
            usuario_id=usuario.id, usuario=usuario.usuario, sede_id=usuario.sede_id)
    db.commit()
    db.refresh(fila)
    return fila


def aplicar_cambios(db: Session, fila, datos, *, entidad: str, usuario: UsuarioActual):
    cambios = datos.model_dump(exclude_unset=True)
    for campo, valor in cambios.items():
        setattr(fila, campo, valor)
    registrar(db, accion="ACTUALIZAR", entidad=entidad, entidad_id=fila.id,
            usuario_id=usuario.id, usuario=usuario.usuario, sede_id=usuario.sede_id,
            detalle=", ".join(cambios.keys()))
    db.commit()
    db.refresh(fila)
    return fila


# -------------------------------------------------------------------- SEDES
sedes = APIRouter(prefix="/sedes", tags=["sedes"])


@sedes.post("", response_model=SedeSalida, status_code=201, summary="Crear sede")
def crear_sede(datos: SedeCrear, usuario: UsuarioActual = Depends(solo_admin), db: Session = Depends(get_db)):
    if db.scalar(select(Sede).where(Sede.nombre == datos.nombre)):
        raise ErrorApp("SEDE_DUPLICADA", f"Ya existe la sede '{datos.nombre}'.", 409)
    return guardar(db, Sede(**datos.model_dump()), accion="CREAR", entidad="sedes", usuario=usuario)


@sedes.get("", response_model=list[SedeSalida], summary="Listar sedes")
def listar_sedes(_: UsuarioActual = Depends(usuario_actual), db: Session = Depends(get_db),
                solo_activas: bool = True):
    consulta = select(Sede)
    if solo_activas:
        consulta = consulta.where(Sede.activa.is_(True))
    return list(db.scalars(consulta.order_by(Sede.nombre)))


@sedes.get("/{sede_id}", response_model=SedeSalida, summary="Consultar sede")
def obtener_sede(sede_id: int, _: UsuarioActual = Depends(usuario_actual), db: Session = Depends(get_db)):
    return obtener_o_404(db, Sede, sede_id, "la sede")


@sedes.patch("/{sede_id}", response_model=SedeSalida, summary="Actualizar sede")
def actualizar_sede(sede_id: int, datos: SedeActualizar,
                    usuario: UsuarioActual = Depends(solo_admin), db: Session = Depends(get_db)):
    sede = obtener_o_404(db, Sede, sede_id, "la sede")

    if datos.activa is False and sede.activa:
        tiene_mesas_activas = db.scalar(
            select(Mesa.id).where(Mesa.sede_id == sede_id, Mesa.activa.is_(True)).limit(1)
        )
        tiene_productos_activos = db.scalar(
            select(Producto.id).where(Producto.sede_id == sede_id, Producto.activo.is_(True)).limit(1)
        )
        if tiene_mesas_activas or tiene_productos_activos:
            raise ErrorApp("SEDE_CON_RECURSOS_ACTIVOS",
                        "No se puede inactivar la sede: tiene mesas o productos activos.", 409)

    return aplicar_cambios(db, sede, datos, entidad="sedes", usuario=usuario)

# -------------------------------------------------------------------- MESAS
mesas = APIRouter(prefix="/mesas", tags=["mesas"])


@mesas.post("", response_model=MesaSalida, status_code=201, summary="Crear mesa")
def crear_mesa(datos: MesaCrear, usuario: UsuarioActual = Depends(solo_admin), db: Session = Depends(get_db)):
    obtener_o_404(db, Sede, datos.sede_id, "la sede")
    existe = db.scalar(select(Mesa).where(Mesa.sede_id == datos.sede_id, Mesa.numero == datos.numero))
    if existe:
        raise ErrorApp("MESA_DUPLICADA", f"La mesa {datos.numero} ya existe en esa sede.", 409)
    return guardar(db, Mesa(**datos.model_dump()), accion="CREAR", entidad="mesas", usuario=usuario)


@mesas.get("", response_model=list[MesaSalida], summary="Listar mesas")
def listar_mesas(_: UsuarioActual = Depends(usuario_actual), db: Session = Depends(get_db),
                sede_id: int | None = None, estado: str | None = None):
    consulta = select(Mesa)
    if sede_id is not None:
        consulta = consulta.where(Mesa.sede_id == sede_id)
    if estado:
        consulta = consulta.where(Mesa.estado == estado.upper())
    return list(db.scalars(consulta.order_by(Mesa.sede_id, Mesa.numero)))


@mesas.patch("/{mesa_id}", response_model=MesaSalida, summary="Actualizar mesa")
def actualizar_mesa(mesa_id: int, datos: MesaActualizar,
                    usuario: UsuarioActual = Depends(solo_admin), db: Session = Depends(get_db)):
    mesa = obtener_o_404(db, Mesa, mesa_id, "la mesa")
    return aplicar_cambios(db, mesa, datos, entidad="mesas", usuario=usuario)


# ------------------------------------------------------------ TIPOS PRODUCTO
tipos = APIRouter(prefix="/tipos-producto", tags=["tipos de producto"])


@tipos.post("", response_model=TipoProductoSalida, status_code=201, summary="Crear tipo de producto")
def crear_tipo(datos: TipoProductoCrear, usuario: UsuarioActual = Depends(solo_admin),
            db: Session = Depends(get_db)):
    if db.scalar(select(TipoProducto).where(TipoProducto.nombre == datos.nombre)):
        raise ErrorApp("TIPO_DUPLICADO", f"Ya existe el tipo '{datos.nombre}'.", 409)
    return guardar(db, TipoProducto(**datos.model_dump()), accion="CREAR",
                entidad="tipos_producto", usuario=usuario)


@tipos.get("", response_model=list[TipoProductoSalida], summary="Listar tipos de producto")
def listar_tipos(_: UsuarioActual = Depends(usuario_actual), db: Session = Depends(get_db)):
    return list(db.scalars(select(TipoProducto).order_by(TipoProducto.nombre)))

@tipos.patch("/{tipo_id}", response_model=TipoProductoSalida, summary="Actualizar tipo de producto")
def actualizar_tipo(tipo_id: int, datos: TipoProductoActualizar,
                    usuario: UsuarioActual = Depends(solo_admin), db: Session = Depends(get_db)):
    tipo = obtener_o_404(db, TipoProducto, tipo_id, "el tipo de producto")
    if datos.activo is False and tipo.activo:
        tiene_productos_activos = db.scalar(
            select(Producto.id).where(Producto.tipo_producto_id == tipo_id, Producto.activo.is_(True)).limit(1)
        )
        if tiene_productos_activos:
            raise ErrorApp("TIPO_CON_PRODUCTOS_ACTIVOS",
                        "No se puede inactivar el tipo: tiene productos activos asociados.", 409)
    return aplicar_cambios(db, tipo, datos, entidad="tipos_producto", usuario=usuario)


# -------------------------------------------------------------- PROVEEDORES
proveedores = APIRouter(prefix="/proveedores", tags=["proveedores"])


@proveedores.post("", response_model=ProveedorSalida, status_code=201, summary="Crear proveedor")
def crear_proveedor(datos: ProveedorCrear, usuario: UsuarioActual = Depends(solo_admin),
                    db: Session = Depends(get_db)):
    if db.scalar(select(Proveedor).where(Proveedor.nit == datos.nit)):
        raise ErrorApp("PROVEEDOR_DUPLICADO", f"Ya existe un proveedor con NIT {datos.nit}.", 409)
    return guardar(db, Proveedor(**datos.model_dump()), accion="CREAR",
                entidad="proveedores", usuario=usuario)


@proveedores.get("", response_model=list[ProveedorSalida], summary="Listar proveedores")
def listar_proveedores(_: UsuarioActual = Depends(usuario_actual), db: Session = Depends(get_db)):
    return list(db.scalars(select(Proveedor).order_by(Proveedor.nombre)))


@proveedores.patch("/{proveedor_id}", response_model=ProveedorSalida, summary="Actualizar proveedor")
def actualizar_proveedor(proveedor_id: int, datos: ProveedorActualizar,
                        usuario: UsuarioActual = Depends(solo_admin), db: Session = Depends(get_db)):
    proveedor = obtener_o_404(db, Proveedor, proveedor_id, "el proveedor")
    if datos.activo is False and proveedor.activo:
        tiene_productos_activos = db.scalar(
            select(Producto.id).where(Producto.proveedor_id == proveedor_id, Producto.activo.is_(True)).limit(1)
        )
        if tiene_productos_activos:
            raise ErrorApp("PROVEEDOR_CON_PRODUCTOS_ACTIVOS",
                        "No se puede inactivar el proveedor: tiene productos activos asociados.", 409)
    return aplicar_cambios(db, proveedor, datos, entidad="proveedores", usuario=usuario)

# ---------------------------------------------------------------- PRODUCTOS
productos = APIRouter(prefix="/productos", tags=["productos"])


@productos.post("", response_model=ProductoSalida, status_code=201, summary="Crear producto")
def crear_producto(datos: ProductoCrear, usuario: UsuarioActual = Depends(solo_admin),
                db: Session = Depends(get_db)):
    obtener_o_404(db, Sede, datos.sede_id, "la sede")
    obtener_o_404(db, TipoProducto, datos.tipo_producto_id, "el tipo de producto")
    obtener_o_404(db, Proveedor, datos.proveedor_id, "el proveedor")
    duplicado = db.scalar(
        select(Producto).where(Producto.sede_id == datos.sede_id, Producto.codigo == datos.codigo)
    )
    if duplicado:
        raise ErrorApp("PRODUCTO_DUPLICADO",
                    f"El código {datos.codigo} ya existe en esa sede.", 409)
    return guardar(db, Producto(**datos.model_dump()), accion="CREAR",
                entidad="productos", usuario=usuario)



@productos.post("/carga-masiva", response_model=ProductoCargaResultado,
                summary="Carga masiva de productos desde CSV")
async def cargar_productos_csv(sede_id: int, archivo: UploadFile = File(...),
                            usuario: UsuarioActual = Depends(solo_admin),
                            db: Session = Depends(get_db)):
    obtener_o_404(db, Sede, sede_id, "la sede")

    if not archivo.filename.lower().endswith(".csv"):
        raise ErrorApp("FORMATO_INVALIDO", "El archivo debe ser un .csv.", 422)

    contenido = (await archivo.read()).decode("utf-8-sig")
    lector = csv.DictReader(StringIO(contenido))

    columnas_esperadas = {"codigo", "nombre", "tipo_producto_id", "proveedor_id",
                        "valor_compra", "valor_venta"}
    if not columnas_esperadas.issubset(set(lector.fieldnames or [])):
        raise ErrorApp("CSV_INVALIDO",
                    f"El CSV debe tener las columnas: {', '.join(sorted(columnas_esperadas))}.", 422)

    creados = 0
    errores: list[ProductoCargaError] = []

    for numero_fila, fila in enumerate(lector, start=2):  # fila 1 = encabezado
        try:
            datos = ProductoCrear(
                codigo=fila["codigo"].strip(),
                nombre=fila["nombre"].strip(),
                sede_id=sede_id,
                tipo_producto_id=int(fila["tipo_producto_id"]),
                proveedor_id=int(fila["proveedor_id"]),
                valor_compra=fila["valor_compra"],
                valor_venta=fila["valor_venta"],
            )
            obtener_o_404(db, TipoProducto, datos.tipo_producto_id, "el tipo de producto")
            obtener_o_404(db, Proveedor, datos.proveedor_id, "el proveedor")

            duplicado = db.scalar(
                select(Producto).where(Producto.sede_id == sede_id, Producto.codigo == datos.codigo)
            )
            if duplicado:
                raise ValueError(f"El código {datos.codigo} ya existe en esa sede.")

            producto = Producto(**datos.model_dump())
            db.add(producto)
            db.flush()
            registrar(db, accion="CREAR", entidad="productos", entidad_id=producto.id,
                    usuario_id=usuario.id, usuario=usuario.usuario, sede_id=usuario.sede_id,
                    detalle="carga_masiva")
            db.commit()
            creados += 1
        except (ErrorApp, ValueError, KeyError) as error:
            db.rollback()
            errores.append(ProductoCargaError(fila=numero_fila, mensaje=str(error)))

    return ProductoCargaResultado(creados=creados, errores=errores)


@productos.get("", response_model=list[ProductoSalida], summary="Listar productos por sede")
def listar_productos(_: UsuarioActual = Depends(usuario_actual), db: Session = Depends(get_db),
                    sede_id: int | None = None, tipo_producto_id: int | None = None,
                    solo_activos: bool = True):
    consulta = select(Producto)
    if sede_id is not None:
        consulta = consulta.where(Producto.sede_id == sede_id)
    if tipo_producto_id is not None:
        consulta = consulta.where(Producto.tipo_producto_id == tipo_producto_id)
    if solo_activos:
        consulta = consulta.where(Producto.activo.is_(True))
    return list(db.scalars(consulta.order_by(Producto.nombre)))


@productos.get("/por-codigo/{codigo}", response_model=ProductoSalida,
            summary="Consultar producto por código y sede")
def obtener_producto_por_codigo(codigo: str, sede_id: int,
                                _: UsuarioActual = Depends(usuario_actual),
                                db: Session = Depends(get_db)):
    producto = db.scalar(
        select(Producto).where(Producto.sede_id == sede_id, Producto.codigo == codigo)
    )
    if producto is None:
        raise ErrorApp("NO_ENCONTRADO",
                    f"No existe el producto con código {codigo} en la sede {sede_id}.", 404)
    return producto


@productos.get("/{producto_id}", response_model=ProductoSalida, summary="Consultar producto")
def obtener_producto(producto_id: int, _: UsuarioActual = Depends(usuario_actual),
                    db: Session = Depends(get_db)):
    return obtener_o_404(db, Producto, producto_id, "el producto")


@productos.patch("/{producto_id}", response_model=ProductoSalida, summary="Actualizar producto")
def actualizar_producto(producto_id: int, datos: ProductoActualizar,
                        usuario: UsuarioActual = Depends(solo_admin), db: Session = Depends(get_db)):
    producto = obtener_o_404(db, Producto, producto_id, "el producto")
    cambios = datos.model_dump(exclude_unset=True)
    compra = cambios.get("valor_compra", producto.valor_compra)
    venta = cambios.get("valor_venta", producto.valor_venta)
    if venta < compra:
        raise ErrorApp("MARGEN_NEGATIVO",
                    "El valor de venta no puede ser menor que el valor de compra.", 422)
    return aplicar_cambios(db, producto, datos, entidad="productos", usuario=usuario)


@productos.post("/{producto_id}/inactivar", response_model=ProductoSalida, summary="Inactivar producto")
def inactivar_producto(producto_id: int, usuario: UsuarioActual = Depends(solo_admin),
                    db: Session = Depends(get_db)):
    producto = obtener_o_404(db, Producto, producto_id, "el producto")
    if not producto.activo:
        raise ErrorApp("PRODUCTO_YA_INACTIVO", "El producto ya está inactivo.", 409)
    producto.activo = False
    registrar(db, accion="INACTIVAR", entidad="productos", entidad_id=producto.id,
            usuario_id=usuario.id, usuario=usuario.usuario, sede_id=usuario.sede_id)
    db.commit()
    db.refresh(producto)
    return producto


@productos.post("/{producto_id}/activar", response_model=ProductoSalida, summary="Activar producto")
def activar_producto(producto_id: int, usuario: UsuarioActual = Depends(solo_admin),
                    db: Session = Depends(get_db)):
    producto = obtener_o_404(db, Producto, producto_id, "el producto")
    if producto.activo:
        raise ErrorApp("PRODUCTO_YA_ACTIVO", "El producto ya está activo.", 409)
    producto.activo = True
    registrar(db, accion="ACTIVAR", entidad="productos", entidad_id=producto.id,
            usuario_id=usuario.id, usuario=usuario.usuario, sede_id=usuario.sede_id)
    db.commit()
    db.refresh(producto)
    return producto


for router in (sedes, mesas, tipos, proveedores, productos):
    app.include_router(router)

