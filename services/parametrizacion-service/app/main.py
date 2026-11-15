"""parametrizacion-service — M2 Parametrización, M3 Inventario, M4 Pedidos, M5 Facturación y M6 Reportes.

Sedes, mesas, tipos de producto, proveedores, productos, inventario, pedidos,
facturas y el reporte de ventas y ganancia.
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

Sprints 3 y 4 (Juan David Tovío · HU-023 y HU-024):
- Facturación: cierra el pedido, numera la factura con un consecutivo que no se
  repite, registra el medio de pago, calcula las vueltas y libera la mesa.
- Reporte de ventas y ganancia por fecha, con la sede según el perfil y
  exportación a Excel con exactamente las mismas filas.
- /algoritmos: ordenamientos, búsqueda binaria, Torres de Hanoi, backtracking,
  MCD y cambio voraz sobre los datos reales del bar.
"""
import csv
from contextlib import asynccontextmanager
from datetime import UTC, date, datetime
from decimal import Decimal
from io import StringIO
from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI, File, Query, Request, Response, UploadFile
from pydantic import ValidationError
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from barmoe_common.app import crear_app
from barmoe_common.auditoria import contexto_http, registrar, router_consulta
from barmoe_common.db import Base, crear_session_factory, dependencia_db
from barmoe_common.deps import UsuarioActual, construir_autenticacion
from barmoe_common.errors import ErrorApp

