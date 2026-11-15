# Evidencia · frontend de los Sprints 3 y 4 (HU-015, HU-016, HU-023, HU-024)

Recorrido automático en Chromium (Playwright) contra la plataforma integrada (`integracion/sprint-3`),
con base recién creada, `scripts/seed.py` y `scripts/datos_demo.py`. Incluye regresión de pantallas del Sprint 2.

- **Fecha:** 2026-11-15
- **Resultado:** 27/27 verificaciones en verde · **0 errores de consola**
- **Perfiles:** administrador, cajero `pbouvier` (Zona T) y mesero `omann` (Zona T); español, inglés y celular (390 px)
- **Capturas:** `capturas/sprint-3-4/`

| # | Verificación | Resultado | Detalle |
|---:|---|---|---|
| 1 | Admin ve Facturación, Consulta de facturas y Reporte de ventas en el menú | ✅ | ['sedes', 'mesas', 'tipos-producto', 'proveedores', 'productos', 'inventario'… |
| 2 | Facturación (admin) lista los pedidos abiertos de las tres sedes | ✅ | 8 pedidos |
| 3 | Facturación muestra las facturas de hoy | ✅ |  |
| 4 | Reporte (admin) consolidado: filas de detalle y totales de las 3 sedes | ✅ | 12 filas · 3 sedes |
| 5 | Reporte (admin) puede elegir la sede | ✅ |  |
| 6 | Filtro por tipo de producto: solo códigos CERV- | ✅ | ['CERV-002', 'CERV-005', 'CERV-001'] |
| 7 | Exportar a Excel descarga un .xlsx | ✅ | reporte-ventas_2026-11-15_2026-11-15.xlsx |
| 8 | Cajero ve Facturación, Consulta y Reporte | ✅ | ['mesas', 'inventario', 'pedidos', 'facturacion', 'consulta-facturas', 'repor… |
| 9 | El cajero solo ve pedidos de su sede (Zona T) | ✅ | {'Zona T'} |
| 10 | Con efectivo insuficiente el botón de cobrar queda deshabilitado | ✅ |  |
| 11 | Al cobrar se abre la factura con número consecutivo | ✅ |  |
| 12 | La factura trae las vueltas y los billetes a entregar (algoritmo 5) | ✅ |  |
| 13 | El pedido cobrado sale de la lista de pendientes | ✅ | 3 → 2 |
| 14 | Aviso de factura emitida y mesa libre | ✅ | Factura 0001-0000007 emitida. El pedido quedó cerrado y la mesa libre. |
| 15 | Consulta por número de factura | ✅ | 0001-0000007 |
| 16 | Consulta filtrada por medio de pago (débito) y solo de su sede | ✅ | ['Tarjeta débito'] |
| 17 | Imprimir carga la tirilla de 80 mm del servidor | ✅ | frames 1 |
| 18 | En el reporte el cajero tiene la sede fija (candado) y no puede elegir otra | ✅ |  |
| 19 | El reporte del cajero solo trae Zona T | ✅ | {'Zona T'} |
| 20 | Regresión S2 · el mapa de mesas del mesero carga sus 10 mesas | ✅ | 10 mesas |
| 21 | Regresión S2 · inventario por sede con los 25 productos | ✅ | 25 filas |
| 22 | Regresión S2 · el inventario muestra productos agotados y bajo el mínimo (datos de demo) | ✅ |  |
| 23 | El mesero NO ve Facturación ni Reporte en el menú | ✅ | ['mesas', 'inventario', 'pedidos'] |
| 24 | El mesero no tiene botón Cobrar en el historial | ✅ |  |
| 25 | Reporte en inglés | ✅ | Sales and profit report |
| 26 | Facturación en celular (390 px) sin desplazamiento horizontal | ✅ | scrollWidth 390 |
| 27 | Sin errores de JavaScript en la consola | ✅ | [] |

## Capturas

| Archivo | Qué muestra |
|---|---|
| `01-admin-facturacion.png` | El administrador ve los pedidos por cobrar de las tres sedes y las facturas de hoy |
| `02-admin-reporte-filtro-tipo.png` | Reporte consolidado filtrado por tipo de producto (filtro de la propuesta M6) |
| `03-cajero-factura.png` | Factura emitida por el cajero: consecutivo, vueltas y billetes a entregar (algoritmo 5) |
| `04-cajero-mesas-tras-cobro.png` | Mapa de mesas del cajero: la mesa cobrada vuelve a estar libre |
| `05-cajero-consulta.png` | Consulta de facturas filtrada por medio de pago, solo de su sede |
| `06-cajero-reporte.png` | Reporte del cajero con la sede fija (candado) |
| `07-reporte-ingles.png` | Reporte en inglés |
| `08-movil-facturacion.png` | Facturación en celular, sin desplazamiento horizontal |
| `09-mesero-inventario.png` | Regresión del Sprint 2: inventario del mesero con alertas |
