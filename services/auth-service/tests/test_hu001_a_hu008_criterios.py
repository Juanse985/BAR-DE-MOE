"""Criterios de aceptación de HU-001 a HU-008 (M1 Seguridad · Angel).

Una prueba por criterio, con el número de HU y de criterio en el nombre, para
que el reporte de pytest sirva directo como evidencia en la Sprint Review.
Los criterios que son solo de pantalla (botón deshabilitado, redirección al
login) se verifican en el navegador; aquí va lo que sostiene el backend.
"""
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.config import config
from app.main import SessionLocal
from app.models import Sesion, Usuario
from barmoe_common.security import verificar_password

from .utilidades import PASSWORD, auditorias, crear_usuario, entrar

INCORRECTA = "Equivocada1"


def _login(cliente, usuario, password=PASSWORD, **cabeceras):
    return cliente.post("/auth/login", json={"usuario": usuario, "password": password},
                        headers=cabeceras or None)


def _codigo(respuesta) -> str:
    return respuesta.json()["error"]["codigo"]


def _fila(usuario: str) -> Usuario:
    with SessionLocal() as db:
        return db.scalar(select(Usuario).where(Usuario.usuario == usuario))


def _envejecer_sesiones(usuario: str, *, segundos_inactiva=0, minutos_desde_creada=0) -> None:
    """Simula el paso del tiempo moviendo hacia atrás las fechas de la sesión."""
    with SessionLocal() as db:
        fila = db.scalar(select(Usuario).where(Usuario.usuario == usuario))
        for sesion in db.scalars(select(Sesion).where(Sesion.usuario_id == fila.id)):
            sesion.ultima_actividad = datetime.now(UTC) - timedelta(seconds=segundos_inactiva)
            sesion.creada_en = datetime.now(UTC) - timedelta(minutes=minutos_desde_creada)
        db.commit()


# =================================================================== HU-001
def test_hu001_c3_c4_credenciales_correctas_entregan_token_y_perfil(cliente, encabezado_admin):
    crear_usuario(cliente, encabezado_admin, usuario="bgumble", perfil="MESERO")
    respuesta = _login(cliente, "bgumble")
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["access_token"] and cuerpo["token_type"] == "bearer"
    # El frontend arma el menú con el perfil que viene en la respuesta.
    assert cuerpo["usuario"]["perfil"] == "MESERO"


def test_hu001_c5_mensaje_unico_sin_decir_que_campo_fallo(cliente, encabezado_admin):
    crear_usuario(cliente, encabezado_admin, usuario="bgumble", perfil="MESERO")
    mala_clave = _login(cliente, "bgumble", INCORRECTA)
    usuario_inexistente = _login(cliente, "noexiste", PASSWORD)
    for respuesta in (mala_clave, usuario_inexistente):
        assert respuesta.status_code == 401
        assert respuesta.json()["error"]["mensaje"] == "Usuario o contraseña incorrectos."


def test_hu001_c6_usuario_inactivo_no_ingresa(cliente, encabezado_admin):
    objetivo = crear_usuario(cliente, encabezado_admin, usuario="bgumble", perfil="MESERO")
    cliente.post(f"/usuarios/{objetivo['id']}/inactivar", headers=encabezado_admin)
    respuesta = _login(cliente, "bgumble")
    assert respuesta.status_code == 403
    assert _codigo(respuesta) == "USUARIO_INACTIVO"


def test_hu001_c6_usuario_bloqueado_no_ingresa(cliente, encabezado_admin):
    crear_usuario(cliente, encabezado_admin, usuario="bgumble", perfil="MESERO")
    for _ in range(config.MAX_INTENTOS_LOGIN):
        _login(cliente, "bgumble", INCORRECTA)
    assert _codigo(_login(cliente, "bgumble")) == "USUARIO_BLOQUEADO"


