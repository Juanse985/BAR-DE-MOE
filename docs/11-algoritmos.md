# Algoritmos de la asignatura en el Bar de Moe

**Asignatura:** Diseño de Algoritmos · **Sprint:** 2 · **Código:** `services/parametrizacion-service/app/algoritmos.py`
**Pruebas:** `tests/test_algoritmos.py` (unitarias) y `tests/test_hu022_pedidos.py` (por la API)
**Evidencia en la plataforma:** `docs/evidencias/algoritmos.md` (`make algoritmos`)

El sistema usa **7 algoritmos**. Todos son funciones puras: no tocan la base de datos, así que
se pueden probar solos y explicar en la sustentación. El servicio les pasa los datos, recibe el
resultado y lo devuelve por la API. Cuatro de las técnicas vienen de los trabajos de clase:

| Trabajo de clase | Idea que se tomó | Algoritmos |
|---|---|---|
| Excel *Problema de la Mochila* | Tabla de programación dinámica beneficio × volumen | 1 (y 2 y 3 que la apoyan) |
| Quiz *recursivos e iterativos* | La misma cuenta en versión iterativa y recursiva | 2 y 4 |
| *Algoritmo voraz · problema de las monedas* | Tomar siempre la moneda más grande que quepa | 5 |
| Quiz *Algoritmos voraces* · punto 1 | Conjuntos **C** (candidatos) y **S** (solución); en cada nodo, la arista más barata sin devolverse | 6 |
| Quiz *Algoritmos voraces* · punto 2 | Cada carácter va al **inicio** o al **final** para formar la cadena lexicográficamente menor | 7 |

## Resumen

| # | Algoritmo | Técnica | Complejidad | Dónde se usa | Endpoint |
|---|---|---|---|---|---|
| 1 | Mochila 0/1 | Programación dinámica | O(n · W/mcd) | Qué reponer con un presupuesto | `GET /inventario/sugerencia-compra` |
| 2 | MCD de Euclides | Iterativo y recursivo | O(log min(a, b)) | Reduce la tabla de la mochila | (dentro del 1) |
| 3 | Mochila por razón beneficio/costo | Voraz | O(n log n) | Respaldo si la tabla no cabe en 2 s | (dentro del 1) |
| 4 | Existencia acumulada | Iterativo y recursivo | O(n) | Conciliar existencia y movimientos | `GET /inventario/conciliacion` |
| 5 | Cambio con billetes y monedas | Voraz | O(d) | Vueltas del cajero | `GET /pedidos/{id}/cambio` |
| 6 | Recorrido voraz en un grafo | Voraz (C y S) | O(n²) | Ruta del mesero por las mesas | `GET /mesas/ruta-entrega` |
| 7 | Cadena lexicográficamente menor | Voraz con deque | O(n) | Orden de las comandas en la barra | `GET /pedidos/cola-barra` |

*n = productos, mesas o movimientos según el caso; W = presupuesto; d = denominaciones.*

---

## 1 · Mochila 0/1 por programación dinámica

**Problema del bar.** El administrador tiene un presupuesto de compra. Cada producto que está por
debajo de su nivel objetivo (2 × stock mínimo) es un **lote** que se puede comprar o no. ¿Qué
lotes comprar para ganar lo máximo sin pasarse del presupuesto?

| Mochila de clase | Bar de Moe |
|---|---|
| Artículo | Lote de reposición de un producto |
| Volumen | Lo que cuesta el lote (unidades × valor de compra) |
| Beneficio | Lo que se ganaría al venderlo (unidades × (venta − compra)) |
| Capacidad | Presupuesto |

**Cómo funciona.** Igual que la tabla del Excel:

```
dp[i][w] = max( dp[i-1][w],                 ← no llevar el artículo i
                dp[i-1][w - v_i] + b_i )    ← llevarlo, si cabe
```

Al final se recorre la tabla de abajo hacia arriba: si `dp[i][w]` es distinto de `dp[i-1][w]`,
el artículo `i` entró.

