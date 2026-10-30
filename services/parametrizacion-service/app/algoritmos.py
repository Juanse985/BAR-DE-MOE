"""Algoritmos de la asignatura Diseño de Algoritmos aplicados al Bar de Moe.

Responsable: Juan David Tovío Montes (Analista RQ) · Sprint 2.

Cada función es pura (no toca la base de datos) para poder probarla sola y
explicarla en la sustentación. Dónde se usa cada una:

1. Mochila 0/1 (programación dinámica) ........ GET /inventario/sugerencia-compra (HU-021)
2. MCD de Euclides (iterativo y recursivo) ..... reduce la tabla de la mochila (HU-021)
3. Mochila por razón beneficio/costo (voraz) ... respaldo si la tabla no cabe en 2 s (RNF-02)
4. Existencia acumulada (iterativa y recursiva)  GET /inventario/conciliacion (HU-021, CU-32)
5. Cambio con billetes y monedas (voraz) ....... GET /pedidos/{id}/cambio (prepara HU-023)
"""
from dataclasses import dataclass
from functools import reduce


# ---------------------------------------------------------------------------
# 2. Máximo común divisor (algoritmo de Euclides) · quiz "recursivos e iterativos"
# ---------------------------------------------------------------------------
def mcd_iterativo(a: int, b: int) -> int:
    """MCD de Euclides, versión iterativa: O(log min(a, b))."""
    a, b = abs(a), abs(b)
    while b != 0:
        a, b = b, a % b
    return a


def mcd_recursivo(a: int, b: int) -> int:
    """MCD de Euclides, versión recursiva. Caso base: mcd(a, 0) = a."""
    a, b = abs(a), abs(b)
    if b == 0:
        return a
    return mcd_recursivo(b, a % b)


def mcd_de_lista(valores: list[int]) -> int:
    """MCD de varios números: mcd(a, b, c) = mcd(mcd(a, b), c)."""
    return reduce(mcd_iterativo, valores, 0)


# ---------------------------------------------------------------------------
# 1 y 3. Problema de la mochila · "PROBLEMA DE LA MOCHILA" (programación dinámica)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Articulo:
    """Un lote de reposición: comprar `unidades` de un producto."""

    clave: int          # producto_id
    nombre: str
    volumen: int        # costo del lote en pesos (lo que "ocupa" del presupuesto)
    beneficio: int      # ganancia esperada del lote en pesos


@dataclass(frozen=True)
class ResultadoMochila:
    seleccionados: list[Articulo]
    beneficio_total: int
    volumen_usado: int
    capacidad: int
    metodo: str          # "PROGRAMACION_DINAMICA" o "VORAZ"
    escala: int          # MCD usado para reducir la tabla


# Límite de celdas de la tabla dp para no pasar de los 2 s del RNF-02 (HU-026).
MAX_CELDAS_DP = 2_000_000