# =================================================================== HU-002
def test_hu002_c1_cuenta_los_intentos_fallidos_consecutivos(cliente, encabezado_admin):
    crear_usuario(cliente, encabezado_admin, usuario="lenny", perfil="MESERO")
    _login(cliente, "lenny", INCORRECTA)
    assert _fila("lenny").intentos_fallidos == 1
    _login(cliente, "lenny", INCORRECTA)
    assert _fila("lenny").intentos_fallidos == 2


def test_hu002_c2_c4_al_tercer_intento_responde_usuario_bloqueado(cliente, encabezado_admin):
    crear_usuario(cliente, encabezado_admin, usuario="lenny", perfil="MESERO")
    assert _login(cliente, "lenny", INCORRECTA).status_code == 401
    assert _login(cliente, "lenny", INCORRECTA).status_code == 401
    tercero = _login(cliente, "lenny", INCORRECTA)
    assert tercero.status_code == 423
    assert _codigo(tercero) == "USUARIO_BLOQUEADO"
    assert "administrador" in tercero.json()["error"]["mensaje"].lower()
    assert _fila("lenny").bloqueado is True


def test_hu002_c2_bloqueado_ni_con_la_password_correcta(cliente, encabezado_admin):
    crear_usuario(cliente, encabezado_admin, usuario="lenny", perfil="MESERO")
    for _ in range(3):
        _login(cliente, "lenny", INCORRECTA)
    respuesta = _login(cliente, "lenny", PASSWORD)
    assert respuesta.status_code == 423
    assert _codigo(respuesta) == "USUARIO_BLOQUEADO"


def test_hu002_c3_un_ingreso_exitoso_deja_el_contador_en_cero(cliente, encabezado_admin):
    crear_usuario(cliente, encabezado_admin, usuario="lenny", perfil="MESERO")
    _login(cliente, "lenny", INCORRECTA)
    _login(cliente, "lenny", INCORRECTA)
    h = entrar(cliente, "lenny")
    assert _fila("lenny").intentos_fallidos == 0
    cliente.post("/auth/logout", headers=h)
    # Dos fallos más no bloquean: el conteo volvió a empezar.
    _login(cliente, "lenny", INCORRECTA)
    _login(cliente, "lenny", INCORRECTA)
    assert _fila("lenny").bloqueado is False


def test_hu002_c5_cada_intento_fallido_queda_en_la_auditoria(cliente, encabezado_admin):
    crear_usuario(cliente, encabezado_admin, usuario="lenny", perfil="MESERO")
    for _ in range(3):
        _login(cliente, "lenny", INCORRECTA, **{"X-Forwarded-For": "10.1.2.3"})
    fallidos = auditorias(accion="LOGIN", usuario="lenny", resultado="FALLIDO")
    assert len(fallidos) == 3
    for fila in fallidos:
        assert fila.fecha is not None  # fecha y hora
        assert fila.ip == "10.1.2.3"


def test_hu002_c6_el_numero_de_intentos_es_parametrizable(cliente, encabezado_admin, monkeypatch):
    monkeypatch.setattr(config, "MAX_INTENTOS_LOGIN", 5)
    crear_usuario(cliente, encabezado_admin, usuario="lenny", perfil="MESERO")
    for _ in range(4):
        assert _login(cliente, "lenny", INCORRECTA).status_code == 401
    assert _codigo(_login(cliente, "lenny", INCORRECTA)) == "USUARIO_BLOQUEADO"


# =================================================================== HU-003
def test_hu003_c1_c2_segundo_ingreso_rechazado_con_sesion_activa(cliente, encabezado_admin):
    crear_usuario(cliente, encabezado_admin, usuario="carlc", perfil="CAJERO")
    entrar(cliente, "carlc")
    segundo = _login(cliente, "carlc")
    assert segundo.status_code == 409
    assert _codigo(segundo) == "SESION_ACTIVA"


