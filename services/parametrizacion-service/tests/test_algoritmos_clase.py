"""Algoritmos 7 a 10 de la asignatura: ordenamientos, búsqueda binaria, Hanoi y backtracking.

Pruebas puras (sin base de datos): se pueden correr solas con
`python -m pytest --noconftest tests/test_algoritmos_clase.py`.
"""
import itertools
import random

import pytest

from app.algoritmos import (
    METODOS_ORDENAMIENTO,
    Opcion,
    busqueda_binaria_iterativa,
    busqueda_binaria_recursiva,
    combo_backtracking,
    combo_voraz,
    hanoi_iterativo,
    hanoi_recursivo,
    mcd_con_pasos,
    mcd_iterativo,
    ordenar_con,
    simular_hanoi,
)

METODOS = list(METODOS_ORDENAMIENTO)


# ------------------------------------------------------------------ 7. ordenamientos
@pytest.mark.parametrize("metodo", METODOS)
def test_cada_metodo_ordena_igual_que_sorted_en_200_casos(metodo):
    azar = random.Random(f"barmoe-{metodo}")
    for _ in range(200):
        datos = [azar.randint(-30, 30) for _ in range(azar.randint(0, 40))]
        assert ordenar_con(metodo, datos)[0] == sorted(datos)
        assert ordenar_con(metodo, datos, descendente=True)[0] == sorted(datos, reverse=True)


@pytest.mark.parametrize("metodo", METODOS)
def test_ordena_productos_por_clave_sin_modificar_la_original(metodo):
    productos = [("Águila", 12), ("Club Colombia", 3), ("Poker", 48), ("Costeña", 0)]
    copia = list(productos)
    ordenados, contador = ordenar_con(metodo, productos, clave=lambda p: p[1])
    assert [p[1] for p in ordenados] == [0, 3, 12, 48]
    assert productos == copia
    assert contador.comparaciones > 0


@pytest.mark.parametrize("metodo", ["burbuja", "insercion", "mezcla"])
def test_los_metodos_estables_conservan_el_orden_en_empates(metodo):
    filas = [("a", 2), ("b", 1), ("c", 2), ("d", 1)]
    assert ordenar_con(metodo, filas, clave=lambda f: f[1])[0] == [("b", 1), ("d", 1), ("a", 2), ("c", 2)]


def test_burbuja_e_insercion_cortan_temprano_si_ya_esta_ordenada():
    datos = list(range(100))
    assert ordenar_con("burbuja", datos)[1].comparaciones == 99
    assert ordenar_con("insercion", datos)[1].comparaciones == 99
    assert ordenar_con("burbuja", datos)[1].intercambios == 0


def test_seleccion_hace_a_lo_sumo_n_menos_1_intercambios():
    datos = list(range(50, 0, -1))
    assert ordenar_con("seleccion", datos)[1].intercambios <= 49


def test_en_datos_grandes_los_n_log_n_comparan_mucho_menos_que_burbuja():
    datos = random.Random(7).sample(range(10_000), 500)
    burbuja = ordenar_con("burbuja", datos)[1].comparaciones
    assert ordenar_con("quicksort", datos)[1].comparaciones < burbuja / 5
    assert ordenar_con("mezcla", datos)[1].comparaciones < burbuja / 5


def test_quicksort_no_se_degrada_con_datos_ya_ordenados():
    datos = list(range(2_000))   # el pivote mediana-de-tres evita el O(n²) y la recursión profunda
    ordenados, contador = ordenar_con("quicksort", datos)
    assert ordenados == datos
    assert contador.comparaciones < 2_000 * 15


def test_metodo_desconocido():
    with pytest.raises(ValueError, match="Unknown sorting method"):
        ordenar_con("shell", [3, 1])


# ------------------------------------------------------------- 8. búsqueda binaria
@pytest.mark.parametrize("buscar", [busqueda_binaria_iterativa, busqueda_binaria_recursiva])
def test_busqueda_binaria_encuentra_cada_elemento_y_rechaza_los_que_no_estan(buscar):
    codigos = [f"CER-{n:03d}" for n in range(0, 200, 3)]
    for i, codigo in enumerate(codigos):
        indice, pasos = buscar(codigos, codigo)
        assert indice == i
        assert pasos[-1].decision == "ENCONTRADO"
        assert len(pasos) <= 7                       # log2(67) ≈ 6,1
    for faltante in ("CER-001", "AAA", "ZZZ"):
        assert buscar(codigos, faltante)[0] == -1
    assert buscar([], "CER-000") == (-1, [])