from . import algoritmos, reportes
from .config import config
from .models import (
    ConsecutivoFactura,
    Factura,
    FacturaLinea,
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
    ColaBarraSalida,
    ComandaEnCola,
    ConciliacionSalida,
    FacturaCrear,
    FacturaSalida,
    IngresoInventario,
    InventarioSalida,
    LineaCrear,
    LineasAgregar,
    LoteSugerido,
    MesaActualizar,
    MesaCrear,
    MesaSalida,
    MovimientoSalida,
    PasoColaSalida,
    PasoRutaSalida,
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
    ReporteVentasSalida,
    RutaEntregaSalida,
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
cajero_o_admin = requiere_perfil("ADMINISTRADOR", "CAJERO")       # HU-023 cobro · HU-024 c4 reporte


@asynccontextmanager
async def ciclo_de_vida(_: FastAPI):
    Base.metadata.create_all(bind=SessionLocal.engine)
    _asegurar_consecutivo()
    yield


def _asegurar_consecutivo() -> None:
    """HU-023 c3: la fila del contador existe desde el arranque.

    Así, las dos primeras facturas simultáneas no compiten por crearla.
    Si ya había facturas (base de datos de antes), arranca desde la mayor.
    """
    with SessionLocal() as db:
        if db.get(ConsecutivoFactura, 1) is None:
            ultimo = db.scalar(select(func.max(Factura.numero))) or 0
            db.add(ConsecutivoFactura(id=1, ultimo=ultimo))
            db.commit()


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


def _sede_obligatoria(usuario: UsuarioActual, sede_id: int | None) -> int:
    sede_id = sede_autorizada(usuario, sede_id)
    if sede_id is None:
        raise ErrorApp("SEDE_REQUERIDA", "Send sede_id: the map belongs to one branch.", 422)
    return sede_id


def _posiciones_en_mapa(db: Session, sede_id: int) -> dict[int, tuple[int, int]]:
    """{numero de mesa: (fila, columna)} igual que el mapa 3×N del frontend (orden por número)."""
    numeros = db.scalars(select(Mesa.numero).where(Mesa.sede_id == sede_id).order_by(Mesa.numero))
    return {numero: algoritmos.posicion_en_mapa(i) for i, numero in enumerate(numeros)}


@mesas.get("/ruta-entrega", response_model=RutaEntregaSalida,
           summary="Waiter route through tables with open orders (greedy graph algorithm)")
def ruta_de_entrega(sede_id: int | None = None, usuario: UsuarioActual = Depends(mesero_o_admin),
                    db: Session = Depends(get_db)):
    """Algoritmo 6. Sale de la barra y va siempre a la mesa con pedido abierto más cercana."""
    sede_id = _sede_obligatoria(usuario, sede_id)
    sede_activa(db, sede_id)
    todas = _posiciones_en_mapa(db, sede_id)
    con_pedido = sorted(set(db.scalars(select(Mesa.numero).join(Pedido, Pedido.mesa_id == Mesa.id)
                                       .where(Pedido.sede_id == sede_id, Pedido.estado == "ABIERTO"))))
    grafo = algoritmos.grafo_de_mesas({numero: todas[numero] for numero in con_pedido})
    resultado = algoritmos.recorrido_voraz(grafo, algoritmos.BARRA)
    return RutaEntregaSalida(
        sede_id=sede_id,
        candidatos=[str(n) for n in [algoritmos.BARRA, *con_pedido]],
        ruta=[str(n) for n in resultado.solucion],
        pasos=[PasoRutaSalida(desde=str(p.desde), elegido=str(p.elegido), distancia=p.costo,
                              opciones={str(k): v for k, v in p.opciones.items()})
               for p in resultado.pasos],
        distancia_total=resultado.costo_total,
        distancia_en_orden_de_numero=algoritmos.costo_de_ruta(grafo, [algoritmos.BARRA, *con_pedido]),
    )


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


@pedidos.get("/cola-barra", response_model=ColaBarraSalida,
             summary="Bar ticket queue: each new ticket goes first or last (greedy, lexicographic)")
def cola_de_la_barra(sede_id: int | None = None, usuario: UsuarioActual = Depends(usuario_actual),
                     db: Session = Depends(get_db)):
    """Algoritmo 7. Las comandas llegan en el orden en que se abrieron los pedidos.

    La barra solo puede poner la comanda nueva al inicio o al final de la fila.
    Clave de comparación: (distancia de la mesa a la barra, número de mesa); así la
    fila queda lexicográficamente menor y se despachan antes las mesas más cercanas.
    """
    sede_id = _sede_obligatoria(usuario, sede_id)
    posiciones = _posiciones_en_mapa(db, sede_id)
    abiertos = db.scalars(select(Pedido).where(Pedido.sede_id == sede_id, Pedido.estado == "ABIERTO")
                          .order_by(Pedido.creado_en, Pedido.id))
    llegada = [ComandaEnCola(pedido_id=p.id, mesa=p.mesa.numero,
                             distancia_a_barra=algoritmos.distancia(algoritmos.POSICION_BARRA,
                                                                    posiciones[p.mesa.numero]))
               for p in abiertos]
    cola, pasos = algoritmos.menor_lexicografico(llegada, clave=lambda c: (c.distancia_a_barra, c.mesa))
    return ColaBarraSalida(
        sede_id=sede_id, llegada=llegada, cola=cola,
        pasos=[PasoColaSalida(comanda=p.elemento, posicion=p.posicion, cola=[c.mesa for c in p.resultado])
               for p in pasos],
    )


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


# -------------------------------------------------------- FACTURACIÓN (M5)
facturas = APIRouter(prefix="/facturas", tags=["invoices (M5)"])


def siguiente_numero_factura(db: Session) -> int:
    """HU-023 c3: consecutivo que no se repite.

    La fila del contador se bloquea hasta el commit, así que dos cajeros que
    facturan a la vez esperan su turno. Si la factura falla (rollback), el
    número vuelve atrás y no queda un hueco. La columna `facturas.numero`
    además es UNIQUE: la base de datos rechaza un repetido aunque fallara el bloqueo.
    """
    contador = db.scalar(select(ConsecutivoFactura).where(ConsecutivoFactura.id == 1).with_for_update())
    if contador is None:
        contador = ConsecutivoFactura(id=1, ultimo=db.scalar(select(func.max(Factura.numero))) or 0)
        db.add(contador)
    contador.ultimo += 1
    db.flush()
    return contador.ultimo


def numero_formateado(numero: int) -> str:
    return f"{config.FACTURA_PREFIJO}-{numero:07d}"


def a_factura_salida(factura: Factura, piezas: dict[int, int] | None = None) -> FacturaSalida:
    return FacturaSalida(
        id=factura.id, numero=factura.numero, numero_formateado=numero_formateado(factura.numero),
        pedido_id=factura.pedido_id, sede_id=factura.sede_id, sede=factura.sede.nombre,
        mesa_id=factura.mesa_id, mesa_numero=factura.mesa_numero, mesero=factura.mesero,
        cajero=factura.cajero, medio_pago=factura.medio_pago, total=factura.total,
        valor_recibido=factura.valor_recibido, cambio=factura.cambio,
        piezas_cambio=[{"denominacion": d, "cantidad": c} for d, c in (piezas or {}).items()],
        emitida_en=factura.emitida_en,
        lineas=[{"producto_id": li.producto_id, "codigo": li.codigo, "nombre": li.nombre,
                 "cantidad": li.cantidad, "precio_unitario": li.precio_unitario,
                 "subtotal": li.subtotal} for li in factura.lineas],
    )


def _factura_de_mi_sede(db: Session, factura_id: int, usuario: UsuarioActual) -> Factura:
    factura = obtener_o_404(db, Factura, factura_id, "invoice")
    if usuario.perfil != PERFIL_ADMIN and factura.sede_id != usuario.sede_id:
        raise ErrorApp("SEDE_NO_AUTORIZADA",
                       f"Invoice {numero_formateado(factura.numero)} belongs to another branch; you can "
                       "only see invoices from yours.", 403)
    return factura


@facturas.post("", response_model=FacturaSalida, status_code=201,
               summary="Invoice an open order and register the payment method (HU-023)")
def facturar_pedido(datos: FacturaCrear, request: Request, usuario: UsuarioActual = Depends(cajero_o_admin),
                    db: Session = Depends(get_db)):
    """Cierra el pedido, emite la factura y libera la mesa en UNA sola transacción.

    - c1 Solo pedidos ABIERTO.  - c2 Toma las líneas del pedido con su precio de venta.
    - c3 Número consecutivo único.  - c4 EFECTIVO, TARJETA_DEBITO o TARJETA_CREDITO.
    - c5 El pedido queda CERRADO y la mesa LIBRE.
    """
    pedido = db.scalar(select(Pedido).where(Pedido.id == datos.pedido_id).with_for_update())
    if pedido is None:
        raise ErrorApp("NO_ENCONTRADO", f"There is no order with id {datos.pedido_id}.", 404)
    sede_autorizada(usuario, pedido.sede_id)  # el cajero solo cobra en su sede
    if pedido.estado != "ABIERTO":
        ya = db.scalar(select(Factura).where(Factura.pedido_id == pedido.id))
        detalle = f" with invoice {numero_formateado(ya.numero)}" if ya else ""
        raise ErrorApp("PEDIDO_NO_ABIERTO",
                       f"Order #{pedido.id} is {pedido.estado}{detalle}: only open orders can be "
                       "invoiced.", 409)
    if not pedido.lineas:
        raise ErrorApp("PEDIDO_SIN_PRODUCTOS",
                       f"Order #{pedido.id} has no products: there is nothing to invoice.", 409)

    total = sum((Decimal(li.subtotal) for li in pedido.lineas), Decimal(0))
    recibido = cambio = None
    piezas: dict[int, int] = {}
    if datos.medio_pago == "EFECTIVO" and datos.valor_recibido is not None:
        recibido = Decimal(datos.valor_recibido)
        if recibido < total:
            raise ErrorApp("PAGO_INSUFICIENTE",
                           f"A payment of ${int(recibido):,} does not cover the total of ${int(total):,}: "
                           f"${int(total - recibido):,} missing.", 422)
        cambio = recibido - total
        try:
            piezas = algoritmos.cambio_voraz(int(cambio))  # algoritmo 5
        except ValueError as exc:
            raise ErrorApp("CAMBIO_IMPOSIBLE", str(exc), 422) from exc

    mesa = pedido.mesa
    factura = Factura(
        numero=siguiente_numero_factura(db), pedido_id=pedido.id, sede_id=pedido.sede_id,
        mesa_id=mesa.id, mesa_numero=mesa.numero, mesero=pedido.mesero,
        cajero_id=usuario.id, cajero=usuario.usuario, medio_pago=datos.medio_pago, total=total,
        valor_recibido=recibido, cambio=cambio,
    )
    for li in pedido.lineas:  # c2: copia de lo que se pidió, con el valor de venta del momento
        producto = db.get(Producto, li.producto_id)
        factura.lineas.append(FacturaLinea(
            producto_id=li.producto_id, codigo=li.codigo, nombre=li.nombre, cantidad=li.cantidad,
            valor_compra=Decimal(producto.valor_compra), precio_unitario=li.precio_unitario,
            subtotal=li.subtotal))
    db.add(factura)

    pedido.estado = "CERRADO"                                      # c5
    pedido.cerrado_en = datetime.now(UTC)
    pedido.total = total
    if _otro_pedido_abierto(db, mesa.id, pedido.id) is None:
        mesa.estado = "LIBRE"                                      # c5
    db.flush()
    registrar(db, accion="FACTURAR", entidad="facturas", entidad_id=factura.id,
              detalle=f"{numero_formateado(factura.numero)} · order #{pedido.id} · table {mesa.numero} · "
                      f"{datos.medio_pago} · ${int(total):,}", **_contexto(usuario, request))
    db.commit()
    db.refresh(factura)
    return a_factura_salida(factura, piezas)


def _otro_pedido_abierto(db: Session, mesa_id: int, pedido_id: int) -> Pedido | None:
    return db.scalar(select(Pedido).where(Pedido.mesa_id == mesa_id, Pedido.estado == "ABIERTO",
                                          Pedido.id != pedido_id))


@facturas.get("", response_model=list[FacturaSalida], summary="List issued invoices (HU-023 c6)")
def listar_facturas(usuario: UsuarioActual = Depends(cajero_o_admin), db: Session = Depends(get_db),
                    sede_id: int | None = None, desde: date | None = None, hasta: date | None = None,
                    medio_pago: str | None = None, limite: int = Query(default=200, ge=1, le=1000)):
    sede_id = sede_autorizada(usuario, sede_id)
    consulta = select(Factura)
    if sede_id is not None:
        consulta = consulta.where(Factura.sede_id == sede_id)
    if desde is not None or hasta is not None:
        inicio, fin = reportes.rango_utc(desde or date(2000, 1, 1), hasta or reportes.hoy_local())
        consulta = consulta.where(Factura.emitida_en >= inicio, Factura.emitida_en < fin)
    if medio_pago:
        if medio_pago.upper() not in ("EFECTIVO", "TARJETA_DEBITO", "TARJETA_CREDITO"):
            raise ErrorApp("MEDIO_PAGO_INVALIDO", f"Payment method '{medio_pago}' does not exist: use "
                           "EFECTIVO, TARJETA_DEBITO or TARJETA_CREDITO.", 422)
        consulta = consulta.where(Factura.medio_pago == medio_pago.upper())
    return [a_factura_salida(f) for f in db.scalars(consulta.order_by(Factura.numero.desc()).limit(limite))]


@facturas.get("/numero/{numero}", response_model=FacturaSalida, summary="Find an invoice by its number")
def obtener_factura_por_numero(numero: int, usuario: UsuarioActual = Depends(cajero_o_admin),
                               db: Session = Depends(get_db)):
    factura = db.scalar(select(Factura).where(Factura.numero == numero))
    if factura is None:
        raise ErrorApp("NO_ENCONTRADO", f"There is no invoice number {numero_formateado(numero)}.", 404)
    return a_factura_salida(_factura_de_mi_sede(db, factura.id, usuario))


@facturas.get("/{factura_id}", response_model=FacturaSalida, summary="Invoice detail (HU-023 c6)")
def obtener_factura(factura_id: int, usuario: UsuarioActual = Depends(cajero_o_admin),
                    db: Session = Depends(get_db)):
    return a_factura_salida(_factura_de_mi_sede(db, factura_id, usuario))


NOMBRES_MEDIO_PAGO = {"EFECTIVO": "Efectivo", "TARJETA_DEBITO": "Tarjeta débito",
                      "TARJETA_CREDITO": "Tarjeta crédito"}


def _pesos(valor) -> str:
    return "$" + f"{int(Decimal(valor)):,}".replace(",", ".")


@facturas.get("/{factura_id}/impresion", summary="Printable invoice (HTML, HU-023 c6)",
              response_class=Response)
def imprimir_factura(factura_id: int, request: Request, usuario: UsuarioActual = Depends(cajero_o_admin),
                     db: Session = Depends(get_db)):
    """Tirilla de 80 mm lista para `window.print()`. Cada reimpresión queda en la auditoría."""
    from html import escape

    factura = _factura_de_mi_sede(db, factura_id, usuario)
    emitida = factura.emitida_en
    if emitida.tzinfo is None:
        emitida = emitida.replace(tzinfo=UTC)
    emitida = emitida.astimezone(reportes.ZONA_BAR)
    filas = "".join(
        f"<tr><td>{li.cantidad} × {escape(li.nombre)}</td><td class=v>{_pesos(li.subtotal)}</td></tr>"
        for li in factura.lineas)
    pago = f"<p>Medio de pago: <b>{NOMBRES_MEDIO_PAGO[factura.medio_pago]}</b></p>"
    if factura.valor_recibido is not None:
        pago += (f"<p>Recibido: {_pesos(factura.valor_recibido)} · Cambio: "
                 f"{_pesos(factura.cambio or 0)}</p>")
    html = f"""<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">
<title>Factura {numero_formateado(factura.numero)}</title>
<style>body{{font-family:monospace;width:72mm;margin:0 auto;font-size:12px}}h1{{font-size:16px;
text-align:center;margin:4px 0}}table{{width:100%;border-collapse:collapse}}td.v{{text-align:right}}
.t td{{border-top:1px dashed #000;font-weight:bold;padding-top:4px}}p{{margin:2px 0}}
@media print{{@page{{size:80mm auto;margin:4mm}}}}</style></head>
<body onload="window.print()"><h1>Bar de Moe</h1>
<p style="text-align:center">{escape(factura.sede.nombre)}</p>
<p><b>FACTURA DE VENTA N.º {numero_formateado(factura.numero)}</b></p>
<p>Fecha: {emitida:%Y-%m-%d %H:%M} · Mesa {factura.mesa_numero}</p>
<p>Mesero: {escape(factura.mesero)} · Cajero: {escape(factura.cajero)}</p>
<table>{filas}<tr class=t><td>TOTAL</td><td class=v>{_pesos(factura.total)}</td></tr></table>
{pago}<p style="text-align:center;margin-top:8px">¡Gracias por su visita!</p></body></html>"""
    registrar(db, accion="IMPRIMIR_FACTURA", entidad="facturas", entidad_id=factura.id,
              detalle=numero_formateado(factura.numero), **_contexto(usuario, request))
    db.commit()
    return Response(content=html, media_type="text/html; charset=utf-8", headers={
        "Content-Disposition": f'inline; filename="factura-{numero_formateado(factura.numero)}.html"'})


# ------------------------------------------------------------ REPORTES (M6)
reportes_router = APIRouter(prefix="/reportes", tags=["reports (M6)"])


def _parsear_sedes(texto: str | None) -> list[int] | None:
    if texto is None or not texto.strip():
        return None
    try:
        ids = sorted({int(p) for p in texto.split(",") if p.strip()})
    except ValueError as exc:
        raise ErrorApp("SEDES_INVALIDAS", f"'{texto}' is not a valid branch list: use ids separated "
                       "by commas, for example 1,3.", 422) from exc
    return ids or None


def _alcance_reporte(db: Session, usuario: UsuarioActual, sedes: str | None) -> tuple[list[int] | None, bool]:
    """HU-024 c1 a c4: la sede la decide el perfil, no el navegador.

    - ADMINISTRADOR: todas (None) o las que pida (c2).
    - CAJERO: solo la suya; si pide otra, 403 aunque llame la URL a mano (c3).
    - MESERO: ya fue rechazado por `cajero_o_admin` (c4).
    """
    pedidas = _parsear_sedes(sedes)
    if usuario.perfil != PERFIL_ADMIN:
        if pedidas is not None and pedidas != [usuario.sede_id]:
            sede_autorizada(usuario, next(s for s in pedidas if s != usuario.sede_id))
        return [sede_autorizada(usuario, None)], True
    for sede_id in pedidas or []:
        obtener_o_404(db, Sede, sede_id, "branch")
    return pedidas, False


def _validar_rango(desde: date | None, hasta: date | None) -> tuple[date, date]:
    hasta = hasta or reportes.hoy_local()
    desde = desde or hasta
    if desde > hasta:
        raise ErrorApp("RANGO_INVALIDO", f"The start date ({desde}) is after the end date ({hasta}).", 422)
    if (hasta - desde).days >= reportes.MAXIMO_DIAS:
        raise ErrorApp("RANGO_INVALIDO", f"The range covers {(hasta - desde).days + 1} days; the maximum "
                       f"is {reportes.MAXIMO_DIAS} to keep the 2-second response time (RNF-02).", 422)
    return desde, hasta


def _filas_reporte(db: Session, desde: date, hasta: date, sedes: list[int] | None,
                   orden: str) -> list[reportes.Fila]:
    """Una sola función arma las filas de la pantalla y del Excel (c7)."""
    inicio, fin = reportes.rango_utc(desde, hasta)
    consulta = (select(FacturaLinea, Factura.emitida_en, Factura.sede_id, Sede.nombre)
                .join(Factura, FacturaLinea.factura_id == Factura.id)
                .join(Sede, Factura.sede_id == Sede.id)
                .where(Factura.emitida_en >= inicio, Factura.emitida_en < fin))
    if sedes is not None:
        consulta = consulta.where(Factura.sede_id.in_(sedes))
    lineas = (reportes.LineaVendida(
        emitida_en=emitida, sede_id=sede_id, sede=nombre_sede, producto_id=li.producto_id,
        codigo=li.codigo, nombre=li.nombre, cantidad=li.cantidad,
        valor_compra=Decimal(li.valor_compra), valor_venta=Decimal(li.precio_unitario))
        for li, emitida, sede_id, nombre_sede in db.execute(consulta))
    return reportes.ordenar(reportes.agrupar(lineas), orden)


ParametroOrden = Annotated[str, Query(pattern="^(fecha|ganancia|cantidad)$",
                                      description="fecha · ganancia · cantidad (merge sort, algoritmo 8)")]
ParametroSedes = Annotated[str | None, Query(max_length=200,
                                             description="Branch ids separated by commas (admin only)")]


@reportes_router.get("/ventas", response_model=ReporteVentasSalida,
                     summary="Sales and profit report (HU-024)")
def reporte_ventas(usuario: UsuarioActual = Depends(cajero_o_admin), db: Session = Depends(get_db),
                   desde: date | None = None, hasta: date | None = None,
                   sedes: ParametroSedes = None, orden: ParametroOrden = "fecha"):
    desde, hasta = _validar_rango(desde, hasta)
    alcance, fija = _alcance_reporte(db, usuario, sedes)
    filas = _filas_reporte(db, desde, hasta, alcance, orden)
    return ReporteVentasSalida(
        desde=desde, hasta=hasta, sedes=alcance, sede_fija=fija, orden=orden,
        filas=[vars(f) for f in filas], totales_por_sede=reportes.totales_por_sede(filas),
        total_cantidad=sum(f.cantidad for f in filas),
        total_ventas=sum((f.valor_venta * f.cantidad for f in filas), Decimal(0)),
        total_ganancia=sum((f.ganancia for f in filas), Decimal(0)),
    )


@reportes_router.get("/ventas/excel", summary="Export the sales report to Excel (HU-024 c7)",
                     response_class=Response)
def exportar_reporte_ventas(request: Request, usuario: UsuarioActual = Depends(cajero_o_admin),
                            db: Session = Depends(get_db), desde: date | None = None,
                            hasta: date | None = None, sedes: ParametroSedes = None,
                            orden: ParametroOrden = "fecha"):
    desde, hasta = _validar_rango(desde, hasta)
    alcance, _ = _alcance_reporte(db, usuario, sedes)
    filas = _filas_reporte(db, desde, hasta, alcance, orden)
    if alcance is None:
        texto_alcance = "todas"
    else:
        nombres = dict(db.execute(select(Sede.id, Sede.nombre).where(Sede.id.in_(alcance))).all())
        texto_alcance = ", ".join(nombres.get(s, str(s)) for s in alcance)
    contenido = reportes.a_excel(filas, desde=desde, hasta=hasta, alcance=texto_alcance,
                                 usuario=usuario.usuario)
    registrar(db, accion="EXPORTAR_REPORTE", entidad="reportes", entidad_id=None,
              detalle=f"ventas {desde}..{hasta} · sedes {texto_alcance} · {len(filas)} fila(s)",
              **_contexto(usuario, request))
    db.commit()
    nombre = f"reporte-ventas_{desde}_{hasta}.xlsx"
    return Response(content=contenido,
                    media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": f'attachment; filename="{nombre}"',
                             "X-Total-Count": str(len(filas))})


