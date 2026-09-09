"""Middlewares transversales: identificador de request y medición del SLA."""
import logging
import time
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

log = logging.getLogger("barmoe")


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Propaga un X-Request-Id para poder seguir una transacción entre servicios."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-Id") or str(uuid4())
        request.state.request_id = request_id
        respuesta = await call_next(request)
        respuesta.headers["X-Request-Id"] = request_id
        return respuesta


class TiempoRespuestaMiddleware(BaseHTTPMiddleware):
    """RNF-02: toda transacción debe responder en 2 segundos o menos.

    Añade la cabecera X-Tiempo-Ms a cada respuesta y deja un WARNING en el log
    cuando se supera el SLA, para que QA pueda auditarlo sin herramientas extra.
    """

    def __init__(self, app, sla_segundos: float = 2.0):
        super().__init__(app)
        self.sla_segundos = sla_segundos

    async def dispatch(self, request: Request, call_next):
        inicio = time.perf_counter()
        respuesta = await call_next(request)
        transcurrido = time.perf_counter() - inicio
        respuesta.headers["X-Tiempo-Ms"] = f"{transcurrido * 1000:.1f}"
        if transcurrido > self.sla_segundos:
            respuesta.headers["X-SLA-Excedido"] = "true"
            log.warning(
                "SLA excedido: %s %s tardó %.3fs (límite %.1fs)",
                request.method,
                request.url.path,
                transcurrido,
                self.sla_segundos,
            )
        return respuesta
