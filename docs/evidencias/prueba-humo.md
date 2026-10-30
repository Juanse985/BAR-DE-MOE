# Evidencia · prueba de humo de punta a punta

- **Fecha:** 2026-10-30T18:30:28
- **Plataforma:** `http://127.0.0.1:18000`
- **Resultado:** ✅ APROBADA
- **SLA verificado en cada paso:** 2000 ms (RNF-02)

| # | Paso | Requisito | Esperado | Obtenido | Servidor (ms) | Cliente (ms) | Estado | Nota |
|---|---|---|---|---|---:|---:|---|---|
| 1 | Plataforma disponible (/health) | Despliegue | 200 | 200 | 33.1 | 54.2 | OK |  |
| 2 | Frontend por perfiles disponible (/) | HU-009 · HU-010 | 200 | 200 | 1.5 | 4.4 | OK |  |
| 3 | Login del administrador | HU-001 · RNF-05 | 200 | 200 | 307.9 | 310.0 | OK |  |
| 4 | Segunda sesión del mismo usuario rechazada | HU-003 · RNF-10 | 409 | 409 | 285.5 | 288.0 | OK |  |
| 5 | Datos del usuario en sesión (/auth/me) | HU-001 | 200 | 200 | 19.4 | 22.1 | OK |  |
| 6 | Crear sede | HU-017 · RNF-12 | 201 | 201 | 49.0 | 51.0 | OK |  |
| 7 | Crear tipo de producto | HU-019 | 201 | 201 | 27.5 | 29.9 | OK |  |
| 8 | Crear proveedor | HU-019 | 201 | 201 | 22.8 | 25.1 | OK |  |
| 9 | Crear producto (queda en todas las sedes) | HU-020 | 201 | 201 | 29.2 | 31.6 | OK |  |
| 10 | Crear mesa en la sede | HU-018 | 201 | 201 | 24.7 | 26.8 | OK |  |
| 11 | Consultar catálogo filtrado por sede | HU-020 | 200 | 200 | 16.9 | 22.4 | OK |  |
| 12 | Consultar la sede creada | HU-017 | 200 | 200 | 17.4 | 19.6 | OK |  |
| 13 | Ingreso de inventario con motivo | HU-021 · CU-15 | 201 | 201 | 27.8 | 30.0 | OK |  |
| 14 | Ingreso sin motivo rechazado | HU-021 c2 | 422 | 422 | 21.0 | 23.1 | OK |  |
| 15 | Existencia independiente por sede | HU-012 · M3 | 200 | 200 | 26.8 | 29.0 | OK |  |
| 16 | Abrir pedido en la mesa (verifica y descuenta) | HU-022 · CU-18/20 | 201 | 201 | 31.8 | 34.0 | OK |  |
| 17 | Descuento automático del inventario | HU-022 c5 · M3 | 200 | 200 | 36.9 | 39.1 | OK |  |
| 18 | La mesa queda ocupada | HU-022 c6 · M4 | 200 | 200 | 19.2 | 21.4 | OK |  |
| 19 | Misma mesa: se agrega al pedido abierto | HU-022 c3 · CU-21 | 200 | 200 | 28.3 | 30.4 | OK |  |
| 20 | Sin existencia suficiente no se registra | HU-022 c4 · M3 | 409 | 409 | 20.9 | 22.7 | OK |  |
| 21 | Trazabilidad de movimientos | HU-025 · CU-32 | 200 | 200 | 20.4 | 23.4 | OK |  |
| 22 | Alg. 4 · conciliación iterativa y recursiva | HU-021 · CU-32 | 200 | 200 | 19.7 | 21.7 | OK |  |
| 23 | Alg. 1-3 · sugerencia de compra (mochila + MCD) | HU-021 | 200 | 200 | 29.7 | 31.6 | OK |  |
| 24 | Alg. 5 · vueltas con billetes y monedas | HU-023 (prep.) | 200 | 200 | 19.1 | 21.1 | OK |  |
| 25 | Alg. 6 · ruta voraz del mesero (C y S) | HU-013 | 200 | 200 | 20.1 | 22.1 | OK |  |
| 26 | Alg. 7 · cola de la barra (lexicográfica) | HU-022 | 200 | 200 | 18.8 | 20.6 | OK |  |
| 27 | Ruta protegida sin token | HU-028 · C-1 | 401 | 401 | 0.3 | 1.9 | OK |  |
| 28 | Token falsificado | HU-028 · C-1 | 401 | 401 | 8.3 | 9.9 | OK |  |
| 29 | Mesero no puede crear sedes | HU-028 · C-1 | 403 | 403 | 20.4 | 22.6 | OK |  |
| 30 | Mesero no puede administrar usuarios | HU-028 · C-1 | 403 | 403 | 21.2 | 23.4 | OK |  |
| 31 | Mesero no ve las mesas de otra sede | HU-028 · C-1 | 403 | 403 | 23.4 | 25.9 | OK |  |
| 32 | Mesero ve las mesas de su sede | HU-013 · C-1 | 200 | 200 | 22.7 | 24.9 | OK |  |
| 33 | Mesero no registra ingresos de inventario | HU-021 · C-1 | 403 | 403 | 20.3 | 22.5 | OK |  |
| 34 | Mesero no toma pedidos en otra sede | HU-022 c2 | 403 | 403 | 20.9 | 22.8 | OK |  |
| 35 | Consultar la auditoría de parametrización | HU-008 · RNF-12 | 200 | 200 | 26.2 | 28.5 | OK |  |
| 36 | Consultar la auditoría de seguridad | HU-008 · RNF-12 | 200 | 200 | 21.1 | 23.4 | OK |  |
| 37 | Logout del administrador | HU-004 | 200 | 200 | 27.3 | 29.5 | OK |  |
| 38 | El token cerrado ya no sirve | HU-004 · C-4 | 401 | 401 | 13.5 | 15.9 | OK |  |
