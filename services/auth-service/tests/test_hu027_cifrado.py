"""HU-027 · RNF-08 — Cifrado de las contraseñas (control C-2).

Verificación de la propuesta: "inspección de la tabla de usuarios: ninguna
contraseña legible". Aquí se hace esa inspección sobre TODAS las tablas.
"""
from sqlalchemy import inspect, text

from app.main import SessionLocal

from .utilidades import PASSWORD, crear_usuario, entrar


def _todos_los_valores() -> list[str]:
    valores = []
    with SessionLocal() as db:
        for tabla in inspect(SessionLocal.engine).get_table_names():
            for fila in db.execute(text(f'SELECT * FROM "{tabla}"')):
                valores.extend(str(v) for v in fila if v is not None)
    return valores


def test_hu027_ninguna_tabla_contiene_una_password_legible(cliente, encabezado_admin):
    crear_usuario(cliente, encabezado_admin, usuario="bgumble", perfil="MESERO")
    objetivo = crear_usuario(cliente, encabezado_admin, usuario="ccarlson", perfil="CAJERO")
    cliente.post(f"/usuarios/{objetivo['id']}/restablecer-password", headers=encabezado_admin,
                 json={"password_nueva": "Restablecida2026"})
    h = entrar(cliente, "bgumble")
    cliente.post("/auth/cambiar-password", headers=h,
                 json={"password_actual": PASSWORD, "password_nueva": "Cambiada2026"})

    valores = _todos_los_valores()
    for secreto in (PASSWORD, "Restablecida2026", "Cambiada2026", "Admin2026"):
        assert not any(secreto in v for v in valores), f"'{secreto}' aparece en la base"


def test_hu027_todos_los_hashes_son_bcrypt_y_unicos(cliente, encabezado_admin):
    for nombre in ("lenny", "carlc", "moesz"):
        crear_usuario(cliente, encabezado_admin, usuario=nombre, perfil="MESERO")
    with SessionLocal() as db:
        hashes = [h for (h,) in db.execute(text("SELECT password_hash FROM usuarios"))]
    assert len(hashes) == 4
    assert all(h.startswith("$2b$12$") and len(h) == 60 for h in hashes)
    assert len(set(hashes)) == len(hashes)  # misma password, sal distinta


def test_hu027_la_api_nunca_devuelve_el_hash(cliente, encabezado_admin):
    creado = crear_usuario(cliente, encabezado_admin, usuario="apunahasapee", perfil="CAJERO")
    respuestas = [
        creado,
        cliente.get(f"/usuarios/{creado['id']}", headers=encabezado_admin).json(),
        cliente.get("/auth/me", headers=encabezado_admin).json(),
        *cliente.get("/usuarios", headers=encabezado_admin).json(),
    ]
    for cuerpo in respuestas:
        assert "password" not in cuerpo
        assert "password_hash" not in cuerpo
        assert "$2b$" not in str(cuerpo)


def test_hu027_el_login_sigue_funcionando_con_la_password_cifrada(cliente, encabezado_admin):
    crear_usuario(cliente, encabezado_admin, usuario="otto", perfil="MESERO")
    assert entrar(cliente, "otto")["Authorization"].startswith("Bearer ")


def test_hu027_la_password_restablecida_se_guarda_cifrada_y_funciona(cliente, encabezado_admin):
    objetivo = crear_usuario(cliente, encabezado_admin, usuario="selma", perfil="CAJERO")
    cliente.post(f"/usuarios/{objetivo['id']}/restablecer-password", headers=encabezado_admin,
                 json={"password_nueva": "Restablecida2026"})
    with SessionLocal() as db:
        hash_ = db.execute(text("SELECT password_hash FROM usuarios WHERE usuario='selma'")).scalar_one()
    assert hash_.startswith("$2b$")
    assert entrar(cliente, "selma", "Restablecida2026")
