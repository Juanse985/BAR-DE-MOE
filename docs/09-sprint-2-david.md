# Sprint 2 · Inventario por sede y toma de pedidos

**Responsable:** Juan David Tovío Montes (Analista de Requisitos) · **Rama:** `dev/david`
**Historias:** HU-021 (M3) y HU-022 (M4) · **Casos de uso:** CU-15, CU-16, CU-17, CU-18, CU-20, CU-21, CU-22, CU-32
**Correcciones del docente atendidas:** producto único para todas las sedes con inventario por sede,
inactivar en todo (parte de M2/M3/M4) y mensajes de error con motivo.

---

## 1. Cambio de modelo (corrección del docente)

Antes, cada sede tenía su propia copia del producto (`productos.sede_id`). Ahora:

| Tabla | Qué guarda |
|---|---|
| `productos` | El producto **una sola vez**: código único, nombre, tipo, proveedor, valores. Sin `sede_id` |
| `inventario_sede` | Una fila por producto y sede: `existencia`, `stock_minimo`, `activo` (se vende o no en esa sede). `CHECK existencia >= 0` |
| `movimientos_inventario` | Histórico inmutable: tipo (`INGRESO`, `AJUSTE`, `VENTA`), cantidad con signo, existencia anterior y resultante, motivo, usuario, pedido, fecha |
| `pedidos` | Pedido de una mesa: sede, mesero, estado (`ABIERTO`/`CERRADO`), total. Índice único parcial: un solo pedido abierto por mesa |
| `pedido_lineas` | Producto, cantidad y precio de venta del momento |

Reglas:

- Crear un producto lo deja en el inventario de **todas las sedes activas** con existencia 0.
- Crear (o reactivar) una sede le carga **todos los productos activos** con existencia 0.
- Inactivar un producto en `/productos/{id}/inactivar` lo saca de todas las sedes;
  inactivarlo en `/inventario/sedes/{s}/productos/{p}/inactivar` lo saca solo de esa sede.
- HU-017 c4 con el modelo nuevo: una sede no se inactiva si tiene mesas activas, productos
  activos **con existencia** o pedidos abiertos. *(Confirmar con el PO.)*

> Inventario y pedidos viven en `parametrizacion-service` y no en servicios nuevos porque
> CU-18 exige que verificar y descontar existencias ocurra **en una sola transacción** con
> el pedido, y eso no se garantiza entre dos bases de datos (ADR-01).

**Migración:** el proyecto aún no tiene Alembic (H-08). Al cambiar `productos` hay que borrar el
volumen de la base: `docker compose down -v && docker compose up --build && python scripts/seed.py`.

## 2. Endpoints nuevos y cambiados

Prefijo en el gateway: `/api/parametrizacion`.

| Método y ruta | Perfil | HU / CU |
|---|---|---|
| `POST /productos` (ya no pide `sede_id`; acepta `stock_minimo`) | ADMIN | HU-020 v2.1 |
| `GET /productos?sede_id=` (trae `existencia` y `activo_en_sede`) | Todos | HU-020, CU-31 |
| `GET /inventario?sede_id=&buscar=` | Todos (su sede) | CU-17, HU-012 |
| `POST /inventario/ingresos` `{sede_id, producto_id, cantidad>0, motivo}` | ADMIN | CU-15 |
| `POST /inventario/ajustes` `{sede_id, producto_id, cantidad (±), motivo, stock_minimo?}` | ADMIN | CU-16 |
| `GET /inventario/movimientos?sede_id=&producto_id=` | ADMIN | CU-32 |
| `GET /inventario/conciliacion?sede_id=&producto_id=` | ADMIN | CU-32 · algoritmo 4 |
| `GET /inventario/sugerencia-compra?sede_id=&presupuesto=` | ADMIN | HU-021 · algoritmos 1, 2, 3 |
| `POST /inventario/sedes/{s}/productos/{p}/inactivar` · `/activar` | ADMIN | Inactivar en todo |
| `POST /pedidos` `{mesa_id, lineas?}` → 201 nuevo / 200 si la mesa ya tenía uno | MESERO, ADMIN | CU-20 |
| `POST /pedidos/{id}/lineas` `{lineas: [...]}` (todas o ninguna) | MESERO, ADMIN | CU-18, CU-21 |
| `GET /pedidos?estado=&mesa_id=` · `GET /pedidos/{id}` | Todos (su sede) | CU-22 |
| `GET /mesas/{id}/pedido-abierto` | Todos (su sede) | CU-22 |
| `GET /pedidos/{id}/cambio?pagado=` | CAJERO, ADMIN | Algoritmo 5 (prepara HU-023) |

