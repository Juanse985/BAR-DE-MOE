"""parametrizacion-service — M2 Parametrización, M3 Inventario por sede y M4 Pedidos.

Sedes, mesas, tipos de producto, proveedores, productos, inventario y pedidos.
Solo el perfil ADMINISTRADOR parametriza y ajusta inventario; el MESERO toma
pedidos; cualquier perfil autenticado puede consultar, pero CAJERO y MESERO
solo ven los datos de su sede (tabla 3.1 de la propuesta).
Toda escritura queda registrada en la tabla de auditoría (RNF-12), con la IP
real y el X-Request-Id que llegan del gateway.

Sprint 2 (Juan David Tovío · HU-021 y HU-022):
- El producto se crea una sola vez para todas las sedes; el inventario es de cada sede.
- Inventario: ingresos, ajustes, movimientos, conciliación y sugerencia de compra.
- Pedidos: abrir sobre mesa libre, agregar productos con verificación y descuento
  de existencias en una sola transacción, y cálculo del cambio.
- Hallazgos H-01, H-02, H-03, H-04 y H-10 corregidos con mensajes que dicen el motivo.
"""
import csv
from contextlib import asynccontextmanager
from decimal import Decimal
from io import StringIO

from fastapi import APIRouter, Depends, FastAPI, File, Query, Request, Response, UploadFile
from pydantic import ValidationError
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from barmoe_common.app import crear_app
from barmoe_common.auditoria import contexto_http, registrar, router_consulta
from barmoe_common.db import Base, crear_session_factory, dependencia_db
from barmoe_common.deps import UsuarioActual, construir_autenticacion
from barmoe_common.errors import ErrorApp

from . import algoritmos
from .config import config
from .models import (
    InventarioSede,
    Mesa,
    MovimientoInventario,
    Pedido,
    PedidoLinea,
    Producto,
    Proveedor,
    Sede,
    TipoProducto,
)
from .schemas import (
    AjusteInventario,
    CambioSalida,
    ConciliacionSalida,
    IngresoInventario,
    InventarioSalida,
    LineaCrear,
    LineasAgregar,
    LoteSugerido,
    MesaActualizar,
    MesaCrear,
    MesaSalida,
    MovimientoSalida,
    PedidoAbrir,
    PedidoSalida,
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
    SugerenciaCompraSalida,
    TipoProductoActualizar,
    TipoProductoCrear,
    TipoProductoSalida,
)

SessionLocal = crear_session_factory(config.DATABASE_URL)
get_db = dependencia_db(SessionLocal)
usuario_actual, requiere_perfil = construir_autenticacion(config.JWT_SECRET, config.JWT_ALGORITMO)
solo_admin = requiere_perfil("ADMINISTRADOR")
mesero_o_admin = requiere_perfil("ADMINISTRADOR", "MESERO")       # CU-20, CU-21
cajero_o_admin = requiere_perfil("ADMINISTRADOR", "CAJERO")       # cobro (prepara HU-023)


@asynccontextmanager
async def ciclo_de_vida(_: FastAPI):
    Base.metadata.create_all(bind=SessionLocal.engine)
    yield


app = crear_app(
    config,
    titulo="Bar de Moe · parametrizacion-service",
    descripcion="M2 Master data · M3 Inventory per branch · M4 Orders. DATHEON S.A.S.",
    lifespan=ciclo_de_vida,
    auditar_rechazos=SessionLocal,  # DEF-05 · C-1
)

PERFIL_ADMIN = "ADMINISTRADOR"


# --------------------------------------------------------------- utilidades
def obtener_o_404(db: Session, modelo, entidad_id: int, etiqueta: str):
    fila = db.get(modelo, entidad_id)
    if fila is None:
        raise ErrorApp("NO_ENCONTRADO", f"There is no {etiqueta} with id {entidad_id}.", 404)
    return fila


def sede_autorizada(usuario: UsuarioActual, sede_id: int | None) -> int | None:
    """DEF-06: CAJERO y MESERO solo operan sobre su sede.

    - ADMINISTRADOR: puede filtrar por cualquier sede o ver todas (None).
    - Otros perfiles: si no mandan sede, se usa la del token; si mandan otra,
      se rechaza con 403 (y el middleware lo deja en la auditoría).
    """
    if usuario.perfil == PERFIL_ADMIN:
        return sede_id
    if usuario.sede_id is None:
        raise ErrorApp("SIN_SEDE", "Your user has no branch assigned. Ask the administrator "
                       "to assign one.", 403)
    if sede_id is not None and sede_id != usuario.sede_id:
        raise ErrorApp("SEDE_NO_AUTORIZADA",
                       f"You can only access data from your own branch (id {usuario.sede_id}); "
                       f"you requested branch {sede_id}.", 403)
    return usuario.sede_id


def sede_activa(db: Session, sede_id: int) -> Sede:
    """H-10: no se crean datos nuevos colgando de una sede que ya no opera."""
    sede = obtener_o_404(db, Sede, sede_id, "branch")
    if not sede.activa:
        raise ErrorApp("SEDE_INACTIVA", f"Branch '{sede.nombre}' is inactive: activate it first.", 409)
    return sede


def tipo_activo(db: Session, tipo_id: int) -> TipoProducto:
    """H-02 y H-04: el tipo debe existir y estar activo."""
    tipo = obtener_o_404(db, TipoProducto, tipo_id, "product type")
    if not tipo.activo:
        raise ErrorApp("TIPO_INACTIVO",
                       f"Product type '{tipo.nombre}' is inactive and cannot be assigned.", 409)
    return tipo


def proveedor_activo(db: Session, proveedor_id: int) -> Proveedor:
    """H-02 y H-04: el proveedor debe existir y estar activo."""
    proveedor = obtener_o_404(db, Proveedor, proveedor_id, "supplier")
    if not proveedor.activo:
        raise ErrorApp("PROVEEDOR_INACTIVO",
                       f"Supplier '{proveedor.nombre}' is inactive and cannot be assigned.", 409)
    return proveedor