def test_hu003_c3_despues_del_logout_puede_entrar_de_inmediato(cliente, encabezado_admin):
    crear_usuario(cliente, encabezado_admin, usuario="carlc", perfil="CAJERO")
    h = entrar(cliente, "carlc")
    assert cliente.post("/auth/logout", headers=h).status_code == 200
    with SessionLocal() as db:
        sesiones = list(db.scalars(select(Sesion).where(Sesion.usuario_id == _fila("carlc").id)))
        assert all(not s.activa and s.motivo_cierre == "LOGOUT" for s in sesiones)
    assert _login(cliente, "carlc").status_code == 200


def test_hu003_c4_sesion_vencida_por_inactividad_no_impide_entrar(cliente, encabezado_admin):
    crear_usuario(cliente, encabezado_admin, usuario="carlc", perfil="CAJERO")
    entrar(cliente, "carlc")
    _envejecer_sesiones("carlc", segundos_inactiva=config.INACTIVIDAD_SEGUNDOS + 1)
    assert _login(cliente, "carlc").status_code == 200


def test_hu003_c4_sesion_con_token_caducado_no_impide_entrar(cliente, encabezado_admin):
    crear_usuario(cliente, encabezado_admin, usuario="carlc", perfil="CAJERO")
    entrar(cliente, "carlc")
    # Trabajó hasta el último minuto: actividad reciente, pero el JWT ya caducó.
    _envejecer_sesiones("carlc", segundos_inactiva=5, minutos_desde_creada=config.JWT_EXPIRA_MINUTOS + 1)
    assert _login(cliente, "carlc").status_code == 200
    with SessionLocal() as db:
        motivos = {s.motivo_cierre for s in db.scalars(select(Sesion).where(Sesion.activa.is_(False)))}
    assert "TOKEN_VENCIDO" in motivos


def test_hu003_c5_la_sesion_unica_es_parametrizable(cliente, encabezado_admin, monkeypatch):
    monkeypatch.setattr(config, "PERMITIR_MULTISESION", True)
    crear_usuario(cliente, encabezado_admin, usuario="carlc", perfil="CAJERO")
    entrar(cliente, "carlc")
    assert _login(cliente, "carlc").status_code == 200


# =================================================================== HU-004
def test_hu004_c1_c2_cada_operacion_registra_y_reinicia_la_ultima_actividad(cliente, encabezado_admin):
    crear_usuario(cliente, encabezado_admin, usuario="carlc", perfil="CAJERO")
    h = entrar(cliente, "carlc")
    _envejecer_sesiones("carlc", segundos_inactiva=120)
    respuesta = cliente.post("/auth/validar-sesion", headers=h)
    assert respuesta.status_code == 200
    assert respuesta.json()["segundos_inactivo"] >= 119
    # El conteo volvió a empezar: la siguiente operación ve ~0 s de inactividad.
    assert cliente.post("/auth/validar-sesion", headers=h).json()["segundos_inactivo"] < 5


def test_hu004_c3_mas_de_tres_minutos_devuelve_sesion_expirada(cliente, encabezado_admin):
    crear_usuario(cliente, encabezado_admin, usuario="carlc", perfil="CAJERO")
    h = entrar(cliente, "carlc")
    _envejecer_sesiones("carlc", segundos_inactiva=181)
    respuesta = cliente.post("/auth/validar-sesion", headers=h)
    assert respuesta.status_code == 401
    assert _codigo(respuesta) == "SESION_EXPIRADA"


def test_hu004_c5_el_tiempo_de_inactividad_es_parametrizable(cliente, encabezado_admin, monkeypatch):
    monkeypatch.setattr(config, "INACTIVIDAD_SEGUNDOS", 600)
    crear_usuario(cliente, encabezado_admin, usuario="carlc", perfil="CAJERO")
    h = entrar(cliente, "carlc")
    _envejecer_sesiones("carlc", segundos_inactiva=300)
    assert cliente.post("/auth/validar-sesion", headers=h).status_code == 200


