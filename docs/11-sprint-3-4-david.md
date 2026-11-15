# Sprints 3 y 4 · Facturación y reporte de ventas

**Responsable:** Juan David Tovío Montes (Analista de Requisitos) · **Rama:** `dev/david`
**Historias:** HU-023 (M5, Sprint 3) y HU-024 (M6, Sprint 4) · **Caso de uso:** CU-23
**También cierra:** el pendiente del Sprint 2 «`auth-service` sigue respondiendo en español»
(`docs/10-integracion-sprint-2.md` §5) y registra el **ADR-08** en `docs/01-arquitectura.md`.

---

## 1. HU-023 · Facturación y registro del medio de pago

### Modelo nuevo (no hay que borrar la base)

Son tablas nuevas, así que `create_all()` las crea solas al arrancar. **No** se cambió
ninguna tabla existente.

| Tabla | Qué guarda |
|---|---|
| `consecutivo_factura` | Una sola fila con el último número emitido. Se lee con `SELECT … FOR UPDATE` |
| `facturas` | Número (`UNIQUE`), pedido (`UNIQUE`: un pedido se factura una vez), sede, mesa, mesero, cajero, medio de pago (`CHECK`), total, valor recibido, cambio, fecha |
| `factura_lineas` | Copia de cada línea del pedido: código, nombre, cantidad, **valor de compra del momento**, precio de venta y subtotal |

### Endpoints

Prefijo en el gateway: `/api/parametrizacion`.

| Método y ruta | Perfil | Criterio |
|---|---|---|
| `POST /facturas` `{pedido_id, medio_pago, valor_recibido?}` | CAJERO (su sede), ADMIN | c1 a c5 |
| `GET /facturas?sede_id=&desde=&hasta=&medio_pago=` | CAJERO (su sede), ADMIN | c6 consultar |
| `GET /facturas/{id}` · `GET /facturas/numero/{numero}` | CAJERO (su sede), ADMIN | c6 consultar |
| `GET /facturas/{id}/impresion` (HTML de 80 mm que abre el diálogo de impresión) | CAJERO (su sede), ADMIN | c6 imprimir |

### Cómo se cumple cada criterio

| # | Criterio | Implementación | Prueba (`tests/test_hu023_facturacion.py`) |
|---|---|---|---|
| 1 | Solo pedidos abiertos | `PEDIDO_NO_ABIERTO` (409) dice el estado y el número de la factura que ya tiene. Un pedido sin productos responde `PEDIDO_SIN_PRODUCTOS` | `test_c1_*` |
| 2 | Productos, cantidades y valores del pedido | Las líneas se copian del pedido con el precio de venta con que se pidió; si después cambia el precio, la factura no cambia | `test_c2_*` |
| 3 | Consecutivo que no se repite | Contador con bloqueo + `UNIQUE` en `facturas.numero`. Un intento fallido no consume número. Es único en toda la cadena (todas las sedes) y se imprime con prefijo: `0001-0000001` (`FACTURA_PREFIJO`) | `test_c3_*` |
| 4 | Efectivo, débito o crédito | `EFECTIVO`, `TARJETA_DEBITO`, `TARJETA_CREDITO` (Pydantic `Literal` + `CHECK` en la base). `valor_recibido` solo se acepta en efectivo | `test_c4_*` |
| 5 | Pedido cerrado y mesa libre | En la **misma transacción** que crea la factura | `test_flujo_completo_*`, `test_la_mesa_liberada_*` |
| 6 | Consultar e imprimir | Listado con filtros, detalle por id o número e impresión HTML. Cada impresión queda en la auditoría (`IMPRIMIR_FACTURA`) | `test_c6_*` |

**Vueltas (algoritmo 5, voraz):** si el cliente paga en efectivo y se manda `valor_recibido`,
la factura devuelve `cambio` y `piezas_cambio` (por ejemplo, $50.000 para $27.000 →
1 × $20.000 + 1 × $2.000 + 1 × $1.000). Si no alcanza: `PAGO_INSUFICIENTE`, y el pedido sigue abierto.

El inventario **no** se vuelve a descontar al facturar: ya se descontó al tomar el pedido (CU-18).

## 2. HU-024 · Reporte de ventas y ganancia por rol y sede

| Método y ruta | Perfil |
|---|---|
| `GET /reportes/ventas?desde=AAAA-MM-DD&hasta=AAAA-MM-DD&sedes=1,3&orden=fecha` | CAJERO (sede fija), ADMIN |
| `GET /reportes/ventas/excel` (mismos parámetros) → `.xlsx` | CAJERO (sede fija), ADMIN |

