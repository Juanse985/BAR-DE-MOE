"""Modelo de datos del auth-service.

Campos de Usuario tomados literalmente del tablero de levantamiento:
cédula, nombre, sede, perfil, usuario, contraseña y estado (activo/inactivo).
"""
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from barmoe_common.auditoria import Auditoria  # noqa: F401  (crea la tabla auditoria)
from barmoe_common.db import Base


def ahora_utc() -> datetime:
    return datetime.now(UTC)


PERFILES = ("ADMINISTRADOR", "CAJERO", "MESERO")
ESTADOS = ("ACTIVO", "INACTIVO")


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cedula: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    nombre: Mapped[str] = mapped_column(String(120))
    sede_id: Mapped[int | None] = mapped_column(Integer, index=True)
    perfil: Mapped[str] = mapped_column(String(20), index=True)
    usuario: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(120))
    estado: Mapped[str] = mapped_column(String(10), default="ACTIVO", index=True)

    # RNF-09 · bloqueo por reintentos
    intentos_fallidos: Mapped[int] = mapped_column(Integer, default=0)
    bloqueado: Mapped[bool] = mapped_column(Boolean, default=False)

    # Fuerza el cambio de contraseña tras un restablecimiento del administrador
    debe_cambiar_password: Mapped[bool] = mapped_column(Boolean, default=False)

    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora_utc)
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=ahora_utc, onupdate=ahora_utc
    )

    sesiones: Mapped[list["Sesion"]] = relationship(back_populates="usuario_rel")


class Sesion(Base):
    """Una fila por sesión emitida.

    Sostiene dos requisitos del tablero:
      · RNF-10 sesión única  -> no puede haber dos filas activas del mismo usuario
      · RNF-03 inactividad   -> `ultima_actividad` se refresca en cada request
    """

    __tablename__ = "sesiones"

    jti: Mapped[str] = mapped_column(String(40), primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), index=True)
    activa: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    creada_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora_utc)
    ultima_actividad: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora_utc)
    cerrada_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    motivo_cierre: Mapped[str | None] = mapped_column(String(30))
    ip: Mapped[str | None] = mapped_column(String(45))

    usuario_rel: Mapped[Usuario] = relationship(back_populates="sesiones")