def _contexto(usuario: UsuarioActual, request: Request | None) -> dict:
    datos = {"usuario_id": usuario.id, "usuario": usuario.usuario, "sede_id": usuario.sede_id}
    if request is not None:
        datos.update(contexto_http(request))  # DEF-07 y DEF-08
    return datos


def guardar(db: Session, fila, *, accion: str, entidad: str, usuario: UsuarioActual,
            request: Request | None = None):
    db.add(fila)
    db.flush()
    registrar(db, accion=accion, entidad=entidad, entidad_id=fila.id, **_contexto(usuario, request))
    db.commit()
    db.refresh(fila)
    return fila


def aplicar_cambios(db: Session, fila, datos, *, entidad: str, usuario: UsuarioActual,
                    request: Request | None = None):
    cambios = datos.model_dump(exclude_unset=True)
    for campo, valor in cambios.items():
        setattr(fila, campo, valor)
    registrar(db, accion="ACTUALIZAR", entidad=entidad, entidad_id=fila.id,
              detalle=", ".join(cambios.keys()), **_contexto(usuario, request))
    db.commit()
    db.refresh(fila)
    return fila


def cambiar_estado(db: Session, fila, campo: str, activo: bool, *, entidad: str, etiqueta: str,
                   usuario: UsuarioActual, request: Request):
    """Activar / inactivar con mensaje claro si ya estaba así ("inactivar en todo")."""
    if getattr(fila, campo) == activo:
        estado = "active" if activo else "inactive"
        codigo = f"{entidad.upper()}_YA_{'ACTIVO' if activo else 'INACTIVO'}"
        raise ErrorApp(codigo, f"{etiqueta} is already {estado}.", 409)
    setattr(fila, campo, activo)
    registrar(db, accion="ACTIVAR" if activo else "INACTIVAR", entidad=entidad, entidad_id=fila.id,
              **_contexto(usuario, request))
    db.commit()
    db.refresh(fila)
    return fila


# ---------------------------------------------- inventario: utilidades internas
def crear_inventario_para_producto(db: Session, producto: Producto, stock_minimo: int = 5) -> int:
    """Corrección del docente: el producto nuevo queda en TODAS las sedes activas, con existencia 0."""
    ya_tiene = set(db.scalars(select(InventarioSede.sede_id)
                              .where(InventarioSede.producto_id == producto.id)))
    creados = 0
    for sede_id in db.scalars(select(Sede.id).where(Sede.activa.is_(True))):
        if sede_id not in ya_tiene:
            db.add(InventarioSede(producto_id=producto.id, sede_id=sede_id, existencia=0,
                                  stock_minimo=stock_minimo))
            creados += 1
    return creados


def crear_inventario_para_sede(db: Session, sede: Sede) -> int:
    """Una sede nueva (o reactivada) recibe todos los productos activos con existencia 0."""
    ya_tiene = set(db.scalars(select(InventarioSede.producto_id)
                              .where(InventarioSede.sede_id == sede.id)))
    creados = 0
    for producto_id in db.scalars(select(Producto.id).where(Producto.activo.is_(True))):
        if producto_id not in ya_tiene:
            db.add(InventarioSede(producto_id=producto_id, sede_id=sede.id, existencia=0))
            creados += 1
    return creados


def inventario_de(db: Session, producto_id: int, sede_id: int, *, bloquear: bool = False) -> InventarioSede:
    consulta = select(InventarioSede).where(InventarioSede.producto_id == producto_id,
                                            InventarioSede.sede_id == sede_id)
    if bloquear:
        consulta = consulta.with_for_update()  # dos meseros a la vez no venden la misma botella
    inventario = db.scalar(consulta)
    if inventario is None:
        producto = obtener_o_404(db, Producto, producto_id, "product")
        obtener_o_404(db, Sede, sede_id, "branch")
        raise ErrorApp("PRODUCTO_NO_ASIGNADO",
                       f"Product '{producto.nombre}' has no inventory in branch {sede_id}.", 404)
    return inventario


def mover_inventario(db: Session, inventario: InventarioSede, cantidad: int, *, tipo: str, motivo: str,
                     usuario: UsuarioActual, pedido_id: int | None = None) -> MovimientoInventario:
    """Único punto que cambia la existencia: valida, aplica y deja el movimiento (HU-021 c3 y c6)."""
    anterior = inventario.existencia
    nueva = anterior + cantidad
    if nueva < 0:
        nombre = inventario.producto.nombre
        if tipo == "VENTA":
            raise ErrorApp("STOCK_INSUFICIENTE",
                           f"Not enough stock of '{nombre}': {-cantidad} requested "
                           f"but only {anterior} left in this branch.", 409)
        raise ErrorApp("EXISTENCIA_NEGATIVA",
                       f"The adjustment would leave '{nombre}' at {nueva} units; current stock is "
                       f"{anterior} and it cannot go negative.", 409)
    inventario.existencia = nueva
    movimiento = MovimientoInventario(
        producto_id=inventario.producto_id, sede_id=inventario.sede_id, tipo=tipo, cantidad=cantidad,
        existencia_anterior=anterior, existencia_resultante=nueva, motivo=motivo,
        usuario_id=usuario.id, usuario=usuario.usuario, pedido_id=pedido_id,
    )
    db.add(movimiento)
    return movimiento


def a_inventario_salida(inventario: InventarioSede) -> InventarioSalida:
    producto = inventario.producto
    return InventarioSalida(
        producto_id=producto.id, codigo=producto.codigo, nombre=producto.nombre,
        tipo_producto=producto.tipo.nombre, sede_id=inventario.sede_id,
        existencia=inventario.existencia, stock_minimo=inventario.stock_minimo,
        agotado=inventario.existencia == 0,
        bajo_minimo=inventario.existencia <= inventario.stock_minimo,
        activo=inventario.activo and producto.activo,
    )


def a_producto_salida(producto: Producto, inventario: InventarioSede | None = None) -> ProductoSalida:
    salida = ProductoSalida.model_validate(producto)
    if inventario is not None:
        salida.sede_id = inventario.sede_id
        salida.existencia = inventario.existencia
        salida.activo_en_sede = inventario.activo
    return salida