def test_hu004_c4_el_login_le_dice_al_frontend_cuanto_es_la_inactividad(cliente):
    respuesta = _login(cliente, config.ADMIN_USUARIO, config.ADMIN_PASSWORD)
    assert respuesta.json()["inactividad_segundos"] == config.INACTIVIDAD_SEGUNDOS


# =================================================================== HU-005
def _cambiar(cliente, h, actual, nueva):
    return cliente.post("/auth/cambiar-password", headers=h,
                        json={"password_actual": actual, "password_nueva": nueva})


def test_hu005_c2_si_la_actual_no_coincide_se_rechaza(cliente, encabezado_admin):
    crear_usuario(cliente, encabezado_admin, usuario="moesz", perfil="CAJERO")
    h = entrar(cliente, "moesz")
    respuesta = _cambiar(cliente, h, "NoEsLaMia1", "NuevaClave2026")
    assert respuesta.status_code == 401
    assert verificar_password(PASSWORD, _fila("moesz").password_hash)  # no cambió


def test_hu005_c3_reglas_de_la_password_nueva(cliente, encabezado_admin):
    crear_usuario(cliente, encabezado_admin, usuario="moesz", perfil="CAJERO")
    h = entrar(cliente, "moesz")
    for debil in ("Corta1", "sinmayuscula1", "SINMINUSCULA1", "SinNumeroAqui"):
        respuesta = _cambiar(cliente, h, PASSWORD, debil)
        assert respuesta.status_code == 422, debil
    assert _cambiar(cliente, h, PASSWORD, "Valida2026").status_code == 200


def test_hu005_c4_la_nueva_no_puede_ser_igual_a_la_actual(cliente, encabezado_admin):
    crear_usuario(cliente, encabezado_admin, usuario="moesz", perfil="CAJERO")
    h = entrar(cliente, "moesz")
    respuesta = _cambiar(cliente, h, PASSWORD, PASSWORD)
    assert respuesta.status_code == 422
    assert _codigo(respuesta) == "PASSWORD_REPETIDA"


def test_hu005_c5_la_password_se_guarda_cifrada(cliente, encabezado_admin):
    crear_usuario(cliente, encabezado_admin, usuario="moesz", perfil="CAJERO")
    h = entrar(cliente, "moesz")
    _cambiar(cliente, h, PASSWORD, "Valida2026")
    guardada = _fila("moesz").password_hash
    assert guardada != "Valida2026" and guardada.startswith("$2")
    assert verificar_password("Valida2026", guardada)


def test_hu005_c6_el_cambio_y_los_intentos_quedan_en_la_auditoria(cliente, encabezado_admin):
    objetivo = crear_usuario(cliente, encabezado_admin, usuario="moesz", perfil="CAJERO")
    h = entrar(cliente, "moesz")
    _cambiar(cliente, h, "NoEsLaMia1", "Valida2026")
    _cambiar(cliente, h, PASSWORD, "Valida2026")
    filas = auditorias(accion="CAMBIO_PASSWORD", usuario="moesz")
    assert [f.resultado for f in filas] == ["FALLIDO", "OK"]
    assert filas[-1].entidad == "usuarios" and filas[-1].entidad_id == str(objetivo["id"])


# =================================================================== HU-006
def _restablecer(cliente, h, usuario_id, nueva="Temporal2026"):
    return cliente.post(f"/usuarios/{usuario_id}/restablecer-password", headers=h,
                        json={"password_nueva": nueva})


def test_hu006_c1_solo_el_administrador_restablece(cliente, encabezado_admin):
    crear_usuario(cliente, encabezado_admin, usuario="mesero1", perfil="MESERO")
    objetivo = crear_usuario(cliente, encabezado_admin, usuario="cajero1", perfil="CAJERO")
    h_mesero = entrar(cliente, "mesero1")
    respuesta = _restablecer(cliente, h_mesero, objetivo["id"])
    assert respuesta.status_code == 403


