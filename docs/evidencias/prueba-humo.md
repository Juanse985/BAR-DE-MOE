# Evidencia · prueba de humo de punta a punta

- **Fecha:** 2026-09-16T07:37:11
- **Plataforma:** `http://localhost:8000`
- **Resultado:** ✅ APROBADA
- **SLA verificado en cada paso:** 2000 ms (RNF-02)

| # | Paso | Requisito | Esperado | Obtenido | Servidor (ms) | Cliente (ms) | Estado | Nota |
|---|---|---|---|---|---:|---:|---|---|
| 1 | Plataforma disponible (/health) | Despliegue | 200 | 200 | 6.0 | 10.0 | OK |  |
| 2 | Frontend por perfiles disponible (/) | HU-009 · HU-010 | 200 | 200 | 5.0 | 7.0 | OK |  |
| 3 | Login del administrador | HU-001 · RNF-05 | 200 | 200 | 280.3 | 282.0 | OK |  |
| 4 | Segunda sesión del mismo usuario rechazada | HU-003 · RNF-10 | 409 | 409 | 278.5 | 280.2 | OK |  |
| 5 | Datos del usuario en sesión (/auth/me) | HU-001 | 200 | 200 | 10.9 | 12.5 | OK |  |
| 6 | Crear sede | HU-017 · RNF-12 | 201 | 201 | 15.1 | 16.5 | OK |  |
| 7 | Crear tipo de producto | HU-019 | 201 | 201 | 12.7 | 14.0 | OK |  |
| 8 | Crear proveedor | HU-019 | 201 | 201 | 12.6 | 13.9 | OK |  |
| 9 | Crear producto en la sede | HU-020 | 201 | 201 | 14.5 | 15.6 | OK |  |
| 10 | Crear mesa en la sede | HU-018 | 201 | 201 | 12.8 | 13.9 | OK |  |
| 11 | Consultar catálogo filtrado por sede | HU-020 | 200 | 200 | 10.3 | 11.4 | OK |  |
| 12 | Consultar la sede creada | HU-017 | 200 | 200 | 8.8 | 9.9 | OK |  |
| 13 | Ruta protegida sin token | HU-028 · C-1 | 401 | 401 | 0.2 | 1.1 | OK |  |
| 14 | Token falsificado | HU-028 · C-1 | 401 | 401 | 4.3 | 5.2 | OK |  |
| 15 | Mesero no puede crear sedes | HU-028 · C-1 | 403 | 403 | 12.8 | 14.2 | OK |  |
| 16 | Mesero no puede administrar usuarios | HU-028 · C-1 | 403 | 403 | 10.6 | 12.0 | OK |  |
| 17 | Mesero no ve las mesas de otra sede | HU-028 · C-1 | 403 | 403 | 12.3 | 13.8 | OK |  |
| 18 | Mesero ve las mesas de su sede | HU-013 · C-1 | 200 | 200 | 13.1 | 14.6 | OK |  |
| 19 | Consultar la auditoría de parametrización | HU-008 · RNF-12 | 200 | 200 | 15.3 | 16.8 | OK |  |
| 20 | Consultar la auditoría de seguridad | HU-008 · RNF-12 | 200 | 200 | 14.8 | 16.2 | OK |  |
| 21 | Logout del administrador | HU-004 | 200 | 200 | 12.1 | 13.3 | OK |  |
| 22 | El token cerrado ya no sirve | HU-004 · C-4 | 401 | 401 | 5.6 | 6.8 | OK |  |