# -------------------------------------------------------------------- SEDES
sedes = APIRouter(prefix="/sedes", tags=["branches"])


@sedes.post("", response_model=SedeSalida, status_code=201, summary="Create branch")
def crear_sede(datos: SedeCrear, request: Request, usuario: UsuarioActual = Depends(solo_admin),
               db: Session = Depends(get_db)):
    if db.scalar(select(Sede).where(Sede.nombre == datos.nombre)):
        raise ErrorApp("SEDE_DUPLICADA", f"Branch '{datos.nombre}' already exists.", 409)
    sede = Sede(**datos.model_dump())
    db.add(sede)
    db.flush()
    crear_inventario_para_sede(db, sede)
    return guardar(db, sede, accion="CREAR", entidad="sedes", usuario=usuario, request=request)


@sedes.get("", response_model=list[SedeSalida], summary="List branches")
def listar_sedes(usuario: UsuarioActual = Depends(usuario_actual), db: Session = Depends(get_db),
                 solo_activas: bool = True):
    consulta = select(Sede)
    propia = sede_autorizada(usuario, None)
    if propia is not None:
        consulta = consulta.where(Sede.id == propia)
    if solo_activas:
        consulta = consulta.where(Sede.activa.is_(True))
    return list(db.scalars(consulta.order_by(Sede.nombre)))


@sedes.get("/{sede_id}", response_model=SedeSalida, summary="Get branch")
def obtener_sede(sede_id: int, usuario: UsuarioActual = Depends(usuario_actual),
                 db: Session = Depends(get_db)):
    sede_autorizada(usuario, sede_id)
    return obtener_o_404(db, Sede, sede_id, "branch")


@sedes.patch("/{sede_id}", response_model=SedeSalida, summary="Update branch")
def actualizar_sede(sede_id: int, datos: SedeActualizar, request: Request,
                    usuario: UsuarioActual = Depends(solo_admin), db: Session = Depends(get_db)):
    sede = obtener_o_404(db, Sede, sede_id, "branch")

    # H-03: el nombre tampoco se puede repetir al editar.
    if datos.nombre and datos.nombre != sede.nombre and db.scalar(
            select(Sede.id).where(Sede.nombre == datos.nombre)):
        raise ErrorApp("SEDE_DUPLICADA", f"Another branch named '{datos.nombre}' already exists.", 409)

    if datos.activa is False and sede.activa:
        mesas_activas = db.scalar(select(func.count(Mesa.id))
                                  .where(Mesa.sede_id == sede_id, Mesa.activa.is_(True)))
        con_existencia = db.scalar(select(func.count(InventarioSede.id)).where(
            InventarioSede.sede_id == sede_id, InventarioSede.activo.is_(True),
            InventarioSede.existencia > 0))
        pedidos_abiertos = db.scalar(select(func.count(Pedido.id))
                                     .where(Pedido.sede_id == sede_id, Pedido.estado == "ABIERTO"))
        if mesas_activas or con_existencia or pedidos_abiertos:
            raise ErrorApp(
                "SEDE_CON_RECURSOS_ACTIVOS",
                f"Branch '{sede.nombre}' cannot be deactivated: it has {mesas_activas} active table(s), "
                f"{con_existencia} active product(s) with stock and {pedidos_abiertos} open order(s).", 409)

    if datos.activa is True and not sede.activa:
        crear_inventario_para_sede(db, sede)
    return aplicar_cambios(db, sede, datos, entidad="sedes", usuario=usuario, request=request)


# -------------------------------------------------------------------- MESAS
mesas = APIRouter(prefix="/mesas", tags=["tables"])


@mesas.post("", response_model=MesaSalida, status_code=201, summary="Create table")
def crear_mesa(datos: MesaCrear, request: Request, usuario: UsuarioActual = Depends(solo_admin),
               db: Session = Depends(get_db)):
    sede = sede_activa(db, datos.sede_id)  # H-10
    existe = db.scalar(select(Mesa).where(Mesa.sede_id == datos.sede_id, Mesa.numero == datos.numero))
    if existe:
        raise ErrorApp("MESA_DUPLICADA",
                       f"Table {datos.numero} already exists in branch '{sede.nombre}'.", 409)
    return guardar(db, Mesa(**datos.model_dump()), accion="CREAR", entidad="mesas", usuario=usuario,
                   request=request)


@mesas.get("", response_model=list[MesaSalida], summary="List tables")
def listar_mesas(usuario: UsuarioActual = Depends(usuario_actual), db: Session = Depends(get_db),
                 sede_id: int | None = None, estado: str | None = None):
    sede_id = sede_autorizada(usuario, sede_id)
    consulta = select(Mesa)
    if sede_id is not None:
        consulta = consulta.where(Mesa.sede_id == sede_id)
    if estado:
        consulta = consulta.where(Mesa.estado == estado.upper())
    return list(db.scalars(consulta.order_by(Mesa.sede_id, Mesa.numero)))


def _pedido_abierto_de_mesa(db: Session, mesa_id: int) -> Pedido | None:
    return db.scalar(select(Pedido).where(Pedido.mesa_id == mesa_id, Pedido.estado == "ABIERTO"))


@mesas.patch("/{mesa_id}", response_model=MesaSalida, summary="Update table")
def actualizar_mesa(mesa_id: int, datos: MesaActualizar, request: Request,
                    usuario: UsuarioActual = Depends(solo_admin), db: Session = Depends(get_db)):
    mesa = obtener_o_404(db, Mesa, mesa_id, "table")
    abierto = _pedido_abierto_de_mesa(db, mesa_id)
    if abierto and (datos.estado == "LIBRE" or datos.activa is False):
        raise ErrorApp("MESA_CON_PEDIDO_ABIERTO",
                       f"Table {mesa.numero} has open order #{abierto.id}: it cannot be "
                       "freed or deactivated until the order is closed.", 409)
    return aplicar_cambios(db, mesa, datos, entidad="mesas", usuario=usuario, request=request)


@mesas.get("/{mesa_id}/pedido-abierto", response_model=PedidoSalida,
           summary="Open order of a table (CU-22)")
