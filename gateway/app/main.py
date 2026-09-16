"""API Gateway — único punto expuesto al exterior.

Responsabilidades:
  1. Enrutar /api/auth/*           -> auth-service
             /api/parametrizacion/* -> parametrizacion-service
  2. Validar la sesión contra auth-service en cada request protegido
     (esto es lo que hace cumplir RNF-03 inactividad y RNF-10 sesión única).
  3. Propagar X-Request-Id para poder seguir una transacción entre servicios.
  4. Exponer /health con el estado agregado de todos los servicios.
  5. Servir el frontend por perfiles (Felipe) en la raíz "/".

Los microservicios NO se publican en la red del host: solo el gateway.
"""
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from barmoe_common.app import crear_app

from .config import config

RUTAS = {
    "auth": config.AUTH_URL,
    "parametrizacion": config.PARAMETRIZACION_URL,
}

# Rutas que no exigen sesión válida.
PUBLICAS = {"/api/auth/auth/login", "/api/auth/health", "/api/parametrizacion/health"}

METODOS_CON_CUERPO = {"POST", "PUT", "PATCH", "DELETE"}

# Cabeceras de la respuesta del servicio que sí se devuelven al navegador.
CABECERAS_DE_RESPUESTA = {"x-total-count", "x-sla-excedido", "content-disposition"}


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    app.state.http = httpx.AsyncClient(timeout=config.TIMEOUT_SEGUNDOS)
    try:
        yield
    finally:
        await app.state.http.aclose()


app = crear_app(
    config,
    titulo="Bar de Moe · API Gateway",
    descripcion="Punto de entrada único. DATHEON S.A.S.",
    lifespan=ciclo_de_vida,
    incluir_health=False,  # el gateway publica un /health agregado, más abajo
)


def _error(codigo: str, mensaje: str, status: int) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"codigo": codigo, "mensaje": mensaje}})


async def _validar_sesion(cliente: httpx.AsyncClient, authorization: str | None, request_id: str,
                          ip: str = ""):
    """Pregunta al auth-service si la sesión sigue viva. Refresca la inactividad."""
    if not authorization:
        return _error("NO_AUTENTICADO", "Falta el token de acceso.", 401)
    try:
        respuesta = await cliente.post(
            f"{config.AUTH_URL}/auth/validar-sesion",
            headers={"Authorization": authorization, "X-Request-Id": request_id, "X-Forwarded-For": ip},
        )
    except httpx.RequestError:
        return _error("AUTH_NO_DISPONIBLE", "El servicio de autenticación no responde.", 503)
    if respuesta.status_code != 200:
        return _reenviar(respuesta, request_id)
    return None


def _ip_cliente(request: Request) -> str:
    """IP de quien llama al gateway, para que los servicios la auditen (DEF-07).

    El gateway es el borde de la plataforma: el X-Forwarded-For que mande el
    navegador NO se reenvía, porque cualquiera podría inventarlo para ocultar
    su IP en la auditoría. Si en producción se pone un proxy con TLS delante,
    su IP se agrega a PROXIES_CONFIABLES y entonces sí se respeta su cabecera.
    """
    directa = request.client.host if request.client else ""
    previa = request.headers.get("x-forwarded-for", "")
    if previa and directa in config.proxies_confiables:
        return previa.split(",")[0].strip()
    return directa


def _reenviar(respuesta: httpx.Response, request_id: str) -> JSONResponse:
    """Devuelve la respuesta del servicio. Si no es JSON responde 502 en vez de caerse (DEF-09)."""
    cabeceras = {k: v for k, v in respuesta.headers.items() if k.lower() in CABECERAS_DE_RESPUESTA}
    cabeceras["X-Request-Id"] = request_id
    if not respuesta.content:
        return JSONResponse(status_code=respuesta.status_code, content=None, headers=cabeceras)
    try:
        contenido = respuesta.json()
    except ValueError:
        return JSONResponse(
            status_code=502,
            content={"error": {"codigo": "RESPUESTA_INVALIDA",
                               "mensaje": "Un servicio interno respondió en un formato inesperado."}},
            headers={"X-Request-Id": request_id},
        )
    return JSONResponse(status_code=respuesta.status_code, content=contenido, headers=cabeceras)


@app.get("/health", tags=["salud"], summary="Estado agregado de la plataforma")
async def health(request: Request):
    cliente: httpx.AsyncClient = request.app.state.http
    estados = {}
    for nombre, url in RUTAS.items():
        try:
            r = await cliente.get(f"{url}/health", timeout=3.0)
            estados[nombre] = "ok" if r.status_code == 200 else f"error-{r.status_code}"
        except httpx.RequestError:
            estados[nombre] = "sin-respuesta"
    global_ok = all(v == "ok" for v in estados.values())
    return {"estado": "ok" if global_ok else "degradado", "servicios": estados}


@app.api_route(
    "/api/{servicio}/{ruta:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    tags=["proxy"],
    summary="Enrutamiento hacia los microservicios",
)
async def proxy(servicio: str, ruta: str, request: Request):
    destino = RUTAS.get(servicio)
    if destino is None:
        return _error("SERVICIO_DESCONOCIDO", f"No existe el servicio '{servicio}'.", 404)

    request_id = getattr(request.state, "request_id", "")
    ruta_completa = f"/api/{servicio}/{ruta}".rstrip("/")

    if ruta_completa not in PUBLICAS:
        fallo = await _validar_sesion(
            request.app.state.http, request.headers.get("authorization"), request_id, _ip_cliente(request)
        )
        if fallo is not None:
            return fallo

    cabeceras = {
        k: v for k, v in request.headers.items()
        if k.lower() in {"authorization", "content-type", "accept"}
    }
    cabeceras["X-Request-Id"] = request_id
    cabeceras["X-Forwarded-For"] = _ip_cliente(request)

    cuerpo = await request.body() if request.method in METODOS_CON_CUERPO else None

    try:
        respuesta = await request.app.state.http.request(
            request.method,
            f"{destino}/{ruta}",
            params=dict(request.query_params),
            headers=cabeceras,
            content=cuerpo,
        )
    except httpx.RequestError:
        return _error("SERVICIO_NO_DISPONIBLE", f"El servicio '{servicio}' no responde.", 503)

    return _reenviar(respuesta, request_id)


def carpeta_frontend() -> Path | None:
    """En Docker el frontend queda en /app/frontend; en el repositorio, en la raíz.

    DEF-10: antes se montaba una ruta fija y, fuera de Docker, la app ni
    siquiera arrancaba (las pruebas del gateway fallaban al importar).
    """
    aqui = Path(__file__).resolve()
    candidatas = [Path(config.FRONTEND_DIR)] if config.FRONTEND_DIR else []
    candidatas += [aqui.parents[1] / "frontend", aqui.parents[2] / "frontend"]
    return next((c for c in candidatas if (c / "index.html").is_file()), None)


FRONTEND = carpeta_frontend()
if FRONTEND is not None:
    # Se monta al final para que /health y /api/... tengan prioridad.
    app.mount("/", StaticFiles(directory=FRONTEND, html=True), name="frontend")
