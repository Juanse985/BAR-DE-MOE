"""Pruebas de los requisitos de seguridad del tablero (RNF-05, 07, 08, 09, 10, 12).

Cada prueba lleva en el nombre el requisito que verifica, para que la evidencia
de la Sprint Review se lea directamente del reporte de pytest.
"""
from datetime import timedelta

from sqlalchemy import select

from app.config import config
from app.main import SessionLocal
from app.models import Sesion, Usuario
from barmoe_common.auditoria import Auditoria
from barmoe_common.security import verificar_password


def test_health_responde_ok(cliente):
    respuesta = cliente.get("/health")
    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "ok"


def test_rnf02_la_respuesta_trae_el_tiempo_medido(cliente):
    respuesta = cliente.get("/health")
    assert "X-Tiempo-Ms" in respuesta.headers
    assert float(respuesta.headers["X-Tiempo-Ms"]) < config.SLA_SEGUNDOS * 1000


def test_login_correcto_devuelve_token(cliente):
    respuesta = cliente.post(
        "/auth/login", json={"usuario": "admin", "password": config.ADMIN_PASSWORD}
    )
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["token_type"] == "bearer"
    assert cuerpo["usuario"]["perfil"] == "ADMINISTRADOR"
    assert cuerpo["inactividad_segundos"] == 180


def test_login_con_password_incorrecta_no_revela_si_el_usuario_existe(cliente):
    inexistente = cliente.post("/auth/login", json={"usuario": "nadie", "password": "Loquesea1"})
    existente = cliente.post("/auth/login", json={"usuario": "admin", "password": "Incorrecta1"})
    assert inexistente.status_code == existente.status_code == 401
    assert inexistente.json()["error"]["mensaje"] == existente.json()["error"]["mensaje"]


def test_rnf08_la_password_se_guarda_cifrada(cliente):
    with SessionLocal() as db:
        admin = db.scalar(select(Usuario).where(Usuario.usuario == "admin"))
        assert admin.password_hash != config.ADMIN_PASSWORD
        assert admin.password_hash.startswith("$2")  # bcrypt
        assert verificar_password(config.ADMIN_PASSWORD, admin.password_hash)


def test_rnf09_la_cuenta_se_bloquea_tras_los_reintentos(cliente):
    for _ in range(config.MAX_INTENTOS_LOGIN):
        cliente.post("/auth/login", json={"usuario": "admin", "password": "Incorrecta1"})

    respuesta = cliente.post(
        "/auth/login", json={"usuario": "admin", "password": config.ADMIN_PASSWORD}
    )
    assert respuesta.status_code == 423
    assert respuesta.json()["error"]["codigo"] == "USUARIO_BLOQUEADO"


def test_rnf10_no_se_permite_una_segunda_sesion(cliente, token_admin):
    segunda = cliente.post(
        "/auth/login", json={"usuario": "admin", "password": config.ADMIN_PASSWORD}
    )
    assert segunda.status_code == 409
    assert segunda.json()["error"]["codigo"] == "SESION_ACTIVA"


def test_logout_libera_la_sesion_y_permite_entrar_de_nuevo(cliente, encabezado_admin):
    assert cliente.post("/auth/logout", headers=encabezado_admin).status_code == 200
    de_nuevo = cliente.post(
        "/auth/login", json={"usuario": "admin", "password": config.ADMIN_PASSWORD}
    )
    assert de_nuevo.status_code == 200


def test_rnf03_la_sesion_caduca_por_inactividad(cliente, encabezado_admin):
    # Envejecemos la sesión más allá de la ventana de 3 minutos.
    with SessionLocal() as db:
        sesion = db.scalar(select(Sesion).where(Sesion.activa.is_(True)))
        sesion.ultima_actividad = sesion.ultima_actividad - timedelta(
            seconds=config.INACTIVIDAD_SEGUNDOS + 30
        )
        db.commit()

    respuesta = cliente.post("/auth/validar-sesion", headers=encabezado_admin)
    assert respuesta.status_code == 401
    assert respuesta.json()["error"]["codigo"] == "SESION_EXPIRADA"