def pedido_abierto_de_mesa(mesa_id: int, usuario: UsuarioActual = Depends(usuario_actual),
                           db: Session = Depends(get_db)):
    mesa = obtener_o_404(db, Mesa, mesa_id, "table")
    sede_autorizada(usuario, mesa.sede_id)
    pedido = _pedido_abierto_de_mesa(db, mesa_id)
    if pedido is None:
        raise ErrorApp("SIN_PEDIDO_ABIERTO", f"Table {mesa.numero} has no open order.", 404)
    return pedido


# ------------------------------------------------------------ TIPOS PRODUCTO
tipos = APIRouter(prefix="/tipos-producto", tags=["product types"])


@tipos.post("", response_model=TipoProductoSalida, status_code=201, summary="Create product type")
def crear_tipo(datos: TipoProductoCrear, request: Request, usuario: UsuarioActual = Depends(solo_admin),
               db: Session = Depends(get_db)):
    if db.scalar(select(TipoProducto).where(TipoProducto.nombre == datos.nombre)):
        raise ErrorApp("TIPO_DUPLICADO", f"Product type '{datos.nombre}' already exists.", 409)
    return guardar(db, TipoProducto(**datos.model_dump()), accion="CREAR",
                   entidad="tipos_producto", usuario=usuario, request=request)


@tipos.get("", response_model=list[TipoProductoSalida], summary="List product types")
def listar_tipos(_: UsuarioActual = Depends(usuario_actual), db: Session = Depends(get_db)):
    return list(db.scalars(select(TipoProducto).order_by(TipoProducto.nombre)))


@tipos.patch("/{tipo_id}", response_model=TipoProductoSalida, summary="Update product type")
def actualizar_tipo(tipo_id: int, datos: TipoProductoActualizar, request: Request,
                    usuario: UsuarioActual = Depends(solo_admin), db: Session = Depends(get_db)):
    tipo = obtener_o_404(db, TipoProducto, tipo_id, "product type")
    if datos.nombre and datos.nombre != tipo.nombre and db.scalar(
            select(TipoProducto.id).where(TipoProducto.nombre == datos.nombre)):
        raise ErrorApp("TIPO_DUPLICADO",  # H-03
                       f"Another product type named '{datos.nombre}' already exists.", 409)
    if datos.activo is False and tipo.activo:
        activos = db.scalar(select(func.count(Producto.id))
                            .where(Producto.tipo_producto_id == tipo_id, Producto.activo.is_(True)))
        if activos:
            raise ErrorApp("TIPO_CON_PRODUCTOS_ACTIVOS",
                           f"Product type '{tipo.nombre}' cannot be deactivated: it has {activos} "
                           "active product(s).", 409)
    return aplicar_cambios(db, tipo, datos, entidad="tipos_producto", usuario=usuario, request=request)


# -------------------------------------------------------------- PROVEEDORES
proveedores = APIRouter(prefix="/proveedores", tags=["suppliers"])


@proveedores.post("", response_model=ProveedorSalida, status_code=201, summary="Create supplier")
def crear_proveedor(datos: ProveedorCrear, request: Request, usuario: UsuarioActual = Depends(solo_admin),
                    db: Session = Depends(get_db)):
    if db.scalar(select(Proveedor).where(Proveedor.nit == datos.nit)):
        raise ErrorApp("PROVEEDOR_DUPLICADO", f"A supplier with NIT {datos.nit} already exists.", 409)
    return guardar(db, Proveedor(**datos.model_dump()), accion="CREAR",
                   entidad="proveedores", usuario=usuario, request=request)


@proveedores.get("", response_model=list[ProveedorSalida], summary="List suppliers")
def listar_proveedores(_: UsuarioActual = Depends(usuario_actual), db: Session = Depends(get_db)):
    return list(db.scalars(select(Proveedor).order_by(Proveedor.nombre)))


@proveedores.patch("/{proveedor_id}", response_model=ProveedorSalida, summary="Update supplier")
def actualizar_proveedor(proveedor_id: int, datos: ProveedorActualizar, request: Request,
                         usuario: UsuarioActual = Depends(solo_admin), db: Session = Depends(get_db)):
    proveedor = obtener_o_404(db, Proveedor, proveedor_id, "supplier")
    if datos.activo is False and proveedor.activo:
        activos = db.scalar(select(func.count(Producto.id))
                            .where(Producto.proveedor_id == proveedor_id, Producto.activo.is_(True)))
        if activos:
            raise ErrorApp("PROVEEDOR_CON_PRODUCTOS_ACTIVOS",
                           f"Supplier '{proveedor.nombre}' cannot be deactivated: it has {activos} "
                           "active product(s).", 409)
    return aplicar_cambios(db, proveedor, datos, entidad="proveedores", usuario=usuario, request=request)


# ---------------------------------------------------------------- PRODUCTOS
productos = APIRouter(prefix="/productos", tags=["products"])


def _crear_producto(db: Session, datos: ProductoCrear) -> Producto:
    tipo_activo(db, datos.tipo_producto_id)
    proveedor_activo(db, datos.proveedor_id)
    duplicado = db.scalar(select(Producto).where(Producto.codigo == datos.codigo))
    if duplicado:
        raise ErrorApp("PRODUCTO_DUPLICADO",
                       f"Code {datos.codigo} already exists ('{duplicado.nombre}'). A product is shared "
                       "by all branches.", 409)
    producto = Producto(**datos.model_dump(exclude={"stock_minimo"}))
    db.add(producto)
    db.flush()
    crear_inventario_para_producto(db, producto, datos.stock_minimo)
    return producto


@productos.post("", response_model=ProductoSalida, status_code=201,
                summary="Create product (available in every branch)")
def crear_producto(datos: ProductoCrear, request: Request, usuario: UsuarioActual = Depends(solo_admin),
                   db: Session = Depends(get_db)):
    producto = _crear_producto(db, datos)
    return guardar(db, producto, accion="CREAR", entidad="productos", usuario=usuario, request=request)


@productos.post("/carga-masiva", response_model=ProductoCargaResultado,
                summary="Bulk product upload from CSV")
