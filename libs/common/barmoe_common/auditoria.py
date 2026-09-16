"""Trazabilidad — RNF-12 · HU-025.

Toda transacción deja registro de QUIÉN la hizo, en QUÉ SEDE y CUÁNDO.
Cada microservicio crea su propia tabla `auditoria` con este mismo modelo.

Además del registro de operaciones exitosas, este módulo deja constancia de
los intentos RECHAZADOS (perfil o sede no autorizados, token inválido). Eso es
lo que pide el control C-1 de la propuesta: "el sistema debe rechazarla y
registrarla".
"""
from datetime import UTC, datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base

# Resultados posibles de una operación auditada.
RESULTADOS = ("OK", "FALLIDO", "BLOQUEADO", "INACTIVO", "RECHAZADO")


def ahora_utc() -> datetime:
    return datetime.now(UTC)


class Auditoria(Base):
    __tablename__ = "auditoria"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora_utc, index=True)
    usuario_id: Mapped[int] = mapped_column(Integer, index=True, nullable=True)
    usuario: Mapped[str] = mapped_column(String(60), nullable=True)
    sede_id: Mapped[int] = mapped_column(Integer, index=True, nullable=True)
    accion: Mapped[str] = mapped_column(String(60), index=True)
    entidad: Mapped[str] = mapped_column(String(60), nullable=True)
    entidad_id: Mapped[str] = mapped_column(String(60), nullable=True)
    resultado: Mapped[str] = mapped_column(String(20), default="OK")
    ip: Mapped[str] = mapped_column(String(45), nullable=True)
    # Mismo identificador que viaja en X-Request-Id: permite seguir una
    # transacción desde el gateway hasta cada microservicio.
    request_id: Mapped[str] = mapped_column(String(64), index=True, nullable=True)
    detalle: Mapped[str] = mapped_column(Text, nullable=True)


def registrar(
    db,
    *,
    accion: str,
    usuario_id: int | None = None,
    usuario: str | None = None,
    sede_id: int | None = None,
    entidad: str | None = None,
    entidad_id: str | int | None = None,
    resultado: str = "OK",
    ip: str | None = None,
    request_id: str | None = None,
    detalle: str | None = None,
) -> Auditoria:
    """Inserta un registro de auditoría. NO hace commit: lo hace quien llama."""
    registro = Auditoria(
        accion=accion,
        usuario_id=usuario_id,
        usuario=usuario,
        sede_id=sede_id,
        entidad=entidad,
        entidad_id=str(entidad_id) if entidad_id is not None else None,
        resultado=resultado,
        ip=ip,
        request_id=request_id,
        detalle=detalle,
    )
    db.add(registro)
    return registro


# ------------------------------------------------------------ utilidades HTTP
def ip_cliente(request) -> str | None:
    """IP real del cliente.

    Detrás del gateway, `request.client.host` es la IP del gateway y no la del
    usuario. Por eso se prefiere la primera IP de `X-Forwarded-For` cuando
    existe (el gateway es el único que puede llegar a los servicios, así que
    la cabecera no la puede falsificar alguien de afuera).
    """
    reenviada = request.headers.get("x-forwarded-for")
    if reenviada:
        primera = reenviada.split(",")[0].strip()
        if primera:
            return primera[:45]
    return request.client.host if request.client else None


def request_id_de(request) -> str | None:
    """X-Request-Id de la petición (lo deja RequestIdMiddleware en `state`)."""
    valor = getattr(request.state, "request_id", None) or request.headers.get("x-request-id")
    return valor[:64] if valor else None


def registrar_rechazo(
    db,
    *,
    metodo: str,
    ruta: str,
    status: int,
    codigo: str | None = None,
    usuario_id: int | None = None,
    usuario: str | None = None,
    sede_id: int | None = None,
    ip: str | None = None,
    request_id: str | None = None,
) -> Auditoria:
    """Deja constancia de una operación rechazada (401/403). Control C-1."""
    detalle = f"{metodo} {ruta} -> {status}"
    if codigo:
        detalle += f" {codigo}"
    return registrar(
        db,
        accion="ACCESO_DENEGADO",
        usuario_id=usuario_id,
        usuario=usuario,
        sede_id=sede_id,
        entidad=ruta[:60],
        resultado="RECHAZADO",
        ip=ip,
        request_id=request_id,
        detalle=detalle,
    )


