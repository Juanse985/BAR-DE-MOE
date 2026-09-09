"""Fábrica de aplicaciones FastAPI con todo lo transversal ya montado."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import ConfigBase
from .errors import registrar_manejadores
from .middleware import RequestIdMiddleware, TiempoRespuestaMiddleware


def crear_app(
    config: ConfigBase,
    *,
    titulo: str,
    descripcion: str,
    version: str = "0.1.0",
    lifespan=None,
    incluir_health: bool = True,
) -> FastAPI:
    app = FastAPI(
        title=titulo,
        description=descripcion,
        version=version,
        docs_url="/docs",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    app.add_middleware(TiempoRespuestaMiddleware, sla_segundos=config.SLA_SEGUNDOS)
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.origenes,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-Id", "X-Tiempo-Ms", "X-SLA-Excedido"],
    )

    registrar_manejadores(app)

    if incluir_health:
        # El gateway define su propio /health agregado y pasa incluir_health=False.
        @app.get("/health", tags=["salud"], summary="Estado del servicio")
        def health() -> dict:
            return {"estado": "ok", "servicio": config.APP_NAME, "entorno": config.ENV}

    return app