def mochila_programacion_dinamica(articulos: list[Articulo], capacidad: int) -> ResultadoMochila:
    """Mochila 0/1 con tabla dp[i][w], igual que en clase, pero escalada con el MCD.

    Los precios en pesos son múltiplos de 100 o de 1.000, así que dividir
    volúmenes y capacidad por su MCD da exactamente la misma respuesta con una
    tabla hasta 1.000 veces más pequeña.

    dp[i][w] = mejor beneficio usando los primeros i artículos con capacidad w
             = max(dp[i-1][w],                       # opción A: no incluir
                   dp[i-1][w - v_i] + b_i)           # opción B: incluir si cabe
    """
    if capacidad <= 0 or not articulos:
        return ResultadoMochila([], 0, 0, max(capacidad, 0), "PROGRAMACION_DINAMICA", 1)

    escala = mcd_de_lista([a.volumen for a in articulos] + [capacidad]) or 1
    m = capacidad // escala
    vols = [a.volumen // escala for a in articulos]
    n = len(articulos)

    if (n + 1) * (m + 1) > MAX_CELDAS_DP:
        return mochila_voraz(articulos, capacidad)

    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        vi, bi = vols[i - 1], articulos[i - 1].beneficio
        fila_anterior, fila = dp[i - 1], dp[i]
        for w in range(m + 1):
            fila[w] = fila_anterior[w]
            if vi <= w and fila_anterior[w - vi] + bi > fila[w]:
                fila[w] = fila_anterior[w - vi] + bi

    # Reconstrucción: si dp[i][w] cambió respecto a dp[i-1][w], el artículo i entró.
    seleccionados: list[Articulo] = []
    w = m
    for i in range(n, 0, -1):
        if dp[i][w] != dp[i - 1][w]:
            seleccionados.append(articulos[i - 1])
            w -= vols[i - 1]
    seleccionados.reverse()

    return ResultadoMochila(
        seleccionados=seleccionados,
        beneficio_total=dp[n][m],
        volumen_usado=sum(a.volumen for a in seleccionados),
        capacidad=capacidad,
        metodo="PROGRAMACION_DINAMICA",
        escala=escala,
    )


def mochila_voraz(articulos: list[Articulo], capacidad: int) -> ResultadoMochila:
    """Voraz: toma primero el lote con mejor ganancia por peso invertido.

    Es rápido (O(n log n)) pero no siempre es óptimo para la mochila 0/1; por
    eso solo se usa cuando la tabla de programación dinámica sería muy grande.
    """
    ordenados = sorted(articulos, key=lambda a: a.beneficio / a.volumen if a.volumen else 0,
                       reverse=True)
    resto, seleccionados = capacidad, []
    for articulo in ordenados:
        if 0 < articulo.volumen <= resto:
            seleccionados.append(articulo)
            resto -= articulo.volumen
    return ResultadoMochila(
        seleccionados=seleccionados,
        beneficio_total=sum(a.beneficio for a in seleccionados),
        volumen_usado=capacidad - resto,
        capacidad=capacidad,
        metodo="VORAZ",
        escala=1,
    )


# ---------------------------------------------------------------------------
# 4. Existencia acumulada · quiz "recursivos e iterativos"
# ---------------------------------------------------------------------------
def existencia_iterativa(movimientos: list[int], inicial: int = 0) -> int:
    """Suma los movimientos (+ingresos, -ventas, ±ajustes) uno por uno."""
    existencia = inicial
    for cantidad in movimientos:
        existencia += cantidad
    return existencia


def existencia_recursiva(movimientos: list[int], inicial: int = 0) -> int:
    """existencia(n) = existencia(n-1) + movimiento(n); caso base: sin movimientos.

    Se recorre por índice (no con slicing) para no copiar la lista en cada
    llamada. Python corta la recursión cerca de 1.000 niveles: por eso el
    servicio usa la versión iterativa y esta solo se usa para comprobar que
    las dos dan lo mismo cuando el histórico es corto.
    """
    def _hasta(n: int) -> int:
        if n == 0:
            return inicial
        return _hasta(n - 1) + movimientos[n - 1]

    return _hasta(len(movimientos))


LIMITE_RECURSION = 900


# ---------------------------------------------------------------------------
# 5. Cambio con billetes y monedas · "Algoritmo Voraz - Problema de las Monedas"
# ---------------------------------------------------------------------------
# Billetes y monedas en circulación en Colombia (Banco de la República).
DENOMINACIONES_COP = (100_000, 50_000, 20_000, 10_000, 5_000, 2_000, 1_000, 500, 200, 100, 50)


def cambio_voraz(cambio: int, denominaciones: tuple[int, ...] = DENOMINACIONES_COP) -> dict[int, int]:
    """Devuelve {denominación: cantidad} tomando siempre la mayor que quepa.

    A diferencia del ejercicio de clase (una moneda de cada valor), aquí cada
    denominación se puede repetir. Con la serie colombiana el voraz da el
    mínimo número de piezas. Si sobra un resto que no se puede entregar
    (por ejemplo 30 pesos), se lanza ValueError: "el resultado no cumple".
    """
    if cambio < 0:
        raise ValueError("Change cannot be negative.")
    resultado: dict[int, int] = {}
    resto = cambio
    for valor in sorted(denominaciones, reverse=True):
        if valor <= resto:
            cantidad, resto = divmod(resto, valor)
            resultado[valor] = cantidad
    if resto != 0:
        raise ValueError(
            f"{resto} pesos cannot be given with the available denominations "
            f"(the smallest is {min(denominaciones)})."
        )
    return resultado
