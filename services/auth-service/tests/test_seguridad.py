def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


# HU-001: ingreso al sistema
def test_login_exitoso(client):
    resp = client.post("/auth/login", json={"username": "admin", "password": "Admin123!"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_credenciales_invalidas(client):
    resp = client.post("/auth/login", json={"username": "admin", "password": "incorrecta"})
    assert resp.status_code == 401


# HU-002: bloqueo de cuenta por intentos fallidos (MAX_FAILED_ATTEMPTS=3 por defecto)
def test_bloqueo_por_intentos_fallidos(client):
    for _ in range(2):
        resp = client.post("/auth/login", json={"username": "admin", "password": "mala"})
        assert resp.status_code == 401

    # tercer intento fallido -> se bloquea
    resp = client.post("/auth/login", json={"username": "admin", "password": "mala"})
    assert resp.status_code == 403

    # incluso con la contraseña correcta, sigue bloqueada
    resp = client.post("/auth/login", json={"username": "admin", "password": "Admin123!"})
    assert resp.status_code == 403


# HU-003: sesión única por usuario
def test_sesion_unica_invalida_token_anterior(client, admin_token):
    # el primer login ya se hizo en el fixture admin_token; probamos que funciona
    resp = client.get("/auth/me", headers=auth_header(admin_token))
    assert resp.status_code == 200

    # un segundo login debe invalidar el primer token
    resp2 = client.post("/auth/login", json={"username": "admin", "password": "Admin123!"})
    nuevo_token = resp2.json()["access_token"]

    resp_viejo = client.get("/auth/me", headers=auth_header(admin_token))
    assert resp_viejo.status_code == 401

    resp_nuevo = client.get("/auth/me", headers=auth_header(nuevo_token))
    assert resp_nuevo.status_code == 200


# HU-005: cambio de contraseña por el propio usuario
def test_cambio_password_propio(client, admin_token):
    resp = client.patch(
        "/users/me/password",
        json={"password_actual": "Admin123!", "password_nueva": "NuevaClave123"},
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 200

    # login con la clave vieja ya no funciona
    resp_login_vieja = client.post("/auth/login", json={"username": "admin", "password": "Admin123!"})
    assert resp_login_vieja.status_code == 401

    # login con la clave nueva sí funciona
    resp_login_nueva = client.post("/auth/login", json={"username": "admin", "password": "NuevaClave123"})
    assert resp_login_nueva.status_code == 200


# HU-007: gestión de usuarios (CRUD) - solo admin
def test_crud_usuarios_como_admin(client, admin_token):
    headers = auth_header(admin_token)

    # crear
    resp = client.post(
        "/users",
        json={"username": "juan", "email": "juan@example.com", "password": "ClaveJuan123", "rol": "usuario"},
        headers=headers,
    )
    assert resp.status_code == 201
    user_id = resp.json()["id"]

    # listar
    resp = client.get("/users", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 2

    # obtener uno
    resp = client.get(f"/users/{user_id}", headers=headers)
    assert resp.status_code == 200

    # actualizar
    resp = client.put(f"/users/{user_id}", json={"activo": False}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["activo"] is False

    # eliminar
    resp = client.delete(f"/users/{user_id}", headers=headers)
    assert resp.status_code == 204

    resp = client.get(f"/users/{user_id}", headers=headers)
    assert resp.status_code == 404


def test_usuario_normal_no_puede_gestionar_usuarios(client, admin_token):
    headers = auth_header(admin_token)
    client.post(
        "/users",
        json={"username": "maria", "email": "maria@example.com", "password": "ClaveMaria123", "rol": "usuario"},
        headers=headers,
    )

    resp = client.post("/auth/login", json={"username": "maria", "password": "ClaveMaria123"})
    token_maria = resp.json()["access_token"]

    # maria no es admin: no puede listar usuarios ni borrar
    resp = client.get("/users", headers=auth_header(token_maria))
    assert resp.status_code == 403

    resp = client.delete("/users/1", headers=auth_header(token_maria))
    assert resp.status_code == 403


# HU-006: restablecimiento de contraseña por el administrador
def test_reset_password_admin(client, admin_token):
    headers = auth_header(admin_token)
    resp = client.post(
        "/users",
        json={"username": "pedro", "email": "pedro@example.com", "password": "ClaveVieja123", "rol": "usuario"},
        headers=headers,
    )
    user_id = resp.json()["id"]

    resp = client.post(
        f"/users/{user_id}/reset-password",
        json={"password_nueva": "ClaveNuevaAdmin123"},
        headers=headers,
    )
    assert resp.status_code == 200

    resp = client.post("/auth/login", json={"username": "pedro", "password": "ClaveNuevaAdmin123"})
    assert resp.status_code == 200


# HU-008: consulta de auditoría
def test_consulta_auditoria(client, admin_token):
    headers = auth_header(admin_token)
    resp = client.get("/audit", headers=headers)
    assert resp.status_code == 200
    acciones = [a["accion"] for a in resp.json()]
    assert "LOGIN_EXITOSO" in acciones
