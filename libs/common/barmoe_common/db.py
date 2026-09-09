"""Motor y sesión de SQLAlchemy.

Cada microservicio tiene su propia base de datos (patrón database-per-service).
La misma función sirve para PostgreSQL en docker y para SQLite en las pruebas.
"""
from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    """Clase base de todos los modelos."""


def crear_engine(url: str):
    opciones: dict = {"pool_pre_ping": True, "future": True}
    if url.startswith("sqlite"):
        # SQLite en pruebas: permite usarlo desde el hilo de TestClient
        opciones["connect_args"] = {"check_same_thread": False}
    return create_engine(url, **opciones)


def crear_session_factory(url: str) -> sessionmaker[Session]:
    """Devuelve la fábrica de sesiones; el engine queda en `.engine`."""
    engine = crear_engine(url)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    factory.engine = engine  # atajo para Base.metadata.create_all(bind=...)
    return factory


def dependencia_db(session_factory: sessionmaker[Session]):
    """Devuelve una dependencia de FastAPI que entrega una sesión por request."""

    def _get_db() -> Iterator[Session]:
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    return _get_db
