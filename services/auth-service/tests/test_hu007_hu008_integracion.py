"""HU-002, HU-007 y HU-008 — funciones traídas de la rama de Angel al integrar.

- Consulta de la auditoría (`GET /auditoria`), antes `GET /audit`.
- Bloqueo temporal configurable (`BLOQUEO_MINUTOS`), antes `LOCKOUT_MINUTOS`.
- Inactivar / activar usuarios, en lugar de `DELETE /users/{id}`.
- Protección para que el administrador no se quite el acceso a sí mismo.
- Paginación del listado de usuarios.
- Límite de intentos fallidos por IP (OBS-02).
"""
from datetime import UTC, datetime, timedelta

import pytest

from app.config import config
from app.main import SessionLocal
from app.models import Usuario

from .utilidades import PASSWORD, auditorias, crear_usuario, entrar


# ------------------------------------------------------------ HU-008 · auditoría
def test_hu008_el_administrador_consulta_la_auditoria_del_mas_reciente_al_mas_antiguo(
    cliente, encabezado_admin
):
    crear_usuario(cliente, encabezado_admin, usuario="bgumble", perfil="MESERO", sede_id=2)
    respuesta = cliente.get("/auditoria", headers=encabezado_admin)
    assert respuesta.status_code == 200
    filas = respuesta.json()
    assert filas[0]["accion"] == "CREAR_USUARIO"
    fechas = [f["fecha"] for f in filas]
    assert fechas == sorted(fechas, reverse=True)
    assert int(respuesta.headers["X-Total-Count"]) == len(filas)
    for campo in ("usuario", "sede_id", "accion", "entidad", "resultado", "fecha", "ip", "request_id"):
        assert campo in filas[0]


def test_hu008_filtros_por_usuario_sede_accion_y_resultado(cliente, encabezado_admin):
    crear_usuario(cliente, encabezado_admin, usuario="bgumble", perfil="MESERO", sede_id=2)
    cliente.post("/auth/login", json={"usuario": "bgumble", "password": "Equivocada1"})
    params = {"usuario": "bgumble", "sede_id": 2, "accion": "login", "resultado": "fallido"}
    filas = cliente.get("/auditoria", headers=encabezado_admin, params=params).json()
    assert len(filas) == 1
    assert filas[0]["detalle"] == "password incorrecta"


def test_hu008_filtro_por_rango_de_fechas(cliente, encabezado_admin):
    ahora = datetime.now(UTC)
    futuro = {"desde": (ahora + timedelta(hours=1)).isoformat()}
    pasado = {"hasta": (ahora - timedelta(days=1)).isoformat()}
    hoy = {"desde": (ahora - timedelta(hours=1)).isoformat(),
           "hasta": (ahora + timedelta(hours=1)).isoformat()}
    assert cliente.get("/auditoria", headers=encabezado_admin, params=futuro).json() == []
    assert cliente.get("/auditoria", headers=encabezado_admin, params=pasado).json() == []
    assert cliente.get("/auditoria", headers=encabezado_admin, params=hoy).json()


def test_hu008_un_rango_al_reves_se_rechaza(cliente, encabezado_admin):
    ahora = datetime.now(UTC)
    params = {"desde": ahora.isoformat(), "hasta": (ahora - timedelta(days=1)).isoformat()}
    respuesta = cliente.get("/auditoria", headers=encabezado_admin, params=params)
    assert respuesta.status_code == 422
    assert respuesta.json()["error"]["codigo"] == "RANGO_INVALIDO"


def test_hu008_la_consulta_es_paginada(cliente, encabezado_admin):
    for i in range(5):
        crear_usuario(cliente, encabezado_admin, usuario=f"mesero{i}", perfil="MESERO")
    pagina1 = cliente.get("/auditoria", headers=encabezado_admin, params={"tamano": 2}).json()
    pagina2 = cliente.get("/auditoria", headers=encabezado_admin, params={"tamano": 2, "pagina": 2}).json()
    assert len(pagina1) == len(pagina2) == 2
    assert {f["id"] for f in pagina1}.isdisjoint({f["id"] for f in pagina2})
    assert cliente.get("/auditoria", headers=encabezado_admin, params={"tamano": 999}).status_code == 422


@pytest.mark.parametrize("metodo", ["POST", "PUT", "PATCH", "DELETE"])
def test_hu008_la_auditoria_no_se_puede_modificar_ni_borrar(cliente, encabezado_admin, metodo):
    assert cliente.request(metodo, "/auditoria", headers=encabezado_admin).status_code == 405
    assert cliente.request(metodo, "/auditoria/1", headers=encabezado_admin).status_code in (404, 405)


