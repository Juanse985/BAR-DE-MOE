"""HU-028 · RNF-11 — Seguridad verificable: cuatro controles OWASP (auth-service).

C-1 Control de acceso roto (A01) · prueba negativa por perfil.
C-3 Inyección (A03)               · cadenas de inyección en el login.
C-4 Fallas de autenticación (A07) · bloqueo, sesión única e inactividad.
(C-2 cifrado está en test_hu027_cifrado.py)
"""
from datetime import UTC, datetime, timedelta

import pytest

from app.main import SessionLocal
from app.models import Sesion

from .utilidades import PASSWORD, auditorias, crear_usuario, entrar

# Todas las operaciones exclusivas del ADMINISTRADOR en este servicio.
OPERACIONES_ADMIN = [
    ("GET", "/usuarios", None),
    ("POST", "/usuarios", {"cedula": "1234567", "nombre": "Intruso", "perfil": "ADMINISTRADOR",
                           "usuario": "intruso", "password": "Intruso2026"}),
    ("GET", "/usuarios/1", None),
    ("PATCH", "/usuarios/1", {"perfil": "MESERO"}),
    ("POST", "/usuarios/1/restablecer-password", {"password_nueva": "Hackeada2026"}),
    ("POST", "/usuarios/1/desbloquear", None),
]


# ------------------------------------------------------------------- C-1
@pytest.mark.parametrize("perfil", ["CAJERO", "MESERO"])
@pytest.mark.parametrize(("metodo", "ruta", "cuerpo"), OPERACIONES_ADMIN)
def test_c1_perfiles_no_admin_no_ejecutan_operaciones_de_administrador(
    cliente, encabezado_admin, perfil, metodo, ruta, cuerpo
):
    nombre = f"u{perfil.lower()}"
    crear_usuario(cliente, encabezado_admin, usuario=nombre, perfil=perfil)
    h = entrar(cliente, nombre)
    respuesta = cliente.request(metodo, ruta, headers=h, json=cuerpo)
    assert respuesta.status_code == 403, respuesta.text
    assert respuesta.json()["error"]["codigo"] == "SIN_PERMISOS"


def test_c1_un_mesero_no_puede_escalar_su_perfil(cliente, encabezado_admin):
    mesero = crear_usuario(cliente, encabezado_admin, usuario="barney", perfil="MESERO")
    h = entrar(cliente, "barney")
    cliente.patch(f"/usuarios/{mesero['id']}", headers=h, json={"perfil": "ADMINISTRADOR"})
    actual = cliente.get(f"/usuarios/{mesero['id']}", headers=encabezado_admin).json()
    assert actual["perfil"] == "MESERO"


def test_c1_la_ruta_interna_de_validacion_exige_token(cliente):
    assert cliente.post("/auth/validar-sesion").status_code == 401


def test_c1_un_usuario_inactivo_no_opera_aunque_tenga_token(cliente, encabezado_admin):
    objetivo = crear_usuario(cliente, encabezado_admin, usuario="hans", perfil="CAJERO")
    h = entrar(cliente, "hans")
    cliente.patch(f"/usuarios/{objetivo['id']}", headers=encabezado_admin, json={"estado": "INACTIVO"})
    assert cliente.get("/auth/me", headers=h).status_code == 403


@pytest.mark.xfail(strict=True, reason="DEF-04: al inactivar un usuario sus sesiones siguen vivas; "
                                       "el gateway lo deja pasar a los demás servicios")
def test_c1_inactivar_un_usuario_cierra_su_sesion(cliente, encabezado_admin):
    objetivo = crear_usuario(cliente, encabezado_admin, usuario="jimbo", perfil="MESERO")
    h = entrar(cliente, "jimbo")
    cliente.patch(f"/usuarios/{objetivo['id']}", headers=encabezado_admin, json={"estado": "INACTIVO"})
    assert cliente.post("/auth/validar-sesion", headers=h).status_code == 401


@pytest.mark.xfail(strict=True, reason="DEF-05: el servicio no activa la auditoría de rechazos "
                                       "(falta auditar_rechazos=SessionLocal en crear_app)")
