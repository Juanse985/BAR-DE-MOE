# Integración del Sprint 2 · Bar de Moe

**Rama:** `integracion/sprint-2` (sale de `main`, commit `9e4bb1b`) · **Integró:** Juan Sebastián Rodríguez (Líder QA)
**Fuentes:** `dev/angel` (`06ef13b`), `dev/david` (`9aef831`) y `dev/felipe` (`18b47ab`).
`dev/juan` no trae cambios nuevos: es la rama del Sprint 1 y ya está en `main`.

---

## 1. Resultado

| Verificación | Resultado |
|---|---|
| Pruebas automáticas (4 componentes) | **383 en verde, 0 fallidas**: common 66 · auth 157 · parametrización 126 · gateway 34 |
| Estilo (`ruff`) | Sin errores |
| Prueba de humo por el gateway | **22/22 pasos** |
| Recorrido en navegador con los 3 perfiles | **39/39 verificaciones**, sin errores de consola, en español e inglés y en celular (390 px) |

## 2. Qué aportó cada uno

### Angel De Jesús Paniza Sierra · Líder Técnico · `dev/angel`
Cierra los criterios de aceptación de HU-001 a HU-008 en el `auth-service`:
- El intento que agota el cupo ya responde `USUARIO_BLOQUEADO`.
- Un JWT vencido no impide volver a entrar.
- Después de un cierre por inactividad, toda operación responde `SESION_EXPIRADA`.
- Los cambios de contraseña fallidos quedan en la auditoría.

Trae 41 pruebas nuevas (`test_hu001_a_hu008_criterios.py`). En el frontend agregó:
- el motivo del cierre de sesión en el login;
- "Cambiar mi contraseña";
- filtros y paginado de usuarios;
- la consulta de auditoría.

**Se fusionó sin conflictos en el backend.** Su `frontend/app.js` chocaba con el de
Felipe, así que sus pantallas se llevaron al archivo de Felipe (ver §4).

### Juan David Tovío Montes · Analista RQ · `dev/david`
Rehízo el `parametrizacion-service` según las correcciones del docente:
- **producto único** con inventario por sede;
- movimientos de inventario (HU-021);
- pedidos con líneas (HU-022);
- los cinco algoritmos de la asignatura (`app/algoritmos.py`);
- mensajes de error **en inglés** con el motivo.

Trae 43 pruebas nuevas y cierra los hallazgos H-01, H-02, H-03, H-04, H-07 y H-10.
**Se fusionó sin conflictos.** Detalle en `docs/09-sprint-2-david.md`.

### Juan Felipe Cortés Mendoza · Arquitecto · `dev/felipe`
Hizo las pantallas de **inventario por sede (HU-012)**, **mapa de mesas 3×N
(HU-013)** y **toma de pedido (HU-014)**. También rediseñó los estilos, agregó el
cambio de idioma español/inglés y creó el script `iniciar.sh`.

**Conflicto:** su rama también traía un backend propio de inventario y pedidos
(`stock` dentro de cada producto por sede, estados `ENTREGADO` y `CANCELADO`,
rutas `/inventario/{id}/ajustar` y `/pedidos/{id}/estado`). Era incompatible
con el de David en `main.py`, `models.py`, `schemas.py` y en las pruebas.

## 3. Decisión: backend de David, pantallas de Felipe

Se conservó el backend de David y se descartó el de `dev/felipe`, por tres razones:

1. **Atiende la corrección del docente.** El producto es único para todas las
   sedes y el inventario es por sede. En el modelo de Felipe, cada sede tenía
   su propia copia del producto.
2. **Es transaccional.** Verifica y descuenta la existencia en una sola transacción
   con el pedido (CU-18), y deja el histórico de movimientos (CU-32).
3. **Ya estaba acordado.** David lo dejó escrito en `docs/09-sprint-2-david.md` §6:
   "Este backend lo reemplaza; las pantallas HU-012/013/014 deben llamar a las rutas de la sección 2".

## 4. Cómo se adaptaron las pantallas

