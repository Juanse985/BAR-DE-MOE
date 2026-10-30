# Evidencia · frontend del Sprint 2 por perfiles (HU-012, HU-013, HU-014)

Recorrido automático en Chromium (Playwright) contra la plataforma integrada, con los tres perfiles,
en español e inglés y en celular (390 px). Base recién creada con `scripts/seed.py`.

- **Fecha:** 2026-10-30
- **Resultado:** 39/39 verificaciones en verde · **0 errores de consola**
- **Capturas:** `capturas/sprint-2/` (las del Sprint 1 siguen en `capturas/`)

| # | Verificación | Resultado | Detalle |
|---:|---|---|---|
| 1 | Admin entra y ve el menú con Auditoría | ✅ |  |
| 2 | Productos: catálogo global sin duplicados (11) | ✅ | 11 |
| 3 | Productos: crear uno lo deja una sola vez (12) | ✅ | 12 |
| 4 | Productos: sin textos 'undefined' | ✅ |  |
| 5 | Inventario: 12 productos × 3 sedes = 36 filas | ✅ | 36 |
| 6 | Inventario: el producto nuevo nace con 0 en Zona T | ✅ |  |
| 7 | Inventario: entrada de 10 → existencia 10 | ✅ | 10 |
| 8 | Inventario: salida de 3 → existencia 7 | ✅ | 7 |
| 9 | Inventario: ajuste exacto a 20 con mínimo 4 | ✅ | ['20', '4'] |
| 10 | Inventario: sin motivo no se envía (HU-021) | ✅ |  |
| 11 | Inventario: el historial muestra los 3 movimientos (CU-32) | ✅ | 3 |
| 12 | Inventario: inactivar solo en Zona T | ✅ | Inactivo en la sede |
| 13 | Inventario: sin textos 'undefined' | ✅ |  |
| 14 | Mesas: el administrador ve las 30 mesas | ✅ |  |
| 15 | Mesas: sin textos 'undefined' | ✅ |  |
| 16 | Usuarios: filtro por perfil en el servidor (3 meseros) | ✅ | Anterior Página 1 de 1 · 3 registros Siguiente |
| 17 | Usuarios: sin textos 'undefined' | ✅ |  |
| 18 | Auditoría: muestra registros de seguridad | ✅ | 12 |
| 19 | Auditoría: el módulo de parametrización registra los ajustes | ✅ |  |
| 20 | Cambiar mi contraseña: formulario voluntario con Cancelar | ✅ |  |
| 21 | Mesero: solo ve las 10 mesas de Zona T | ✅ | {'Zona T'} |
| 22 | Mesero: no puede ocupar ni liberar mesas a mano | ✅ |  |
| 23 | Mesero: 'Tomar pedido' abre la toma de pedido | ✅ |  |
| 24 | Pedidos: catálogo de la sede de la mesa (12) | ✅ | 12 |
| 25 | Pedidos: se abre el pedido y descuenta existencia | ✅ | ¡Pedido #1 registrado con éxito! Se descontó el stock de la sede y la mesa pasó a ocupada. |
| 26 | Pedidos: la misma mesa agrega al pedido abierto (CU-20) | ✅ | Se agregaron los productos al pedido #1: la mesa ya tenía un pedido abierto. |
| 27 | Pedidos: un solo pedido abierto con las 4 unidades | ✅ | ['#1\tMesa #1\tZona T\tOtto Mann\t2x Águila 330 ml, 2x Poker 330 ml\t$24,000\tABIERTO\t… |
| 28 | Toma de pedido: sin textos 'undefined' | ✅ |  |
| 29 | Mapa: la mesa queda ocupada con su pedido (HU-022 c6) | ✅ | Pedido #1 · $24,000 (4 ítems) |
| 30 | Inventario del mesero: Águila bajó de 48 a 46 | ✅ | 46 |
| 31 | Mesero: no ve botones de ajuste | ✅ |  |
| 32 | Cajero: no puede agregar productos | ✅ |  |
| 33 | Cajero: calcula vueltas con el algoritmo voraz | ✅ | Pedido #1 · vueltas $26,000: 1 × $20,000, 1 × $5,000, 1 × $1,000 |
| 34 | Cajero: solo 'Ver pedido' en la mesa ocupada | ✅ |  |
| 35 | Admin: no ofrece liberar una mesa con pedido abierto | ✅ |  |
| 36 | EN · inventario: sin textos 'undefined' | ✅ |  |
| 37 | EN · pedidos: sin textos 'undefined' | ✅ |  |
| 38 | EN · auditoria: sin textos 'undefined' | ✅ |  |
| 39 | Móvil (390 px): toma de pedido sin desplazamiento horizontal | ✅ |  |

## Capturas

| Archivo | Qué muestra |
|---|---|
| `01-productos.png` | Catálogo global: un solo producto para las tres sedes (corrección del docente) |
| `02-movimientos.png` | Historial de movimientos de un producto en Zona T: ingreso, salida y ajuste con motivo y usuario (CU-32) |
| `03-inventario.png` | Inventario por sede con existencia, mínimo y alertas (HU-012) |
| `04-usuarios.png` | Usuarios filtrados por perfil en el servidor, con paginado |
| `05-auditoria.png` | Consulta de la auditoría (HU-008) |
| `06-toma-pedido.png` | Toma de pedido del mesero: la misma mesa agrega al pedido abierto (HU-014, CU-20/21) |
| `07-mapa-mesas.png` | Mapa 3×N del mesero de Zona T: la mesa 1 quedó ocupada con su pedido (HU-013) |
| `08-cajero-vueltas.png` | Cajero calculando las vueltas con el algoritmo voraz |
| `09-ingles-auditoria.png` | Interfaz en inglés |
| `10-movil-pedido.png` | Toma de pedido en celular, sin desplazamiento horizontal |
