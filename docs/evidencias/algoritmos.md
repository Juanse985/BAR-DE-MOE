# Evidencia · los 7 algoritmos funcionando en la plataforma

- **Fecha:** 2026-10-30T18:31:40
- **Plataforma:** `http://127.0.0.1:18000` (todo por el gateway)
- **Escenario:** sede `QA Algoritmos 20261030183139` con 9 mesas (mapa 3×3), 3 cervezas con 24 unidades y pedidos en las mesas 9, 1, 8, 3, en ese orden.
- **Se regenera con:** `python scripts/evidencia_algoritmos.py --evidencia docs/evidencias`

## 1, 2 y 3 · Sugerencia de compra (mochila 0/1 + MCD + voraz de respaldo)

`GET /inventario/sugerencia-compra?presupuesto=120000` · método **PROGRAMACION_DINAMICA** · MCD usado para reducir la tabla: **1.000**

Presupuesto $120.000 → se gastan $119.000 y se espera ganar $201.000 (sobran $1.000).

| Lote | Unidades | Costo (volumen) | Ganancia (beneficio) | ¿Entra? |
|---|---:|---:|---:|---|
| Poker 330 ml | 10 | $22.000 | $38.000 | ✅ |
| Costeña 330 ml | 10 | $20.000 | $35.000 | ✅ |
| Pilsen 330 ml | 10 | $22.000 | $38.000 | ✅ |
| Andina 330 ml | 10 | $20.000 | $35.000 | ✅ |
| Heineken 330 ml | 10 | $35.000 | $55.000 | ✅ |
| Águila Light 330 ml | 10 | $23.000 | $37.000 | — |
| Club Colombia Dorada 330 ml | 10 | $28.000 | $47.000 | — |
| Corona 355 ml | 10 | $40.000 | $60.000 | — |
| Águila Imperial 330 ml | 10 | $25.000 | $40.000 | — |
| Cerveza Duff QA | 10 | $25.000 | $35.000 | — |

## 4 · Conciliación de existencia (iterativa y recursiva)

`GET /inventario/conciliacion` de **BBC Cajicá Honey Ale 330 ml**: 3 movimientos · existencia guardada **17** · iterativa **17** · recursiva **17** → ✅ cuadra.

## 5 · Vueltas con billetes y monedas (voraz)

`GET /pedidos/7/cambio?pagado=50000`: total $24.000, vueltas **$26.000** en 3 piezas:

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
| Mesa 9 (pedido #7) | (4, 9) | INICIO | 9 |
| Mesa 1 (pedido #8) | (2, 1) | INICIO | 1 · 9 |
| Mesa 8 (pedido #9) | (3, 8) | FIN | 1 · 9 · 8 |
| Mesa 3 (pedido #10) | (2, 3) | FIN | 1 · 9 · 8 · 3 |

Orden de despacho: **Mesa 1 → Mesa 9 → Mesa 8 → Mesa 3**
