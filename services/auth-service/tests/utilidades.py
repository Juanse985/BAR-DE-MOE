"""Ayudas compartidas por las pruebas de QA del auth-service."""
import zlib

from sqlalchemy import select

from app.main import SessionLocal
from barmoe_common.auditoria import Auditoria

PASSWORD = "Cerveza2026"


def crear_usuario(cliente, encabezado_admin, *, usuario: str, perfil: str, sede_id: int | None = 1,
                  cedula: str | None = None) -> dict:
    respuesta = cliente.post("/usuarios", headers=encabezado_admin, json={
        "cedula": cedula or str(zlib.crc32(usuario.encode())).zfill(10),
        "nombre": f"Usuario {usuario}",
        "sede_id": sede_id,
        "perfil": perfil,
        "usuario": usuario,
        "password": PASSWORD,
    })
    assert respuesta.status_code == 201, respuesta.text
    return respuesta.json()


def entrar(cliente, usuario: str, password: str = PASSWORD, **cabeceras) -> dict:
    respuesta = cliente.post("/auth/login", json={"usuario": usuario, "password": password},
                             headers=cabeceras or None)
    assert respuesta.status_code == 200, respuesta.text
    return {"Authorization": f"Bearer {respuesta.json()['access_token']}"}


def auditorias(**filtros) -> list[Auditoria]:
    with SessionLocal() as db:
        consulta = select(Auditoria).filter_by(**filtros).order_by(Auditoria.id)
        return list(db.scalars(consulta))