# ------------------------------------------- ALGORITMOS DE LA ASIGNATURA (lab)
algoritmos_router = APIRouter(prefix="/algoritmos", tags=["algorithms (Diseño de Algoritmos)"])

CATALOGO_ALGORITMOS = [
    {"numero": 1, "algoritmo": "Mochila 0/1 (programación dinámica)", "tecnica": "programación dinámica",
     "ruta": "GET /inventario/sugerencia-compra", "uso": "Qué reponer con un presupuesto (HU-021)"},
    {"numero": 2, "algoritmo": "MCD de Euclides", "tecnica": "iterativo y recursivo",
     "ruta": "GET /algoritmos/mcd", "uso": "Reduce la tabla de la mochila"},
    {"numero": 3, "algoritmo": "Mochila por razón beneficio/costo", "tecnica": "voraz",
     "ruta": "GET /inventario/sugerencia-compra", "uso": "Respaldo cuando la tabla no cabe en 2 s"},
    {"numero": 4, "algoritmo": "Existencia acumulada", "tecnica": "iterativo y recursivo",
     "ruta": "GET /inventario/conciliacion", "uso": "Comprueba el saldo contra los movimientos (CU-32)"},
    {"numero": 5, "algoritmo": "Cambio en billetes y monedas", "tecnica": "voraz",
     "ruta": "GET /algoritmos/cambio · POST /facturas", "uso": "Vueltas al cobrar en efectivo (HU-023)"},
    {"numero": 6, "algoritmo": "Recorrido en un grafo (conjuntos C y S)", "tecnica": "voraz",
     "ruta": "GET /mesas/ruta-entrega", "uso": "Ruta del mesero por las mesas con pedido abierto (HU-013)"},
    {"numero": 7, "algoritmo": "Cadena lexicográficamente menor", "tecnica": "voraz",
     "ruta": "GET /pedidos/cola-barra", "uso": "Orden de las comandas en la barra (HU-022)"},
    {"numero": 8, "algoritmo": "Merge sort estable", "tecnica": "divide y vencerás",
     "ruta": "GET /reportes/ventas?orden=", "uso": "Orden del reporte de ventas (HU-024)"},
    {"numero": 9, "algoritmo": "Burbuja, inserción, selección, quicksort y mezcla", "tecnica": "ordenamiento",
     "ruta": "GET /algoritmos/ordenar-inventario", "uso": "Ordena el inventario y compara los métodos"},
    {"numero": 10, "algoritmo": "Búsqueda binaria", "tecnica": "iterativo y recursivo",
     "ruta": "GET /algoritmos/buscar-producto", "uso": "Busca un producto por código (catálogo ordenado)"},
    {"numero": 11, "algoritmo": "Torres de Hanoi", "tecnica": "recursivo e iterativo",
     "ruta": "GET /algoritmos/hanoi", "uso": "Pasar canastas apiladas entre las estibas A, B y C"},
    {"numero": 12, "algoritmo": "Suma exacta (combo por monto)", "tecnica": "backtracking vs. voraz",
     "ruta": "GET /algoritmos/combo", "uso": "Armar un pedido que gaste exactamente un monto"},
]


