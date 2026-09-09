"""Formato único de error para toda la plataforma.

Todos los servicios responden los errores con la misma envoltura, para que el
frontend y el gateway no tengan que adivinar la forma:

    {"error": {"codigo": "CREDENCIALES_INVALIDAS", "mensaje": "..."}}
"""
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class ErrorApp(Exception):
    """Error de negocio con código legible."""

    def __init__(self, codigo: str, mensaje: str, status: int = 400):
        self.codigo = codigo
        self.mensaje = mensaje
        self.status = status
        super().__init__(mensaje)


def _cuerpo(codigo: str, mensaje: str, detalle=None) -> dict:
    error: dict = {"codigo": codigo, "mensaje": mensaje}
    if detalle is not None:
        error["detalle"] = detalle
    return {"error": error}


def registrar_manejadores(app: FastAPI) -> None:
    @app.exception_handler(ErrorApp)
    async def _error_app(_: Request, exc: ErrorApp):
        return JSONResponse(status_code=exc.status, content=_cuerpo(exc.codigo, exc.mensaje))

    @app.exception_handler(RequestValidationError)
    async def _validacion(_: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content=_cuerpo(
                "DATOS_INVALIDOS",
                "Los datos enviados no son válidos.",
                [{"campo": ".".join(str(p) for p in e["loc"][1:]), "error": e["msg"]} for e in exc.errors()],
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, exc: StarletteHTTPException):
        codigos = {
            401: "NO_AUTENTICADO",
            403: "SIN_PERMISOS",
            404: "NO_ENCONTRADO",
            409: "CONFLICTO",
        }
        return JSONResponse(
            status_code=exc.status_code,
            content=_cuerpo(codigos.get(exc.status_code, "ERROR"), str(exc.detail)),
        )
