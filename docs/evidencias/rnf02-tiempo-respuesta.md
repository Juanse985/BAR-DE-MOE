# Evidencia · RNF-02 tiempo de respuesta (HU-026)

- **Fecha:** 2026-11-15T11:04:13
- **Plataforma:** `http://127.0.0.1:18000` · ambiente: local
- **Carga:** 50 peticiones por operación, 4 en paralelo
- **Criterio:** p95 del tiempo visto por el cliente ≤ 2000 ms y cero errores
- **Resultado:** ✅ CUMPLE

| Operación | n | Promedio (ms) | p50 (ms) | p95 (ms) | Máx (ms) | p95 servidor (ms) | SLA excedido | Errores | Cumple |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Login (bcrypt 12 rondas) | 10 | 295.0 | 293.8 | **305.9** | 305.9 | 304.2 | 0 | 0 | ✅ |
| Estado de la plataforma | 50 | 21.2 | 20.3 | **30.6** | 32.4 | 24.2 | 0 | 0 | ✅ |
| Usuario en sesión (auth/me) | 50 | 39.9 | 39.6 | **55.1** | 59.5 | 52.3 | 0 | 0 | ✅ |
| Listar sedes | 50 | 42.6 | 32.9 | **164.5** | 171.0 | 158.2 | 0 | 0 | ✅ |
| Listar mesas de la sede | 50 | 29.6 | 29.0 | **46.5** | 61.7 | 44.3 | 0 | 0 | ✅ |
| Catálogo de la sede | 50 | 35.5 | 32.9 | **54.6** | 77.7 | 51.7 | 0 | 0 | ✅ |
| Listar tipos de producto | 50 | 30.2 | 28.4 | **46.2** | 92.4 | 41.6 | 0 | 0 | ✅ |
| Listar proveedores | 50 | 31.8 | 28.0 | **49.1** | 84.0 | 44.6 | 0 | 0 | ✅ |
| Listar usuarios | 50 | 39.5 | 37.9 | **55.7** | 70.5 | 53.1 | 0 | 0 | ✅ |
| Inventario de la sede | 50 | 71.9 | 70.8 | **118.3** | 140.1 | 111.3 | 0 | 0 | ✅ |
| Pedidos abiertos de la sede | 50 | 32.5 | 31.4 | **47.3** | 76.9 | 42.6 | 0 | 0 | ✅ |
| Movimientos de inventario | 50 | 31.3 | 28.5 | **54.6** | 63.4 | 49.2 | 0 | 0 | ✅ |
| Alg. 4 · conciliación | 50 | 32.6 | 30.6 | **54.4** | 67.8 | 46.8 | 0 | 0 | ✅ |
| Alg. 1-3 · sugerencia de compra | 50 | 77.1 | 72.4 | **121.4** | 150.5 | 117.8 | 0 | 0 | ✅ |
| Alg. 6 · ruta del mesero | 50 | 33.6 | 32.1 | **53.5** | 55.9 | 49.3 | 0 | 0 | ✅ |
| Alg. 7 · cola de la barra | 50 | 33.8 | 32.9 | **50.4** | 81.8 | 46.9 | 0 | 0 | ✅ |
| Listar facturas de la sede | 50 | 45.4 | 37.6 | **125.9** | 137.5 | 111.3 | 0 | 0 | ✅ |
| Reporte de ventas (30 días) | 50 | 35.9 | 31.4 | **81.1** | 89.5 | 77.6 | 0 | 0 | ✅ |
| Reporte de ventas a Excel (30 días) | 50 | 63.8 | 63.6 | **89.2** | 93.4 | 86.5 | 0 | 0 | ✅ |
| Alg. 9 · ordenar inventario (quicksort) | 50 | 70.2 | 66.8 | **104.7** | 124.8 | 98.7 | 0 | 0 | ✅ |
| Alg. 10 · búsqueda binaria | 50 | 33.8 | 31.6 | **52.0** | 57.5 | 46.9 | 0 | 0 | ✅ |
| Alg. 12 · combo por monto (backtracking) | 50 | 62.2 | 59.2 | **101.5** | 113.9 | 95.9 | 0 | 0 | ✅ |

> El login incluye el cálculo de bcrypt con 12 rondas (RNF-08); es la operación más costosa
> a propósito, y aun así debe quedar bajo el límite.
