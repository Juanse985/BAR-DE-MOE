# Reporte de pruebas · Sprints 3 y 4 (versión final)

Generado el 2026-11-15 11:12 con `python scripts/reporte_pruebas.py`.

## Resumen

- **Pruebas ejecutadas:** 514
- **En verde:** 514
- **Fallidas:** 0
- **Defectos abiertos documentados (xfail):** 0
- **Umbral de cobertura acordado:** 70 %
- **Veredicto:** ✅ SUITE EN VERDE

| Componente | Pruebas | Verde | Fallidas | Defectos abiertos | Cobertura |
|---|---:|---:|---:|---:|---:|
| Librería común | 66 | 66 | 0 | 0 | 97.5 % |
| auth-service (M1) | 157 | 157 | 0 | 0 | 98.7 % |
| parametrizacion-service (M2 a M6) | 255 | 255 | 0 | 0 | 96.6 % |
| API Gateway | 36 | 36 | 0 | 0 | 99.0 % |

## Cobertura por requisito

| Requisito | Pruebas en verde | Defectos abiertos |
|---|---:|---:|
| Diseño de Algoritmos · los 12 algoritmos | 86 | 0 |
| HU-023 · Facturación y medio de pago (M5) | 31 | 0 |
| HU-024 · Reporte de ventas y ganancia (M6) | 27 | 0 |
| HU-001 a HU-008 · Criterios de aceptación (Angel) | 41 | 0 |
| HU-021 · Inventario por sede (M3) | 10 | 0 |
| HU-022 · Pedidos y mesas (M4) | 12 | 0 |
| Hallazgos del docente · Sprint 1 | 7 | 0 |
| HU-002 · Bloqueo por reintentos (usuario e IP) | 6 | 0 |
| HU-007 · Gestión de usuarios | 19 | 0 |
| HU-008 · Consulta de la auditoría | 15 | 0 |
| HU-009/010 · Frontend servido por el gateway | 3 | 0 |
| HU-025 · RNF-12 Trazabilidad | 42 | 0 |
| HU-026 · RNF-02 Tiempo de respuesta | 19 | 0 |
| HU-027 · RNF-08 Cifrado | 20 | 0 |
| HU-028 · C-1 Control de acceso | 74 | 0 |
| HU-028 · C-3 Inyección | 35 | 0 |
| HU-028 · C-4 Autenticación | 16 | 0 |
| RNF-07 Gestión de contraseñas | 2 | 0 |
| HU-017 a HU-020 · Parametrización (David) | 18 | 0 |

## Defectos abiertos

Ninguno. Los defectos DEF-02 a DEF-10 del informe de QA se corrigieron al integrar el Sprint 1 y sus pruebas ya no llevan `xfail`.

## Evidencias contra la plataforma levantada

- **Prueba de humo** (2026-11-15T11:03:53): 44/44 pasos OK → ✅ aprobada · detalle en `prueba-humo.md`
- **RNF-02** (2026-11-15T11:04:13): ✅ cumple; el p95 más alto fue 305.9 ms en «Login (bcrypt 12 rondas)» · detalle en `rnf02-tiempo-respuesta.md`
- **Algoritmos:** los 7 corriendo por el gateway sobre un escenario propio · detalle en `algoritmos.md`
- **Frontend por perfiles:** revisión en navegador con los 3 perfiles · detalle en `frontend-perfiles.md`
