# Evidencia · los 12 algoritmos funcionando en la plataforma

- **Fecha:** 2026-11-15T11:04:29
- **Plataforma:** `http://127.0.0.1:18000` (todo por el gateway)
- **Escenario:** sede `QA Algoritmos 20261115110428` con 9 mesas (mapa 3×3), 3 cervezas con 24 unidades y pedidos en las mesas 9, 1, 8, 3, en ese orden.
- **Se regenera con:** `python scripts/evidencia_algoritmos.py --evidencia docs/evidencias`

## 1, 2 y 3 · Sugerencia de compra (mochila 0/1 + MCD + voraz de respaldo)

`GET /inventario/sugerencia-compra?presupuesto=120000` · método **PROGRAMACION_DINAMICA** · MCD usado para reducir la tabla: **1.000**

Presupuesto $120.000 → se gastan $120.000 y se espera ganar $230.000 (sobran $0).

| Lote | Unidades | Costo (volumen) | Ganancia (beneficio) | ¿Entra? |
|---|---:|---:|---:|---|
| Águila 330 ml | 10 | $22.000 | $38.000 | ✅ |
| Poker 330 ml | 10 | $22.000 | $38.000 | ✅ |
| Pilsen 330 ml | 10 | $22.000 | $38.000 | ✅ |
| Agua Cristal 600 ml | 10 | $12.000 | $28.000 | ✅ |
| Soda Bretaña 300 ml | 10 | $15.000 | $30.000 | ✅ |
| Papas fritas de paquete 45 g | 10 | $15.000 | $30.000 | ✅ |
| Maní salado 50 g | 10 | $12.000 | $28.000 | ✅ |
| Águila Light 330 ml | 10 | $23.000 | $37.000 | — |
| Costeña 330 ml | 10 | $20.000 | $35.000 | — |
| Club Colombia Dorada 330 ml | 10 | $28.000 | $47.000 | — |
| Andina 330 ml | 10 | $20.000 | $35.000 | — |
| Corona 355 ml | 10 | $40.000 | $60.000 | — |
| Heineken 330 ml | 10 | $35.000 | $55.000 | — |
| Aguardiente Antioqueño sin azúcar 375 ml | 10 | $280.000 | $270.000 | — |
| Aguardiente Néctar Club 375 ml | 10 | $250.000 | $250.000 | — |
| Ron Viejo de Caldas 3 años 375 ml | 10 | $300.000 | $300.000 | — |
| Ron Medellín Añejo 375 ml | 10 | $290.000 | $290.000 | — |
| Whisky Old Parr 12 años 750 ml | 10 | $1.500.000 | $1.400.000 | — |
| Whisky Buchanan's 12 años 750 ml | 10 | $1.400.000 | $1.300.000 | — |
| Jugo Hit mango 500 ml | 10 | $18.000 | $32.000 | — |
| Chicharrones de paquete 40 g | 10 | $16.000 | $29.000 | — |
| Picada para dos personas | 10 | $180.000 | $240.000 | — |
| Cerveza Duff QA | 10 | $25.000 | $35.000 | — |

## 4 · Conciliación de existencia (iterativa y recursiva)

`GET /inventario/conciliacion` de **BBC Cajicá Honey Ale 330 ml**: 3 movimientos · existencia guardada **17** · iterativa **17** · recursiva **17** → ✅ cuadra.

## 5 · Vueltas con billetes y monedas (voraz)

`GET /pedidos/20/cambio?pagado=50000`: total $24.000, vueltas **$26.000** en 3 piezas:

- 1 × $20.000
- 1 × $5.000
- 1 × $1.000

## 6 · Ruta del mesero (recorrido voraz en un grafo, conjuntos C y S)

`GET /mesas/ruta-entrega` · la barra está arriba del mapa; el costo es la distancia en casillas.

- **C** (candidatos) = {BARRA, 1, 3, 8, 9}
- **S** (solución, en orden) = BARRA → 1 → 3 → 9 → 8
- Distancia total: **7** casillas (en orden de número serían 8)