def test_hu006_c2_c3_desbloquea_pone_en_cero_y_marca_cambio(cliente, encabezado_admin):
    objetivo = crear_usuario(cliente, encabezado_admin, usuario="lenny", perfil="MESERO")
    for _ in range(3):
        _login(cliente, "lenny", INCORRECTA)
    assert _fila("lenny").bloqueado is True
    assert _restablecer(cliente, encabezado_admin, objetivo["id"]).status_code == 200
    fila = _fila("lenny")
    assert fila.bloqueado is False and fila.intentos_fallidos == 0
    assert fila.debe_cambiar_password is True
    respuesta = _login(cliente, "lenny", "Temporal2026")
    assert respuesta.status_code == 200
    assert respuesta.json()["usuario"]["debe_cambiar_password"] is True


def test_hu006_c4_cierra_las_sesiones_activas_del_usuario(cliente, encabezado_admin):
    objetivo = crear_usuario(cliente, encabezado_admin, usuario="lenny", perfil="MESERO")
    h = entrar(cliente, "lenny")
    _restablecer(cliente, encabezado_admin, objetivo["id"])
    respuesta = cliente.post("/auth/validar-sesion", headers=h)
    assert respuesta.status_code == 401
    assert _codigo(respuesta) == "SESION_CERRADA"


def test_hu006_c5_queda_en_la_auditoria_quien_lo_ejecuto(cliente, encabezado_admin):
    objetivo = crear_usuario(cliente, encabezado_admin, usuario="lenny", perfil="MESERO")
    _restablecer(cliente, encabezado_admin, objetivo["id"])
    fila = auditorias(accion="RESTABLECER_PASSWORD")[-1]
    assert fila.usuario == config.ADMIN_USUARIO
    assert fila.entidad == "usuarios" and fila.entidad_id == str(objetivo["id"])


# =================================================================== HU-007
def test_hu007_c1_campos_obligatorios(cliente, encabezado_admin):
    completo = {"cedula": "1032456789", "nombre": "Moe Szyslak", "sede_id": 1,
                "perfil": "CAJERO", "usuario": "mszyslak", "password": PASSWORD}
    for campo in ("cedula", "nombre", "perfil", "usuario", "password"):
        incompleto = {k: v for k, v in completo.items() if k != campo}
        assert cliente.post("/usuarios", headers=encabezado_admin, json=incompleto).status_code == 422
    # Cajero y mesero sin sede: rechazado (el administrador puede ser de todas las sedes).
    sin_sede = {**completo, "sede_id": None}
    assert cliente.post("/usuarios", headers=encabezado_admin, json=sin_sede).status_code == 422
    assert cliente.post("/usuarios", headers=encabezado_admin, json=completo).status_code == 201


def test_hu007_c2_solo_tres_perfiles(cliente, encabezado_admin):
    for perfil in ("ADMINISTRADOR", "CAJERO", "MESERO"):
        crear_usuario(cliente, encabezado_admin, usuario=f"u{perfil.lower()}", perfil=perfil)
    respuesta = cliente.post("/usuarios", headers=encabezado_admin, json={
        "cedula": "99999999", "nombre": "Otro", "sede_id": 1, "perfil": "BARTENDER",
        "usuario": "otro", "password": PASSWORD})
    assert respuesta.status_code == 422


def test_hu007_c3_no_se_repite_cedula_ni_usuario(cliente, encabezado_admin):
    crear_usuario(cliente, encabezado_admin, usuario="lenny", perfil="MESERO", cedula="11111111")
    misma_cedula = cliente.post("/usuarios", headers=encabezado_admin, json={
        "cedula": "11111111", "nombre": "Otro", "sede_id": 1, "perfil": "MESERO",
        "usuario": "otro", "password": PASSWORD})
    mismo_usuario = cliente.post("/usuarios", headers=encabezado_admin, json={
        "cedula": "22222222", "nombre": "Otro", "sede_id": 1, "perfil": "MESERO",
        "usuario": "lenny", "password": PASSWORD})
    assert (misma_cedula.status_code, _codigo(misma_cedula)) == (409, "CEDULA_DUPLICADA")
    assert (mismo_usuario.status_code, _codigo(mismo_usuario)) == (409, "USUARIO_DUPLICADO")


