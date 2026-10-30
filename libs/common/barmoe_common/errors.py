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


def _campo(error: dict) -> str:
    """('body', 'lineas', 0, 'cantidad') -> 'lineas[0].cantidad'."""
    partes = ""
    for p in error.get("loc", ())[1:]:
        partes += f"[{p}]" if isinstance(p, int) else (f".{p}" if partes else str(p))
    return partes


def traducir_error(error: dict) -> str:
    """Turns a Pydantic error into a short, clear reason (the professor asked for English)."""
    tipo, ctx = error.get("type", ""), error.get("ctx") or {}
    plantillas = {
        "missing": "is required",
        "extra_forbidden": "cannot be sent or modified",
        "greater_than": "must be greater than {gt}",
        "greater_than_equal": "must be greater than or equal to {ge}",
        "less_than": "must be less than {lt}",
        "less_than_equal": "must be less than or equal to {le}",
        "string_too_short": "must have at least {min_length} characters",
        "string_too_long": "must have at most {max_length} characters",
        "too_short": "must have at least {min_length} item(s)",
        "too_long": "must have at most {max_length} item(s)",
        "int_parsing": "must be a whole number",
        "int_type": "must be a whole number",
        "int_from_float": "must be a whole number",
        "decimal_parsing": "must be a number",
        "decimal_type": "must be a number",
        "bool_parsing": "must be true or false",
        "string_type": "must be text",
        "literal_error": "must be one of: {expected}",
        "json_invalid": "the body is not valid JSON",
    }
    if tipo == "value_error":
        return str(error.get("msg", "")).removeprefix("Value error, ")
    if tipo in plantillas:
        try:
            return plantillas[tipo].format(**ctx)
        except (KeyError, IndexError):
            return plantillas[tipo]
    return str(error.get("msg", "invalid value"))


def registrar_manejadores(app: FastAPI) -> None:
    @app.exception_handler(ErrorApp)
    async def _error_app(_: Request, exc: ErrorApp):
        return JSONResponse(status_code=exc.status, content=_cuerpo(exc.codigo, exc.mensaje))

    @app.exception_handler(RequestValidationError)
    async def _validacion(_: Request, exc: RequestValidationError):
        # Professor's correction: the message says WHICH field failed and WHY.
        detalle = [{"campo": _campo(e), "error": traducir_error(e)} for e in exc.errors()]
        motivos = "; ".join(f"{d['campo']}: {d['error']}" if d["campo"] else d["error"] for d in detalle)
        return JSONResponse(
            status_code=422,
            content=_cuerpo("DATOS_INVALIDOS", f"The submitted data is not valid. {motivos}", detalle),
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