async def cargar_productos_csv(request: Request, archivo: UploadFile = File(...),
                               sede_id: int | None = Query(default=None, deprecated=True),
                               usuario: UsuarioActual = Depends(solo_admin),
                               db: Session = Depends(get_db)):
    """Cada producto queda en todas las sedes. `sede_id` se acepta pero ya no se usa."""
    if not (archivo.filename or "").lower().endswith(".csv"):
        raise ErrorApp("FORMATO_INVALIDO", f"File '{archivo.filename}' must be a .csv.", 422)

    try:
        contenido = (await archivo.read()).decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ErrorApp("CSV_INVALIDO", "The file is not UTF-8. Save it as 'CSV UTF-8'.",
                       422) from exc
    lector = csv.DictReader(StringIO(contenido))

    columnas_esperadas = {"codigo", "nombre", "tipo_producto_id", "proveedor_id",
                          "valor_compra", "valor_venta"}
    faltan = columnas_esperadas - set(lector.fieldnames or [])
    if faltan:
        raise ErrorApp("CSV_INVALIDO", f"The CSV is missing these columns: {', '.join(sorted(faltan))}.", 422)

    creados = 0
    errores: list[ProductoCargaError] = []

    for numero_fila, fila in enumerate(lector, start=2):  # fila 1 = encabezado
        try:
            datos = ProductoCrear(
                codigo=fila["codigo"].strip(),
                nombre=fila["nombre"].strip(),
                tipo_producto_id=int(fila["tipo_producto_id"]),
                proveedor_id=int(fila["proveedor_id"]),
                valor_compra=fila["valor_compra"],
                valor_venta=fila["valor_venta"],
            )
            producto = _crear_producto(db, datos)
            registrar(db, accion="CREAR", entidad="productos", entidad_id=producto.id,
                      detalle="carga_masiva", **_contexto(usuario, request))
            db.commit()
            creados += 1
        except ValidationError as error:
            db.rollback()
            mensaje = "; ".join(e["msg"].removeprefix("Value error, ") for e in error.errors())
            errores.append(ProductoCargaError(fila=numero_fila, mensaje=mensaje))
        except ErrorApp as error:
            db.rollback()
            errores.append(ProductoCargaError(fila=numero_fila, mensaje=error.mensaje))
        except (ValueError, KeyError, AttributeError):
            db.rollback()
            errores.append(ProductoCargaError(
                fila=numero_fila, mensaje="Incomplete row or a value that is not a number."))

    return ProductoCargaResultado(creados=creados, errores=errores)


@productos.get("", response_model=list[ProductoSalida],
               summary="List products (with stock when a branch is given)")
def listar_productos(usuario: UsuarioActual = Depends(usuario_actual), db: Session = Depends(get_db),
                     sede_id: int | None = None, tipo_producto_id: int | None = None,
                     solo_activos: bool = True):
    sede_id = sede_autorizada(usuario, sede_id)
    if sede_id is None:  # administrador sin filtro: catálogo global
        consulta = select(Producto)
        if tipo_producto_id is not None:
            consulta = consulta.where(Producto.tipo_producto_id == tipo_producto_id)
        if solo_activos:
            consulta = consulta.where(Producto.activo.is_(True))
        return [a_producto_salida(p) for p in db.scalars(consulta.order_by(Producto.nombre))]

    consulta = (select(Producto, InventarioSede)
                .join(InventarioSede, InventarioSede.producto_id == Producto.id)
                .where(InventarioSede.sede_id == sede_id))
    if tipo_producto_id is not None:
        consulta = consulta.where(Producto.tipo_producto_id == tipo_producto_id)
    if solo_activos:
        consulta = consulta.where(Producto.activo.is_(True), InventarioSede.activo.is_(True))
    return [a_producto_salida(p, i) for p, i in db.execute(consulta.order_by(Producto.nombre))]


@productos.get("/por-codigo/{codigo}", response_model=ProductoSalida,
               summary="Get product by code in a branch")
def obtener_producto_por_codigo(codigo: str, sede_id: int,
                                usuario: UsuarioActual = Depends(usuario_actual),
                                db: Session = Depends(get_db)):
    sede_autorizada(usuario, sede_id)
    producto = db.scalar(select(Producto).where(Producto.codigo == codigo.strip().upper()))
    if producto is None:
        raise ErrorApp("NO_ENCONTRADO", f"There is no product with code {codigo}.", 404)
    return a_producto_salida(producto, inventario_de(db, producto.id, sede_id))


@productos.get("/{producto_id}", response_model=ProductoSalida, summary="Get product")
def obtener_producto(producto_id: int, usuario: UsuarioActual = Depends(usuario_actual),
                     db: Session = Depends(get_db), sede_id: int | None = None):
    sede_id = sede_autorizada(usuario, sede_id)
    producto = obtener_o_404(db, Producto, producto_id, "product")
    if sede_id is None:
        return a_producto_salida(producto)
    return a_producto_salida(producto, inventario_de(db, producto_id, sede_id))


@productos.patch("/{producto_id}", response_model=ProductoSalida, summary="Update product")
def actualizar_producto(producto_id: int, datos: ProductoActualizar, request: Request,
                        usuario: UsuarioActual = Depends(solo_admin), db: Session = Depends(get_db)):
    producto = obtener_o_404(db, Producto, producto_id, "product")
    if datos.tipo_producto_id is not None:
        tipo_activo(db, datos.tipo_producto_id)          # H-02 y H-04
    if datos.proveedor_id is not None:
        proveedor_activo(db, datos.proveedor_id)         # H-02 y H-04
    cambios = datos.model_dump(exclude_unset=True)
    compra = cambios.get("valor_compra", producto.valor_compra)
    venta = cambios.get("valor_venta", producto.valor_venta)
    if venta < compra:
        raise ErrorApp("MARGEN_NEGATIVO",
                       f"Sale price ({venta}) cannot be lower than purchase price ({compra}).",
                       422)
    return a_producto_salida(
        aplicar_cambios(db, producto, datos, entidad="productos", usuario=usuario, request=request))


@productos.post("/{producto_id}/inactivar", response_model=ProductoSalida,
                summary="Deactivate product in every branch")
