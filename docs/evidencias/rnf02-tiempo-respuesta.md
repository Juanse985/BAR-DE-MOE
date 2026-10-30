# Evidencia · RNF-02 tiempo de respuesta (HU-026)

- **Fecha:** 2026-10-30T18:30:49
- **Plataforma:** `http://127.0.0.1:18000` · ambiente: local
- **Carga:** 50 peticiones por operación, 4 en paralelo
- **Criterio:** p95 del tiempo visto por el cliente ≤ 2000 ms y cero errores
- **Resultado:** ✅ CUMPLE

| Operación | n | Promedio (ms) | p50 (ms) | p95 (ms) | Máx (ms) | p95 servidor (ms) | SLA excedido | Errores | Cumple |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Login (bcrypt 12 rondas) | 10 | 291.6 | 288.6 | **297.4** | 297.4 | 295.5 | 0 | 0 | ✅ |
| Estado de la plataforma | 50 | 27.9 | 27.0 | **37.6** | 41.6 | 31.8 | 0 | 0 | ✅ |
| Usuario en sesión (auth/me) | 50 | 49.2 | 46.2 | **76.9** | 81.9 | 70.9 | 0 | 0 | ✅ |
| Listar sedes | 50 | 42.7 | 41.5 | **65.5** | 72.0 | 61.2 | 0 | 0 | ✅ |
| Listar mesas de la sede | 50 | 47.6 | 46.4 | **77.8** | 90.7 | 74.0 | 0 | 0 | ✅ |
| Catálogo de la sede | 50 | 44.9 | 44.6 | **66.8** | 84.6 | 62.7 | 0 | 0 | ✅ |
| Listar tipos de producto | 50 | 46.1 | 42.7 | **63.2** | 78.6 | 58.3 | 0 | 0 | ✅ |
| Listar proveedores | 50 | 47.0 | 45.4 | **72.6** | 80.5 | 66.6 | 0 | 0 | ✅ |
| Listar usuarios | 50 | 55.5 | 54.3 | **80.4** | 89.9 | 76.3 | 0 | 0 | ✅ |
| Inventario de la sede | 50 | 74.0 | 75.4 | **105.1** | 118.6 | 98.4 | 0 | 0 | ✅ |
| Pedidos abiertos de la sede | 50 | 49.8 | 47.7 | **70.2** | 79.3 | 65.5 | 0 | 0 | ✅ |
| Movimientos de inventario | 50 | 56.3 | 50.1 | **148.2** | 162.0 | 143.2 | 0 | 0 | ✅ |
| Alg. 4 · conciliación | 50 | 40.5 | 38.5 | **61.8** | 65.1 | 56.0 | 0 | 0 | ✅ |
| Alg. 1-3 · sugerencia de compra | 50 | 71.8 | 62.8 | **149.6** | 185.1 | 145.8 | 0 | 0 | ✅ |
| Alg. 6 · ruta del mesero | 50 | 47.4 | 48.7 | **66.4** | 71.3 | 60.1 | 0 | 0 | ✅ |
| Alg. 7 · cola de la barra | 50 | 54.1 | 50.9 | **80.1** | 102.4 | 73.8 | 0 | 0 | ✅ |

> El login incluye el cálculo de bcrypt con 12 rondas (RNF-08); es la operación más costosa
> a propósito, y aun así debe quedar bajo el límite.
