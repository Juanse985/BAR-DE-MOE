"""Pruebas unitarias de los algoritmos de Diseño de Algoritmos (app/algoritmos.py)."""
import itertools
import random

import pytest

from app.algoritmos import (
    BARRA,
    Articulo,
    cambio_voraz,
    costo_de_ruta,
    existencia_iterativa,
    existencia_recursiva,
    grafo_de_mesas,
    mcd_de_lista,
    mcd_iterativo,
    mcd_recursivo,
    menor_lexicografico,
    mochila_programacion_dinamica,
    mochila_voraz,
    posicion_en_mapa,
    recorrido_voraz,
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


def test_mochila_del_excel_problema_de_la_mochila():
    """Hoja "Problema_de_la_Mochila.xlsx": capacidad 7, la tabla termina en 11 con A y B."""
    articulos = [Articulo(1, "A", 5, 6), Articulo(2, "B", 2, 5),
                 Articulo(3, "C", 7, 8), Articulo(4, "D", 6, 2)]
    resultado = mochila_programacion_dinamica(articulos, 7)
    assert resultado.beneficio_total == 11
    assert [a.nombre for a in resultado.seleccionados] == ["A", "B"]
    # Última fila de la tabla del Excel, capacidades 1 a 7.
    fila = [mochila_programacion_dinamica(articulos, w).beneficio_total for w in range(1, 8)]
    assert fila == [0, 5, 5, 5, 6, 6, 11]


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


# ------------------------------------------- 6. Recorrido voraz (conjuntos C y S)
GRAFO_DEL_QUIZ = {"A": {"C": 4, "B": 5}, "C": {"D": 2, "E": 3}, "D": {"F": 2}}


def test_recorrido_voraz_punto_1_del_quiz():
    r = recorrido_voraz(GRAFO_DEL_QUIZ, "A", "F")
    assert r.candidatos == ["A", "B", "C", "D", "E", "F"]   # conjunto C
    assert r.solucion == ["A", "C", "D", "F"]               # conjunto S
    assert r.costo_total == 8
    assert [p.elegido for p in r.pasos] == ["C", "D", "F"]
    assert r.completo


def test_recorrido_voraz_punto_2_del_quiz_s_no_cambia():
    grafo = {**GRAFO_DEL_QUIZ, "A": {"C": 3, "B": 6}}
    r = recorrido_voraz(grafo, "A", "F")
    assert r.solucion == ["A", "C", "D", "F"]
    assert r.costo_total == 7


def test_recorrido_voraz_sin_salida_no_es_completo():
    r = recorrido_voraz({"A": {"B": 1}}, "A", "Z")
    assert r.solucion == ["A", "B"] and not r.completo


def test_posiciones_del_mapa_3xn():
    assert [posicion_en_mapa(i) for i in range(5)] == [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1)]


def test_ruta_del_mesero_va_siempre_a_la_mesa_mas_cercana():
    # Mesas 1, 3, 8 y 9 con pedido abierto en el mapa 3×N; la barra está arriba al centro.
    posiciones = {n: posicion_en_mapa(n - 1) for n in (9, 1, 8, 3)}
    grafo = grafo_de_mesas(posiciones)
    r = recorrido_voraz(grafo, BARRA)
    assert r.solucion == [BARRA, 1, 3, 9, 8]    # empate 1 vs 3 (2 casillas): gana el menor
    assert r.costo_total == 2 + 2 + 2 + 1
    assert set(r.solucion) == {BARRA, *posiciones}
    assert r.costo_total <= costo_de_ruta(grafo, [BARRA, 1, 3, 8, 9])


# ------------------------------------- 7. Cadena lexicográficamente menor
def _mejor_por_fuerza_bruta(texto: str) -> str:
    resultados = {""}
    for caracter in texto:
        resultados = {r for parcial in resultados for r in (caracter + parcial, parcial + caracter)}
    return min(resultados)


def test_cadena_del_quiz_juanjuan():
    resultado, pasos = menor_lexicografico("JUANJUAN")
    assert "".join(resultado) == "AAJUNJUN"
    assert ["".join(p.resultado) for p in pasos] == [
        "J", "JU", "AJU", "AJUN", "AJUNJ", "AJUNJU", "AAJUNJU", "AAJUNJUN"]
    assert [p.posicion for p in pasos][:3] == ["INICIO", "FIN", "INICIO"]


def test_cadena_voraz_es_optima_contra_fuerza_bruta():
    azar = random.Random(30)
    for _ in range(200):
        texto = "".join(azar.choice("ABCD") for _ in range(azar.randint(1, 9)))
        assert "".join(menor_lexicografico(texto)[0]) == _mejor_por_fuerza_bruta(texto)


def test_cadena_con_clave_ordena_comandas_por_distancia():
    # (pedido, distancia a la barra, mesa): llegan en este orden.
    comandas = [(1, 3, 7), (2, 1, 2), (3, 4, 9), (4, 1, 1)]
    cola, _ = menor_lexicografico(comandas, clave=lambda c: (c[1], c[2]))
    assert [c[0] for c in cola] == [4, 2, 1, 3]