def test_hu008_los_accesos_denegados_se_ven_en_la_consulta(cliente, encabezado_admin):
    crear_usuario(cliente, encabezado_admin, usuario="kearney", perfil="MESERO", sede_id=3)
    h = entrar(cliente, "kearney")
    assert cliente.get("/auditoria", headers=h).status_code == 403
    filas = cliente.get("/auditoria", headers=encabezado_admin,
                        params={"accion": "ACCESO_DENEGADO"}).json()
    assert filas[0]["usuario"] == "kearney"
    assert filas[0]["sede_id"] == 3
    assert filas[0]["detalle"] == "GET /auditoria -> 403"


# ------------------------------------------------------------ HU-007 · usuarios
def test_hu007_inactivar_y_activar_con_endpoints_propios(cliente, encabezado_admin):
    objetivo = crear_usuario(cliente, encabezado_admin, usuario="otto", perfil="MESERO")
    h = entrar(cliente, "otto")

    inactivo = cliente.post(f"/usuarios/{objetivo['id']}/inactivar", headers=encabezado_admin)
    assert inactivo.status_code == 200
    assert inactivo.json()["estado"] == "INACTIVO"
    assert cliente.post("/auth/validar-sesion", headers=h).status_code in (401, 403)
    assert cliente.post("/auth/login", json={"usuario": "otto", "password": PASSWORD}).status_code == 403
    assert cliente.post(f"/usuarios/{objetivo['id']}/inactivar", headers=encabezado_admin).status_code == 409

    activo = cliente.post(f"/usuarios/{objetivo['id']}/activar", headers=encabezado_admin)
    assert activo.json()["estado"] == "ACTIVO"
    assert entrar(cliente, "otto")
    assert cliente.post(f"/usuarios/{objetivo['id']}/activar", headers=encabezado_admin).status_code == 409

    acciones = [f.accion for f in auditorias(entidad_id=str(objetivo["id"]))]
    assert "INACTIVAR_USUARIO" in acciones and "ACTIVAR_USUARIO" in acciones


def test_hu007_un_usuario_inactivo_conserva_su_historial(cliente, encabezado_admin):
    objetivo = crear_usuario(cliente, encabezado_admin, usuario="hans", perfil="CAJERO")
    cliente.post(f"/usuarios/{objetivo['id']}/inactivar", headers=encabezado_admin)
    assert cliente.get(f"/usuarios/{objetivo['id']}", headers=encabezado_admin).status_code == 200
    assert auditorias(accion="CREAR_USUARIO", entidad_id=str(objetivo["id"]))


def test_hu007_no_existe_borrado_fisico_de_usuarios(cliente, encabezado_admin):
    objetivo = crear_usuario(cliente, encabezado_admin, usuario="troy", perfil="MESERO")
    assert cliente.delete(f"/usuarios/{objetivo['id']}", headers=encabezado_admin).status_code == 405


@pytest.mark.parametrize("cambio", [{"estado": "INACTIVO"}, {"perfil": "MESERO"}])
def test_hu007_el_administrador_no_se_quita_el_acceso_a_si_mismo(cliente, encabezado_admin, cambio):
    yo = cliente.get("/auth/me", headers=encabezado_admin).json()
    respuesta = cliente.patch(f"/usuarios/{yo['id']}", headers=encabezado_admin, json=cambio)
    assert respuesta.status_code == 409
    assert respuesta.json()["error"]["codigo"] == "OPERACION_SOBRE_SI_MISMO"
    assert cliente.post(f"/usuarios/{yo['id']}/inactivar", headers=encabezado_admin).status_code == 409


def test_hu007_el_administrador_si_puede_editar_su_nombre(cliente, encabezado_admin):
    yo = cliente.get("/auth/me", headers=encabezado_admin).json()
    respuesta = cliente.patch(f"/usuarios/{yo['id']}", headers=encabezado_admin,
                              json={"nombre": "Moe Szyslak"})
    assert respuesta.status_code == 200
    assert respuesta.json()["nombre"] == "Moe Szyslak"


def test_hu007_listado_filtrado_y_paginado(cliente, encabezado_admin):
    for i in range(3):
        crear_usuario(cliente, encabezado_admin, usuario=f"meseroc{i}", perfil="MESERO", sede_id=1)
    crear_usuario(cliente, encabezado_admin, usuario="cajeron1", perfil="CAJERO", sede_id=2)

    meseros = cliente.get("/usuarios", headers=encabezado_admin, params={"perfil": "mesero", "sede_id": 1})
    assert [u["perfil"] for u in meseros.json()] == ["MESERO"] * 3
    assert meseros.headers["X-Total-Count"] == "3"

    pagina = cliente.get("/usuarios", headers=encabezado_admin, params={"tamano": 2, "pagina": 3})
    assert len(pagina.json()) == 1
    assert pagina.headers["X-Total-Count"] == "5"

    inactivos = cliente.get("/usuarios", headers=encabezado_admin, params={"estado": "INACTIVO"})
    assert inactivos.json() == []


