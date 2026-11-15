# Algoritmos de la asignatura en el Bar de Moe

**Responsable:** Juan David Tovío Montes · **Rama:** `dev/david` · **Código:** `services/parametrizacion-service/app/algoritmos.py`
Todos son funciones puras (no tocan la base de datos) y además están expuestos en la API con los
datos reales del bar. Prefijo en el gateway: `/api/parametrizacion`. Se prueban con Postman (o con
`curl`) mandando el token de cualquier perfil en `Authorization: Bearer …`. Son solo de consulta: no
cambian nada en la base de datos.

`GET /algoritmos` devuelve este mismo catálogo.

| # | Algoritmo | Técnica | Dónde se usa (endpoint) | Para qué sirve en el bar |
|---|---|---|---|---|
| 1 | Mochila 0/1 con tabla `dp[i][w]` | Programación dinámica | `GET /inventario/sugerencia-compra?sede_id=&presupuesto=` | Qué productos reponer con un presupuesto para ganar lo máximo |
| 2 | MCD de Euclides | Iterativo y recursivo | `GET /algoritmos/mcd?a=&b=` (y dentro de la mochila) | Reduce la tabla de la mochila hasta 1.000 veces |
| 3 | Mochila por razón beneficio/costo | Voraz | `GET /inventario/sugerencia-compra` | Respaldo rápido si la tabla no cabe en 2 s |
| 4 | Existencia acumulada | Iterativo y recursivo | `GET /inventario/conciliacion?sede_id=&producto_id=` | Comprueba que el saldo se explica con los movimientos |
| 5 | Cambio en billetes y monedas | Voraz | `GET /algoritmos/cambio?monto=` · `POST /facturas` | Vueltas al cobrar en efectivo |
| 6 | Recorrido en un grafo (conjuntos C y S) | Voraz | `GET /mesas/ruta-entrega` | Ruta del mesero por las mesas con pedido (ver `11-algoritmos.md`) |
| 7 | Cadena lexicográficamente menor | Voraz | `GET /pedidos/cola-barra` | Orden de las comandas en la barra (ver `11-algoritmos.md`) |
| 8 | Merge sort estable | Divide y vencerás | `GET /reportes/ventas?orden=ganancia` | Orden del reporte de ventas |
| 9 | Burbuja, inserción, selección, quicksort y mezcla | Ordenamiento | `GET /algoritmos/ordenar-inventario` | Ordena el inventario y compara los cinco métodos |
| 10 | Búsqueda binaria | Iterativo y recursivo | `GET /algoritmos/buscar-producto?codigo=&modo=` | Encuentra un producto por código en ⌊log₂ n⌋+1 pasos |
| 11 | Torres de Hanoi | Recursivo e iterativo | `GET /algoritmos/hanoi?discos=&modo=` | Pasar canastas apiladas entre tres estibas de la bodega |
| 12 | Suma exacta (combo por monto) | Backtracking vs. voraz | `GET /algoritmos/combo?sede_id=&monto=` | Armar un pedido que gaste exactamente un monto |

> Numeración unificada en la integración de los Sprints 3 y 4: los algoritmos 6 y 7 son los del
> Sprint 2 (QA), y los de esta rama pasan a ser del 8 al 12.
---

## 9. Métodos de ordenamiento

`GET /algoritmos/ordenar-inventario?sede_id=1&metodo=quicksort&campo=existencia&descendente=true`

- `metodo`: `burbuja`, `insercion`, `seleccion`, `quicksort`, `mezcla`.
- `campo`: `existencia`, `nombre`, `codigo`, `valor_venta`, `ganancia_unitaria`.
- Responde las filas ordenadas, las **comparaciones**, los **intercambios** y el tiempo.
- Con `comparar=true` (por defecto) corre los cinco sobre los mismos datos y dice si todos dan el
  mismo orden. Los O(n²) se omiten con más de 3.000 filas para cumplir los 2 s (RNF-02).

| Método | Complejidad | Detalle que se puede explicar |
|---|---|---|
| Burbuja | O(n²) | Corta si una pasada no intercambia nada: con datos ya ordenados hace n−1 comparaciones |
| Inserción | O(n²), O(n) casi ordenada | Estable; inserta cada elemento en la parte ya ordenada |
| Selección | O(n²) | A lo sumo n−1 intercambios |
| Quicksort | O(n log n) promedio | Pivote **mediana de tres** (no se degrada con datos ordenados) y recursión sobre la mitad menor |
| Mezcla | O(n log n) siempre | Estable; es el que usa el reporte |

## 10. Búsqueda binaria

`GET /algoritmos/buscar-producto?codigo=PIC-001&modo=recursiva`

El catálogo se ordena por código con merge sort y se busca partiendo el rango a la mitad. La
respuesta trae cada paso (`bajo`, `alto`, `medio`, código del medio y si siguió a la izquierda o a la
derecha) y `maximo_teorico` = ⌊log₂ n⌋ + 1. Caso base de la recursiva: el rango quedó vacío.

## 11. Torres de Hanoi

`GET /algoritmos/hanoi?discos=4&modo=iterativo`

Canastas de distinto tamaño apiladas en la estiba A; hay que pasarlas a la C usando la B, de a una
y sin poner nunca una grande sobre una pequeña.

- **Recursivo:** `hanoi(n) = hanoi(n−1, A→B) + mover la canasta n de A a C + hanoi(n−1, B→C)`; caso base n = 0.
- **Iterativo:** tres pilas explícitas. En los movimientos impares la canasta 1 avanza siempre en el
  mismo sentido circular; en los pares se hace el único movimiento legal que no la toca.
- La respuesta **verifica** el resultado simulando cada movimiento, comprueba `2ⁿ − 1` y que los dos
  modos den exactamente los mismos movimientos. Máximo 12 discos (4.095 movimientos).

## 12. Backtracking: combo por monto exacto

`GET /algoritmos/combo?sede_id=1&monto=33000&max_unidades=6&max_por_producto=3`

Un cliente quiere gastar exactamente un monto (un bono, cerrar la cuenta en un número redondo).
Solo entran los productos activos **con existencia** en la sede.

- **Backtracking:** para cada producto (del más caro al más barato) prueba llevar k = máximo … 0
  unidades. **Poda** cuando lo acumulado se pasa, cuando ni con todo lo que queda se alcanza el monto
  o cuando se llegó al límite de unidades. Devuelve la combinación con menos unidades, los nodos
  explorados y las podas.
- **Voraz:** toma siempre lo más caro que quepa. Ejemplo de la prueba con $33.000: el voraz toma un
  aguardiente de $30.000 y se queda corto; el backtracking encuentra picada ($28.000) + Poker ($5.000).

## Pruebas

| Archivo | Qué prueba | Cómo correrlo |
|---|---|---|
| `tests/test_algoritmos.py` | Algoritmos 1 a 8 (mochila contra fuerza bruta, MCD, voraz, ruta, cadena, merge sort) | `python -m pytest --noconftest tests/test_algoritmos.py` |
| `tests/test_algoritmos_clase.py` | Algoritmos 9 a 12: cada ordenamiento contra `sorted()` en 200 casos, estabilidad, búsqueda binaria en ambos modos, Hanoi legal y con 2ⁿ−1 de 0 a 10 discos, backtracking contra fuerza bruta | `python -m pytest --noconftest tests/test_algoritmos_clase.py` |
| `tests/test_algoritmos_api.py` | Los endpoints `/algoritmos` con datos del bar, permisos por sede y validaciones | `python -m pytest tests/test_algoritmos_api.py` |