def inactivar_producto(producto_id: int, request: Request, usuario: UsuarioActual = Depends(solo_admin),
                       db: Session = Depends(get_db)):
    producto = obtener_o_404(db, Producto, producto_id, "product")
    return a_producto_salida(cambiar_estado(db, producto, "activo", False, entidad="producto",
                                            etiqueta=f"Product '{producto.nombre}'",
                                            usuario=usuario, request=request))


@productos.post("/{producto_id}/activar", response_model=ProductoSalida,
                summary="Activate product in every branch")
def activar_producto(producto_id: int, request: Request, usuario: UsuarioActual = Depends(solo_admin),
                     db: Session = Depends(get_db)):
    producto = obtener_o_404(db, Producto, producto_id, "product")
    tipo_activo(db, producto.tipo_producto_id)
    proveedor_activo(db, producto.proveedor_id)
    crear_inventario_para_producto(db, producto)
    return a_producto_salida(cambiar_estado(db, producto, "activo", True, entidad="producto",
                                            etiqueta=f"Product '{producto.nombre}'",
                                            usuario=usuario, request=request))


# ------------------------------------------------- INVENTARIO POR SEDE (M3)
inventario = APIRouter(prefix="/inventario", tags=["inventory (M3)"])


@inventario.get("", response_model=list[InventarioSalida], summary="Branch stock (CU-17)")
def listar_inventario(usuario: UsuarioActual = Depends(usuario_actual), db: Session = Depends(get_db),
                      sede_id: int | None = None, buscar: str | None = Query(default=None, max_length=60),
                      solo_activos: bool = True):
    sede_id = sede_autorizada(usuario, sede_id)
    consulta = select(InventarioSede).join(Producto, InventarioSede.producto_id == Producto.id)
    if sede_id is not None:
        consulta = consulta.where(InventarioSede.sede_id == sede_id)
    if buscar:
        patron = f"%{buscar.strip()}%"
        consulta = consulta.where(or_(Producto.codigo.ilike(patron), Producto.nombre.ilike(patron)))
    if solo_activos:
        consulta = consulta.where(InventarioSede.activo.is_(True), Producto.activo.is_(True))
    filas = db.scalars(consulta.order_by(InventarioSede.sede_id, Producto.nombre))
    return [a_inventario_salida(i) for i in filas]


@inventario.post("/ingresos", response_model=InventarioSalida, status_code=201,
                 summary="Register stock entry (CU-15)")
def registrar_ingreso(datos: IngresoInventario, request: Request,
                      usuario: UsuarioActual = Depends(solo_admin), db: Session = Depends(get_db)):
    sede_activa(db, datos.sede_id)
    fila = inventario_de(db, datos.producto_id, datos.sede_id, bloquear=True)
    if not fila.activo or not fila.producto.activo:
        raise ErrorApp("PRODUCTO_INACTIVO_EN_SEDE",
                       f"'{fila.producto.nombre}' is inactive in this branch: activate it before adding "
                       "stock.", 409)
    mov = mover_inventario(db, fila, datos.cantidad, tipo="INGRESO", motivo=datos.motivo, usuario=usuario)
    db.flush()
    registrar(db, accion="INGRESO_INVENTARIO", entidad="inventario_sede", entidad_id=fila.id,
              detalle=f"+{datos.cantidad} (mov {mov.id}): {datos.motivo}", **_contexto(usuario, request))
    db.commit()
    return a_inventario_salida(fila)


@inventario.post("/ajustes", response_model=InventarioSalida, status_code=201,
                 summary="Adjust stock (CU-16)")
def registrar_ajuste(datos: AjusteInventario, request: Request,
                     usuario: UsuarioActual = Depends(solo_admin), db: Session = Depends(get_db)):
    fila = inventario_de(db, datos.producto_id, datos.sede_id, bloquear=True)
    mov = mover_inventario(db, fila, datos.cantidad, tipo="AJUSTE", motivo=datos.motivo, usuario=usuario)
    if datos.stock_minimo is not None:
        fila.stock_minimo = datos.stock_minimo
    db.flush()
    registrar(db, accion="AJUSTE_INVENTARIO", entidad="inventario_sede", entidad_id=fila.id,
              detalle=f"{datos.cantidad:+d} (mov {mov.id}): {datos.motivo}", **_contexto(usuario, request))
    db.commit()
    return a_inventario_salida(fila)


@inventario.get("/movimientos", response_model=list[MovimientoSalida],
                summary="Stock movements of a product in a branch (CU-32)")
def listar_movimientos(sede_id: int, producto_id: int | None = None,
                       _: UsuarioActual = Depends(solo_admin), db: Session = Depends(get_db),
                       limite: int = Query(default=200, ge=1, le=1000)):
    obtener_o_404(db, Sede, sede_id, "branch")
    consulta = select(MovimientoInventario).where(MovimientoInventario.sede_id == sede_id)
    if producto_id is not None:
        consulta = consulta.where(MovimientoInventario.producto_id == producto_id)
    return list(db.scalars(consulta.order_by(MovimientoInventario.id.desc()).limit(limite)))


@inventario.get("/conciliacion", response_model=ConciliacionSalida,
                summary="Does stock match its movements? (recursive/iterative algorithm)")
def conciliar(sede_id: int, producto_id: int, _: UsuarioActual = Depends(solo_admin),
              db: Session = Depends(get_db)):
    fila = inventario_de(db, producto_id, sede_id)
    cantidades = list(db.scalars(
        select(MovimientoInventario.cantidad)
        .where(MovimientoInventario.sede_id == sede_id, MovimientoInventario.producto_id == producto_id)
        .order_by(MovimientoInventario.id)))
    iterativa = algoritmos.existencia_iterativa(cantidades)
    recursiva = (algoritmos.existencia_recursiva(cantidades)
                 if len(cantidades) <= algoritmos.LIMITE_RECURSION else None)
    cuadra = iterativa == fila.existencia and (recursiva is None or recursiva == iterativa)
    if not cantidades:
        mensaje = "The product has no movements in this branch."
    elif cuadra:
        mensaje = f"Balanced: {len(cantidades)} movement(s) explain the stock of {fila.existencia}."
    else:
        mensaje = (f"Not balanced: stored stock is {fila.existencia} but the movements "
                   f"add up to {iterativa}. Check the audit log.")
    return ConciliacionSalida(producto_id=producto_id, sede_id=sede_id, movimientos=len(cantidades),
                              existencia_registrada=fila.existencia, existencia_iterativa=iterativa,
                              existencia_recursiva=recursiva, cuadra=cuadra, mensaje=mensaje)


