# Informe de QA · Sprint 1

> **Actualización (integración).** Todos los defectos de este informe
> (DEF-01 a DEF-10) quedaron resueltos en la rama `integracion/sprint-1`, y las
> pruebas ya no llevan `xfail`. El detalle está en
> [`08-integracion-sprint-1.md`](08-integracion-sprint-1.md). Lo que sigue es
> el informe tal como se emitió antes de integrar.

**Preparado por:** Juan Sebastián Rodríguez (Líder QA) · **Rama:** `dev/juan`
**Alcance:** HU-025 a HU-028, integración de las ramas del Sprint 1 y evidencia para la Sprint Review.

---

## 1. Qué se entregó en `dev/juan`

| Tarea del plan (`docs/02-plan-ramas-sprint-1.md`) | Entregable | Estado |
|---|---|---|
| Prueba de humo end-to-end | `scripts/prueba_humo.py` · `make humo` | ✅ 17/17 pasos contra la plataforma levantada |
| Seed de datos del Bar de Moe | `scripts/seed.py` · `make seed` (ahora se puede repetir sin duplicar y crea usuarios en las dos sedes) | ✅ |
| Medición del RNF-02 (falla si p95 > 2 s) | `scripts/medir_rnf02.py` · `make rnf02` | ✅ p95 máximo ≈ 0,3 s (login) |
| Checklist OWASP con evidencia | `docs/06-owasp.md` (los 4 controles de la propuesta v2) | ✅ |
| Cobertura con umbral | `make cov` y CI con `--cov-fail-under=70` | ✅ 96–100 % por componente |
| Reporte consolidado para la Review | `scripts/reporte_pruebas.py` · `make reporte` → `docs/evidencias/reporte-pruebas.md` | ✅ |
| Auditoría transversal | `libs/common/barmoe_common/auditoria.py` y `middleware.py` | ✅ ver sección 2 |

Además:

- **Pruebas:** la suite pasó de **37 a 226** pruebas (215 en verde y 11 que
  documentan defectos abiertos). La librería común no tenía pruebas y ahora
  tiene 52.
- **CI:** también corre en las ramas `dev/**`, que son las que el equipo usa de verdad.

## 2. Cambios en `libs/common` (avisar en el Daily)

Todos son **aditivos**: no rompen a ningún servicio ni obligan a tocar su código.

1. **`auditoria.py`**
   - Nueva columna `request_id` para seguir una transacción desde el gateway.
   - Nuevas funciones:
     - `ip_cliente(request)`: usa `X-Forwarded-For` cuando existe.
     - `request_id_de(request)`.
     - `registrar_rechazo(...)`.
   - ⚠️ Una base de Postgres **ya creada** no recibe la columna nueva, porque
     `create_all` no altera tablas existentes. Mientras llega Alembic, hay que
     correr `make limpiar` o esta sentencia en `auth_db` y en `parametrizacion_db`:
     `ALTER TABLE auditoria ADD COLUMN request_id VARCHAR(64);`
2. **`middleware.py`:** nuevo `AuditoriaRechazosMiddleware`. Registra cada
   401/403 como `ACCESO_DENEGADO` con usuario, sede, IP y request id (control C-1).
3. **`app.py`:** `crear_app(..., auditar_rechazos=SessionLocal)` activa el
   middleware. Si no se pasa, todo sigue igual que antes.
4. **`security.py`:** corrección de un defecto real. Un hash bcrypt truncado
   hacía entrar en *pánico* a la librería (Rust) y el login devolvía 500. Ahora
   se valida el formato antes.

## 3. Defectos encontrados en el código de `main`

Cada defecto tiene una prueba `xfail(strict=True)`. Cuando alguien lo corrija,
esa prueba pasará a verde y pytest pedirá quitar la marca: así sabemos que el
arreglo funciona y que no vuelve a romperse.

| ID | Severidad | Defecto | Dónde se corrige | Responsable sugerido |
|---|---|---|---|---|
| DEF-02 | Media | `PATCH /usuarios/{id}` (editar o inactivar) no deja registro en auditoría → incumple RNF-12 | `services/auth-service/app/main.py` → `actualizar` | Angel |
| DEF-03 | Baja | El `LOGOUT` se audita sin nombre de usuario ni sede | `servicio.logout` | Angel |
| DEF-04 | **Alta** | Al inactivar un usuario sus sesiones siguen vivas y `validar-sesion` responde 200 → sigue operando en parametrización | `main.actualizar`: cerrar las sesiones al inactivar. **Ya viene corregido en `dev/felipe`** | Felipe (ya hecho) |
| DEF-05 | Media | Ningún servicio activa la auditoría de rechazos (C-1 exige registrarlos) | Una línea en cada `main.py`: `auditar_rechazos=SessionLocal` | Angel y David |
| DEF-06 | **Alta** | Un mesero o cajero puede ver mesas y catálogo de **otra sede** con `?sede_id=` → incumple la regla "solo su sede" de la propuesta | `parametrizacion-service/app/main.py` → forzar `sede_id` del token para perfiles distintos de ADMINISTRADOR | David |
| DEF-07 | Media | La auditoría guarda la IP del gateway, no la del cliente | Gateway: reenviar `X-Forwarded-For`. Servicios: usar `auditoria.ip_cliente(request)` | Felipe y Angel |
| DEF-08 | Baja | El `X-Request-Id` no se guarda en la auditoría | Pasar `request_id=auditoria.request_id_de(request)` al registrar | Angel y David |
| DEF-09 | Media | Si un servicio responde algo que no es JSON, el gateway lanza una excepción (500) | `gateway/app/main.py` → `proxy`: capturar `ValueError` y responder 502 | Felipe |