def test_hu007_c4_listado_filtrado_por_sede_y_perfil_y_paginado(cliente, encabezado_admin):
    for i in range(3):
        crear_usuario(cliente, encabezado_admin, usuario=f"meseros1n{i}", perfil="MESERO", sede_id=1)
    crear_usuario(cliente, encabezado_admin, usuario="cajeros1", perfil="CAJERO", sede_id=1)
    crear_usuario(cliente, encabezado_admin, usuario="meseros2", perfil="MESERO", sede_id=2)
    respuesta = cliente.get("/usuarios", headers=encabezado_admin,
                            params={"sede_id": 1, "perfil": "MESERO", "pagina": 1, "tamano": 2})
    assert respuesta.headers["X-Total-Count"] == "3"
    assert len(respuesta.json()) == 2
    assert all(u["sede_id"] == 1 and u["perfil"] == "MESERO" for u in respuesta.json())
    segunda = cliente.get("/usuarios", headers=encabezado_admin,
                          params={"sede_id": 1, "perfil": "MESERO", "pagina": 2, "tamano": 2})
    assert len(segunda.json()) == 1


def test_hu007_c5_inactivo_no_entra_pero_conserva_su_historial(cliente, encabezado_admin):
    objetivo = crear_usuario(cliente, encabezado_admin, usuario="lenny", perfil="MESERO")
    h = entrar(cliente, "lenny")
    cliente.post("/auth/logout", headers=h)
    cliente.post(f"/usuarios/{objetivo['id']}/inactivar", headers=encabezado_admin)
    assert _codigo(_login(cliente, "lenny")) == "USUARIO_INACTIVO"
    # Sigue existiendo (no hay borrado) y su historial está intacto.
    assert cliente.get(f"/usuarios/{objetivo['id']}", headers=encabezado_admin).status_code == 200
    assert auditorias(accion="LOGIN", usuario="lenny", resultado="OK")
    assert cliente.delete(f"/usuarios/{objetivo['id']}", headers=encabezado_admin).status_code == 405


def test_hu007_c5_modificar_y_reactivar(cliente, encabezado_admin):
    objetivo = crear_usuario(cliente, encabezado_admin, usuario="lenny", perfil="MESERO")
    editado = cliente.patch(f"/usuarios/{objetivo['id']}", headers=encabezado_admin,
                            json={"nombre": "Lenny Leonard", "perfil": "CAJERO", "sede_id": 2})
    assert editado.status_code == 200
    assert (editado.json()["nombre"], editado.json()["perfil"]) == ("Lenny Leonard", "CAJERO")
    cliente.post(f"/usuarios/{objetivo['id']}/inactivar", headers=encabezado_admin)
    assert cliente.post(f"/usuarios/{objetivo['id']}/activar",
                        headers=encabezado_admin).json()["estado"] == "ACTIVO"
    assert entrar(cliente, "lenny")


def test_hu007_c6_solo_el_administrador_entra_al_modulo(cliente, encabezado_admin):
    crear_usuario(cliente, encabezado_admin, usuario="cajero1", perfil="CAJERO")
    h = entrar(cliente, "cajero1")
    assert cliente.get("/usuarios", headers=h).status_code == 403
    assert cliente.post("/usuarios", headers=h, json={}).status_code in (403, 422)
    assert cliente.post("/usuarios/1/inactivar", headers=h).status_code == 403


