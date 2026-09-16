"""HU-025 · RNF-12 — Trazabilidad de las transacciones en el auth-service.

Criterio: toda transacción registra usuario, sede, fecha y hora, y es
consultable por el administrador. Las pruebas marcadas `xfail` documentan
defectos abiertos: pasan a verde solas cuando se corrigen (strict=True obliga
a quitar la marca en ese momento).
"""
from datetime import UTC, datetime, timedelta

import pytest

from .utilidades import auditorias, crear_usuario, entrar


def _fecha(fila) -> datetime:
    return fila.fecha if fila.fecha.tzinfo else fila.fecha.replace(tzinfo=UTC)


def test_hu025_login_exitoso_guarda_usuario_sede_fecha_e_ip(cliente, encabezado_admin):
    crear_usuario(cliente, encabezado_admin, usuario="bgumble", perfil="MESERO", sede_id=2)
    antes = datetime.now(UTC) - timedelta(seconds=1)
    entrar(cliente, "bgumble")

    fila = auditorias(accion="LOGIN", usuario="bgumble", resultado="OK")[-1]
    assert fila.usuario_id is not None
    assert fila.sede_id == 2
    assert fila.ip  # TestClient reporta "testclient"
    assert antes <= _fecha(fila) <= datetime.now(UTC) + timedelta(seconds=1)


def test_hu025_login_fallido_queda_registrado_con_el_motivo(cliente, encabezado_admin):
    crear_usuario(cliente, encabezado_admin, usuario="ccarlson", perfil="CAJERO", sede_id=1)
    cliente.post("/auth/login", json={"usuario": "ccarlson", "password": "Equivocada1"})

    fila = auditorias(accion="LOGIN", usuario="ccarlson", resultado="FALLIDO")[-1]
    assert fila.sede_id == 1
    assert fila.detalle == "password incorrecta"


def test_hu025_login_de_usuario_inexistente_tambien_se_registra(cliente):
    cliente.post("/auth/login", json={"usuario": "fantasma", "password": "Cualquiera1"})
    fila = auditorias(accion="LOGIN", usuario="fantasma")[-1]
    assert fila.resultado == "FALLIDO"
    assert fila.usuario_id is None


def test_hu025_bloqueo_e_intento_bloqueado_quedan_registrados(cliente, encabezado_admin):
    crear_usuario(cliente, encabezado_admin, usuario="lenny", perfil="MESERO")
    for _ in range(3):
        cliente.post("/auth/login", json={"usuario": "lenny", "password": "Equivocada1"})
    cliente.post("/auth/login", json={"usuario": "lenny", "password": "Cerveza2026"})

    filas = auditorias(accion="LOGIN", usuario="lenny")
    assert filas[2].detalle == "bloqueado tras 3 intentos"
    assert filas[-1].resultado == "BLOQUEADO"


def test_hu025_la_creacion_de_usuarios_registra_al_administrador(cliente, encabezado_admin):
    creado = crear_usuario(cliente, encabezado_admin, usuario="apunahasapee", perfil="CAJERO")
    fila = auditorias(accion="CREAR_USUARIO", entidad_id=str(creado["id"]))[-1]
    assert fila.usuario == "admin"
    assert fila.entidad == "usuarios"


def test_hu025_restablecer_y_desbloquear_registran_quien_y_a_quien(cliente, encabezado_admin):
    objetivo = crear_usuario(cliente, encabezado_admin, usuario="otto", perfil="MESERO")
    cliente.post(f"/usuarios/{objetivo['id']}/restablecer-password", headers=encabezado_admin,
                 json={"password_nueva": "NuevaClave2026"})
    cliente.post(f"/usuarios/{objetivo['id']}/desbloquear", headers=encabezado_admin)

    for accion in ("RESTABLECER_PASSWORD", "DESBLOQUEAR_USUARIO"):
        fila = auditorias(accion=accion)[-1]
        assert fila.usuario == "admin"
        assert fila.entidad_id == str(objetivo["id"])


def test_hu025_el_cambio_de_password_propio_se_registra(cliente, encabezado_admin):
    crear_usuario(cliente, encabezado_admin, usuario="skinner", perfil="CAJERO", sede_id=3)
    h = entrar(cliente, "skinner")
    cliente.post("/auth/cambiar-password", headers=h,
                 json={"password_actual": "Cerveza2026", "password_nueva": "Director2026"})
    fila = auditorias(accion="CAMBIO_PASSWORD", usuario="skinner")[-1]
    assert fila.sede_id == 3


def test_hu025_ninguna_fila_de_auditoria_guarda_passwords(cliente, encabezado_admin):
    crear_usuario(cliente, encabezado_admin, usuario="wiggum", perfil="MESERO")
    cliente.post("/auth/login", json={"usuario": "wiggum", "password": "ClaveErrada99"})
    for fila in auditorias():
        texto = " ".join(str(v) for v in (fila.detalle, fila.usuario, fila.entidad))
        assert "Cerveza2026" not in texto
        assert "ClaveErrada99" not in texto


# ------------------------------------------------------ defectos abiertos
@pytest.mark.xfail(strict=True, reason="DEF-02: PATCH /usuarios/{id} no deja registro en auditoría")
def test_hu025_la_edicion_de_un_usuario_queda_registrada(cliente, encabezado_admin):
    objetivo = crear_usuario(cliente, encabezado_admin, usuario="nelson", perfil="MESERO")
    cliente.patch(f"/usuarios/{objetivo['id']}", headers=encabezado_admin, json={"estado": "INACTIVO"})
    assert any(f.entidad_id == str(objetivo["id"]) and f.accion != "CREAR_USUARIO" for f in auditorias())


@pytest.mark.xfail(strict=True, reason="DEF-03: el LOGOUT se registra sin nombre de usuario ni sede")
def test_hu025_el_logout_registra_usuario_y_sede(cliente, encabezado_admin):
    crear_usuario(cliente, encabezado_admin, usuario="milhouse", perfil="MESERO", sede_id=2)
    h = entrar(cliente, "milhouse")
    cliente.post("/auth/logout", headers=h)
    fila = auditorias(accion="LOGOUT")[-1]
    assert fila.usuario == "milhouse"
    assert fila.sede_id == 2


@pytest.mark.xfail(strict=True, reason="DEF-07: detrás del gateway se guarda la IP del gateway y no la del "
                                       "cliente (falta reenviar y usar X-Forwarded-For)")
def test_hu025_la_ip_registrada_es_la_del_cliente_real(cliente, encabezado_admin):
    crear_usuario(cliente, encabezado_admin, usuario="kent", perfil="MESERO")
    entrar(cliente, "kent", **{"X-Forwarded-For": "181.60.10.20"})
    assert auditorias(accion="LOGIN", usuario="kent")[-1].ip == "181.60.10.20"


@pytest.mark.xfail(strict=True, reason="DEF-08: el X-Request-Id del gateway no se guarda en auditoría")
def test_hu025_la_auditoria_guarda_el_request_id(cliente, encabezado_admin):
    crear_usuario(cliente, encabezado_admin, usuario="patty", perfil="CAJERO")
    entrar(cliente, "patty", **{"X-Request-Id": "req-demo-001"})
    assert auditorias(accion="LOGIN", usuario="patty")[-1].request_id == "req-demo-001"
