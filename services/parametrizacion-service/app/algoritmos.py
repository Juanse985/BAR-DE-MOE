"""Algoritmos de la asignatura Diseño de Algoritmos aplicados al Bar de Moe.

Responsables: Juan David Tovío Montes (Analista RQ) · algoritmos 1-5 y 8-12;
Juan Sebastián Rodríguez (QA) · algoritmos 6 y 7. Sprints 2 a 4.

Cada función es pura (no toca la base de datos) para poder probarla sola y
explicarla en la sustentación. Dónde se usa cada una:

1. Mochila 0/1 (programación dinámica) ........ GET /inventario/sugerencia-compra (HU-021)
2. MCD de Euclides (iterativo y recursivo) ..... reduce la tabla de la mochila (HU-021)
3. Mochila por razón beneficio/costo (voraz) ... respaldo si la tabla no cabe en 2 s (RNF-02)
4. Existencia acumulada (iterativa y recursiva)  GET /inventario/conciliacion (HU-021, CU-32)
5. Cambio con billetes y monedas (voraz) ....... GET /pedidos/{id}/cambio y POST /facturas (HU-023)
6. Recorrido voraz en un grafo (conjuntos C y S)  GET /mesas/ruta-entrega (HU-013)
7. Cadena lexicográficamente menor (voraz) ..... GET /pedidos/cola-barra (HU-022)
8. Ordenamiento por mezcla (divide y vencerás) . GET /reportes/ventas (HU-024, Sprint 3-4)
9. Ordenamientos burbuja, inserción, selección,
   quicksort y mezcla, con contadores ......... GET /algoritmos/ordenar-inventario
10. Búsqueda binaria (iterativa y recursiva) ... GET /algoritmos/buscar-producto
11. Torres de Hanoi (recursiva e iterativa) .... GET /algoritmos/hanoi
12. Backtracking · suma exacta (combo por monto) GET /algoritmos/combo
    comparado con un voraz que puede fallar.
Además, MCD y cambio con pasos:                 GET /algoritmos/mcd · GET /algoritmos/cambio
"""
from collections import deque
from collections.abc import Callable, Hashable, Sequence
from dataclasses import dataclass, field
from functools import reduce
from typing import Any


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


# ---------------------------------------------------------------------------
# 6. Recorrido voraz en un grafo · quiz "Algoritmos voraces", punto 1
# ---------------------------------------------------------------------------
# Idea de clase: C es el conjunto de candidatos (todos los nodos) y S la
# solución que se va armando. En cada nodo se escoge la arista de menor costo
# hacia un nodo que todavía no está en S, sin devolverse. Nunca se deshace una
# elección: por eso es voraz y no garantiza el recorrido más corto posible.
@dataclass(frozen=True)
class PasoRecorrido:
    desde: Hashable
    opciones: dict[Hashable, int]     # nodo -> costo de las aristas que se podían tomar
    elegido: Hashable
    costo: int


@dataclass(frozen=True)
class ResultadoRecorrido:
    candidatos: list[Hashable]        # conjunto C
    solucion: list[Hashable]          # conjunto S, en el orden en que se eligió
    costo_total: int
    pasos: list[PasoRecorrido] = field(default_factory=list)
    completo: bool = True             # llegó al destino (o visitó todos si no había destino)


def recorrido_voraz(grafo: dict[Hashable, dict[Hashable, int]], origen: Hashable,
                    destino: Hashable | None = None) -> ResultadoRecorrido:
    """Desde `origen`, toma siempre la arista más barata hacia un nodo no visitado.

    - Con `destino`: se detiene al llegar (punto 1 del quiz: de A hasta F).
    - Sin `destino`: sigue hasta visitar todos los nodos alcanzables (ruta del mesero).

    Empates: gana el nodo "menor" (str), para que el resultado siempre sea el mismo.
    Complejidad: O(n²) con n nodos (en cada paso se revisan las aristas del nodo actual).
    """
    candidatos = sorted({origen, *grafo, *(v for aristas in grafo.values() for v in aristas)}, key=str)
    solucion, visitados = [origen], {origen}
    pasos: list[PasoRecorrido] = []
    actual, costo_total = origen, 0
    while actual != destino:
        opciones = {v: c for v, c in grafo.get(actual, {}).items() if v not in visitados}
        if not opciones:
            break
        elegido = min(opciones, key=lambda v: (opciones[v], str(v)))
        pasos.append(PasoRecorrido(actual, opciones, elegido, opciones[elegido]))
        costo_total += opciones[elegido]
        solucion.append(elegido)
        visitados.add(elegido)
        actual = elegido
    completo = actual == destino if destino is not None else True
    return ResultadoRecorrido(candidatos, solucion, costo_total, pasos, completo)