# =================================================================== HU-008
def test_hu008_c1_cada_transaccion_registra_los_siete_datos(cliente, encabezado_admin):
    crear_usuario(cliente, encabezado_admin, usuario="lenny", perfil="MESERO", sede_id=2)
    entrar(cliente, "lenny")
    acciones = {"LOGIN": auditorias(accion="LOGIN", usuario="lenny", resultado="OK")[-1],
                "CREAR_USUARIO": auditorias(accion="CREAR_USUARIO")[-1]}
    for nombre, fila in acciones.items():
        assert fila.usuario, nombre
        assert fila.accion and fila.entidad and fila.resultado, nombre
        assert fila.fecha is not None, nombre
    assert acciones["LOGIN"].sede_id == 2


def test_hu008_c2_filtros_por_usuario_sede_y_fechas(cliente, encabezado_admin):
    crear_usuario(cliente, encabezado_admin, usuario="lenny", perfil="MESERO", sede_id=2)
    entrar(cliente, "lenny")
    por_usuario = cliente.get("/auditoria", headers=encabezado_admin, params={"usuario": "lenny"}).json()
    assert por_usuario and all(r["usuario"] == "lenny" for r in por_usuario)
    por_sede = cliente.get("/auditoria", headers=encabezado_admin, params={"sede_id": 2}).json()
    assert por_sede and all(r["sede_id"] == 2 for r in por_sede)
    ahora = datetime.now(UTC)
    rango = {"desde": (ahora - timedelta(minutes=5)).isoformat(),
             "hasta": (ahora + timedelta(minutes=5)).isoformat()}
    assert cliente.get("/auditoria", headers=encabezado_admin, params=rango).json()
    futuro = {"desde": (ahora + timedelta(days=1)).isoformat()}
    assert cliente.get("/auditoria", headers=encabezado_admin, params=futuro).json() == []


def test_hu008_c3_paginado_del_mas_reciente_al_mas_antiguo(cliente, encabezado_admin):
    for i in range(4):
        crear_usuario(cliente, encabezado_admin, usuario=f"lenny{i}", perfil="MESERO")
    pagina1 = cliente.get("/auditoria", headers=encabezado_admin, params={"tamano": 3, "pagina": 1})
    pagina2 = cliente.get("/auditoria", headers=encabezado_admin, params={"tamano": 3, "pagina": 2})
    total = int(pagina1.headers["X-Total-Count"])
    assert len(pagina1.json()) == 3 and total > 3
    ids = [r["id"] for r in pagina1.json() + pagina2.json()]
    assert ids == sorted(ids, reverse=True)
    fechas = [r["fecha"] for r in pagina1.json()]
    assert fechas == sorted(fechas, reverse=True)


def test_hu008_c4_solo_el_administrador_consulta(cliente, encabezado_admin):
    crear_usuario(cliente, encabezado_admin, usuario="cajero1", perfil="CAJERO")
    h = entrar(cliente, "cajero1")
    assert cliente.get("/auditoria", headers=h).status_code == 403
    assert cliente.get("/auditoria").status_code == 401


def test_hu008_c5_no_se_puede_modificar_ni_borrar(cliente, encabezado_admin):
    fila_id = cliente.get("/auditoria", headers=encabezado_admin).json()[0]["id"]
    for metodo in ("put", "patch", "delete"):
        enviar = getattr(cliente, metodo)
        assert enviar(f"/auditoria/{fila_id}", headers=encabezado_admin).status_code in (404, 405)
        assert enviar("/auditoria", headers=encabezado_admin).status_code == 405


def test_hu004_c3_toda_operacion_posterior_sigue_diciendo_sesion_expirada(cliente, encabezado_admin):
    crear_usuario(cliente, encabezado_admin, usuario="carlc", perfil="CAJERO")
    h = entrar(cliente, "carlc")
    _envejecer_sesiones("carlc", segundos_inactiva=181)
    # La pantalla suele lanzar varias peticiones a la vez: todas deben ver el mismo motivo.
    for _ in range(3):
        respuesta = cliente.post("/auth/validar-sesion", headers=h)
        assert (respuesta.status_code, _codigo(respuesta)) == (401, "SESION_EXPIRADA")