@algoritmos_router.get("", summary="Catalog of the course algorithms and where they are used")
def catalogo_algoritmos(_: UsuarioActual = Depends(usuario_actual)):
    return CATALOGO_ALGORITMOS


CAMPOS_ORDEN = {
    "existencia": lambda f: f["existencia"],
    "nombre": lambda f: f["nombre"].lower(),
    "codigo": lambda f: f["codigo"],
    "valor_venta": lambda f: f["valor_venta"],
    "ganancia_unitaria": lambda f: f["ganancia_unitaria"],
}
MAX_FILAS_CUADRATICOS = 3_000   # n² comparaciones: por encima no caben en los 2 s del RNF-02


@algoritmos_router.get("/ordenar-inventario", summary="Sort the branch stock with a chosen method")
def ordenar_inventario(
    usuario: UsuarioActual = Depends(usuario_actual), db: Session = Depends(get_db),
    sede_id: int | None = None,
    metodo: Annotated[str, Query(pattern="^(burbuja|insercion|seleccion|quicksort|mezcla)$")] = "quicksort",
    campo: Annotated[str, Query(pattern="^(existencia|nombre|codigo|valor_venta|ganancia_unitaria)$")]
    = "existencia",
    descendente: bool = False, comparar: bool = True,
):
    """Ordena el inventario real con el método pedido y cuenta comparaciones e intercambios.

    Con `comparar=true` corre los cinco métodos sobre los mismos datos: así se ve en
    la sustentación que los O(n²) comparan muchísimo más que quicksort y mezcla.
    """
    import time

    sede_id = sede_autorizada(usuario, sede_id)
    consulta = select(InventarioSede).join(Producto).where(InventarioSede.activo.is_(True),
                                                           Producto.activo.is_(True))
    if sede_id is not None:
        consulta = consulta.where(InventarioSede.sede_id == sede_id)
    filas = [{"producto_id": i.producto_id, "codigo": i.producto.codigo, "nombre": i.producto.nombre,
              "sede_id": i.sede_id, "existencia": i.existencia,
              "valor_venta": int(Decimal(i.producto.valor_venta)),
              "ganancia_unitaria": int(Decimal(i.producto.valor_venta) - Decimal(i.producto.valor_compra))}
             for i in db.scalars(consulta.order_by(InventarioSede.id))]
    clave = CAMPOS_ORDEN[campo]

    def correr(nombre: str) -> tuple[list, dict]:
        inicio = time.perf_counter()
        ordenadas, contador = algoritmos.ordenar_con(nombre, filas, clave=clave, descendente=descendente)
        return ordenadas, {"metodo": nombre, "complejidad": algoritmos.METODOS_ORDENAMIENTO[nombre][1],
                           "comparaciones": contador.comparaciones, "intercambios": contador.intercambios,
                           "tiempo_ms": round((time.perf_counter() - inicio) * 1000, 3)}

    ordenadas, estadistica = correr(metodo)
    comparativa = []
    if comparar:
        esperado = [clave(f) for f in ordenadas]
        for nombre in algoritmos.METODOS_ORDENAMIENTO:
            if nombre in ("burbuja", "insercion", "seleccion") and len(filas) > MAX_FILAS_CUADRATICOS:
                comparativa.append({"metodo": nombre, "omitido": f"more than {MAX_FILAS_CUADRATICOS} rows"})
                continue
            otras, datos = correr(nombre)
            datos["mismo_orden"] = [clave(f) for f in otras] == esperado
            comparativa.append(datos)
    return {"sede_id": sede_id, "campo": campo, "descendente": descendente, "n": len(filas),
            **estadistica, "filas": ordenadas, "comparativa": comparativa}


