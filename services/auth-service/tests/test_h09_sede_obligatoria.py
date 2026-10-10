"""H-09 · Cajero y mesero siempre tienen una sede (docs/05-contratos.md).

Sin sede, el parametrizacion-service les responde 403 SIN_SEDE en todo: el
usuario existe pero no puede trabajar. Por eso la regla se aplica al crear y
al editar. El administrador sí puede no tener sede: ve todas.
"""
import zlib

import pytest

from .utilidades import PASSWORD, crear_usuario


def _nuevo(perfil: str, sede_id: int | None, usuario: str) -> dict:
    return {"cedula": str(zlib.crc32(usuario.encode())).zfill(10), "nombre": f"Usuario {usuario}",
            "sede_id": sede_id, "perfil": perfil, "usuario": usuario, "password": PASSWORD}


@pytest.mark.parametrize("perfil", ["CAJERO", "MESERO"])
def test_h09_no_se_crea_cajero_ni_mesero_sin_sede(cliente, encabezado_admin, perfil):
    respuesta = cliente.post("/usuarios", headers=encabezado_admin,
                             json=_nuevo(perfil, None, f"sinsede{perfil.lower()}"))
    assert respuesta.status_code == 422
    assert respuesta.json()["error"]["codigo"] == "DATOS_INVALIDOS"


@pytest.mark.parametrize("perfil", ["CAJERO", "MESERO"])
def test_h09_cajero_y_mesero_con_sede_si_se_crean(cliente, encabezado_admin, perfil):
    respuesta = cliente.post("/usuarios", headers=encabezado_admin,
                             json=_nuevo(perfil, 3, f"consede{perfil.lower()}"))
    assert respuesta.status_code == 201
    assert respuesta.json()["sede_id"] == 3


def test_h09_administrador_puede_no_tener_sede(cliente, encabezado_admin):
    respuesta = cliente.post("/usuarios", headers=encabezado_admin,
                             json=_nuevo("ADMINISTRADOR", None, "otroadmin"))
    assert respuesta.status_code == 201
    assert respuesta.json()["sede_id"] is None


def test_h09_no_se_le_quita_la_sede_a_un_mesero(cliente, encabezado_admin):
    mesero = crear_usuario(cliente, encabezado_admin, usuario="meseroh09", perfil="MESERO", sede_id=2)
    respuesta = cliente.patch(f"/usuarios/{mesero['id']}", headers=encabezado_admin,
                              json={"sede_id": None})
    assert respuesta.status_code == 422
    assert respuesta.json()["error"]["codigo"] == "SEDE_OBLIGATORIA"


def test_h09_administrador_sin_sede_no_pasa_a_cajero_sin_asignarle_sede(cliente, encabezado_admin):
    admin2 = crear_usuario(cliente, encabezado_admin, usuario="adminh09", perfil="ADMINISTRADOR",
                           sede_id=None)
    respuesta = cliente.patch(f"/usuarios/{admin2['id']}", headers=encabezado_admin,
                              json={"perfil": "CAJERO"})
    assert respuesta.status_code == 422
    assert respuesta.json()["error"]["codigo"] == "SEDE_OBLIGATORIA"

    respuesta = cliente.patch(f"/usuarios/{admin2['id']}", headers=encabezado_admin,
                              json={"perfil": "CAJERO", "sede_id": 1})
    assert respuesta.status_code == 200
    assert respuesta.json()["perfil"] == "CAJERO"