def test_c1_el_intento_no_autorizado_queda_registrado(cliente, encabezado_admin):
    crear_usuario(cliente, encabezado_admin, usuario="kearney", perfil="MESERO")
    h = entrar(cliente, "kearney")
    cliente.get("/usuarios", headers=h)
    assert auditorias(accion="ACCESO_DENEGADO", usuario="kearney")


# ------------------------------------------------------------------- C-3
INYECCIONES = [
    "' OR '1'='1",
    "admin'--",
    "admin' OR 1=1 --",
    "\"; DROP TABLE usuarios; --",
    "admin' UNION SELECT password_hash FROM usuarios --",
    "%' OR usuario LIKE '%",
]


@pytest.mark.parametrize("carga", INYECCIONES)
def test_c3_la_inyeccion_en_el_usuario_no_abre_sesion(cliente, carga):
    respuesta = cliente.post("/auth/login", json={"usuario": carga, "password": "x"})
    assert respuesta.status_code == 401
    assert respuesta.json()["error"]["codigo"] == "CREDENCIALES_INVALIDAS"


@pytest.mark.parametrize("carga", INYECCIONES)
def test_c3_la_inyeccion_en_la_password_no_abre_sesion(cliente, carga):
    respuesta = cliente.post("/auth/login", json={"usuario": "admin", "password": carga})
    assert respuesta.status_code == 401


def test_c3_despues_de_los_ataques_la_tabla_sigue_intacta(cliente, encabezado_admin):
    for carga in INYECCIONES:
        cliente.post("/auth/login", json={"usuario": carga, "password": carga})
    assert len(cliente.get("/usuarios", headers=encabezado_admin).json()) == 1


def test_c3_los_filtros_del_listado_no_se_pueden_inyectar(cliente, encabezado_admin):
    crear_usuario(cliente, encabezado_admin, usuario="moeszyslak", perfil="MESERO")
    respuesta = cliente.get("/usuarios", headers=encabezado_admin, params={"perfil": "' OR '1'='1"})
    assert respuesta.status_code == 200
    assert respuesta.json() == []
    assert cliente.get("/usuarios", headers=encabezado_admin,
                       params={"sede_id": "1 OR 1=1"}).status_code == 422


@pytest.mark.parametrize(("campo", "valor"), [
    ("perfil", "SUPERADMIN"),
    ("usuario", "x" * 61),
    ("cedula", "12"),
    ("password", "A1b" + "x" * 80),
])
def test_c3_la_entrada_se_valida_por_tipo_y_longitud(cliente, encabezado_admin, campo, valor):
    cuerpo = {"cedula": "1234567", "nombre": "Prueba", "perfil": "MESERO",
              "usuario": "prueba", "password": PASSWORD, campo: valor}
    respuesta = cliente.post("/usuarios", headers=encabezado_admin, json=cuerpo)
    assert respuesta.status_code == 422
    assert respuesta.json()["error"]["codigo"] == "DATOS_INVALIDOS"


# ------------------------------------------------------------------- C-4
def test_c4_bloqueada_la_cuenta_ni_la_password_correcta_entra(cliente, encabezado_admin):
    crear_usuario(cliente, encabezado_admin, usuario="lenny", perfil="MESERO")
    for _ in range(3):
        cliente.post("/auth/login", json={"usuario": "lenny", "password": "Equivocada1"})
    respuesta = cliente.post("/auth/login", json={"usuario": "lenny", "password": PASSWORD})
    assert respuesta.status_code == 423
    assert respuesta.json()["error"]["codigo"] == "USUARIO_BLOQUEADO"


def test_c4_el_desbloqueo_del_admin_devuelve_el_acceso(cliente, encabezado_admin):
    objetivo = crear_usuario(cliente, encabezado_admin, usuario="carlc", perfil="CAJERO")
    for _ in range(3):
        cliente.post("/auth/login", json={"usuario": "carlc", "password": "Equivocada1"})
    cliente.post(f"/usuarios/{objetivo['id']}/desbloquear", headers=encabezado_admin)
    assert entrar(cliente, "carlc")