@algoritmos_router.get("/buscar-producto", summary="Binary search of a product by code")
def buscar_producto_binaria(
    codigo: Annotated[str, Query(min_length=1, max_length=30)],
    modo: Annotated[str, Query(pattern="^(iterativa|recursiva)$")] = "iterativa",
    _: UsuarioActual = Depends(usuario_actual), db: Session = Depends(get_db),
):
    """El catálogo se ordena por código (merge sort) y se busca partiendo el rango a la mitad.

    Devuelve cada paso (rango, posición del medio y hacia dónde siguió). Con n
    productos nunca hay más de ⌊log₂ n⌋ + 1 pasos.
    """
    catalogo = algoritmos.ordenar_mezcla(
        [{"id": p.id, "codigo": p.codigo, "nombre": p.nombre, "valor_venta": int(Decimal(p.valor_venta))}
         for p in db.scalars(select(Producto).where(Producto.activo.is_(True)))],
        clave=lambda p: p["codigo"])
    buscar = (algoritmos.busqueda_binaria_iterativa if modo == "iterativa"
              else algoritmos.busqueda_binaria_recursiva)
    objetivo = codigo.strip().upper()
    indice, pasos = buscar(catalogo, objetivo, clave=lambda p: p["codigo"])
    return {"codigo": objetivo, "modo": modo, "n": len(catalogo), "encontrado": indice >= 0,
            "producto": catalogo[indice] if indice >= 0 else None,
            "pasos": [{"bajo": p.bajo, "alto": p.alto, "medio": p.medio, "codigo_medio": p.valor_medio,
                       "decision": p.decision} for p in pasos],
            "maximo_teorico": max(len(catalogo), 1).bit_length()}


