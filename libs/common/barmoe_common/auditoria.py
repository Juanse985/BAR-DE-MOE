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
    usuario_id: Mapped[int | None] = mapped_column(Integer, index=True)
    usuario: Mapped[str | None] = mapped_column(String(60))
    sede_id: Mapped[int | None] = mapped_column(Integer, index=True)
    accion: Mapped[str] = mapped_column(String(60), index=True)
    entidad: Mapped[str | None] = mapped_column(String(60))
    entidad_id: Mapped[str | None] = mapped_column(String(60))
    resultado: Mapped[str] = mapped_column(String(20), default="OK")
    ip: Mapped[str | None] = mapped_column(String(45))
    # Mismo identificador que viaja en X-Request-Id: permite seguir una
    # transacción desde el gateway hasta cada microservicio.
    request_id: Mapped[str | None] = mapped_column(String(64), index=True)
    detalle: Mapped[str | None] = mapped_column(Text)


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