BARRA = "BARRA"
COLUMNAS_MAPA = 3   # el mapa de mesas del frontend es una rejilla 3×N (HU-013)


def posicion_en_mapa(indice: int) -> tuple[int, int]:
    """(fila, columna) de la mesa número `indice` (desde 0) en la rejilla 3×N."""
    return divmod(indice, COLUMNAS_MAPA)


# La barra está arriba del mapa, centrada sobre la columna del medio.
POSICION_BARRA = (-1, 1)


def distancia(a: tuple[int, int], b: tuple[int, int]) -> int:
    """Pasos entre dos casillas moviéndose por los pasillos (distancia Manhattan)."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def grafo_de_mesas(posiciones: dict[Hashable, tuple[int, int]]) -> dict[Hashable, dict[Hashable, int]]:
    """Grafo completo: la barra y cada mesa, con la distancia como costo de la arista."""
    nodos = {BARRA: POSICION_BARRA, **posiciones}
    return {a: {b: distancia(pa, pb) for b, pb in nodos.items() if b != a} for a, pa in nodos.items()}


def costo_de_ruta(grafo: dict[Hashable, dict[Hashable, int]], ruta: list[Hashable]) -> int:
    return sum(grafo[a][b] for a, b in zip(ruta, ruta[1:], strict=False))


# ---------------------------------------------------------------------------
# 7. Cadena lexicográficamente menor · quiz "Algoritmos voraces", punto 2
# ---------------------------------------------------------------------------
# Idea de clase: se leen los caracteres uno por uno y cada uno solo puede ir al
# inicio o al final del resultado. Regla voraz: si el nuevo es menor o igual que
# el primero del resultado, va al inicio; si es mayor, va al final.
@dataclass(frozen=True)
class PasoCadena:
    elemento: Any
    posicion: str          # "INICIO" o "FIN"
    resultado: list[Any]   # cómo quedó el resultado después de este paso


def menor_lexicografico(elementos: Sequence[Any], clave: Callable[[Any], Any] = lambda x: x
                        ) -> tuple[list[Any], list[PasoCadena]]:
    """Arma con una deque la secuencia lexicográficamente menor. O(n): cada paso es O(1).

    >>> "".join(menor_lexicografico("JUANJUAN")[0])
    'AAJUNJUN'
    """
    resultado: deque[Any] = deque()
    pasos: list[PasoCadena] = []
    for elemento in elementos:
        if not resultado or clave(elemento) <= clave(resultado[0]):
            resultado.appendleft(elemento)
            posicion = "INICIO"
        else:
            resultado.append(elemento)
            posicion = "FIN"
        pasos.append(PasoCadena(elemento, posicion, list(resultado)))
    return list(resultado), pasos
# 8. Ordenamiento por mezcla (merge sort) · divide y vencerás
# ---------------------------------------------------------------------------
def ordenar_mezcla(elementos: list, clave: Callable[[Any], Any] = lambda x: x,
                   descendente: bool = False) -> list:
    """Merge sort estable: O(n log n) en el peor caso, sin modificar la lista original.

    Divide: parte la lista en dos mitades.  Vence: ordena cada mitad (recursión).
    Combina: mezcla las dos mitades ya ordenadas tomando siempre el menor.
    Es estable (a igual clave conserva el orden de llegada), por eso el reporte
    puede ordenar primero por fecha y luego por ganancia sin desordenar fechas.
    """
    if len(elementos) <= 1:
        return list(elementos)
    mitad = len(elementos) // 2
    izquierda = ordenar_mezcla(elementos[:mitad], clave, descendente)
    derecha = ordenar_mezcla(elementos[mitad:], clave, descendente)
    return _mezclar(izquierda, derecha, clave, descendente)


def _mezclar(izquierda: list, derecha: list, clave: Callable[[Any], Any], descendente: bool) -> list:
    resultado = []
    i = j = 0
    while i < len(izquierda) and j < len(derecha):
        a, b = clave(izquierda[i]), clave(derecha[j])
        # "<=" (o ">=") deja primero el de la izquierda en un empate: eso lo hace estable.
        tomar_izquierda = a >= b if descendente else a <= b
        if tomar_izquierda:
            resultado.append(izquierda[i])
            i += 1
        else:
            resultado.append(derecha[j])
            j += 1
    resultado.extend(izquierda[i:])
    resultado.extend(derecha[j:])
    return resultado


# ---------------------------------------------------------------------------
# 9. Métodos de ordenamiento con contadores (comparaciones e intercambios)
# ---------------------------------------------------------------------------
@dataclass
class Contador:
    """Lo que se compara en clase entre métodos: cuántas comparaciones y movimientos."""

    comparaciones: int = 0
    intercambios: int = 0


class _Comparador:
    def __init__(self, clave: Callable[[Any], Any], descendente: bool, contador: Contador):
        self.clave, self.descendente, self.contador = clave, descendente, contador

    def antes(self, a, b) -> bool:
        """True si `a` debe ir estrictamente antes que `b`."""
        self.contador.comparaciones += 1
        ka, kb = self.clave(a), self.clave(b)
        return ka > kb if self.descendente else ka < kb


def burbuja(elementos: list, cmp: _Comparador) -> list:
    """O(n²). Cada pasada lleva el mayor al final; si una pasada no intercambia, ya está."""
    datos = list(elementos)
    n = len(datos)
    for i in range(n - 1):
        hubo_cambio = False
        for j in range(n - 1 - i):
            if cmp.antes(datos[j + 1], datos[j]):
                datos[j], datos[j + 1] = datos[j + 1], datos[j]
                cmp.contador.intercambios += 1
                hubo_cambio = True
        if not hubo_cambio:
            break
    return datos


def insercion(elementos: list, cmp: _Comparador) -> list:
    """O(n²), O(n) si ya viene casi ordenada. Inserta cada elemento en la parte ya ordenada."""
    datos = list(elementos)
    for i in range(1, len(datos)):
        actual = datos[i]
        j = i - 1
        while j >= 0 and cmp.antes(actual, datos[j]):
            datos[j + 1] = datos[j]
            cmp.contador.intercambios += 1
            j -= 1
        datos[j + 1] = actual
    return datos


def seleccion(elementos: list, cmp: _Comparador) -> list:
    """O(n²) comparaciones pero a lo sumo n-1 intercambios: busca el menor y lo pone en su lugar."""
    datos = list(elementos)
    n = len(datos)
    for i in range(n - 1):
        minimo = i
        for j in range(i + 1, n):
            if cmp.antes(datos[j], datos[minimo]):
                minimo = j
        if minimo != i:
            datos[i], datos[minimo] = datos[minimo], datos[i]
            cmp.contador.intercambios += 1
    return datos


def quicksort(elementos: list, cmp: _Comparador) -> list:
    """Divide y vencerás, O(n log n) en promedio. Pivote: mediana de tres (evita el peor caso
    con datos ya ordenados). Partición de Lomuto, recursivo sobre la parte más pequeña."""
    datos = list(elementos)

    def mediana_de_tres(bajo: int, alto: int) -> int:
        medio = (bajo + alto) // 2
        trio = sorted((bajo, medio, alto), key=lambda k: cmp.clave(datos[k]))
        return trio[1]

    def particion(bajo: int, alto: int) -> int:
        p = mediana_de_tres(bajo, alto)
        datos[p], datos[alto] = datos[alto], datos[p]
        pivote = datos[alto]
        i = bajo
        for j in range(bajo, alto):
            if cmp.antes(datos[j], pivote):
                if i != j:
                    datos[i], datos[j] = datos[j], datos[i]
                    cmp.contador.intercambios += 1
                i += 1
        if i != alto:
            datos[i], datos[alto] = datos[alto], datos[i]
            cmp.contador.intercambios += 1
        return i

    def ordenar(bajo: int, alto: int) -> None:
        while bajo < alto:
            p = particion(bajo, alto)
            if p - bajo < alto - p:           # recursión sobre la mitad menor: pila O(log n)
                ordenar(bajo, p - 1)
                bajo = p + 1
            else:
                ordenar(p + 1, alto)
                alto = p - 1

    ordenar(0, len(datos) - 1)
    return datos


def mezcla_contada(elementos: list, cmp: _Comparador) -> list:
    """Merge sort con contador (la versión 6, `ordenar_mezcla`, es la que usa el reporte)."""
    if len(elementos) <= 1:
        return list(elementos)
    mitad = len(elementos) // 2
    izquierda, derecha = mezcla_contada(elementos[:mitad], cmp), mezcla_contada(elementos[mitad:], cmp)
    resultado, i, j = [], 0, 0
    while i < len(izquierda) and j < len(derecha):
        if cmp.antes(derecha[j], izquierda[i]):   # estricto: en empate gana la izquierda (estable)
            resultado.append(derecha[j])
            j += 1
        else:
            resultado.append(izquierda[i])
            i += 1
        cmp.contador.intercambios += 1
    resultado.extend(izquierda[i:])
    resultado.extend(derecha[j:])
    return resultado


METODOS_ORDENAMIENTO: dict[str, tuple[Callable[[list, _Comparador], list], str]] = {
    "burbuja": (burbuja, "O(n²)"),
    "insercion": (insercion, "O(n²) · O(n) casi ordenada"),
    "seleccion": (seleccion, "O(n²)"),
    "quicksort": (quicksort, "O(n log n) promedio"),
    "mezcla": (mezcla_contada, "O(n log n)"),
}


def ordenar_con(metodo: str, elementos: list, clave: Callable[[Any], Any] = lambda x: x,
                descendente: bool = False) -> tuple[list, Contador]:
    """Ordena con el método pedido y devuelve la lista y sus contadores."""
    if metodo not in METODOS_ORDENAMIENTO:
        raise ValueError(f"Unknown sorting method '{metodo}': use {', '.join(METODOS_ORDENAMIENTO)}.")
    contador = Contador()
    funcion, _ = METODOS_ORDENAMIENTO[metodo]
    return funcion(elementos, _Comparador(clave, descendente, contador)), contador


# ---------------------------------------------------------------------------
# 10. Búsqueda binaria · iterativa y recursiva
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class PasoBusqueda:
    bajo: int
    alto: int
    medio: int
    valor_medio: Any
    decision: str        # "ENCONTRADO", "IZQUIERDA" o "DERECHA"


def busqueda_binaria_iterativa(ordenada: list, objetivo, clave: Callable[[Any], Any] = lambda x: x
                               ) -> tuple[int, list[PasoBusqueda]]:
    """O(log n) sobre una lista ORDENADA. Devuelve (índice o -1, pasos)."""
    bajo, alto, pasos = 0, len(ordenada) - 1, []
    while bajo <= alto:
        medio = (bajo + alto) // 2
        valor = clave(ordenada[medio])
        if valor == objetivo:
            pasos.append(PasoBusqueda(bajo, alto, medio, valor, "ENCONTRADO"))
            return medio, pasos
        if objetivo < valor:
            pasos.append(PasoBusqueda(bajo, alto, medio, valor, "IZQUIERDA"))
            alto = medio - 1
        else:
            pasos.append(PasoBusqueda(bajo, alto, medio, valor, "DERECHA"))
            bajo = medio + 1
    return -1, pasos


def busqueda_binaria_recursiva(ordenada: list, objetivo, clave: Callable[[Any], Any] = lambda x: x
                               ) -> tuple[int, list[PasoBusqueda]]:
    """Misma búsqueda, recursiva. Caso base: el rango quedó vacío (bajo > alto)."""
    pasos: list[PasoBusqueda] = []

    def buscar(bajo: int, alto: int) -> int:
        if bajo > alto:
            return -1
        medio = (bajo + alto) // 2
        valor = clave(ordenada[medio])
        if valor == objetivo:
            pasos.append(PasoBusqueda(bajo, alto, medio, valor, "ENCONTRADO"))
            return medio
        if objetivo < valor:
            pasos.append(PasoBusqueda(bajo, alto, medio, valor, "IZQUIERDA"))
            return buscar(bajo, medio - 1)
        pasos.append(PasoBusqueda(bajo, alto, medio, valor, "DERECHA"))
        return buscar(medio + 1, alto)

    return buscar(0, len(ordenada) - 1), pasos


# ---------------------------------------------------------------------------
# 11. Torres de Hanoi · recursiva e iterativa
# ---------------------------------------------------------------------------
# En el bar: canastas de cerveza de distinto tamaño apiladas en la estiba A de la
# bodega; hay que pasarlas a la estiba C usando la B, moviendo una a la vez y sin
# poner nunca una canasta grande sobre una pequeña (se aplasta).
MAX_DISCOS_HANOI = 12   # 4.095 movimientos: cabe de sobra en los 2 s del RNF-02


def hanoi_recursivo(n: int, origen: str = "A", auxiliar: str = "B", destino: str = "C"
                    ) -> list[tuple[int, str, str]]:
    """hanoi(n) = hanoi(n-1, origen→auxiliar) + mover disco n + hanoi(n-1, auxiliar→destino).

    Caso base: n = 0, no hay nada que mover. Total: 2ⁿ − 1 movimientos.
    Cada movimiento es (disco, desde, hacia); el disco 1 es el más pequeño.
    """
    if n < 0:
        raise ValueError("The number of disks cannot be negative.")
    movimientos: list[tuple[int, str, str]] = []

    def mover(k: int, desde: str, via: str, hacia: str) -> None:
        if k == 0:
            return
        mover(k - 1, desde, hacia, via)
        movimientos.append((k, desde, hacia))
        mover(k - 1, via, desde, hacia)

    mover(n, origen, auxiliar, destino)
    return movimientos


def hanoi_iterativo(n: int, origen: str = "A", auxiliar: str = "B", destino: str = "C"
                    ) -> list[tuple[int, str, str]]:
    """Versión iterativa con tres pilas explícitas (sin recursión).

    Regla clásica: en los movimientos impares se mueve el disco 1 siempre en el
    mismo sentido circular (A→B→C→A si n es par; A→C→B→A si n es impar); en los
    pares se hace el único movimiento legal que no toca el disco 1.
    """
    if n < 0:
        raise ValueError("The number of disks cannot be negative.")
    pilas = {origen: list(range(n, 0, -1)), auxiliar: [], destino: []}
    ciclo = [origen, auxiliar, destino] if n % 2 == 0 else [origen, destino, auxiliar]
    posicion_pequeno = 0
    movimientos: list[tuple[int, str, str]] = []
    for numero in range(1, 2 ** n):
        if numero % 2 == 1:
            desde = ciclo[posicion_pequeno]
            posicion_pequeno = (posicion_pequeno + 1) % 3
            hacia = ciclo[posicion_pequeno]
        else:
            a, b = (p for p in pilas if p != ciclo[posicion_pequeno])
            if pilas[a] and (not pilas[b] or pilas[a][-1] < pilas[b][-1]):
                desde, hacia = a, b
            else:
                desde, hacia = b, a
        disco = pilas[desde].pop()
        pilas[hacia].append(disco)
        movimientos.append((disco, desde, hacia))
    return movimientos


def simular_hanoi(n: int, movimientos: list[tuple[int, str, str]]) -> dict[str, list[int]]:
    """Ejecuta los movimientos y falla si alguno es ilegal. Devuelve cómo quedan las estibas."""
    pilas = {"A": list(range(n, 0, -1)), "B": [], "C": []}
    for numero, (disco, desde, hacia) in enumerate(movimientos, start=1):
        if not pilas[desde] or pilas[desde][-1] != disco:
            raise ValueError(f"Move {numero}: disk {disco} is not on top of {desde}.")
        if pilas[hacia] and pilas[hacia][-1] < disco:
            raise ValueError(f"Move {numero}: disk {disco} cannot go on top of a smaller disk.")
        pilas[hacia].append(pilas[desde].pop())
    return pilas


# ---------------------------------------------------------------------------
# 12. Backtracking · suma exacta (combo por monto) y su voraz
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Opcion:
    clave: int
    nombre: str
    precio: int
    maximo: int          # unidades disponibles para el combo


@dataclass
class ResultadoCombo:
    encontrado: bool
    combinacion: dict[int, int]      # clave -> unidades
    total: int
    nodos_explorados: int
    podas: int
    soluciones: list[dict[int, int]]
    limite_alcanzado: bool = False


MAX_NODOS_BACKTRACKING = 200_000     # tope para no pasar de 2 s (RNF-02)


def combo_backtracking(opciones: list[Opcion], monto: int, max_unidades_total: int = 6,
                       max_soluciones: int = 5) -> ResultadoCombo:
    """¿Qué productos suman EXACTAMENTE `monto`? (suma de subconjuntos con repetición acotada).

    Árbol de decisión: para el producto i se prueba llevar k = máximo … 0 unidades.
    Se poda (se devuelve sin seguir) cuando:
      1. lo acumulado ya pasa del monto;
      2. ni llevando todo lo que queda se alcanza el monto;
      3. ya se usaron las unidades permitidas en el combo.
    Las opciones se recorren de la más cara a la más barata para podar antes.
    Prefiere combos con menos unidades: la primera solución hallada se mejora si
    aparece otra con menos productos.
    """
    orden = sorted((o for o in opciones if o.precio > 0 and o.maximo > 0), key=lambda o: -o.precio)
    # resto_max[i] = lo máximo que se puede sumar con las opciones i..n-1
    resto_max = [0] * (len(orden) + 1)
    for i in range(len(orden) - 1, -1, -1):
        resto_max[i] = resto_max[i + 1] + orden[i].precio * orden[i].maximo

    estado = {"nodos": 0, "podas": 0, "corte": False}
    soluciones: list[dict[int, int]] = []
    elegido: dict[int, int] = {}

    def explorar(i: int, suma: int, unidades: int) -> None:
        if estado["corte"]:
            return
        estado["nodos"] += 1
        if estado["nodos"] > MAX_NODOS_BACKTRACKING:
            estado["corte"] = True
            return
        if suma == monto:
            soluciones.append(dict(elegido))
            if len(soluciones) >= max_soluciones:
                estado["corte"] = True
            return
        if i == len(orden) or suma > monto or suma + resto_max[i] < monto or unidades >= max_unidades_total:
            estado["podas"] += 1
            return
        opcion = orden[i]
        tope = min(opcion.maximo, (monto - suma) // opcion.precio, max_unidades_total - unidades)
        for k in range(tope, -1, -1):
            if k:
                elegido[opcion.clave] = k
            else:
                elegido.pop(opcion.clave, None)
            explorar(i + 1, suma + k * opcion.precio, unidades + k)
        elegido.pop(opcion.clave, None)

    if monto > 0:
        explorar(0, 0, 0)
    mejor = min(soluciones, key=lambda s: sum(s.values())) if soluciones else {}
    precios = {o.clave: o.precio for o in orden}
    return ResultadoCombo(
        encontrado=bool(soluciones), combinacion=mejor,
        total=sum(precios[c] * k for c, k in mejor.items()),
        nodos_explorados=estado["nodos"], podas=estado["podas"], soluciones=soluciones,
        limite_alcanzado=estado["nodos"] > MAX_NODOS_BACKTRACKING,
    )


def combo_voraz(opciones: list[Opcion], monto: int, max_unidades_total: int = 6) -> ResultadoCombo:
    """Voraz: toma siempre el producto más caro que todavía quepa. Rápido, pero puede
    quedarse corto aunque exista una combinación exacta (ahí se ve por qué hace falta
    el backtracking)."""
    resto, unidades, combinacion = monto, 0, {}
    for o in sorted(opciones, key=lambda o: -o.precio):
        if o.precio <= 0:
            continue
        k = min(o.maximo, resto // o.precio, max_unidades_total - unidades)
        if k > 0:
            combinacion[o.clave] = k
            resto -= k * o.precio
            unidades += k
    exacto = resto == 0 and monto > 0
    return ResultadoCombo(encontrado=exacto, combinacion=combinacion, total=monto - resto,
                          nodos_explorados=len(opciones), podas=0,
                          soluciones=[combinacion] if exacto else [])


# ---------------------------------------------------------------------------
# MCD y cambio con pasos (para mostrar el recorrido en la API)
# ---------------------------------------------------------------------------
def mcd_con_pasos(a: int, b: int) -> list[tuple[int, int, int]]:
    """Cada paso de Euclides como (a, b, a mod b), hasta que b = 0."""
    a, b = abs(a), abs(b)
    pasos = []
    while b != 0:
        pasos.append((a, b, a % b))
        a, b = b, a % b
    return pasos