@algoritmos_router.get("/hanoi", summary="Towers of Hanoi: move stacked crates between pallets")
def torres_de_hanoi(
    discos: Annotated[int, Query(ge=1, le=algoritmos.MAX_DISCOS_HANOI, description="Crates (disks)")] = 3,
    modo: Annotated[str, Query(pattern="^(recursivo|iterativo)$")] = "recursivo",
    _: UsuarioActual = Depends(usuario_actual),
):
    """Canastas apiladas de mayor (abajo) a menor en la estiba A; pasarlas a la C usando la B,
    una por vez y sin poner nunca una grande sobre una pequeña. Se calcula con el modo
    pedido, se verifica simulando cada movimiento y se compara con el otro modo."""
    funcion = algoritmos.hanoi_recursivo if modo == "recursivo" else algoritmos.hanoi_iterativo
    otra = algoritmos.hanoi_iterativo if modo == "recursivo" else algoritmos.hanoi_recursivo
    movimientos = funcion(discos)
    final = algoritmos.simular_hanoi(discos, movimientos)
    return {"discos": discos, "modo": modo, "total_movimientos": len(movimientos),
            "formula": f"2^{discos} - 1 = {2 ** discos - 1}",
            "verificado": final["C"] == list(range(discos, 0, -1)),
            "coincide_con_el_otro_modo": otra(discos) == movimientos,
            "estado_final": final,
            "movimientos": [{"numero": i, "canasta": d, "desde": a, "hacia": b}
                            for i, (d, a, b) in enumerate(movimientos, start=1)]}