def test_las_dos_busquedas_dan_los_mismos_pasos():
    lista = list(range(0, 1000, 7))
    for objetivo in (0, 7, 500, 994, 3, 2000):
        assert busqueda_binaria_iterativa(lista, objetivo) == busqueda_binaria_recursiva(lista, objetivo)


# ------------------------------------------------------------------ 9. Hanoi
@pytest.mark.parametrize("n", range(0, 11))
def test_hanoi_recursivo_e_iterativo_son_legales_y_dan_2n_menos_1(n):
    recursivo, iterativo = hanoi_recursivo(n), hanoi_iterativo(n)
    assert len(recursivo) == len(iterativo) == 2 ** n - 1
    assert recursivo == iterativo                    # el iterativo reproduce exactamente al recursivo
    final = simular_hanoi(n, recursivo)
    assert final == {"A": [], "B": [], "C": list(range(n, 0, -1))}


def test_hanoi_3_discos_movimientos_de_clase():
    assert hanoi_recursivo(3) == [(1, "A", "C"), (2, "A", "B"), (1, "C", "B"), (3, "A", "C"),
                                  (1, "B", "A"), (2, "B", "C"), (1, "A", "C")]


def test_simular_detecta_un_movimiento_ilegal():
    with pytest.raises(ValueError, match="smaller"):
        simular_hanoi(2, [(1, "A", "B"), (2, "A", "B")])
    with pytest.raises(ValueError, match="not on top"):
        simular_hanoi(2, [(2, "A", "C")])


def test_hanoi_negativo():
    with pytest.raises(ValueError):
        hanoi_recursivo(-1)
    with pytest.raises(ValueError):
        hanoi_iterativo(-1)


# --------------------------------------------------------------- 10. backtracking
CARTA = [Opcion(1, "Picada mixta", 28000, 2), Opcion(2, "Aguardiente media", 30000, 1),
         Opcion(3, "Cerveza nacional", 5000, 6), Opcion(4, "Gaseosa", 3500, 4)]


def _suma(opciones, combinacion):
    precios = {o.clave: o.precio for o in opciones}
    return sum(precios[c] * k for c, k in combinacion.items())


def test_backtracking_encuentra_una_combinacion_exacta():
    # $41.500 = 1 picada (28.000) + 2 cervezas (10.000) + 1 gaseosa (3.500)
    r = combo_backtracking(CARTA, 41500)
    assert r.encontrado and r.total == 41500 == _suma(CARTA, r.combinacion)
    for solucion in r.soluciones:
        assert _suma(CARTA, solucion) == 41500


def test_el_voraz_falla_donde_el_backtracking_acierta():
    opciones = [Opcion(1, "Botella", 6000, 1), Opcion(2, "Copa", 4000, 2)]
    voraz = combo_voraz(opciones, 8000)          # toma la botella (6.000) y ya no cabe nada
    exacto = combo_backtracking(opciones, 8000)  # 2 copas = 8.000
    assert not voraz.encontrado and voraz.total == 6000
    assert exacto.encontrado and exacto.combinacion == {2: 2}


def test_backtracking_coincide_con_fuerza_bruta_en_casos_al_azar():
    azar = random.Random(2026)
    for _ in range(40):
        opciones = [Opcion(i, f"P{i}", azar.choice([1500, 2000, 3500, 5000, 7000, 12000]), azar.randint(1, 2))
                    for i in range(azar.randint(1, 5))]
        monto = azar.choice([5000, 8500, 10000, 14000, 17500, 21000])
        rangos = [range(o.maximo + 1) for o in opciones]
        existe = any(sum(k * o.precio for k, o in zip(ks, opciones, strict=True)) == monto
                     and sum(ks) <= 6 for ks in itertools.product(*rangos))
        r = combo_backtracking(opciones, monto)
        assert r.encontrado == existe
        if existe:
            assert _suma(opciones, r.combinacion) == monto


def test_backtracking_poda_y_respeta_el_limite_de_unidades():
    r = combo_backtracking(CARTA, 30000, max_unidades_total=6)
    assert r.podas > 0
    assert all(sum(s.values()) <= 6 for s in r.soluciones)
    assert sum(r.combinacion.values()) == min(sum(s.values()) for s in r.soluciones)  # prefiere menos


def test_backtracking_sin_solucion():
    r = combo_backtracking(CARTA, 1000)
    assert not r.encontrado and r.combinacion == {} and r.total == 0


# ---------------------------------------------------------------- MCD con pasos
def test_mcd_con_pasos_de_euclides():
    pasos = mcd_con_pasos(252, 105)
    assert pasos == [(252, 105, 42), (105, 42, 21), (42, 21, 0)]
    assert pasos[-1][1] == mcd_iterativo(252, 105) == 21
