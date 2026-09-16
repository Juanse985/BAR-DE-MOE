"""HU-027 · RNF-08 — Cifrado de las contraseñas (control C-2)."""
import pytest

from barmoe_common.security import RONDAS, hashear_password, password_es_valida, verificar_password


def test_rnf08_el_hash_es_bcrypt_con_el_costo_acordado():
    hash_ = hashear_password("Cerveza2026")
    assert hash_.startswith(f"$2b${RONDAS:02d}$")
    assert RONDAS >= 12
    assert "Cerveza2026" not in hash_


def test_rnf08_la_misma_password_da_hashes_distintos_por_la_sal():
    assert hashear_password("Cerveza2026") != hashear_password("Cerveza2026")


def test_rnf08_la_verificacion_acepta_la_correcta_y_rechaza_las_demas():
    hash_ = hashear_password("Cerveza2026")
    assert verificar_password("Cerveza2026", hash_)
    assert not verificar_password("cerveza2026", hash_)
    assert not verificar_password("", hash_)


@pytest.mark.parametrize(
    "hash_invalido",
    ["", "texto-plano", "Cerveza2026", "$2b$12$corto", "$2b$12$" + "x" * 40, None],
)
def test_rnf08_un_hash_corrupto_nunca_valida(hash_invalido):
    assert verificar_password("Cerveza2026", hash_invalido) is False


@pytest.mark.parametrize("password", ["Corta1", "sinmayusculas1", "SINMINUSCULAS1", "SinNumerosAqui"])
def test_se_rechazan_passwords_que_no_cumplen_las_reglas(password):
    valida, mensaje = password_es_valida(password)
    assert valida is False
    assert "Mínimo 8 caracteres" in mensaje


def test_una_password_que_cumple_las_reglas_es_valida():
    assert password_es_valida("Cerveza2026") == (True, "")