@algoritmos_router.get("/combo", summary="Backtracking: products that add up exactly to an amount")
def combo_por_monto(
    monto: Annotated[int, Query(gt=0, le=2_000_000)],
    usuario: UsuarioActual = Depends(usuario_actual), db: Session = Depends(get_db),
    sede_id: int | None = None,
    max_unidades: Annotated[int, Query(ge=1, le=12, description="Units in the whole combo")] = 6,
    max_por_producto: Annotated[int, Query(ge=1, le=6)] = 3,
):
    """Un cliente quiere gastar exactamente `monto` (un bono, la cuenta de la mesa redonda…).

    - Backtracking: explora el árbol de decisiones con poda y encuentra una combinación
      exacta si existe (prefiere la de menos unidades).
    - Voraz: toma siempre lo más caro que quepa. Es rápido pero puede quedarse corto.
    Solo entran productos activos con existencia en la sede.
    """
    sede_id = sede_autorizada(usuario, sede_id)
    if sede_id is None:
        raise ErrorApp("SEDE_REQUERIDA", "Send sede_id: the combo depends on the stock of one branch.", 422)
    sede_activa(db, sede_id)
    filas = db.scalars(select(InventarioSede).join(Producto).where(
        InventarioSede.sede_id == sede_id, InventarioSede.activo.is_(True), Producto.activo.is_(True),
        InventarioSede.existencia > 0))
    opciones = [algoritmos.Opcion(clave=f.producto_id, nombre=f.producto.nombre,
                                  precio=int(Decimal(f.producto.valor_venta)),
                                  maximo=min(f.existencia, max_por_producto)) for f in filas]
    nombres = {o.clave: (o.nombre, o.precio) for o in opciones}

    def detalle(combinacion: dict[int, int]) -> list[dict]:
        return [{"producto_id": c, "nombre": nombres[c][0], "unidades": k, "precio": nombres[c][1],
                 "subtotal": k * nombres[c][1]} for c, k in combinacion.items()]

    bt = algoritmos.combo_backtracking(opciones, monto, max_unidades_total=max_unidades)
    voraz = algoritmos.combo_voraz(opciones, monto, max_unidades_total=max_unidades)
    return {
        "sede_id": sede_id, "monto": monto, "productos_considerados": len(opciones),
        "backtracking": {"encontrado": bt.encontrado, "total": bt.total, "combo": detalle(bt.combinacion),
                         "soluciones_halladas": len(bt.soluciones), "nodos_explorados": bt.nodos_explorados,
                         "podas": bt.podas, "limite_alcanzado": bt.limite_alcanzado},
        "voraz": {"encontrado": voraz.encontrado, "total": voraz.total, "faltante": monto - voraz.total,
                  "combo": detalle(voraz.combinacion)},
        "conclusion": ("Both reach the exact amount." if bt.encontrado and voraz.encontrado else
                       "Only backtracking reaches the exact amount: greedy is not always optimal."
                       if bt.encontrado else "No combination of the available products adds up exactly "
                       "to that amount."),
    }


