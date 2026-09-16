# Reporte de pruebas · Sprint 1

Generado el 2026-09-16 07:39 con `python scripts/reporte_pruebas.py`.

## Resumen

- **Pruebas ejecutadas:** 292
- **En verde:** 292
- **Fallidas:** 0
- **Defectos abiertos documentados (xfail):** 0
- **Umbral de cobertura acordado:** 70 %
- **Veredicto:** ✅ SUITE EN VERDE

| Componente | Pruebas | Verde | Fallidas | Defectos abiertos | Cobertura |
|---|---:|---:|---:|---:|---:|
| Librería común | 66 | 66 | 0 | 0 | 98.7 % |
| auth-service (M1) | 109 | 109 | 0 | 0 | 97.8 % |
| parametrizacion-service (M2) | 83 | 83 | 0 | 0 | 94.2 % |
| API Gateway | 34 | 34 | 0 | 0 | 99.0 % |

## Cobertura por requisito

| Requisito | Pruebas en verde | Defectos abiertos |
|---|---:|---:|
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
| HU-017 a HU-020 · Parametrización (David) | 17 | 0 |

## Defectos abiertos

Ninguno. Los defectos DEF-02 a DEF-10 del informe de QA se corrigieron al integrar el Sprint 1 y sus pruebas ya no llevan `xfail`.

## Evidencias contra la plataforma levantada

- **Prueba de humo** (2026-09-16T07:37:11): 22/22 pasos OK → ✅ aprobada · detalle en `prueba-humo.md`
- **RNF-02** (2026-09-16T07:37:22): ✅ cumple; el p95 más alto fue 290.2 ms en «Login (bcrypt 12 rondas)» · detalle en `rnf02-tiempo-respuesta.md`
- **Frontend por perfiles:** revisión en navegador con los 3 perfiles · detalle en `frontend-perfiles.md`