@inventario.get("/sugerencia-compra", response_model=SugerenciaCompraSalida,
                summary="What to restock with a budget (knapsack algorithm)")
def sugerir_compra(sede_id: int, presupuesto: int = Query(gt=0, le=1_000_000_000),
                   _: UsuarioActual = Depends(solo_admin), db: Session = Depends(get_db)):
    """Cada producto bajo su nivel objetivo (2 × stock mínimo) es un lote candidato:

    - volumen  = lo que cuesta reponerlo (unidades × valor de compra)
    - beneficio = lo que se ganaría al venderlo (unidades × (venta − compra))

    La mochila elige el conjunto de lotes que más ganancia deja sin pasarse del presupuesto.
    """
    sede_activa(db, sede_id)
    filas = db.scalars(select(InventarioSede).join(Producto).where(
        InventarioSede.sede_id == sede_id, InventarioSede.activo.is_(True), Producto.activo.is_(True)))

    candidatos: dict[int, LoteSugerido] = {}
    articulos: list[algoritmos.Articulo] = []
    for fila in filas:
        objetivo = max(fila.stock_minimo * 2, 1)
        unidades = objetivo - fila.existencia
        producto = fila.producto
        costo = int(Decimal(unidades) * Decimal(producto.valor_compra)) if unidades > 0 else 0
        if unidades <= 0 or costo <= 0:
            continue
        ganancia = int(Decimal(unidades) * (Decimal(producto.valor_venta) - Decimal(producto.valor_compra)))
        candidatos[producto.id] = LoteSugerido(producto_id=producto.id, codigo=producto.codigo,
                                               nombre=producto.nombre, existencia=fila.existencia,
                                               unidades=unidades, costo=costo, ganancia_esperada=ganancia)
        articulos.append(algoritmos.Articulo(clave=producto.id, nombre=producto.nombre,
                                             volumen=costo, beneficio=ganancia))

    resultado = algoritmos.mochila_programacion_dinamica(articulos, presupuesto)
    elegidos = {a.clave for a in resultado.seleccionados}
    return SugerenciaCompraSalida(
        sede_id=sede_id, presupuesto=presupuesto, metodo=resultado.metodo, escala_mcd=resultado.escala,
        costo_total=resultado.volumen_usado, ganancia_esperada=resultado.beneficio_total,
        sobrante=presupuesto - resultado.volumen_usado,
        lotes=[candidatos[a.clave] for a in resultado.seleccionados],
        descartados=[lote for clave, lote in candidatos.items() if clave not in elegidos],
    )


def _cambiar_estado_en_sede(db: Session, sede_id: int, producto_id: int, activo: bool,
                            usuario: UsuarioActual, request: Request) -> InventarioSalida:
    fila = inventario_de(db, producto_id, sede_id)
    etiqueta = f"Product '{fila.producto.nombre}' in branch {sede_id}"
    return a_inventario_salida(cambiar_estado(db, fila, "activo", activo, entidad="inventario_sede",
                                              etiqueta=etiqueta, usuario=usuario, request=request))


@inventario.post("/sedes/{sede_id}/productos/{producto_id}/inactivar", response_model=InventarioSalida,
                 summary="Stop selling a product in this branch only")
def inactivar_en_sede(sede_id: int, producto_id: int, request: Request,
                      usuario: UsuarioActual = Depends(solo_admin), db: Session = Depends(get_db)):
    return _cambiar_estado_en_sede(db, sede_id, producto_id, False, usuario, request)


@inventario.post("/sedes/{sede_id}/productos/{producto_id}/activar", response_model=InventarioSalida,
                 summary="Resume selling a product in this branch")
def activar_en_sede(sede_id: int, producto_id: int, request: Request,
                    usuario: UsuarioActual = Depends(solo_admin), db: Session = Depends(get_db)):
    return _cambiar_estado_en_sede(db, sede_id, producto_id, True, usuario, request)


# ------------------------------------------------------------- PEDIDOS (M4)
pedidos = APIRouter(prefix="/pedidos", tags=["orders (M4)"])


def agregar_lineas(db: Session, pedido: Pedido, lineas: list[LineaCrear], usuario: UsuarioActual) -> None:
    """CU-18 y CU-21: verifica, descuenta y agrega. Si una línea falla, no queda ninguna.

    No se hace commit aquí: si se lanza un ErrorApp la sesión se cierra sin
    confirmar y la base de datos queda como estaba.
    """
    numero_mesa = pedido.mesa.numero
    for linea in lineas:
        producto = obtener_o_404(db, Producto, linea.producto_id, "product")
        if not producto.activo:
            raise ErrorApp("PRODUCTO_INACTIVO", f"Product '{producto.nombre}' is inactive.", 409)
        fila = db.scalar(select(InventarioSede).where(
            InventarioSede.producto_id == producto.id, InventarioSede.sede_id == pedido.sede_id
        ).with_for_update())
        if fila is None or not fila.activo:
            raise ErrorApp("PRODUCTO_NO_DISPONIBLE_EN_SEDE",
                           f"'{producto.nombre}' is not in this branch's catalog.", 409)
        mover_inventario(db, fila, -linea.cantidad, tipo="VENTA",
                         motivo=f"Order #{pedido.id} · table {numero_mesa}",
                         usuario=usuario, pedido_id=pedido.id)
        precio = Decimal(producto.valor_venta)
        subtotal = precio * linea.cantidad
        pedido.lineas.append(PedidoLinea(producto_id=producto.id, codigo=producto.codigo,
                                         nombre=producto.nombre, cantidad=linea.cantidad,
                                         precio_unitario=precio, subtotal=subtotal))
        pedido.total = Decimal(pedido.total or 0) + subtotal


