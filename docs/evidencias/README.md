# Evidencias de pruebas (E-07)

**Sprint vigente: 3 y 4, versión final** (M5 Facturación · M6 Reportería, sobre M1 a M4).
Regeneradas el 15/11/2026 sobre la rama `integracion/sprint-3`.

| Archivo | Qué demuestra | Cómo se regenera |
|---|---|---|
| **`Informe_Pruebas_Sprint_3_4_Bar_de_Moe_v1.0.pdf`** | **Informe de QA final: consolida todo lo de esta tabla, los casos por criterio de aceptación, los controles de seguridad y los defectos** | Se arma con las evidencias de abajo |
| `reporte-pruebas.md` | Toda la suite (514 pruebas), cobertura por componente y por requisito | `make reporte` |
| `prueba-humo.md` / `.json` | 44 pasos por el gateway: login, parametrización, inventario, pedido, **factura, mesa libre, impresión, reporte y Excel**, los 12 algoritmos, permisos por perfil y logout | `make humo` |
| `rnf02-tiempo-respuesta.md` / `.json` | p95 de 22 operaciones, incluidas facturas, reporte, Excel y algoritmos (RNF-02) | `make rnf02` |
| `algoritmos.md` | Los 12 algoritmos funcionando en la plataforma, con sus pasos | `make algoritmos` |
| `frontend-sprint-3-4.md` + `capturas/sprint-3-4/` | Facturación, consulta de facturas y reporte con los tres perfiles, en español, inglés y celular, más regresión del Sprint 2 (27 verificaciones) | Recorrido en Chromium |
| `postman-sprint-3-4.txt` | Colección `docs/postman/bar-de-moe-sprint-3-4.postman_collection.json` corrida con newman: 75 peticiones, 99 aserciones, 0 fallas | `npx newman run docs/postman/bar-de-moe-sprint-3-4.postman_collection.json` |
| `Informe_Pruebas_Sprint_2_…pdf`, `frontend-sprint-2.md`, `postman-sprint-2.txt`, `capturas/sprint-2/` | Evidencias del Sprint 2 (histórico) | — |
| `frontend-perfiles.md` + `capturas/` | Evidencias del Sprint 1 (histórico) | — |

Se generaron con los servicios en `uvicorn` sobre SQLite. **Antes de la Review, vuelvan a
generarlas con Docker** en el portátil de la demo (PostgreSQL 16):

```bash
docker compose down -v      # base limpia
make up                     # terminal 1
make seed demo              # terminal 2: datos de la demo (sedes, catálogo, pedidos y facturas)
make evidencias             # humo + rnf02 + algoritmos + reporte
```

En Windows sin `make`:

```powershell
docker cp scripts/seed.py barmoe-gateway:/tmp/seed.py
docker exec barmoe-gateway python /tmp/seed.py
docker cp scripts/datos_demo.py barmoe-gateway:/tmp/datos_demo.py
docker exec barmoe-gateway python /tmp/datos_demo.py
python scripts/prueba_humo.py --evidencia docs/evidencias
python scripts/medir_rnf02.py --evidencia docs/evidencias
python scripts/evidencia_algoritmos.py --evidencia docs/evidencias
python scripts/reporte_pruebas.py
```

> Si el administrador ya cambió su contraseña, pásenla en `ADMIN_PASSWORD`
> (`$env:ADMIN_PASSWORD="..."` en PowerShell) y en Postman en la variable `admin_password`.
