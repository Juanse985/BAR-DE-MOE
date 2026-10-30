"""Pruebas unitarias de los algoritmos de Diseño de Algoritmos (app/algoritmos.py)."""
import itertools
import random

import pytest

from app.algoritmos import (
    Articulo,
    cambio_voraz,
    existencia_iterativa,
    existencia_recursiva,
    mcd_de_lista,
    mcd_iterativo,
    mcd_recursivo,
    mochila_programacion_dinamica,
    mochila_voraz,
)


# ---------------------------------------------------------------- MCD
@pytest.mark.parametrize("a,b,esperado", [(48, 18, 6), (18, 48, 6), (17, 5, 1), (0, 9, 9), (100, 100, 100)])
def test_mcd_iterativo_y_recursivo_coinciden(a, b, esperado):
    assert mcd_iterativo(a, b) == mcd_recursivo(a, b) == esperado


def test_mcd_de_lista_de_precios():
    assert mcd_de_lista([22_000, 60_000, 15_000, 500_000]) == 1_000


# -------------------------------------------------------------- Mochila
def _fuerza_bruta(articulos, capacidad):
    mejor = 0
    for r in range(len(articulos) + 1):
        for combo in itertools.combinations(articulos, r):
            if sum(a.volumen for a in combo) <= capacidad:
                mejor = max(mejor, sum(a.beneficio for a in combo))
    return mejor


def test_mochila_del_ejercicio_de_clase():
    articulos = [Articulo(1, "A", 2, 3), Articulo(2, "B", 3, 4),
                 Articulo(3, "C", 4, 5), Articulo(4, "D", 5, 6)]
    resultado = mochila_programacion_dinamica(articulos, 5)
    assert resultado.beneficio_total == 7
    assert [a.nombre for a in resultado.seleccionados] == ["A", "B"]


def test_mochila_dp_es_optima_contra_fuerza_bruta():
    azar = random.Random(2026)
    for _ in range(50):
        articulos = [Articulo(i, str(i), azar.randint(1, 20) * 100, azar.randint(0, 50) * 100)
                     for i in range(azar.randint(1, 8))]
        capacidad = azar.randint(1, 60) * 100
        assert mochila_programacion_dinamica(articulos, capacidad).beneficio_total == \
            _fuerza_bruta(articulos, capacidad)


def test_el_voraz_puede_no_ser_optimo_en_la_mochila_0_1():
    # Ejemplo clásico: el voraz por razón toma A (razón 6) y ya no caben B ni C.
    articulos = [Articulo(1, "A", 10, 60), Articulo(2, "B", 20, 100), Articulo(3, "C", 30, 120)]
    assert mochila_voraz(articulos, 50).beneficio_total == 160
    assert mochila_programacion_dinamica(articulos, 50).beneficio_total == 220


def test_la_mochila_nunca_se_pasa_de_la_capacidad():
    articulos = [Articulo(i, str(i), 7_000 + i * 1_000, 5_000) for i in range(10)]
    resultado = mochila_programacion_dinamica(articulos, 30_000)
    assert resultado.volumen_usado <= 30_000


# ------------------------------------------- Existencia recursiva / iterativa
def test_existencia_recursiva_e_iterativa_del_mockup():
    movimientos = [60, -4, -8]           # mockup de HU-021: ingreso +60, venta -4, ajuste -8
    assert existencia_iterativa(movimientos) == existencia_recursiva(movimientos) == 48
    assert existencia_iterativa([]) == existencia_recursiva([]) == 0


# ------------------------------------------------------------- Cambio voraz
def test_cambio_voraz_con_billetes_colombianos():
    assert cambio_voraz(38_750) == {20_000: 1, 10_000: 1, 5_000: 1, 2_000: 1, 1_000: 1, 500: 1, 200: 1, 50: 1}


def test_cambio_voraz_no_cumple_si_sobra_un_resto():
    with pytest.raises(ValueError, match="30 pesos cannot be given"):
        cambio_voraz(1_030)