**Comprobación con el ejercicio de clase.** La prueba
`test_mochila_del_excel_problema_de_la_mochila` usa los mismos datos del Excel (A 6/5, B 5/2,
C 8/7, D 2/6, capacidad 7). Llega a la misma última fila, `0 5 5 5 6 6 11`, y elige **A y B**.

## 2 · Máximo común divisor de Euclides (iterativo y recursivo)

Los precios en pesos son múltiplos de 100 o de 1.000. Si se dividen todos los costos y el
presupuesto por su MCD, la tabla de la mochila da exactamente la misma respuesta y es hasta
1.000 veces más pequeña. Ejemplo: con presupuesto de $120.000 y lotes de $20.000, $22.000,
$35.000…, el MCD es 1.000 y la tabla pasa de 120.001 columnas a 121.

- Iterativo: `while b != 0: a, b = b, a % b`
- Recursivo: `mcd(a, b) = a si b = 0; si no, mcd(b, a mod b)`

## 3 · Mochila voraz por razón beneficio/costo

Ordena los lotes por ganancia por peso invertido y toma los que quepan. Es rápido, pero **no
siempre es óptimo** en la mochila 0/1; la prueba `test_el_voraz_puede_no_ser_optimo_en_la_mochila_0_1`
lo demuestra (el voraz da 160 y la programación dinámica 220). Por eso solo se usa como respaldo,
si la tabla tendría más de 2 millones de celdas y pondría en riesgo los 2 s del RNF-02.

## 4 · Existencia acumulada (iterativa y recursiva)

**Problema del bar.** ¿La existencia guardada coincide con el historial de movimientos? Si no
coincide, alguien la cambió por fuera del sistema.

```
existencia(0) = 0
existencia(n) = existencia(n-1) + movimiento(n)     (+ingreso, −venta, ±ajuste)
```

El servicio calcula las dos versiones y responde si **cuadra**. La recursiva solo se usa con
menos de 900 movimientos, porque Python corta la recursión cerca de 1.000 niveles. Ese límite es
justamente lo que se discute en clase sobre recursión contra iteración.

## 5 · Vueltas con billetes y monedas (voraz)

Con las denominaciones colombianas (100.000, 50.000, 20.000, 10.000, 5.000, 2.000, 1.000, 500,
200, 100 y 50), en cada paso se toma la más grande que quepa en lo que falta devolver. Con esta
serie el voraz entrega el menor número de piezas. Si sobra un resto imposible de entregar (por
ejemplo $30), responde que "el resultado no cumple", como en el ejercicio de clase.

Ejemplo: total $24.000, pagan $50.000 → 1 × $20.000 + 1 × $5.000 + 1 × $1.000.

## 6 · Ruta del mesero: recorrido voraz en un grafo (conjuntos C y S)

**Idea de clase (quiz, punto 1).** C es el conjunto de candidatos y S la solución que se va
armando. En cada nodo se escoge la arista de **menor costo** hacia un nodo que todavía no está
en S, sin devolverse. Una elección nunca se deshace.

**Problema del bar.** El mesero sale de la barra y tiene que pasar por todas las mesas que tienen
pedido abierto. ¿En qué orden?

| Quiz | Bar de Moe |
|---|---|
| Nodos A…F | La barra y las mesas con pedido abierto |
| Peso de la arista | Casillas que hay que caminar entre dos puntos del mapa 3×N (distancia Manhattan) |
| C | {BARRA} ∪ mesas con pedido abierto |
| S | La ruta, en el orden en que se eligió |

La mesa *k* (contando desde 0 en orden de número) está en la fila `k ÷ 3` y la columna `k mod 3`,
igual que en el mapa del frontend. La barra está arriba del mapa, en la columna del medio. Si dos
mesas están a la misma distancia, gana la de número menor, para que el resultado siempre sea el
mismo.

**Comprobación con el quiz.** `test_recorrido_voraz_punto_1_del_quiz` usa el grafo del quiz y
obtiene C = {A, B, C, D, E, F}, S = {A, C, D, F} y costo 8. Con A-C = 3 y A-B = 6
(`..._punto_2_...`), S no cambia y el costo baja a 7, como se concluyó en clase.

