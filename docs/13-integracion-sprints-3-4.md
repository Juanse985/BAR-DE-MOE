# Integración de los Sprints 3 y 4 (versión final) · Bar de Moe

**Rama:** `integracion/sprint-3`. Sale de `main` (`ccc3388`) más los commits del 30 y 31 de
octubre que no se habían subido. **Integró:** Juan Sebastián Rodríguez (Líder QA).
**Fuentes:** `dev/david` (`05f0991`) y `dev/felipe` (`c3789e4`). `dev/angel` y `dev/juan` no
traen cambios nuevos. Los zips de la carpeta `SPRINT 3` son idénticos a esas ramas de GitHub.

---

## 1. Resultado

| Verificación | Resultado |
|---|---|
| Pruebas automáticas (4 componentes) | **514 en verde, 0 fallidas**: common 66 · auth 157 · parametrización 255 · gateway 36 |
| Cobertura | 96,6 % a 99 % por componente (umbral acordado: 70 %) |
| Estilo (`ruff`) | Sin errores |
| Prueba de humo por el gateway | **44/44 pasos**, de punta a punta: inventario → pedido → factura → mesa libre → reporte → Excel |
| Tiempo de respuesta (RNF-02) | Cumple en 22 operaciones; lo más lento es el login (0,31 s) |
| Recorrido en navegador con los 3 perfiles | **27/27 verificaciones**, sin errores de consola, en español, inglés y celular |
| Colección Postman (newman) | **75 peticiones, 99 aserciones, 0 fallas** |

Detalle en `docs/evidencias/` y en el **Informe de pruebas de los Sprints 3 y 4** (PDF).

## 2. Qué aportó cada uno

### Juan David Tovío Montes · Analista RQ · `dev/david`
- **HU-023 · Facturación (M5):** `POST /facturas` cierra el pedido, emite la factura con
  consecutivo único y registra el medio de pago (efectivo, débito o crédito). Calcula las
  vueltas con el algoritmo 5 y libera la mesa, todo en una sola transacción. También trae
  la consulta por id, por número y el listado, y la impresión HTML de 80 mm.
- **HU-024 · Reporte de ventas y ganancia (M6):** fechas en hora de Bogotá; el alcance
  depende del perfil (el cajero tiene su sede fija y el mesero no tiene acceso). La
  ganancia se calcula con el valor de compra del momento de la venta. Exporta a Excel
  las mismas filas que muestra la pantalla.
- **Algoritmos 8 a 12:** merge sort; burbuja, inserción, selección y quicksort con
  contadores; búsqueda binaria; Torres de Hanoi; backtracking. Todos están en `/algoritmos`.
- **`auth-service` en inglés:** cierra el pendiente del Sprint 2.
- **Documentación:** el ADR-08 ampliado y `docs/11-sprint-3-4-david.md`.

### Juan Felipe Cortés Mendoza · Arquitecto · `dev/felipe`
Hizo las pantallas de **facturación (HU-015)**, **consulta de facturas** y **reporte de
ventas (HU-016)**, con sus estilos.

## 3. Conflictos y cómo se resolvieron

### 3.1 `dev/david` contra lo del Sprint 2
David partió de `main`, así que no tenía los algoritmos 6 y 7 (ruta del mesero y cola
de la barra). Los dos lados agregaban código en los mismos archivos, y se conservó todo:

| Archivo | Decisión |
|---|---|
| `algoritmos.py` | Quedan **12 algoritmos**: del 1 al 7 los del Sprint 2 y del 8 al 12 los de David. Su merge sort era el «6», ahora es el **8** |
| `main.py` · `GET /algoritmos` | El catálogo lista los 12, numerados (se agregó una prueba) |
| `schemas.py`, `test_algoritmos.py` | Se suman las dos partes |
| `prueba_humo.py` | El flujo del Sprint 2 abre el pedido y el de David lo factura y lo reporta |
| `01-arquitectura.md` | Queda el ADR-08 ampliado de David y se conserva el ADR-09 (ahora con 12 algoritmos) |

### 3.2 `dev/felipe`: backend propio otra vez
Igual que en el Sprint 2, la rama de Felipe traía **su propio backend** de facturas y
reportes, y no era compatible con el de David:
- usaba una tabla `PedidoDetalle` que no existe;
- tenía propina, nombre y documento del cliente y «pago mixto», que la propuesta no pide;
- el reporte tenía una forma distinta.