**Observaciones** (no bloquean el sprint; el detalle está en `docs/06-owasp.md`):

- **OBS-01:** falta HTTPS.
- **OBS-02:** el bloqueo es por usuario y no por IP.
- **OBS-03:** nada obliga al administrador a cambiar la contraseña inicial.
- **OBS-04:** el secreto JWT es de ejemplo.

## 4. Riesgo de integración: rama `dev/angel` (DEF-01 · bloqueante)

El commit `4e75f16` reescribe el `auth-service` desde cero y **no es compatible**
con el resto de la plataforma. Si se integra tal como está, se rompen el
gateway, el seed, el frontend y la parametrización.

| # | Qué cambió | Qué rompe |
|---|---|---|
| 1 | Se eliminó `POST /auth/validar-sesion` | **El gateway** lo llama en cada petición: toda ruta protegida responde 404/401. RNF-03 y RNF-10 dejan de cumplirse. |
| 2 | Perfiles `admin` / `usuario` en lugar de `ADMINISTRADOR` / `CAJERO` / `MESERO` | RNF-05 y la tabla 3.1 de la propuesta. `parametrizacion-service` exige `ADMINISTRADOR` y rechazaría a todos. |
| 3 | El usuario ya no tiene **cédula ni sede**; se agregó `email` | Los campos pactados con el cliente en M1 y la regla "solo su sede". |
| 4 | Rutas en inglés: `/users`, `/audit`, `/users/me/password` | `scripts/seed.py`, el frontend de Felipe y la convención "el código habla el idioma del tablero". |
| 5 | Ya no usa `libs/common` (tiene su propio JWT con `python-jose`, su propio `bcrypt` con `passlib`) | Se pierden `X-Tiempo-Ms` (RNF-02), `X-Request-Id`, el formato único de errores y la auditoría compartida. Los tokens firmados por `python-jose` no están probados contra `PyJWT` de los demás servicios. |
| 6 | La auditoría no guarda sede | RNF-12 / HU-025. |
| 7 | Inactividad por defecto de **1800 s** (30 min) | RNF-03 si alguien corre sin `.env`. |
| 8 | Contraseña por defecto del admin `Admin123!` | Todo el equipo y el seed usan `Admin2026`. |
| 9 | `docker-compose.yml` publica el puerto `8001` del auth-service | ADR-02: solo el gateway se expone. |
| 10 | `requirements-dev.txt` se reemplazó por dependencias de ejecución: ya no trae `pytest`, `pytest-cov`, `httpx` ni `ruff` | **El CI no puede correr las pruebas ni el estilo.** |
| 11 | `libs/common/pyproject.toml` fija `bcrypt==4.0.1` | Cambia la versión para todos los servicios sin avisarlo en el Daily. |

**Recomendación.** No hacer merge de `dev/angel` como está. La versión de
`main` ya cubre HU-001 a HU-008, con 72 pruebas en verde en el auth-service. Lo más rápido es que
Angel parta de `main` y agregue solo lo pendiente de su lista: auditoría
consultable, paginación, activar/inactivar, límite por IP y los defectos
DEF-02, DEF-03, DEF-04 y DEF-05. Esa decisión la toma el equipo en el Daily;
QA solo deja el riesgo documentado.

### Integración de prueba con `dev/david` y `dev/felipe`

Se fusionó `dev/juan` con cada rama en una copia aparte y se corrió toda la suite:

- **`dev/david`:**
  - Fusiona sin conflictos y las 70 pruebas del parametrizacion-service pasan.
  - DEF-06 sigue abierto.
- **`dev/felipe`:**
  - **Conflicto** en `libs/common/barmoe_common/auditoria.py`. Felipe solo
    cambió el estilo de los tipos, así que se conserva la versión de
    `dev/juan`, que agrega `request_id`.
  - **Corrige DEF-04:** la prueba `test_c1_inactivar_un_usuario_cierra_su_sesion`
    pasa. Al integrar, hay que quitarle la marca `xfail` (pytest lo exige con
    `strict=True`).
  - **DEF-10 (Alta, CI en rojo).** El gateway monta `StaticFiles` sobre una
    carpeta `frontend` relativa a `gateway/`. En Docker existe (`COPY frontend`),
    pero al correr las pruebas desde el repositorio no, así que `pytest` del
    gateway ni siquiera arranca: `RuntimeError: Directory '.../gateway/frontend'
    does not exist`. **Esto ya pasa en su rama, no lo causa QA.** Solución:
    montar la carpeta solo si existe
    (`if RUTA_FRONTEND.is_dir(): app.mount(...)`) o usar `check_dir=False`.

## 5. Cómo se verificó

- **Pruebas automáticas:** `make cov` con Python 3.11 y SQLite. Resultado:
  226 pruebas, 0 fallidas y cobertura ≥ 95 % en cada componente.
- **Plataforma real:** PostgreSQL 16 con los tres servicios en `uvicorn`, con
  la misma configuración del `docker-compose.yml`. Sobre ella se corrieron
  `seed` (dos veces, para comprobar que no duplica), `prueba_humo` y `medir_rnf02`
  (100 peticiones por operación, 8 en paralelo).
- **Pendiente para el equipo:** repetir `make evidencias` con `docker compose up`
  en un portátil del equipo antes de la Review. Así las evidencias quedan con
  el ambiente real de la demo.
