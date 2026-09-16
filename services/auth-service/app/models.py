import enum
from datetime import datetime

from sqlalchemy import Column, String, Boolean, Integer, DateTime, Enum, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.database import Base


class RolEnum(str, enum.Enum):
    admin = "admin"
    usuario = "usuario"


class User(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    rol = Column(Enum(RolEnum), default=RolEnum.usuario, nullable=False)
    activo = Column(Boolean, default=True, nullable=False)

    # HU-002: bloqueo por intentos fallidos
    intentos_fallidos = Column(Integer, default=0, nullable=False)
    bloqueado_hasta = Column(DateTime, nullable=True)

    # HU-003 y HU-004: sesión única + cierre por inactividad
    session_id = Column(String(64), nullable=True)
    ultima_actividad = Column(DateTime, nullable=True)

    creado_en = Column(DateTime, default=datetime.utcnow)
    actualizado_en = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    auditorias = relationship("Auditoria", back_populates="usuario")


class Auditoria(Base):
    __tablename__ = "auditoria"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    username = Column(String(50), nullable=True)  # se guarda aparte por si el usuario se elimina
    accion = Column(String(50), nullable=False)
    detalle = Column(Text, nullable=True)
    ip = Column(String(45), nullable=True)
    fecha = Column(DateTime, default=datetime.utcnow, index=True)

    usuario = relationship("User", back_populates="auditorias")