| # | Criterio | Implementación | Prueba (`tests/test_hu024_reportes.py`) |
|---|---|---|---|
| 1 | Rango de fechas; la sede la decide el perfil | Fechas en **hora de Bogotá** (UTC-5): una venta a las 11:30 p. m. cuenta para ese día. Sin fechas = hoy. Máximo 366 días (RNF-02) | `test_c1_*`, `test_rango_*` |
| 2 | Admin: todas consolidadas o una o varias | Sin `sedes` = todas (`"sedes": null`); con `sedes=1,3` = esas. Trae totales por sede y total general | `test_c2_*` |
| 3 | Cajero: solo su sede, sin poder cambiarla | Se toma la sede del token; si pide otra, `SEDE_NO_AUTORIZADA` (403), también en el Excel. La respuesta trae `"sede_fija": true` para que la pantalla muestre el candado | `test_c3_*` |
| 4 | Mesero sin acceso aunque llame la URL | `SIN_PERMISOS` (403) en las dos rutas; el rechazo queda en la auditoría (C-1) | `test_c4_*` |
| 5 | Columnas | `fecha, codigo, nombre, cantidad, valor_compra, valor_venta, ganancia, sede` | `test_c5_c6_*` |
| 6 | Ganancia = (venta − compra) × cantidad | Con los valores guardados en la factura: editar el precio después **no** cambia el reporte | `test_c5_c6_*`, `test_el_reporte_no_cambia_*` |
| 7 | El Excel trae exactamente las filas autorizadas | La pantalla y el Excel salen de la **misma función** (`_filas_reporte`). La prueba abre el `.xlsx` y lo compara fila por fila con el JSON | `test_c7_*` |

Agrupación: una fila por **día, sede, producto y precio**. Si el precio cambió dentro del
mismo día, salen dos filas, para que la ganancia de cada una siga siendo exacta.

### Algoritmo 6 · ordenamiento por mezcla (merge sort)

`app/algoritmos.py · ordenar_mezcla` (divide y vencerás, O(n log n), estable). El reporte se
ordena por `fecha` (por defecto), `ganancia` o `cantidad`. Como es estable, al ordenar por
ganancia las filas empatadas conservan el orden por fecha. Pruebas: contra `sorted()` en 100
casos al azar, estabilidad y casos borde (`tests/test_algoritmos.py`).

### Cambio en el gateway

Hasta ahora el gateway convertía en 502 cualquier respuesta que no fuera JSON (DEF-09). Ahora deja
pasar **solo** dos documentos, y solo si la respuesta es exitosa y trae `Content-Disposition`:
el Excel (`application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`) y la factura
imprimible (`text/html`). Cualquier otro cuerpo raro sigue respondiendo 502.
Pruebas: `gateway/tests/test_qa_gateway.py` (`test_hu024_c7_*`, `test_hu023_c6_*`).

Dependencia nueva: `openpyxl==3.1.5` (en `requirements.txt` del servicio y en `requirements-dev.txt`).
**Hay que reconstruir la imagen:** `docker compose up -d --build`.

## 3. `auth-service` en inglés

Corrección del docente aplicada al servicio de Angel, sin tocar los códigos (`CREDENCIALES_INVALIDAS`,
`USUARIO_BLOQUEADO`…), que son los que usa el frontend para mostrar su mensaje en español o inglés.
Se tradujeron los mensajes de error, las respuestas `{"mensaje": …}` y los títulos de Swagger.
El `detalle` interno de la auditoría sigue en español. Se ajustaron tres pruebas que comparaban el texto.

## 4. Prueba de humo

`scripts/prueba_humo.py` ahora recorre también: ingreso de inventario → pedido con 3 cervezas →
factura en efectivo con $20.000 (cambio $2.000) → mesa libre → impresión → reporte → Excel, y
verifica que el mesero no vea el reporte. Correr con `make evidencias`.

## 5. Pendiente y coordinación

- **Felipe (HU-015 y HU-016, pantallas):** las rutas de §1 y §2 ya están en Swagger.
  - *Cobro (HU-015):* en el historial de pedidos, el botón «Calcular vueltas» puede pasar a
    «Cobrar»: `POST /facturas` con el medio de pago y, si es efectivo, `valor_recibido`.
    Para imprimir: abrir `/api/parametrizacion/facturas/{id}/impresion` con el token (por
    ejemplo, `fetch` + `blob` + `window.open`), porque la ruta exige sesión.
  - *Reportes (HU-016):* si `sede_fija` es `true`, mostrar la sede bloqueada (🔒). Para exportar,
    `fetch` a `/reportes/ventas/excel` con los mismos parámetros y descargar el `blob`.
  - Códigos nuevos para `ERROR_MESSAGES`: `PEDIDO_NO_ABIERTO`, `PEDIDO_SIN_PRODUCTOS`,
    `MEDIO_PAGO_INVALIDO`, `RANGO_INVALIDO`, `SEDES_INVALIDAS` (y ya existían `PAGO_INSUFICIENTE`
    y `CAMBIO_IMPOSIBLE`).
- **Juan Sebastián (QA, HU-032):** la prueba de humo ya cubre el flujo completo del MVP; falta
  regenerar `docs/evidencias/`.
- **Angel:** revisar que la traducción del `auth-service` no choque con algo que tenga sin subir.
