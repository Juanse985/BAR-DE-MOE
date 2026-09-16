# Evidencia · RNF-02 tiempo de respuesta (HU-026)

- **Fecha:** 2026-09-16T07:37:22
- **Plataforma:** `http://localhost:8000` · ambiente: integración Sprint 1 · Postgres 16 + uvicorn (sin Docker)
- **Carga:** 100 peticiones por operación, 8 en paralelo
- **Criterio:** p95 del tiempo visto por el cliente ≤ 2000 ms y cero errores
- **Resultado:** ✅ CUMPLE

| Operación | n | Promedio (ms) | p50 (ms) | p95 (ms) | Máx (ms) | p95 servidor (ms) | SLA excedido | Errores | Cumple |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Login (bcrypt 12 rondas) | 10 | 281.5 | 280.2 | **290.2** | 290.2 | 286.5 | 0 | 0 | ✅ |
| Estado de la plataforma | 100 | 36.0 | 30.4 | **67.5** | 88.3 | 58.9 | 0 | 0 | ✅ |
| Usuario en sesión (auth/me) | 100 | 74.9 | 68.2 | **136.9** | 155.6 | 127.5 | 0 | 0 | ✅ |
| Listar sedes | 100 | 60.4 | 59.6 | **84.0** | 99.2 | 74.7 | 0 | 0 | ✅ |
| Listar mesas de la sede | 100 | 63.0 | 58.2 | **105.3** | 130.0 | 96.4 | 0 | 0 | ✅ |
| Catálogo de la sede | 100 | 62.8 | 61.5 | **98.2** | 113.8 | 88.4 | 0 | 0 | ✅ |
| Listar tipos de producto | 100 | 63.5 | 64.0 | **90.1** | 96.4 | 80.5 | 0 | 0 | ✅ |
| Listar proveedores | 100 | 64.7 | 61.7 | **100.9** | 117.0 | 94.8 | 0 | 0 | ✅ |
| Listar usuarios | 100 | 86.2 | 86.5 | **122.6** | 159.1 | 116.4 | 0 | 0 | ✅ |

> El login incluye el cálculo de bcrypt con 12 rondas (RNF-08); es la operación más costosa
> a propósito, y aun así debe quedar bajo el límite.