**Ejemplo en el bar** (mesas 1, 3, 8 y 9 con pedido; evidencia en `docs/evidencias/algoritmos.md`):

| Paso | Nodo actual | Opciones (casillas) | Elegido |
|---|---|---|---|
| 1 | BARRA | 1 = 2, 3 = 2, 8 = 3, 9 = 4 | **1** |
| 2 | 1 | 3 = 2, 8 = 3, 9 = 4 | **3** |
| 3 | 3 | 8 = 3, 9 = 2 | **9** |
| 4 | 9 | 8 = 1 | **8** |

S = BARRA → 1 → 3 → 9 → 8, con 7 casillas. Recorrerlas en orden de número costaría 8.

**Limitación honesta.** Es el algoritmo del vecino más cercano: es rápido, pero no garantiza la
ruta más corta posible. Encontrar la óptima es el problema del viajante, que crece de forma
exponencial con el número de mesas. Por eso la respuesta también trae
`distancia_en_orden_de_numero`, para comparar.

## 7 · Cola de la barra: cadena lexicográficamente menor

**Idea de clase (quiz, punto 2).** Se leen los caracteres en orden y cada uno solo puede ir al
**inicio** o al **final** del resultado. Regla voraz: si el nuevo es menor o igual que el primero
del resultado, va al inicio; si no, va al final. Con `JUANJUAN` da `AAJUNJUN`, paso por paso igual
que en la diapositiva (`test_cadena_del_quiz_juanjuan`). Además,
`test_cadena_voraz_es_optima_contra_fuerza_bruta` compara contra las 2ⁿ combinaciones posibles en
200 cadenas al azar, y en todas el voraz da la menor.

**Problema del bar.** Las comandas llegan a la barra en el orden en que se abren los pedidos. El
barman solo puede poner la comanda nueva **delante** o **detrás** de las que ya tiene en el riel;
no la mete en el medio. Conviene despachar primero las mesas más cercanas, porque se entregan
más rápido.

| Quiz | Bar de Moe |
|---|---|
| Carácter | Comanda (pedido abierto) |
| Orden alfabético | Clave (distancia de la mesa a la barra, número de mesa) |
| Agregar al inicio o al final | Poner la comanda delante o detrás en el riel |
| Cadena resultado | Orden de despacho |

Se implementa con una `deque`, así que cada paso cuesta O(1).

**Ejemplo** (llegan las comandas de las mesas 9, 1, 8 y 3):

| Llega | Clave | Va al | Cola |
|---|---|---|---|
| Mesa 9 | (4, 9) | INICIO | 9 |
| Mesa 1 | (2, 1) | INICIO | 1 · 9 |
| Mesa 8 | (3, 8) | FIN | 1 · 9 · 8 |
| Mesa 3 | (2, 3) | FIN | 1 · 9 · 8 · 3 |

La mesa 3 está cerca, pero llegó de última y la regla solo permite ponerla en un extremo. Por eso
queda al final. Es el mismo comportamiento del quiz: la cadena es la menor que se puede formar
**con esa restricción**, no la que daría ordenar todo.

---

## Cómo mostrarlo en la sustentación

1. `make algoritmos` (o `python scripts/evidencia_algoritmos.py`) con la plataforma levantada.
   Arma un escenario propio y deja `docs/evidencias/algoritmos.md` con los pasos de los 7.
2. En Postman, la carpeta *7 · Algoritmos* de `docs/postman/bar-de-moe-sprint-2.postman_collection.json`
   llama los endpoints uno por uno. Las carpetas anteriores preparan la sesión y el pedido.
   (Swagger no abre por el gateway porque toda ruta, salvo login y health, exige token.)
3. Las pruebas: `cd services/parametrizacion-service && python -m pytest tests/test_algoritmos.py -v`.

Por ahora solo el algoritmo 5 (vueltas) tiene botón en las pantallas. Los demás se ven por la API,
Swagger y Postman.
