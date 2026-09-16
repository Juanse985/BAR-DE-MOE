# Evidencia · prueba de humo de punta a punta

- **Fecha:** 2026-09-16T06:13:08
- **Plataforma:** `http://localhost:8000`
- **Resultado:** ✅ APROBADA
- **SLA verificado en cada paso:** 2000 ms (RNF-02)

| # | Paso | Requisito | Esperado | Obtenido | Servidor (ms) | Cliente (ms) | Estado | Nota |
|---|---|---|---|---|---:|---:|---|---|
| 1 | Plataforma disponible (/health) | Despliegue | 200 | 200 | 14.9 | 21.1 | OK |  |
| 2 | Login del administrador | HU-001 · RNF-05 | 200 | 200 | 298.3 | 300.3 | OK |  |
| 3 | Segunda sesión del mismo usuario rechazada | HU-003 · RNF-10 | 409 | 409 | 281.3 | 283.3 | OK |  |
| 4 | Datos del usuario en sesión (/auth/me) | HU-001 | 200 | 200 | 15.5 | 17.4 | OK |  |
| 5 | Crear sede | HU-017 · RNF-12 | 201 | 201 | 22.4 | 24.3 | OK |  |
| 6 | Crear tipo de producto | HU-019 | 201 | 201 | 20.2 | 22.2 | OK |  |
| 7 | Crear proveedor | HU-019 | 201 | 201 | 19.7 | 21.6 | OK |  |
| 8 | Crear producto en la sede | HU-020 | 201 | 201 | 25.6 | 27.8 | OK |  |
| 9 | Crear mesa en la sede | HU-018 | 201 | 201 | 22.7 | 24.7 | OK |  |
| 10 | Consultar catálogo filtrado por sede | HU-020 | 200 | 200 | 15.6 | 17.5 | OK |  |
| 11 | Consultar la sede creada | HU-017 | 200 | 200 | 20.3 | 22.8 | OK |  |
| 12 | Ruta protegida sin token | HU-028 · C-1 | 401 | 401 | 0.3 | 2.9 | OK |  |
| 13 | Token falsificado | HU-028 · C-1 | 401 | 401 | 4.6 | 6.5 | OK |  |
| 14 | Mesero no puede crear sedes | HU-028 · C-1 | 403 | 403 | 11.1 | 12.9 | OK |  |
| 15 | Mesero no puede administrar usuarios | HU-028 · C-1 | 403 | 403 | 10.5 | 12.1 | OK |  |
| 16 | Logout del administrador | HU-004 | 200 | 200 | 15.8 | 17.5 | OK |  |
| 17 | El token cerrado ya no sirve | HU-004 · C-4 | 401 | 401 | 5.6 | 7.2 | OK |  |
