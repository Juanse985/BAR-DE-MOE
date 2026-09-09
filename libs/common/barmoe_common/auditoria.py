"""Trazabilidad — RNF-12.

Toda transacción deja registro de QUIÉN la hizo, en QUÉ SEDE y CUÁNDO.
Cada microservicio crea su propia tabla `auditoria` con este mismo modelo.
"""
from datetime import UTC, datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


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
        detalle=detalle,
    )
    db.add(registro)
    return registro
