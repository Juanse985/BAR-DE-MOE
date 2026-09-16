# Evidencias para la Sprint Review

| Archivo | Qué demuestra | Cómo se regenera |
|---|---|---|
| `reporte-pruebas.md` | Resultado de toda la suite, cobertura por componente y por requisito, defectos abiertos | `make reporte` |
| `prueba-humo.md` / `.json` | El flujo login → parametrización → permisos → logout funciona por el gateway y cada paso tarda menos de 2 s | `make humo` (con la plataforma levantada y el seed cargado) |
| `rnf02-tiempo-respuesta.md` / `.json` | p95 de las operaciones más usadas bajo carga (RNF-02 · HU-026) | `make rnf02` |

Las evidencias que hay ahora se generaron durante la verificación de QA con
PostgreSQL 16 y los servicios en `uvicorn`. **Antes de la Review, vuelvan a
generarlas con `docker compose up`** en el portátil que se va a usar en la demo:

```bash
make up            # terminal 1
make evidencias    # terminal 2
```