def contexto_http(request) -> dict:
    """`ip` y `request_id` listos para pasarle a `registrar(**contexto_http(request))`."""
    return {"ip": ip_cliente(request), "request_id": request_id_de(request)}


# ------------------------------------------------ HU-008 · consulta paginada
def router_consulta(get_db, solo_admin, prefijo: str = "/auditoria"):
    """Router de solo lectura sobre la tabla `auditoria` del servicio.

    Criterios de HU-008: filtros por usuario, sede, acción, resultado y rango
    de fechas; paginado del más reciente al más antiguo; solo ADMINISTRADOR; y
    ningún endpoint para modificar o borrar registros (solo existe GET).
    El total de registros viaja en la cabecera `X-Total-Count`.

    Aporte original de Angel (`GET /audit`), llevado al contrato común para
    que todos los servicios expongan la misma consulta.
    """
    from datetime import datetime as _dt

    from fastapi import APIRouter, Depends, Query, Response
    from pydantic import BaseModel, ConfigDict
    from sqlalchemy import func, select

    from .errors import ErrorApp

    class AuditoriaSalida(BaseModel):
        model_config = ConfigDict(from_attributes=True)

        id: int
        fecha: _dt
        usuario_id: int | None
        usuario: str | None
        sede_id: int | None
        accion: str
        entidad: str | None
        entidad_id: str | None
        resultado: str
        ip: str | None
        request_id: str | None
        detalle: str | None

    def _utc(fecha):
        if fecha is None:
            return None
        return fecha.replace(tzinfo=UTC) if fecha.tzinfo is None else fecha.astimezone(UTC)

    router = APIRouter(prefix=prefijo, tags=["auditoría"])

    @router.get("", response_model=list[AuditoriaSalida], summary="Consultar la auditoría (HU-008)")
    def consultar(
        response: Response,
        _=Depends(solo_admin),
        db=Depends(get_db),
        usuario_id: int | None = None,
        usuario: str | None = Query(default=None, max_length=60),
        sede_id: int | None = None,
        accion: str | None = Query(default=None, max_length=60),
        resultado: str | None = Query(default=None, max_length=20),
        desde: _dt | None = None,
        hasta: _dt | None = None,
        pagina: int = Query(default=1, ge=1),
        tamano: int = Query(default=50, ge=1, le=200),
    ):
        # Fechas sin zona se toman como UTC; con zona (ej. -05:00) se pasan a UTC.
        desde, hasta = (_utc(f) for f in (desde, hasta))
        if desde and hasta and desde > hasta:
            raise ErrorApp("RANGO_INVALIDO", "La fecha 'desde' no puede ser posterior a 'hasta'.", 422)
        filtros = []
        if usuario_id is not None:
            filtros.append(Auditoria.usuario_id == usuario_id)
        if usuario:
            filtros.append(Auditoria.usuario == usuario)
        if sede_id is not None:
            filtros.append(Auditoria.sede_id == sede_id)
        if accion:
            filtros.append(Auditoria.accion == accion.upper())
        if resultado:
            filtros.append(Auditoria.resultado == resultado.upper())
        if desde:
            filtros.append(Auditoria.fecha >= desde)
        if hasta:
            filtros.append(Auditoria.fecha <= hasta)

        total = db.scalar(select(func.count()).select_from(Auditoria).where(*filtros))
        response.headers["X-Total-Count"] = str(total)
        consulta = (
            select(Auditoria).where(*filtros)
            .order_by(Auditoria.fecha.desc(), Auditoria.id.desc())
            .offset((pagina - 1) * tamano).limit(tamano)
        )
        return list(db.scalars(consulta))

    return router