| Pantalla | Antes (`dev/felipe`) | Ahora (API de David) |
|---|---|---|
| Inventario · consultar | `GET /inventario` con `stock` del producto | `GET /inventario` (existencia, mínimo, agotado y bajo mínimo por sede) + `GET /productos` para el precio |
| Inventario · entrada | `POST /inventario/{id}/ajustar` | `POST /inventario/ingresos` con motivo obligatorio |
| Inventario · salida y ajuste exacto | `POST /inventario/{id}/ajustar` | `POST /inventario/ajustes` (la salida resta; el ajuste exacto manda la diferencia) |
| Inventario · historial *(nuevo)* | — | `GET /inventario/movimientos` (CU-32) |
| Inventario · activar/inactivar en una sede *(nuevo)* | — | `POST /inventario/sedes/{s}/productos/{p}/inactivar` · `/activar` |
| Mapa de mesas | `POST /mesas/{id}/estado` para cualquier perfil | Ocupación según `GET /pedidos?estado=ABIERTO`. Solo el administrador libera u ocupa con `PATCH /mesas/{id}`, y nunca con un pedido abierto |
| Toma de pedido | `POST /pedidos` con `items` y observaciones | `POST /pedidos` con `lineas`: abre el pedido o agrega al abierto (CU-20, CU-21) |
| Historial de pedidos | Entregar, cerrar y cancelar | Agregar productos (mesero) y **calcular vueltas** (cajero, algoritmo voraz). El cierre llega con HU-023 en el Sprint 3 |
| Productos | Una copia por sede, creada desde el navegador | Un solo producto (`POST /productos`): queda en el inventario de todas las sedes |

**Se quitaron** los respaldos en `localStorage` de `dev/felipe`: stock, mesas y
pedidos "locales" que se guardaban en el navegador cuando el servidor fallaba.
Ahora todo sale del servidor. Así, lo que ve un perfil es lo mismo que ve otro.

**Aportes de Angel en el `app.js` de Felipe**, traducidos al español y al inglés:
- motivo del cierre de sesión;
- "Cambiar mi contraseña" con confirmación;
- filtros de usuarios por sede y perfil, con paginado;
- consulta de auditoría (menú del administrador).

## 5. Lo que queda pendiente

- **El `auth-service` sigue respondiendo en español.** David menciona en `09-sprint-2-david.md` §4
  un parche `angel-auth-mensajes-en-ingles.patch` para la rama de Angel, pero no está en
  ninguna rama. Hay que pedírselo a David y aplicarlo.
- **Arquitectura.** Inventario y pedidos quedaron dentro del `parametrizacion-service`,
  no en servicios propios con `inventario_db` y `pedidos_db`, como dicen el ADR-01 y el
  documento de arquitectura v1.1. El motivo está en `09-sprint-2-david.md` §1: CU-18 exige
  una sola transacción. Para la sustentación conviene registrarlo como **ADR-08** y
  publicar la versión 1.2 del documento.
- **Sin pantalla todavía:** la sugerencia de compra (mochila, algoritmos 1 a 3) y la
  conciliación de inventario (algoritmo 4). Ya existen en la API y en Swagger.
- **Cerrar el pedido y liberar la mesa** es HU-023 (Sprint 3).
- **`docs/evidencias/`** no se regeneró: las capturas y reportes son del Sprint 1.

## 6. Cómo probarlo

El modelo de datos cambió y el proyecto aún no tiene migraciones (H-08), así que
**hay que borrar la base**:

```powershell
docker compose down -v
docker compose up -d --build
docker cp scripts/seed.py barmoe-gateway:/tmp/seed.py
docker exec barmoe-gateway python /tmp/seed.py
```

El seed crea las tres sedes, 30 mesas y 11 cervezas con **48 unidades en cada sede**.
También crea un cajero y un mesero por sede (usuarios en `08-integracion-sprint-1.md` §6).

Recorrido sugerido para la Review:

1. **Mesero `omann` (Zona T):** en *Mapa de mesas*, usa *Tomar pedido* en la mesa 1,
   agrega cervezas y confirma. La mesa pasa a ocupada y la existencia baja.
2. **Cajero `pbouvier` (Zona T):** en *Toma de pedidos*, usa *Calcular vueltas*
   con $50.000.
3. **Administrador:** en *Inventario por sede*, abre *Movimientos* del producto
   vendido y verás la venta registrada. Después, en *Auditoría*, consulta el módulo
   de parametrización.
