# Evidencia · RNF-02 tiempo de respuesta (HU-026)

- **Fecha:** 2026-09-16T06:05:37
- **Plataforma:** `http://localhost:8000` · ambiente: verificación QA · Postgres 16 + uvicorn (sin Docker)
- **Carga:** 100 peticiones por operación, 8 en paralelo
- **Criterio:** p95 del tiempo visto por el cliente ≤ 2000 ms y cero errores
- **Resultado:** ✅ CUMPLE

| Operación | n | Promedio (ms) | p50 (ms) | p95 (ms) | Máx (ms) | p95 servidor (ms) | SLA excedido | Errores | Cumple |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Login (bcrypt 12 rondas) | 10 | 285.7 | 284.1 | **297.3** | 297.3 | 290.7 | 0 | 0 | ✅ |
| Estado de la plataforma | 100 | 39.8 | 38.7 | **55.6** | 70.6 | 47.9 | 0 | 0 | ✅ |
| Usuario en sesión (auth/me) | 100 | 67.8 | 65.7 | **99.0** | 120.5 | 90.2 | 0 | 0 | ✅ |
| Listar sedes | 100 | 78.8 | 72.0 | **132.4** | 153.0 | 120.6 | 0 | 0 | ✅ |
| Listar mesas de la sede | 100 | 71.5 | 70.7 | **109.4** | 152.0 | 101.2 | 0 | 0 | ✅ |
| Catálogo de la sede | 100 | 74.4 | 67.6 | **141.7** | 190.8 | 132.4 | 0 | 0 | ✅ |
| Listar tipos de producto | 100 | 61.2 | 59.1 | **86.4** | 107.7 | 74.6 | 0 | 0 | ✅ |
| Listar proveedores | 100 | 65.2 | 62.5 | **92.2** | 107.3 | 77.2 | 0 | 0 | ✅ |
| Listar usuarios | 100 | 69.5 | 66.1 | **109.0** | 117.6 | 102.2 | 0 | 0 | ✅ |

> El login incluye el cálculo de bcrypt con 12 rondas (RNF-08); es la operación más costosa
> a propósito, y aun así debe quedar bajo el límite.