@algoritmos_router.get("/mcd", summary="GCD by Euclid: iterative, recursive and its steps")
def mcd(a: Annotated[int, Query(ge=0, le=10**12)], b: Annotated[int, Query(ge=0, le=10**12)],
        _: UsuarioActual = Depends(usuario_actual)):
    pasos = algoritmos.mcd_con_pasos(a, b)
    return {"a": a, "b": b, "iterativo": algoritmos.mcd_iterativo(a, b),
            "recursivo": algoritmos.mcd_recursivo(a, b),
            "pasos": [{"a": x, "b": y, "residuo": r} for x, y, r in pasos]}


@algoritmos_router.get("/cambio", summary="Change in Colombian bills and coins (greedy)")
def cambio(monto: Annotated[int, Query(ge=0, le=100_000_000)], _: UsuarioActual = Depends(usuario_actual)):
    try:
        piezas = algoritmos.cambio_voraz(monto)
    except ValueError as exc:
        raise ErrorApp("CAMBIO_IMPOSIBLE", str(exc), 422) from exc
    return {"monto": monto, "piezas": [{"denominacion": d, "cantidad": c} for d, c in piezas.items()],
            "total_piezas": sum(piezas.values())}


for router in (sedes, mesas, tipos, proveedores, productos, inventario, pedidos, facturas, reportes_router,
               algoritmos_router):
    app.include_router(router)
# HU-008: la auditoría de este servicio también se puede consultar (solo ADMINISTRADOR).
app.include_router(router_consulta(get_db, solo_admin))

