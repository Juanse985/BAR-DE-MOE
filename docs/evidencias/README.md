# Evidencias para la Sprint Review

**Sprint vigente: 2** (M3 Inventario por sede · M4 Toma de pedidos y gestión de mesas).
Las evidencias se regeneraron el 30/10/2026 sobre la rama `integracion/sprint-2`.

| Archivo | Qué demuestra | Cómo se regenera |
|---|---|---|
| `reporte-pruebas.md` | Resultado de toda la suite (394 pruebas), cobertura por componente y por requisito | `make reporte` |
| `prueba-humo.md` / `.json` | 38 pasos por el gateway: login, parametrización, **inventario, pedido con descuento automático, mesa ocupada, sin existencia no se vende, trazabilidad, los 7 algoritmos**, permisos y logout; cada paso tarda menos de 2 s | `make humo` (plataforma levantada y seed cargado) |
| `rnf02-tiempo-respuesta.md` / `.json` | p95 bajo carga de 15 operaciones, incluidas las de inventario, pedidos y algoritmos (RNF-02 · HU-026) | `make rnf02` |
| `algoritmos.md` | Los 7 algoritmos de Diseño de Algoritmos funcionando en la plataforma, con sus pasos | `make algoritmos` |
| `frontend-sprint-2.md` + `capturas/sprint-2/` | Pantallas del Sprint 2 con los tres perfiles, en español, inglés y celular (39 verificaciones) | Recorrido en Chromium durante la integración |
| `postman-sprint-2.txt` | Corrida de la colección `docs/postman/bar-de-moe-sprint-2.postman_collection.json` con newman: 48 peticiones, 53 aserciones, 0 fallas | `npx newman run docs/postman/bar-de-moe-sprint-2.postman_collection.json` |
| `frontend-perfiles.md` + `capturas/` | Frontend del **Sprint 1** (se conserva como histórico) | — |

Se generaron con los servicios en `uvicorn` sobre SQLite. **Antes de la Review, vuelvan a
generarlas con Docker** en el portátil de la demo (PostgreSQL 16):

```bash
docker compose down -v      # base limpia: el modelo de datos cambió en el Sprint 2
make up                     # terminal 1
make evidencias             # terminal 2: seed + humo + rnf02 + algoritmos + reporte
```

En Windows sin `make`, los mismos pasos son:

```powershell
docker cp scripts/seed.py barmoe-gateway:/tmp/seed.py
docker exec barmoe-gateway python /tmp/seed.py
python scripts/prueba_humo.py --evidencia docs/evidencias
python scripts/medir_rnf02.py --evidencia docs/evidencias
python scripts/evidencia_algoritmos.py --evidencia docs/evidencias
python scripts/reporte_pruebas.py
```

> Si el administrador ya cambió su contraseña, pásenla en la variable `ADMIN_PASSWORD`
> (`$env:ADMIN_PASSWORD="..."` en PowerShell) antes de correr los scripts.
