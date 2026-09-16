# Reporte de pruebas · Sprint 1

Generado el 2026-09-16 06:14 con `python scripts/reporte_pruebas.py`.

## Resumen

- **Pruebas ejecutadas:** 226
- **En verde:** 215
- **Fallidas:** 0
- **Defectos abiertos documentados (xfail):** 11
- **Umbral de cobertura acordado:** 70 %
- **Veredicto:** ✅ SUITE EN VERDE

| Componente | Pruebas | Verde | Fallidas | Defectos abiertos | Cobertura |
|---|---:|---:|---:|---:|---:|
| Librería común | 52 | 52 | 0 | 0 | 98.4 % |
| auth-service (M1) | 78 | 72 | 0 | 6 | 95.9 % |
| parametrizacion-service (M2) | 70 | 67 | 0 | 3 | 96.0 % |
| API Gateway | 26 | 24 | 0 | 2 | 100.0 % |

## Cobertura por requisito

| Requisito | Pruebas en verde | Defectos abiertos |
|---|---:|---:|
| HU-025 · RNF-12 Trazabilidad | 31 | 6 |
| HU-026 · RNF-02 Tiempo de respuesta | 19 | 0 |
| HU-027 · RNF-08 Cifrado | 20 | 0 |
| HU-028 · C-1 Control de acceso | 60 | 4 |
| HU-028 · C-3 Inyección | 35 | 0 |
| HU-028 · C-4 Autenticación | 16 | 0 |
| RNF-07 Gestión de contraseñas | 2 | 0 |

## Defectos abiertos

Cada uno tiene una prueba marcada `xfail(strict=True)`: cuando se corrija, la prueba
pasará a verde y pytest obligará a quitar la marca. Detalle y responsable en
`docs/07-informe-qa-sprint-1.md`.

- DEF-02: PATCH /usuarios/{id} no deja registro en auditoría
- DEF-03: el LOGOUT se registra sin nombre de usuario ni sede
- DEF-04: al inactivar un usuario sus sesiones siguen vivas; el gateway lo deja pasar a los demás servicios
- DEF-05: el servicio no activa la auditoría de rechazos (falta auditar_rechazos=SessionLocal en crear_app)
- DEF-06: un mesero/cajero puede consultar el catálogo y las mesas de OTRA sede pasando sede_id (la sede no se valida)
- DEF-07: detrás del gateway se guarda la IP del gateway y no la del cliente (falta reenviar y usar X-Forwarded-For)
- DEF-08: el X-Request-Id del gateway no se guarda en auditoría
- DEF-09: si un servicio responde algo que no es JSON el gateway se cae con 500

## Evidencias contra la plataforma levantada

- **Prueba de humo** (2026-09-16T06:13:08): 17/17 pasos OK → ✅ aprobada · detalle en `prueba-humo.md`
- **RNF-02** (2026-09-16T06:05:37): ✅ cumple; el p95 más alto fue 297.3 ms en «Login (bcrypt 12 rondas)» · detalle en `rnf02-tiempo-respuesta.md`