## 3. Algoritmos de la asignatura (`app/algoritmos.py`)

| # | Algoritmo | Visto en | Uso en el sistema |
|---|---|---|---|
| 1 | Mochila 0/1 con tabla `dp[i][w]` | Problema de la mochila | Con un presupuesto de compra (capacidad), elige qué productos reponer para maximizar la ganancia. Volumen = costo del lote, beneficio = ganancia del lote |
| 2 | MCD de Euclides, iterativo y recursivo | Quiz recursivos e iterativos | Divide costos y presupuesto por su MCD: misma respuesta con una tabla hasta 1.000 veces menor (cumple RNF-02 de 2 s) |
| 3 | Voraz por razón beneficio/costo | Algoritmo voraz | Respaldo de la mochila cuando la tabla pasaría de 2 millones de celdas. La prueba muestra un caso donde el voraz **no** es óptimo |
| 4 | Existencia acumulada, iterativa y recursiva | Quiz recursivos e iterativos | `existencia(n) = existencia(n-1) + movimiento(n)`. Comprueba que el saldo guardado se explica con los movimientos (CU-32) |
| 5 | Cambio de monedas voraz | Algoritmo voraz (monedas) | Vueltas en billetes y monedas colombianos; si sobra un resto imposible, "el resultado no cumple" |

Pruebas: `tests/test_algoritmos.py` (incluye la mochila contra fuerza bruta en 50 casos al azar).

## 4. Mensajes de error con motivo, en inglés

Corrección del docente: el sistema responde **en inglés** y cada mensaje dice **qué** falló y **por qué**.
Los códigos (`STOCK_INSUFICIENTE`, `SEDE_INACTIVA`…) no cambian: son identificadores que usa el frontend.

- Negocio: `Not enough stock of 'Águila 330 ml': 5 requested but only 3 left in this branch.`
- Validación (422): nombra el campo y el motivo (`The submitted data is not valid. cantidad: must be
  greater than 0`). Los nombres de campo siguen siendo los del contrato de la API.
- Traducidos: `parametrizacion-service`, `libs/common` (token, permisos, validación, reglas de
  contraseña, auditoría) y `gateway`. Los títulos de Swagger también quedaron en inglés.
- `auth-service` es de Angel y tiene cambios sin integrar en `dev/angel`: su traducción va en un
  parche aparte (`angel-auth-mensajes-en-ingles.patch`) para aplicarlo en su rama sin conflictos.

## 5. Hallazgos del Sprint 1 cerrados

H-01, H-02, H-03, H-04, H-07 y H-10. Ver `05-contratos.md` §9.1 y `tests/test_hallazgos_sprint1.py`.
Siguen abiertos: H-06 (necesita HTTP al auth-service), H-08 (Alembic, Felipe) y H-11 (paginación).

## 6. Pendiente y coordinación

- **Felipe (frontend):** su rama `dev/felipe` tenía un backend propio de inventario/pedidos con
  `stock` dentro de `productos`. Este backend lo reemplaza; las pantallas HU-012/013/014 deben
  llamar a las rutas de la sección 2. El formulario de producto ya no necesita el selector de sede.
- **Juan (QA):** se ajustó `test_c1_un_operario_no_abre_un_producto_de_otra_sede` al modelo nuevo
  (el producto es global; la restricción por sede se prueba con `?sede_id=`).
- **Sprint 3 (HU-023, también de David):** cerrar el pedido al facturar y liberar la mesa (CU-23).