def test_validar_sesion_refresca_la_ventana(cliente, encabezado_admin):
    primera = cliente.post("/auth/validar-sesion", headers=encabezado_admin)
    assert primera.status_code == 200
    assert primera.json()["segundos_inactivo"] < config.INACTIVIDAD_SEGUNDOS


def test_sin_token_no_se_accede(cliente):
    assert cliente.get("/auth/me").status_code == 401


def test_rnf05_un_mesero_no_puede_administrar_usuarios(cliente, encabezado_admin):
    creado = cliente.post(
        "/usuarios",
        headers=encabezado_admin,
        json={
            "cedula": "1032456789",
            "nombre": "Moe Szyslak",
            "sede_id": 1,
            "perfil": "MESERO",
            "usuario": "mszyslak",
            "password": "Cerveza2026",
        },
    )
    assert creado.status_code == 201, creado.text

    cliente.post("/auth/logout", headers=encabezado_admin)
    login = cliente.post("/auth/login", json={"usuario": "mszyslak", "password": "Cerveza2026"})
    assert login.status_code == 200
    mesero = {"Authorization": f"Bearer {login.json()['access_token']}"}

    respuesta = cliente.get("/usuarios", headers=mesero)
    assert respuesta.status_code == 403
    assert respuesta.json()["error"]["codigo"] == "SIN_PERMISOS"


def test_no_se_permiten_usuarios_duplicados(cliente, encabezado_admin):
    payload = {
        "cedula": "1099887766",
        "nombre": "Barney Gumble",
        "sede_id": 1,
        "perfil": "CAJERO",
        "usuario": "bgumble",
        "password": "Duff123456",
    }
    assert cliente.post("/usuarios", headers=encabezado_admin, json=payload).status_code == 201
    repetido = cliente.post("/usuarios", headers=encabezado_admin, json=payload)
    assert repetido.status_code == 409


def test_se_rechaza_una_password_debil(cliente, encabezado_admin):
    respuesta = cliente.post(
        "/usuarios",
        headers=encabezado_admin,
        json={
            "cedula": "1055443322",
            "nombre": "Lenny Leonard",
            "sede_id": 1,
            "perfil": "MESERO",
            "usuario": "lleonard",
            "password": "todominusculas",
        },
    )
    assert respuesta.status_code == 422
    assert respuesta.json()["error"]["codigo"] == "PASSWORD_DEBIL"


def test_rnf07_el_usuario_cambia_su_propia_password(cliente, encabezado_admin):
    respuesta = cliente.post(
        "/auth/cambiar-password",
        headers=encabezado_admin,
        json={"password_actual": config.ADMIN_PASSWORD, "password_nueva": "NuevaClave2026"},
    )
    assert respuesta.status_code == 200

    cliente.post("/auth/logout", headers=encabezado_admin)
    assert cliente.post(
        "/auth/login", json={"usuario": "admin", "password": "NuevaClave2026"}
    ).status_code == 200


def test_rnf07_el_administrador_restablece_la_password_de_otro(cliente, encabezado_admin):
    creado = cliente.post(
        "/usuarios",
        headers=encabezado_admin,
        json={
            "cedula": "1011223344",
            "nombre": "Carl Carlson",
            "sede_id": 2,
            "perfil": "CAJERO",
            "usuario": "ccarlson",
            "password": "Inicial2026",
        },
    ).json()

    respuesta = cliente.post(
        f"/usuarios/{creado['id']}/restablecer-password",
        headers=encabezado_admin,
        json={"password_nueva": "Restablecida2026"},
    )
    assert respuesta.status_code == 200

    cliente.post("/auth/logout", headers=encabezado_admin)
    login = cliente.post("/auth/login", json={"usuario": "ccarlson", "password": "Restablecida2026"})
    assert login.status_code == 200
    assert login.json()["usuario"]["debe_cambiar_password"] is True


def test_rnf12_cada_accion_queda_en_la_auditoria(cliente, encabezado_admin):
    with SessionLocal() as db:
        registros = list(db.scalars(select(Auditoria).where(Auditoria.accion == "LOGIN")))
        assert registros, "el login debe dejar rastro en la auditoría"
        ultimo = registros[-1]
        assert ultimo.usuario == "admin"
        assert ultimo.resultado == "OK"
        assert ultimo.fecha is not None
