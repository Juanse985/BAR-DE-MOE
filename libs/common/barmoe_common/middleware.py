"""Middlewares transversales: identificador de request, medición del SLA y
auditoría de accesos rechazados."""
import logging
import time
from uuid import uuid4

import jwt
from starlette.concurrency import run_in_threadpool
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from .auditoria import ip_cliente, registrar_rechazo
from .tokens import decodificar_token

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
    """RNF-02 · HU-026: toda transacción debe responder en 2 segundos o menos.

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


class AuditoriaRechazosMiddleware(BaseHTTPMiddleware):
    """Control C-1 · HU-025 / HU-028: todo intento rechazado queda registrado.

    Cuando un servicio responde 401 o 403 (sin token, token inválido, perfil o
    sede no autorizados), se guarda una fila `ACCESO_DENEGADO` con el usuario
    y la sede que traía el token, la IP, el método y la ruta.

    Las rutas de `excluir` no se auditan aquí porque ya se auditan en su propia
    lógica (por ejemplo, el login fallido lo registra el auth-service con más
    detalle).

    Se activa pasando `auditar_rechazos=SessionLocal` a `crear_app`.
    """

    ESTADOS = (401, 403)

    def __init__(self, app, session_factory, secreto: str, algoritmo: str = "HS256",
                 excluir: tuple[str, ...] = ()):
        super().__init__(app)
        self.session_factory = session_factory
        self.secreto = secreto
        self.algoritmo = algoritmo
        self.excluir = set(excluir)

    def _datos_token(self, request: Request) -> dict:
        autorizacion = request.headers.get("authorization", "")
        if not autorizacion.lower().startswith("bearer "):
            return {}
        try:
            datos = decodificar_token(autorizacion.split(" ", 1)[1].strip(), self.secreto, self.algoritmo)
        except jwt.PyJWTError:
            # Token falso o vencido: no confiamos en su contenido.
            return {}
        try:
            usuario_id = int(datos.get("sub"))
        except (TypeError, ValueError):
            usuario_id = None
        return {"usuario_id": usuario_id, "usuario": datos.get("usr"), "sede_id": datos.get("sede_id")}

    def _guardar(self, **campos) -> None:
        db = self.session_factory()
        try:
            registrar_rechazo(db, **campos)
            db.commit()
        except Exception:  # noqa: BLE001 - la auditoría nunca debe tumbar la respuesta
            db.rollback()
            log.exception("No se pudo registrar el acceso denegado en auditoría")
        finally:
            db.close()

    async def dispatch(self, request: Request, call_next):
        respuesta = await call_next(request)
        if respuesta.status_code in self.ESTADOS and request.url.path not in self.excluir:
            await run_in_threadpool(
                self._guardar,
                metodo=request.method,
                ruta=request.url.path,
                status=respuesta.status_code,
                ip=ip_cliente(request),
                request_id=getattr(request.state, "request_id", None),
                **self._datos_token(request),
            )
        return respuesta