def test_hu007_editar_un_usuario_inexistente_da_404(cliente, encabezado_admin):
    for metodo, ruta in [("PATCH", "/usuarios/999"), ("POST", "/usuarios/999/inactivar"),
                         ("POST", "/usuarios/999/activar"), ("POST", "/usuarios/999/desbloquear"),
                         ("GET", "/usuarios/999")]:
        cuerpo = {"nombre": "Nadie Nunca"} if metodo == "PATCH" else None
        assert cliente.request(metodo, ruta, headers=encabezado_admin, json=cuerpo).status_code == 404


# ------------------------------------------------------------ HU-002 · bloqueo
def _bloquear(cliente, usuario: str) -> None:
    for _ in range(config.MAX_INTENTOS_LOGIN):
        cliente.post("/auth/login", json={"usuario": usuario, "password": "Equivocada1"})


def test_hu002_por_defecto_el_bloqueo_es_hasta_que_el_admin_desbloquee(cliente, encabezado_admin):
    assert config.BLOQUEO_MINUTOS == 0
    crear_usuario(cliente, encabezado_admin, usuario="lenny", perfil="MESERO")
    _bloquear(cliente, "lenny")
    with SessionLocal() as db:
        usuario = db.query(Usuario).filter_by(usuario="lenny").one()
        assert usuario.bloqueado and usuario.bloqueado_hasta is None


def test_hu002_bloqueo_temporal_de_angel_se_levanta_solo(cliente, encabezado_admin, monkeypatch):
    monkeypatch.setattr(config, "BLOQUEO_MINUTOS", 15)
    crear_usuario(cliente, encabezado_admin, usuario="carlc", perfil="CAJERO")
    _bloquear(cliente, "carlc")

    respuesta = cliente.post("/auth/login", json={"usuario": "carlc", "password": PASSWORD})
    assert respuesta.status_code == 423
    assert "15 minutos" in respuesta.json()["error"]["mensaje"]

    with SessionLocal() as db:
        usuario = db.query(Usuario).filter_by(usuario="carlc").one()
        usuario.bloqueado_hasta = datetime.now(UTC) - timedelta(seconds=1)
        db.commit()
    assert entrar(cliente, "carlc")
    assert auditorias(accion="DESBLOQUEO_AUTOMATICO", usuario="carlc")


def test_hu002_el_restablecimiento_limpia_el_bloqueo_temporal(cliente, encabezado_admin, monkeypatch):
    monkeypatch.setattr(config, "BLOQUEO_MINUTOS", 15)
    objetivo = crear_usuario(cliente, encabezado_admin, usuario="selma", perfil="CAJERO")
    _bloquear(cliente, "selma")
    cliente.post(f"/usuarios/{objetivo['id']}/restablecer-password", headers=encabezado_admin,
                 json={"password_nueva": "Nueva2026Clave"})
    with SessionLocal() as db:
        usuario = db.query(Usuario).filter_by(usuario="selma").one()
        assert not usuario.bloqueado and usuario.bloqueado_hasta is None


# ------------------------------------------------------------ OBS-02 · límite por IP
def test_obs02_demasiados_fallos_desde_una_ip_frenan_a_cualquier_usuario(cliente, monkeypatch):
    monkeypatch.setattr(config, "MAX_INTENTOS_POR_IP", 4)
    for i in range(4):  # un atacante prueba contra usuarios distintos: ninguno llega a bloquearse
        cliente.post("/auth/login", json={"usuario": f"victima{i}", "password": "Adivina123"})
    respuesta = cliente.post("/auth/login", json={"usuario": "admin", "password": "Admin2026"})
    assert respuesta.status_code == 429
    assert respuesta.json()["error"]["codigo"] == "DEMASIADOS_INTENTOS"
    assert auditorias(accion="LOGIN", resultado="BLOQUEADO", usuario="admin")


def test_obs02_otra_ip_no_se_ve_afectada(cliente, encabezado_admin, monkeypatch):
    monkeypatch.setattr(config, "MAX_INTENTOS_POR_IP", 2)
    for _ in range(2):
        cliente.post("/auth/login", json={"usuario": "x-fake", "password": "Adivina123"},
                     headers={"X-Forwarded-For": "200.1.1.1"})
    crear_usuario(cliente, encabezado_admin, usuario="bart", perfil="MESERO")
    assert entrar(cliente, "bart", **{"X-Forwarded-For": "200.2.2.2"})


def test_obs02_con_limite_cero_se_desactiva(cliente, monkeypatch):
    monkeypatch.setattr(config, "MAX_INTENTOS_POR_IP", 0)
    for _ in range(5):
        cliente.post("/auth/login", json={"usuario": "nadie", "password": "Adivina123"})
    assert cliente.post("/auth/login", json={"usuario": "nadie", "password": "x"}).status_code == 401


def test_la_segunda_sesion_rechazada_queda_en_la_auditoria(cliente, encabezado_admin):
    cliente.post("/auth/login", json={"usuario": "admin", "password": "Admin2026"})
    fila = auditorias(accion="LOGIN", usuario="admin", resultado="RECHAZADO")[-1]
    assert fila.detalle == "ya tiene una sesión activa"