def test_c4_un_login_correcto_reinicia_el_contador(cliente, encabezado_admin):
    crear_usuario(cliente, encabezado_admin, usuario="samuel", perfil="MESERO")
    for _ in range(2):
        cliente.post("/auth/login", json={"usuario": "samuel", "password": "Equivocada1"})
    h = entrar(cliente, "samuel")
    cliente.post("/auth/logout", headers=h)
    for _ in range(2):
        cliente.post("/auth/login", json={"usuario": "samuel", "password": "Equivocada1"})
    assert entrar(cliente, "samuel")  # 2 + 2 fallos no bloquean: el contador se reinició


def test_c4_la_segunda_sesion_se_rechaza_y_la_primera_sigue_viva(cliente, encabezado_admin):
    crear_usuario(cliente, encabezado_admin, usuario="moeszyslak", perfil="CAJERO")
    h = entrar(cliente, "moeszyslak")
    segunda = cliente.post("/auth/login", json={"usuario": "moeszyslak", "password": PASSWORD})
    assert segunda.status_code == 409
    assert segunda.json()["error"]["codigo"] == "SESION_ACTIVA"
    assert cliente.post("/auth/validar-sesion", headers=h).status_code == 200


def test_c4_una_sesion_vencida_por_inactividad_libera_el_login(cliente, encabezado_admin):
    crear_usuario(cliente, encabezado_admin, usuario="homer", perfil="MESERO")
    entrar(cliente, "homer")
    with SessionLocal() as db:
        for sesion in db.query(Sesion).all():
            sesion.ultima_actividad = datetime.now(UTC) - timedelta(seconds=181)
        db.commit()
    assert entrar(cliente, "homer")  # la sesión vieja se cerró por INACTIVIDAD
    with SessionLocal() as db:
        motivos = {s.motivo_cierre for s in db.query(Sesion).all()}
    assert "INACTIVIDAD" in motivos


def test_c4_la_inactividad_se_cuenta_desde_la_ultima_actividad(cliente, encabezado_admin):
    """179 s quieto todavía vale; 181 s ya no (RNF-03 = 180 s)."""
    with SessionLocal() as db:
        sesion = db.query(Sesion).one()
        sesion.ultima_actividad = datetime.now(UTC) - timedelta(seconds=179)
        db.commit()
    assert cliente.post("/auth/validar-sesion", headers=encabezado_admin).status_code == 200
    with SessionLocal() as db:
        sesion = db.query(Sesion).one()
        sesion.ultima_actividad = datetime.now(UTC) - timedelta(seconds=181)
        db.commit()
    assert cliente.post("/auth/validar-sesion", headers=encabezado_admin).status_code == 401


def test_c4_despues_del_logout_el_token_no_sirve(cliente, encabezado_admin):
    cliente.post("/auth/logout", headers=encabezado_admin)
    respuesta = cliente.post("/auth/validar-sesion", headers=encabezado_admin)
    assert respuesta.status_code == 401
    assert respuesta.json()["error"]["codigo"] == "SESION_CERRADA"


def test_c4_el_restablecimiento_cierra_las_sesiones_del_usuario(cliente, encabezado_admin):
    objetivo = crear_usuario(cliente, encabezado_admin, usuario="nedflanders", perfil="MESERO")
    h = entrar(cliente, "nedflanders")
    cliente.post(f"/usuarios/{objetivo['id']}/restablecer-password", headers=encabezado_admin,
                 json={"password_nueva": "Vecinillo2026"})
    assert cliente.post("/auth/validar-sesion", headers=h).status_code == 401


def test_c4_el_mensaje_de_error_no_distingue_usuario_de_password(cliente):
    inexistente = cliente.post("/auth/login", json={"usuario": "nadie", "password": "Algo12345"})
    errada = cliente.post("/auth/login", json={"usuario": "admin", "password": "Algo12345"})
    assert inexistente.status_code == errada.status_code == 401
    assert inexistente.json() == errada.json()
