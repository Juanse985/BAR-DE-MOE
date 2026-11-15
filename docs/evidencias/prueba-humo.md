# Evidencia · prueba de humo de punta a punta

- **Fecha:** 2026-11-15T11:03:53
- **Plataforma:** `http://127.0.0.1:18000`
- **Resultado:** ✅ APROBADA
- **SLA verificado en cada paso:** 2000 ms (RNF-02)

| # | Paso | Requisito | Esperado | Obtenido | Servidor (ms) | Cliente (ms) | Estado | Nota |
|---|---|---|---|---|---:|---:|---|---|
| 1 | Plataforma disponible (/health) | Despliegue | 200 | 200 | 7.1 | 10.1 | OK |  |
| 2 | Frontend por perfiles disponible (/) | HU-009 · HU-010 | 200 | 200 | 14.8 | 18.6 | OK |  |
| 3 | Login del administrador | HU-001 · RNF-05 | 200 | 200 | 299.2 | 301.3 | OK |  |
| 4 | Segunda sesión del mismo usuario rechazada | HU-003 · RNF-10 | 409 | 409 | 291.3 | 293.2 | OK |  |
| 5 | Datos del usuario en sesión (/auth/me) | HU-001 | 200 | 200 | 16.0 | 17.8 | OK |  |
| 6 | Crear sede | HU-017 · RNF-12 | 201 | 201 | 22.9 | 24.6 | OK |  |
| 7 | Crear tipo de producto | HU-019 | 201 | 201 | 17.3 | 19.0 | OK |  |
| 8 | Crear proveedor | HU-019 | 201 | 201 | 17.1 | 18.9 | OK |  |
| 9 | Crear producto (queda en todas las sedes) | HU-020 | 201 | 201 | 20.3 | 21.8 | OK |  |
| 10 | Crear mesa en la sede | HU-018 | 201 | 201 | 15.5 | 17.1 | OK |  |
| 11 | Consultar catálogo filtrado por sede | HU-020 | 200 | 200 | 14.5 | 16.4 | OK |  |
| 12 | Consultar la sede creada | HU-017 | 200 | 200 | 12.3 | 13.8 | OK |  |
| 13 | Ingreso de inventario con motivo | HU-021 · CU-15 | 201 | 201 | 16.6 | 18.2 | OK |  |
| 14 | Ingreso sin motivo rechazado | HU-021 c2 | 422 | 422 | 11.6 | 12.9 | OK |  |
| 15 | Existencia independiente por sede | HU-012 · M3 | 200 | 200 | 20.6 | 22.0 | OK |  |
| 16 | Abrir pedido en la mesa (verifica y descuenta) | HU-022 · CU-18/20 | 201 | 201 | 19.4 | 20.8 | OK |  |
| 17 | Descuento automático del inventario | HU-022 c5 · M3 | 200 | 200 | 21.0 | 22.6 | OK |  |
| 18 | La mesa queda ocupada | HU-022 c6 · M4 | 200 | 200 | 10.7 | 12.3 | OK |  |
| 19 | Misma mesa: se agrega al pedido abierto | HU-022 c3 · CU-21 | 200 | 200 | 18.6 | 20.3 | OK |  |
| 20 | Sin existencia suficiente no se registra | HU-022 c4 · M3 | 409 | 409 | 15.3 | 16.9 | OK |  |
| 21 | Trazabilidad de movimientos | HU-025 · CU-32 | 200 | 200 | 14.4 | 16.4 | OK |  |
| 22 | Alg. 4 · conciliación iterativa y recursiva | HU-021 · CU-32 | 200 | 200 | 15.6 | 17.1 | OK |  |
| 23 | Alg. 1-3 · sugerencia de compra (mochila + MCD) | HU-021 | 200 | 200 | 22.4 | 24.0 | OK |  |
| 24 | Alg. 5 · vueltas con billetes y monedas | HU-023 (prep.) | 200 | 200 | 13.5 | 15.0 | OK |  |
| 25 | Alg. 6 · ruta voraz del mesero (C y S) | HU-013 | 200 | 200 | 14.0 | 15.5 | OK |  |
| 26 | Alg. 7 · cola de la barra (lexicográfica) | HU-022 | 200 | 200 | 12.9 | 14.3 | OK |  |
| 27 | Facturar en efectivo con $50.000 | HU-023 c1-c5 | 201 | 201 | 21.8 | 23.3 | OK |  |
| 28 | La mesa vuelve a libre | HU-023 c5 | 200 | 200 | 11.1 | 12.8 | OK |  |
| 29 | Imprimir la factura | HU-023 c6 | 200 | 200 | 15.4 | 16.7 | OK |  |
| 30 | Reporte de ventas y ganancia de hoy | HU-024 c1-c6 | 200 | 200 | 13.7 | 15.1 | OK |  |
| 31 | Exportar el reporte a Excel | HU-024 c7 | 200 | 200 | 154.4 | 156.0 | OK |  |
| 32 | Ruta protegida sin token | HU-028 · C-1 | 401 | 401 | 0.3 | 1.6 | OK |  |
| 33 | Token falsificado | HU-028 · C-1 | 401 | 401 | 7.9 | 9.3 | OK |  |
| 34 | Mesero no puede crear sedes | HU-028 · C-1 | 403 | 403 | 16.0 | 17.9 | OK |  |
| 35 | Mesero no puede administrar usuarios | HU-028 · C-1 | 403 | 403 | 15.5 | 17.3 | OK |  |
| 36 | Mesero no ve el reporte de ventas | HU-024 c4 | 403 | 403 | 15.7 | 17.4 | OK |  |
| 37 | Mesero no ve las mesas de otra sede | HU-028 · C-1 | 403 | 403 | 17.1 | 18.7 | OK |  |
| 38 | Mesero ve las mesas de su sede | HU-013 · C-1 | 200 | 200 | 14.9 | 16.5 | OK |  |
| 39 | Mesero no registra ingresos de inventario | HU-021 · C-1 | 403 | 403 | 22.2 | 24.2 | OK |  |
| 40 | Mesero no toma pedidos en otra sede | HU-022 c2 | 403 | 403 | 21.3 | 23.2 | OK |  |
| 41 | Consultar la auditoría de parametrización | HU-008 · RNF-12 | 200 | 200 | 15.7 | 17.2 | OK |  |
| 42 | Consultar la auditoría de seguridad | HU-008 · RNF-12 | 200 | 200 | 15.8 | 17.6 | OK |  |
| 43 | Logout del administrador | HU-004 | 200 | 200 | 14.8 | 16.2 | OK |  |
| 44 | El token cerrado ya no sirve | HU-004 · C-4 | 401 | 401 | 7.2 | 8.8 | OK |  |
