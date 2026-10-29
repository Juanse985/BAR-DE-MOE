"""parametrizacion-service — M2 Parametrización maestra.

Sedes, mesas, tipos de producto, proveedores y productos. Solo el perfil
ADMINISTRADOR puede escribir; cualquier perfil autenticado puede consultar,
pero CAJERO y MESERO solo ven los datos de su sede (tabla 3.1 de la propuesta).
Toda escritura queda registrada en la tabla de auditoría (RNF-12), con la IP
real y el X-Request-Id que llegan del gateway.
"""
import csv
from contextlib import asynccontextmanager
from io import StringIO

from fastapi import APIRouter, Depends, FastAPI, File, Request, UploadFile
from sqlalchemy import inspect, select, text
from sqlalchemy.orm import Session

from barmoe_common.app import crear_app
from barmoe_common.auditoria import contexto_http, registrar, router_consulta
from barmoe_common.db import Base, crear_session_factory, dependencia_db
from barmoe_common.deps import UsuarioActual, construir_autenticacion
from barmoe_common.errors import ErrorApp

from .config import config
from .models import Mesa, Pedido, PedidoDetalle, Producto, Proveedor, Sede, TipoProducto
from .schemas import (
    InventarioAjuste,
    MesaActualizar,
    MesaCrear,
    MesaEstadoActualizar,
    MesaSalida,
    PedidoCrear,
    PedidoEstadoActualizar,
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
    engine = SessionLocal.engine
    Base.metadata.create_all(bind=engine)
    cols = {c["name"] for c in inspect(engine).get_columns("productos")}
    with engine.begin() as conn:
        if "stock" not in cols:
            conn.execute(text("ALTER TABLE productos ADD COLUMN stock INTEGER DEFAULT 24"))
        if "stock_minimo" not in cols:
            conn.execute(text("ALTER TABLE productos ADD COLUMN stock_minimo INTEGER DEFAULT 5"))
    yield


app = crear_app(
    config,
    titulo="Bar de Moe · parametrizacion-service",
    descripcion="M2 · Parametrización maestra. DATHEON S.A.S.",
    lifespan=ciclo_de_vida,
    auditar_rechazos=SessionLocal,  # DEF-05 · C-1
)

PERFIL_ADMIN = "ADMINISTRADOR"


# --------------------------------------------------------------- utilidades
def obtener_o_404(db: Session, modelo, entidad_id: int, etiqueta: str):
    fila = db.get(modelo, entidad_id)
    if fila is None:
        raise ErrorApp("NO_ENCONTRADO", f"No existe {etiqueta} con id {entidad_id}.", 404)
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
        raise ErrorApp("SIN_SEDE", "Su usuario no tiene una sede asignada.", 403)
    if sede_id is not None and sede_id != usuario.sede_id:
        raise ErrorApp("SEDE_NO_AUTORIZADA", "Solo puede consultar la información de su sede.", 403)
    return usuario.sede_id


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


# -------------------------------------------------------------------- SEDES
sedes = APIRouter(prefix="/sedes", tags=["sedes"])


@sedes.post("", response_model=SedeSalida, status_code=201, summary="Crear sede")
def crear_sede(datos: SedeCrear, request: Request, copiar_catalogo: bool = False,
               usuario: UsuarioActual = Depends(solo_admin), db: Session = Depends(get_db)):
    if db.scalar(select(Sede).where(Sede.nombre == datos.nombre)):
        raise ErrorApp("SEDE_DUPLICADA", f"Ya existe la sede '{datos.nombre}'.", 409)
    nueva = guardar(db, Sede(**datos.model_dump()), accion="CREAR", entidad="sedes", usuario=usuario,
                    request=request)
    if copiar_catalogo:
        existentes = list(db.scalars(select(Producto).order_by(Producto.id)))
        vistos: set[str] = set()
        for base_prod in existentes:
            if base_prod.codigo in vistos:
                continue
            vistos.add(base_prod.codigo)
            db.add(
                Producto(
                    codigo=base_prod.codigo,
                    nombre=base_prod.nombre,
                    sede_id=nueva.id,
                    tipo_producto_id=base_prod.tipo_producto_id,
                    proveedor_id=base_prod.proveedor_id,
                    valor_compra=base_prod.valor_compra,
                    valor_venta=base_prod.valor_venta,
                    stock=24,
                    stock_minimo=base_prod.stock_minimo or 5,
                    activo=base_prod.activo,
                )
            )
        db.commit()
    return nueva


@sedes.get("", response_model=list[SedeSalida], summary="Listar sedes")
def listar_sedes(usuario: UsuarioActual = Depends(usuario_actual), db: Session = Depends(get_db),
                 solo_activas: bool = True):
    consulta = select(Sede)
    propia = sede_autorizada(usuario, None)
    if propia is not None:
        consulta = consulta.where(Sede.id == propia)
    if solo_activas:
        consulta = consulta.where(Sede.activa.is_(True))
    return list(db.scalars(consulta.order_by(Sede.nombre)))


@sedes.get("/{sede_id}", response_model=SedeSalida, summary="Consultar sede")
def obtener_sede(sede_id: int, usuario: UsuarioActual = Depends(usuario_actual),
                 db: Session = Depends(get_db)):
    sede_autorizada(usuario, sede_id)
    return obtener_o_404(db, Sede, sede_id, "la sede")


@sedes.patch("/{sede_id}", response_model=SedeSalida, summary="Actualizar sede")
def actualizar_sede(sede_id: int, datos: SedeActualizar, request: Request,
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

    return aplicar_cambios(db, sede, datos, entidad="sedes", usuario=usuario, request=request)

# -------------------------------------------------------------------- MESAS
mesas = APIRouter(prefix="/mesas", tags=["mesas"])


@mesas.post("", response_model=MesaSalida, status_code=201, summary="Crear mesa")
def crear_mesa(datos: MesaCrear, request: Request, usuario: UsuarioActual = Depends(solo_admin),
               db: Session = Depends(get_db)):
    obtener_o_404(db, Sede, datos.sede_id, "la sede")
    existe = db.scalar(select(Mesa).where(Mesa.sede_id == datos.sede_id, Mesa.numero == datos.numero))
    if existe:
        raise ErrorApp("MESA_DUPLICADA", f"La mesa {datos.numero} ya existe en esa sede.", 409)
    return guardar(db, Mesa(**datos.model_dump()), accion="CREAR", entidad="mesas", usuario=usuario,
                   request=request)


@mesas.get("", response_model=list[MesaSalida], summary="Listar mesas")
def listar_mesas(usuario: UsuarioActual = Depends(usuario_actual), db: Session = Depends(get_db),
                 sede_id: int | None = None, estado: str | None = None):
    sede_id = sede_autorizada(usuario, sede_id)
    consulta = select(Mesa)
    if sede_id is not None:
        consulta = consulta.where(Mesa.sede_id == sede_id)
    if estado:
        consulta = consulta.where(Mesa.estado == estado.upper())
    return list(db.scalars(consulta.order_by(Mesa.sede_id, Mesa.numero)))


@mesas.patch("/{mesa_id}", response_model=MesaSalida, summary="Actualizar mesa")
def actualizar_mesa(mesa_id: int, datos: MesaActualizar, request: Request,
                    usuario: UsuarioActual = Depends(solo_admin), db: Session = Depends(get_db)):
    mesa = obtener_o_404(db, Mesa, mesa_id, "la mesa")
    return aplicar_cambios(db, mesa, datos, entidad="mesas", usuario=usuario, request=request)


@mesas.post("/{mesa_id}/estado", response_model=MesaSalida, summary="Cambiar estado operativo de mesa")
def cambiar_estado_mesa(mesa_id: int, datos: MesaEstadoActualizar, request: Request,
                        usuario: UsuarioActual = Depends(usuario_actual), db: Session = Depends(get_db)):
    mesa = obtener_o_404(db, Mesa, mesa_id, "la mesa")
    sede_autorizada(usuario, mesa.sede_id)
    if not mesa.activa:
        raise ErrorApp("MESA_INACTIVA", "No se puede operar una mesa inactiva.", 409)
    mesa.estado = datos.estado
    if datos.estado == "LIBRE":
        abiertos = list(
            db.scalars(
                select(Pedido).where(
                    Pedido.mesa_id == mesa.id,
                    Pedido.estado.in_(("ABIERTO", "ENTREGADO")),
                )
            )
        )
        for ped in abiertos:
            ped.estado = "CERRADO"
    registrar(db, accion="CAMBIAR_ESTADO_MESA", entidad="mesas", entidad_id=mesa.id,
              detalle=f"estado={datos.estado}", **_contexto(usuario, request))
    db.commit()
    db.refresh(mesa)
    return mesa


# ------------------------------------------------------------ TIPOS PRODUCTO
tipos = APIRouter(prefix="/tipos-producto", tags=["tipos de producto"])


@tipos.post("", response_model=TipoProductoSalida, status_code=201, summary="Crear tipo de producto")
def crear_tipo(datos: TipoProductoCrear, request: Request, usuario: UsuarioActual = Depends(solo_admin),
               db: Session = Depends(get_db)):
    if db.scalar(select(TipoProducto).where(TipoProducto.nombre == datos.nombre)):
        raise ErrorApp("TIPO_DUPLICADO", f"Ya existe el tipo '{datos.nombre}'.", 409)
    return guardar(db, TipoProducto(**datos.model_dump()), accion="CREAR",
                   entidad="tipos_producto", usuario=usuario, request=request)


@tipos.get("", response_model=list[TipoProductoSalida], summary="Listar tipos de producto")
def listar_tipos(_: UsuarioActual = Depends(usuario_actual), db: Session = Depends(get_db)):
    return list(db.scalars(select(TipoProducto).order_by(TipoProducto.nombre)))

@tipos.patch("/{tipo_id}", response_model=TipoProductoSalida, summary="Actualizar tipo de producto")
def actualizar_tipo(tipo_id: int, datos: TipoProductoActualizar, request: Request,
                    usuario: UsuarioActual = Depends(solo_admin), db: Session = Depends(get_db)):
    tipo = obtener_o_404(db, TipoProducto, tipo_id, "el tipo de producto")
    if datos.activo is False and tipo.activo:
        tiene_productos_activos = db.scalar(
            select(Producto.id)
            .where(Producto.tipo_producto_id == tipo_id, Producto.activo.is_(True)).limit(1)
        )
        if tiene_productos_activos:
            raise ErrorApp("TIPO_CON_PRODUCTOS_ACTIVOS",
                           "No se puede inactivar el tipo: tiene productos activos asociados.", 409)
    return aplicar_cambios(db, tipo, datos, entidad="tipos_producto", usuario=usuario, request=request)


# -------------------------------------------------------------- PROVEEDORES
proveedores = APIRouter(prefix="/proveedores", tags=["proveedores"])


@proveedores.post("", response_model=ProveedorSalida, status_code=201, summary="Crear proveedor")
def crear_proveedor(datos: ProveedorCrear, request: Request, usuario: UsuarioActual = Depends(solo_admin),
                    db: Session = Depends(get_db)):
    if db.scalar(select(Proveedor).where(Proveedor.nit == datos.nit)):
        raise ErrorApp("PROVEEDOR_DUPLICADO", f"Ya existe un proveedor con NIT {datos.nit}.", 409)
    return guardar(db, Proveedor(**datos.model_dump()), accion="CREAR",
                   entidad="proveedores", usuario=usuario, request=request)


@proveedores.get("", response_model=list[ProveedorSalida], summary="Listar proveedores")
def listar_proveedores(_: UsuarioActual = Depends(usuario_actual), db: Session = Depends(get_db)):
    return list(db.scalars(select(Proveedor).order_by(Proveedor.nombre)))


@proveedores.patch("/{proveedor_id}", response_model=ProveedorSalida, summary="Actualizar proveedor")
def actualizar_proveedor(proveedor_id: int, datos: ProveedorActualizar, request: Request,
                         usuario: UsuarioActual = Depends(solo_admin), db: Session = Depends(get_db)):
    proveedor = obtener_o_404(db, Proveedor, proveedor_id, "el proveedor")
    if datos.activo is False and proveedor.activo:
        tiene_productos_activos = db.scalar(
            select(Producto.id)
            .where(Producto.proveedor_id == proveedor_id, Producto.activo.is_(True)).limit(1)
        )
        if tiene_productos_activos:
            raise ErrorApp("PROVEEDOR_CON_PRODUCTOS_ACTIVOS",
                           "No se puede inactivar el proveedor: tiene productos activos asociados.", 409)
    return aplicar_cambios(db, proveedor, datos, entidad="proveedores", usuario=usuario, request=request)

# ---------------------------------------------------------------- PRODUCTOS
productos = APIRouter(prefix="/productos", tags=["productos"])


@productos.post("", response_model=ProductoSalida, status_code=201, summary="Crear producto")
def crear_producto(datos: ProductoCrear, request: Request, todas_las_sedes: bool = False,
                   usuario: UsuarioActual = Depends(solo_admin), db: Session = Depends(get_db)):
    obtener_o_404(db, TipoProducto, datos.tipo_producto_id, "el tipo de producto")
    obtener_o_404(db, Proveedor, datos.proveedor_id, "el proveedor")

    if todas_las_sedes or datos.sede_id is None:
        lista_sedes = list(db.scalars(select(Sede).order_by(Sede.id)))
        if not lista_sedes:
            raise ErrorApp("NO_ENCONTRADO", "No existen sedes registradas para asociar el producto.", 404)
        creados: list[Producto] = []
        base_dict = datos.model_dump(exclude={"sede_id"})
        for s in lista_sedes:
            dup = db.scalar(
                select(Producto).where(Producto.sede_id == s.id, Producto.codigo == datos.codigo)
            )
            if dup is None:
                nuevo = Producto(sede_id=s.id, **base_dict)
                db.add(nuevo)
                db.flush()
                registrar(db, accion="CREAR", entidad="productos", entidad_id=nuevo.id,
                          **_contexto(usuario, request))
                creados.append(nuevo)
        if not creados:
            raise ErrorApp("PRODUCTO_DUPLICADO",
                           f"El código {datos.codigo} ya existe en todas las sedes.", 409)
        db.commit()
        db.refresh(creados[0])
        return creados[0]

    obtener_o_404(db, Sede, datos.sede_id, "la sede")
    duplicado = db.scalar(
        select(Producto).where(Producto.sede_id == datos.sede_id, Producto.codigo == datos.codigo)
    )
    if duplicado:
        raise ErrorApp("PRODUCTO_DUPLICADO",
                    f"El código {datos.codigo} ya existe en esa sede.", 409)
    return guardar(db, Producto(**datos.model_dump()), accion="CREAR",
                   entidad="productos", usuario=usuario, request=request)



@productos.post("/carga-masiva", response_model=ProductoCargaResultado,
                summary="Carga masiva de productos desde CSV")
async def cargar_productos_csv(sede_id: int, request: Request, archivo: UploadFile = File(...),
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
                      detalle="carga_masiva", **_contexto(usuario, request))
            db.commit()
            creados += 1
        except (ErrorApp, ValueError, KeyError) as error:
            db.rollback()
            errores.append(ProductoCargaError(fila=numero_fila, mensaje=str(error)))

    return ProductoCargaResultado(creados=creados, errores=errores)


@productos.get("", response_model=list[ProductoSalida], summary="Listar productos por sede")
def listar_productos(usuario: UsuarioActual = Depends(usuario_actual), db: Session = Depends(get_db),
                     sede_id: int | None = None, tipo_producto_id: int | None = None,
                     solo_activos: bool = True):
    sede_id = sede_autorizada(usuario, sede_id)
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
                                usuario: UsuarioActual = Depends(usuario_actual),
                                db: Session = Depends(get_db)):
    sede_autorizada(usuario, sede_id)
    producto = db.scalar(
        select(Producto).where(Producto.sede_id == sede_id, Producto.codigo == codigo)
    )
    if producto is None:
        raise ErrorApp("NO_ENCONTRADO",
                    f"No existe el producto con código {codigo} en la sede {sede_id}.", 404)
    return producto


@productos.get("/{producto_id}", response_model=ProductoSalida, summary="Consultar producto")
def obtener_producto(producto_id: int, usuario: UsuarioActual = Depends(usuario_actual),
                     db: Session = Depends(get_db)):
    producto = obtener_o_404(db, Producto, producto_id, "el producto")
    sede_autorizada(usuario, producto.sede_id)
    return producto


@productos.patch("/{producto_id}", response_model=ProductoSalida, summary="Actualizar producto")
def actualizar_producto(producto_id: int, datos: ProductoActualizar, request: Request,
                        todas_las_sedes: bool = False,
                        usuario: UsuarioActual = Depends(solo_admin), db: Session = Depends(get_db)):
    producto = obtener_o_404(db, Producto, producto_id, "el producto")
    cambios = datos.model_dump(exclude_unset=True)
    compra = cambios.get("valor_compra", producto.valor_compra)
    venta = cambios.get("valor_venta", producto.valor_venta)
    if venta < compra:
        raise ErrorApp("MARGEN_NEGATIVO",
                    "El valor de venta no puede ser menor que el valor de compra.", 422)
    if todas_las_sedes:
        campos_maestros = {
            k: v for k, v in cambios.items() if k not in ("stock", "stock_minimo")
        }
        hermanos = list(db.scalars(select(Producto).where(Producto.codigo == producto.codigo)))
        for h in hermanos:
            for k, v in campos_maestros.items():
                setattr(h, k, v)
        registrar(db, accion="ACTUALIZAR", entidad="productos", entidad_id=producto.id,
                  detalle=", ".join(campos_maestros.keys()), **_contexto(usuario, request))
        db.commit()
        db.refresh(producto)
        return producto
    return aplicar_cambios(db, producto, datos, entidad="productos", usuario=usuario, request=request)


@productos.post("/{producto_id}/inactivar", response_model=ProductoSalida, summary="Inactivar producto")
def inactivar_producto(producto_id: int, request: Request, todas_las_sedes: bool = False,
                       usuario: UsuarioActual = Depends(solo_admin), db: Session = Depends(get_db)):
    producto = obtener_o_404(db, Producto, producto_id, "el producto")
    if not producto.activo:
        raise ErrorApp("PRODUCTO_YA_INACTIVO", "El producto ya está inactivo.", 409)
    objetivos = (
        list(db.scalars(select(Producto).where(Producto.codigo == producto.codigo)))
        if todas_las_sedes
        else [producto]
    )
    for obj in objetivos:
        obj.activo = False
    registrar(db, accion="INACTIVAR", entidad="productos", entidad_id=producto.id,
              **_contexto(usuario, request))
    db.commit()
    db.refresh(producto)
    return producto


@productos.post("/{producto_id}/activar", response_model=ProductoSalida, summary="Activar producto")
def activar_producto(producto_id: int, request: Request, todas_las_sedes: bool = False,
                     usuario: UsuarioActual = Depends(solo_admin), db: Session = Depends(get_db)):
    producto = obtener_o_404(db, Producto, producto_id, "el producto")
    if producto.activo:
        raise ErrorApp("PRODUCTO_YA_ACTIVO", "El producto ya está activo.", 409)
    objetivos = (
        list(db.scalars(select(Producto).where(Producto.codigo == producto.codigo)))
        if todas_las_sedes
        else [producto]
    )
    for obj in objetivos:
        obj.activo = True
    registrar(db, accion="ACTIVAR", entidad="productos", entidad_id=producto.id,
              **_contexto(usuario, request))
    db.commit()
    db.refresh(producto)
    return producto


# ------------------------------------------- SPRINT 2: INVENTARIO POR SEDE
inventario = APIRouter(prefix="/inventario", tags=["inventario"])


@inventario.get("", response_model=list[ProductoSalida], summary="Consultar inventario por sede")
def listar_inventario(usuario: UsuarioActual = Depends(usuario_actual), db: Session = Depends(get_db),
                      sede_id: int | None = None, tipo_producto_id: int | None = None,
                      solo_activos: bool = True):
    sede_id = sede_autorizada(usuario, sede_id)
    consulta = select(Producto)
    if sede_id is not None:
        consulta = consulta.where(Producto.sede_id == sede_id)
    if tipo_producto_id is not None:
        consulta = consulta.where(Producto.tipo_producto_id == tipo_producto_id)
    if solo_activos:
        consulta = consulta.where(Producto.activo.is_(True))
    return list(db.scalars(consulta.order_by(Producto.sede_id, Producto.nombre)))


@inventario.post("/{producto_id}/ajustar", response_model=ProductoSalida,
                 summary="Registrar movimiento o ajuste de inventario")
def ajustar_inventario(producto_id: int, datos: InventarioAjuste, request: Request,
                       usuario: UsuarioActual = Depends(solo_admin), db: Session = Depends(get_db)):
    producto = obtener_o_404(db, Producto, producto_id, "el producto")
    actual = producto.stock or 0
    if datos.tipo == "ENTRADA":
        nuevo = actual + datos.cantidad
    elif datos.tipo == "SALIDA":
        if datos.cantidad > actual:
            msg = f"Stock insuficiente para '{producto.nombre}': disponible {actual}."
            raise ErrorApp("STOCK_INSUFICIENTE", msg, 409)
        nuevo = actual - datos.cantidad
    else:
        nuevo = datos.cantidad

    producto.stock = nuevo
    if datos.stock_minimo is not None:
        producto.stock_minimo = datos.stock_minimo
    detalle = f"{datos.tipo}: {actual} -> {nuevo}"
    if datos.motivo:
        detalle += f" ({datos.motivo})"
    registrar(db, accion="AJUSTAR_INVENTARIO", entidad="productos", entidad_id=producto.id,
              detalle=detalle, **_contexto(usuario, request))
    db.commit()
    db.refresh(producto)
    return producto


# ------------------------------------------- SPRINT 2: TOMA DE PEDIDOS
pedidos = APIRouter(prefix="/pedidos", tags=["pedidos"])


@pedidos.get("", response_model=list[PedidoSalida], summary="Listar pedidos por sede")
def listar_pedidos(usuario: UsuarioActual = Depends(usuario_actual), db: Session = Depends(get_db),
                   sede_id: int | None = None, mesa_id: int | None = None, estado: str | None = None):
    sede_id = sede_autorizada(usuario, sede_id)
    consulta = select(Pedido)
    if sede_id is not None:
        consulta = consulta.where(Pedido.sede_id == sede_id)
    if mesa_id is not None:
        consulta = consulta.where(Pedido.mesa_id == mesa_id)
    if estado:
        consulta = consulta.where(Pedido.estado == estado.upper())
    return list(db.scalars(consulta.order_by(Pedido.id.desc())))


@pedidos.post("", response_model=PedidoSalida, status_code=201,
              summary="Registrar pedido con verificación de inventario")
def crear_pedido(datos: PedidoCrear, request: Request,
                 usuario: UsuarioActual = Depends(usuario_actual), db: Session = Depends(get_db)):
    mesa = obtener_o_404(db, Mesa, datos.mesa_id, "la mesa")
    sede_autorizada(usuario, mesa.sede_id)
    if not mesa.activa:
        raise ErrorApp("MESA_INACTIVA", f"La mesa #{mesa.numero} está inactiva.", 409)

    detalles: list[PedidoDetalle] = []
    total = 0.0
    for item in datos.items:
        producto = obtener_o_404(db, Producto, item.producto_id, "el producto")
        if producto.sede_id != mesa.sede_id:
            raise ErrorApp(
                "SEDE_NO_AUTORIZADA",
                f"El producto '{producto.nombre}' no pertenece a la sede de la mesa #{mesa.numero}.",
                409,
            )
        if not producto.activo:
            raise ErrorApp("PRODUCTO_INACTIVO", f"El producto '{producto.nombre}' está inactivo.", 409)
        disponible = producto.stock if producto.stock is not None else 0
        if item.cantidad > disponible:
            msg = (
                f"Existencias insuficientes para '{producto.nombre}': "
                f"disponibles {disponible}, solicitadas {item.cantidad}."
            )
            raise ErrorApp("STOCK_INSUFICIENTE", msg, 409)
        producto.stock = disponible - item.cantidad
        precio = float(producto.valor_venta)
        sub = round(precio * item.cantidad, 2)
        total = round(total + sub, 2)
        detalles.append(
            PedidoDetalle(
                producto_id=producto.id,
                codigo_producto=producto.codigo,
                nombre_producto=producto.nombre,
                cantidad=item.cantidad,
                precio_unitario=precio,
                subtotal=sub,
            )
        )

    mesa.estado = "OCUPADA"
    nombre_mesero = (datos.mesero_nombre or usuario.usuario)[:60]
    pedido = Pedido(
        sede_id=mesa.sede_id,
        mesa_id=mesa.id,
        usuario_id=usuario.id,
        mesero=nombre_mesero,
        estado="ABIERTO",
        observaciones=datos.observaciones,
        total=total,
        detalles=detalles,
    )
    db.add(pedido)
    db.flush()
    registrar(db, accion="CREAR_PEDIDO", entidad="pedidos", entidad_id=pedido.id,
              detalle=f"mesa={mesa.numero}, items={len(detalles)}, total={total}",
              **_contexto(usuario, request))
    db.commit()
    db.refresh(pedido)
    return pedido


@pedidos.post("/{pedido_id}/estado", response_model=PedidoSalida, summary="Actualizar estado del pedido")
def cambiar_estado_pedido(pedido_id: int, datos: PedidoEstadoActualizar, request: Request,
                          usuario: UsuarioActual = Depends(usuario_actual), db: Session = Depends(get_db)):
    pedido = obtener_o_404(db, Pedido, pedido_id, "el pedido")
    sede_autorizada(usuario, pedido.sede_id)
    anterior = pedido.estado
    if anterior == datos.estado:
        return pedido

    if datos.estado == "CANCELADO" and anterior != "CANCELADO":
        for det in pedido.detalles:
            prod = db.get(Producto, det.producto_id)
            if prod is not None:
                prod.stock = (prod.stock or 0) + det.cantidad

    pedido.estado = datos.estado
    if datos.estado in ("CERRADO", "CANCELADO"):
        abiertos = db.scalar(
            select(Pedido.id).where(
                Pedido.mesa_id == pedido.mesa_id,
                Pedido.id != pedido.id,
                Pedido.estado.in_(("ABIERTO", "ENTREGADO")),
            ).limit(1)
        )
        if not abiertos:
            mesa = db.get(Mesa, pedido.mesa_id)
            if mesa is not None:
                mesa.estado = "LIBRE"

    registrar(db, accion="ESTADO_PEDIDO", entidad="pedidos", entidad_id=pedido.id,
              detalle=f"{anterior} -> {datos.estado}", **_contexto(usuario, request))
    db.commit()
    db.refresh(pedido)
    return pedido


for router in (sedes, mesas, tipos, proveedores, productos, inventario, pedidos):
    app.include_router(router)
# HU-008: la auditoría de este servicio también se puede consultar (solo ADMINISTRADOR).
app.include_router(router_consulta(get_db, solo_admin))