| Paso | Nodo actual | Opciones (distancia) | Elegido |
|---|---|---|---|
| 1 | BARRA | BARRA→1=2, BARRA→3=2, BARRA→8=3, BARRA→9=4 | **1** (2) |
| 2 | 1 | 1→3=2, 1→8=3, 1→9=4 | **3** (2) |
| 3 | 3 | 3→8=3, 3→9=2 | **9** (2) |
| 4 | 9 | 9→8=1 | **8** (1) |

## 7 · Cola de la barra (cadena lexicográficamente menor)

`GET /pedidos/cola-barra` · clave de cada comanda = (distancia de la mesa a la barra, número de mesa).

| Llega la comanda de | Clave | Va al | Cola resultante (mesas) |
|---|---|---|---|
| Mesa 9 (pedido #20) | (4, 9) | INICIO | 9 |
| Mesa 1 (pedido #21) | (2, 1) | INICIO | 1 · 9 |
| Mesa 8 (pedido #22) | (3, 8) | FIN | 1 · 9 · 8 |
| Mesa 3 (pedido #23) | (2, 3) | FIN | 1 · 9 · 8 · 3 |

Orden de despacho: **Mesa 1 → Mesa 9 → Mesa 8 → Mesa 3**

## 8 · Merge sort estable · reporte de ventas

`GET /reportes/ventas?orden=ganancia`: dos pedidos cobrados en la sede de prueba, de mayor a menor ganancia (estable: los empates conservan el orden por fecha).

| Código | Producto | Cant. | Ganancia |
|---|---|---:|---:|
| ART-002 | BBC Chapinero Porter 330 ml | 3 | $21.000 |
| ART-001 | BBC Cajicá Honey Ale 330 ml | 2 | $14.000 |

## 9 · Burbuja, inserción, selección, quicksort y mezcla

`GET /algoritmos/ordenar-inventario`: los 26 productos de la sede ordenados por existencia con cada método; todos dan el mismo orden.

| Método | Complejidad | Comparaciones | Intercambios | ¿Mismo orden? |
|---|---|---:|---:|---|
| burbuja | O(n²) | 94 | 41 | ✅ |
| insercion | O(n²) · O(n) casi ordenada | 66 | 41 | ✅ |
| seleccion | O(n²) | 325 | 17 | ✅ |
| quicksort | O(n log n) promedio | 295 | 38 | ✅ |
| mezcla | O(n log n) | 77 | 77 | ✅ |

## 10 · Búsqueda binaria (recursiva)

`GET /algoritmos/buscar-producto?codigo=ART-002`: 26 productos ordenados por código; lo encuentra en 5 pasos (máximo teórico 5).

| Paso | Bajo | Alto | Medio | Código en el medio | Decisión |
|---:|---:|---:|---:|---|---|
| 1 | 0 | 25 | 12 | CERV-007 | IZQUIERDA |
| 2 | 0 | 11 | 5 | BEB-004 | IZQUIERDA |
| 3 | 0 | 4 | 2 | BEB-001 | IZQUIERDA |
| 4 | 0 | 1 | 0 | ART-001 | DERECHA |
| 5 | 1 | 1 | 1 | ART-002 | ENCONTRADO |

## 11 · Torres de Hanoi (recursiva)

`GET /algoritmos/hanoi?discos=3`: 7 movimientos (2^3 - 1 = 7); verificado por simulación: ✅.

1) canasta 1: A→C · 2) canasta 2: A→B · 3) canasta 1: C→B · 4) canasta 3: A→C · 5) canasta 1: B→A · 6) canasta 2: B→C · 7) canasta 1: A→C

## 12 · Backtracking · combo por monto exacto

`GET /algoritmos/combo?monto=39000` en la sede de prueba: el backtracking encontró un combo de $39.000 explorando 31 nodos con 16 podas; el voraz no lo encontró (le faltaron $3.000).


| Producto | Unidades | Subtotal |
|---|---:|---:|
| BBC Cajicá Honey Ale 330 ml | 2 | $24.000 |
| Coca-Cola 350 ml | 3 | $15.000 |