**Decisión: backend de David, pantallas de Felipe.** David lo dejó acordado en su
documento (§5), y además su backend es el que tiene las pruebas de cada criterio.

Además, **la pantalla de reporte de Felipe se rompía al abrirla**, porque llamaba
funciones que no existen en ningún lado (`ensureRefs`, `loadUserDirectory`). Se
reescribió sobre la API de David, conservando su diseño.

| Pantalla | Cómo quedó |
|---|---|
| Facturación | Pedidos abiertos por cobrar → medio de pago → valor recibido (solo en efectivo) → `POST /facturas`. Muestra la factura con las vueltas y los billetes a entregar. Si el efectivo no alcanza, el botón se deshabilita |
| Impresión | Pide la tirilla de 80 mm con el token (`GET /facturas/{id}/impresion`) y abre el diálogo de impresión |
| Consulta de facturas | Por número (`0001-0000012` o `12`), sede (administrador), medio de pago y fechas |
| Reporte de ventas | Fechas, sede (el cajero la tiene fija con candado), tipo de producto, producto y orden. Muestra totales por sede, margen y el detalle con las columnas de la propuesta. Exporta a Excel con los mismos filtros |
| Menú | El administrador ahora también ve Facturación, Consulta y Reporte. El historial de pedidos tiene «Cobrar» |

**Se descartó de `dev/felipe`:**
- su backend de facturas y reportes, con sus pruebas;
- el bloque de pedidos y facturas que agregó al `seed.py`, porque usaba su API;
- los respaldos en `localStorage`.

### 3.3 Lo que faltaba frente a la propuesta (agregado por QA)
| Faltante | Qué se hizo |
|---|---|
| M6 pide filtrar el reporte por **producto** y **tipo de producto**; ninguna rama lo tenía | `producto_id` y `tipo_producto_id` en `/reportes/ventas` y en el Excel. Se agregaron 8 pruebas, entre ellas el cajero filtrando sin salir de su sede y el Excel con los mismos filtros |
| C-3 pide probar cadenas de inyección en los **filtros del reporte** | Pruebas con `1 OR 1=1`, `;DROP TABLE` y otras: se rechazan por tipo y no alteran la consulta |
| HU-032 (QA): datos del MVP para la demo | `datos_demo.py` ahora también deja **6 facturas** (efectivo, débito y crédito) emitidas por el cajero de cada sede |
| Postman y evidencias del Sprint 3 y 4 | Colección nueva, humo, RNF-02, algoritmos, capturas e informe en PDF |

## 4. Lo que queda pendiente

- **E-08 Manuales** (manual de usuario por perfil y manual técnico o de instalación) y
  **E-10 Informe de cierre** (velocidad, historias entregadas y backlog remanente). La
  propuesta los pide para el Sprint 4 y todavía no están en el repositorio.
- **Migraciones (Alembic):** las tablas nuevas de facturación las crea solo `create_all()`,
  pero un cambio a una tabla existente sigue obligando a borrar la base.
- **HTTPS y límite de peticiones en el gateway:** los pide C-2 y quedan para el despliegue.
- **Observación menor:** en la factura y en la consulta, el mesero sale con su usuario
  (`omann`) y no con su nombre, porque el cajero no puede listar usuarios.

## 5. Cómo probarlo

Las tablas de facturación son nuevas y se crean solas: **no hace falta borrar la base**.
Sí hay que reconstruir las imágenes, porque hay una dependencia nueva (`openpyxl`):

```powershell
docker compose up -d --build
docker cp scripts/seed.py barmoe-gateway:/tmp/seed.py
docker exec barmoe-gateway python /tmp/seed.py
docker cp scripts/datos_demo.py barmoe-gateway:/tmp/datos_demo.py
docker exec barmoe-gateway python /tmp/datos_demo.py
```

Recorrido sugerido para la Review:
1. **Mesero `omann` (Zona T):** toma un pedido. La mesa queda ocupada y baja la existencia.
2. **Cajero `pbouvier` (Zona T):** en *Facturación*, cobra ese pedido en efectivo con
   $100.000. Sale la factura con las vueltas y los billetes, y la mesa vuelve a libre.
   Después usa *Imprimir*.
3. **Cajero:** en *Reporte de ventas*, la sede está fija. Exporta el Excel.
4. **Administrador:** en *Reporte de ventas*, ve todas las sedes y filtra por tipo de
   producto. En *Consulta de facturas*, busca por número.
5. **Mesero:** no ve Facturación ni Reporte, y si llama la URL, el servidor responde 403.