def _pedido_de_mi_sede(db: Session, pedido_id: int, usuario: UsuarioActual) -> Pedido:
    pedido = obtener_o_404(db, Pedido, pedido_id, "order")
    if usuario.perfil != PERFIL_ADMIN and pedido.sede_id != usuario.sede_id:
        raise ErrorApp("SEDE_NO_AUTORIZADA",
                       f"Order #{pedido_id} belongs to another branch; you can only see orders "
                       "from yours.", 403)
    return pedido


@pedidos.post("", response_model=PedidoSalida, status_code=201, summary="Open an order on a table (CU-20)")
def abrir_pedido(datos: PedidoAbrir, request: Request, response: Response,
                 usuario: UsuarioActual = Depends(mesero_o_admin), db: Session = Depends(get_db)):
    mesa = obtener_o_404(db, Mesa, datos.mesa_id, "table")
    sede_autorizada(usuario, mesa.sede_id)  # HU-022 c2: solo mesas de la sede del mesero
    if not mesa.activa:
        raise ErrorApp("MESA_INACTIVA", f"Table {mesa.numero} is inactive.", 409)
    sede_activa(db, mesa.sede_id)

    existente = _pedido_abierto_de_mesa(db, mesa.id)
    if existente is not None:
        # CU-20: si la mesa ya está ocupada se abre el pedido existente en lugar de crear otro.
        agregar_lineas(db, existente, datos.lineas, usuario)
        if datos.lineas:
            registrar(db, accion="AGREGAR_PRODUCTOS", entidad="pedidos", entidad_id=existente.id,
                      detalle=f"{len(datos.lineas)} line(s)", **_contexto(usuario, request))
        db.commit()
        response.status_code = 200
        return existente

    pedido = Pedido(sede_id=mesa.sede_id, mesa_id=mesa.id, mesero_id=usuario.id, mesero=usuario.usuario,
                    estado="ABIERTO", total=Decimal(0))
    db.add(pedido)
    db.flush()
    pedido.mesa = mesa
    agregar_lineas(db, pedido, datos.lineas, usuario)
    mesa.estado = "OCUPADA"  # HU-022 c6
    registrar(db, accion="ABRIR_PEDIDO", entidad="pedidos", entidad_id=pedido.id,
              detalle=f"mesa {mesa.numero}", **_contexto(usuario, request))
    db.commit()
    db.refresh(pedido)
    return pedido


@pedidos.post("/{pedido_id}/lineas", response_model=PedidoSalida,
              summary="Add products to the order (CU-21)")
def agregar_productos(pedido_id: int, datos: LineasAgregar, request: Request,
                      usuario: UsuarioActual = Depends(mesero_o_admin), db: Session = Depends(get_db)):
    pedido = _pedido_de_mi_sede(db, pedido_id, usuario)
    if pedido.estado != "ABIERTO":
        raise ErrorApp("PEDIDO_CERRADO",
                       f"Order #{pedido_id} is already closed: no products can be added.", 409)
    agregar_lineas(db, pedido, datos.lineas, usuario)
    registrar(db, accion="AGREGAR_PRODUCTOS", entidad="pedidos", entidad_id=pedido.id,
              detalle=f"{len(datos.lineas)} line(s)", **_contexto(usuario, request))
    db.commit()
    db.refresh(pedido)
    return pedido


@pedidos.get("", response_model=list[PedidoSalida], summary="List branch orders")
def listar_pedidos(usuario: UsuarioActual = Depends(usuario_actual), db: Session = Depends(get_db),
                   sede_id: int | None = None, estado: str | None = None, mesa_id: int | None = None):
    sede_id = sede_autorizada(usuario, sede_id)
    consulta = select(Pedido)
    if sede_id is not None:
        consulta = consulta.where(Pedido.sede_id == sede_id)
    if estado:
        if estado.upper() not in ("ABIERTO", "CERRADO"):
            raise ErrorApp("ESTADO_INVALIDO",
                           f"Status '{estado}' does not exist: use ABIERTO or CERRADO.", 422)
        consulta = consulta.where(Pedido.estado == estado.upper())
    if mesa_id is not None:
        consulta = consulta.where(Pedido.mesa_id == mesa_id)
    return list(db.scalars(consulta.order_by(Pedido.id.desc())))


@pedidos.get("/{pedido_id}", response_model=PedidoSalida, summary="Order detail (CU-22)")
def obtener_pedido(pedido_id: int, usuario: UsuarioActual = Depends(usuario_actual),
                   db: Session = Depends(get_db)):
    return _pedido_de_mi_sede(db, pedido_id, usuario)


@pedidos.get("/{pedido_id}/cambio", response_model=CambioSalida,
             summary="Change in bills and coins (greedy algorithm)")
def calcular_cambio(pedido_id: int, pagado: int = Query(gt=0, le=100_000_000),
                    usuario: UsuarioActual = Depends(cajero_o_admin), db: Session = Depends(get_db)):
    pedido = _pedido_de_mi_sede(db, pedido_id, usuario)
    total = int(Decimal(pedido.total))
    if pagado < total:
        raise ErrorApp("PAGO_INSUFICIENTE",
                       f"A payment of ${pagado:,} does not cover the total of ${total:,}: "
                       f"${total - pagado:,} missing.", 422)
    try:
        piezas = algoritmos.cambio_voraz(pagado - total)
    except ValueError as exc:
        raise ErrorApp("CAMBIO_IMPOSIBLE", str(exc), 422) from exc
    return CambioSalida(pedido_id=pedido.id, total=total, pagado=pagado, cambio=pagado - total,
                        piezas=[{"denominacion": d, "cantidad": c} for d, c in piezas.items()],
                        total_piezas=sum(piezas.values()))


for router in (sedes, mesas, tipos, proveedores, productos, inventario, pedidos):
    app.include_router(router)
# HU-008: la auditoría de este servicio también se puede consultar (solo ADMINISTRADOR).
app.include_router(router_consulta(get_db, solo_admin))

