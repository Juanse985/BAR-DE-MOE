# Plan de ramas — Sprint 1 (semanas 1 y 2)

**Sprint Goal:** *el bar queda parametrizado y con acceso seguro por perfil.*
Módulos comprometidos: **M1 Seguridad** y **M2 Parametrización**.

El esqueleto ya está construido, probado y funcionando. Lo que sigue es que
cada quien complete su parte en su rama. Los roles definen **quién decide**, no
quién programa: los cuatro escriben código.

---

## Reparto

| Rama | Responsable | Rol | Qué le toca |
|---|---|---|---|
| `feat/auth-usuarios` | **Angel** | Líder Técnico | Completar el M1: gestión de usuarios y endurecimiento del login |
| `feat/infra-gateway` | **Felipe** | Arquitecto | Gateway, Docker, migraciones y CI |
| `feat/parametrizacion` | **David** | Analista RQ | Completar el M2 y dejar los contratos alineados con el tablero |
| `feat/calidad-trazabilidad` | **Juan** | Líder QA | Auditoría transversal, pruebas y evidencia de los RNF |

Todas salen de `develop` y vuelven a `develop` por Pull Request.

---

## `feat/auth-usuarios` — Angel (Líder Técnico)

**Archivos suyos:** `services/auth-service/`

Ya está hecho: login con bloqueo por reintentos, sesión única, inactividad,
cifrado bcrypt, CRUD básico de usuarios, cambio y restablecimiento de contraseña.

Pendiente en este sprint:

- [ ] `GET /auth/auditoria` — consulta paginada del log, solo ADMINISTRADOR.
- [ ] Paginación real en `GET /usuarios` (`?pagina=&tamano=`), hoy devuelve todo.
- [ ] `POST /usuarios/{id}/inactivar` y `/activar` como endpoints propios
      (hoy se hace por `PATCH`, que es menos explícito para el frontend).
- [ ] Límite de intentos **por IP** además de por usuario: hoy un atacante puede
      probar contraseñas contra 50 usuarios distintos sin que nada lo frene.
- [ ] Registrar en auditoría el `X-Request-Id` que llega del gateway.
- [ ] Pruebas de los endpoints nuevos.

**Decisión que le corresponde tomar:** hoy, si un usuario ya tiene sesión abierta,
el segundo login se **rechaza** (`SESION_ACTIVA`, 409). La alternativa es **cerrar
la sesión anterior** y dejar entrar al nuevo. Hay que decidirlo con el Product
Owner y dejarlo escrito en `docs/01-arquitectura.md`.

---

## `feat/infra-gateway` — Felipe (Arquitecto)

**Archivos suyos:** `gateway/`, `infra/`, `docker-compose.yml`, `.github/`

Ya está hecho: gateway con enrutamiento, validación de sesión, `/health`
agregado, docker-compose con Postgres y una BD por servicio, Dockerfiles con
healthcheck, CI que corre las pruebas.

Pendiente en este sprint:

- [ ] **Alembic para migraciones.** Hoy las tablas se crean con
      `Base.metadata.create_all()`, que sirve para arrancar pero **no versiona
      cambios**: en cuanto alguien altere una columna, la BD de los demás queda
      desincronizada. Esto es lo más urgente de la rama.
- [ ] Logging estructurado en JSON con `X-Request-Id`, para poder rastrear una
      transacción entre los tres servicios.
- [ ] Rate limiting en el gateway (al menos en `/api/auth/auth/login`).
- [ ] Cerrar CORS a los orígenes reales; hoy está abierto a `localhost`.
- [ ] `docker-compose.override.yml` para desarrollo con hot-reload.
- [ ] Sacar `JWT_SECRET` del `.env` de ejemplo y documentar cómo se genera uno
      real (`openssl rand -hex 32`).

---

## `feat/parametrizacion` — David (Analista RQ)

**Archivos suyos:** `services/parametrizacion-service/`

Ya está hecho: CRUD de sedes, mesas, tipos de producto, proveedores y productos,
con catálogo por sede, validación de margen y auditoría en cada escritura.

Pendiente en este sprint:

- [ ] `GET /productos/por-codigo/{codigo}?sede_id=` — lo va a necesitar el M4
      (toma de pedidos) del Sprint 2. Mejor dejarlo listo ahora.
- [ ] Inactivación lógica (`activo=false`) en vez de borrado, con endpoint propio.
- [ ] Carga masiva de productos desde CSV para la parametrización inicial del bar.
- [ ] Validar que no se pueda inactivar una sede que tenga mesas o productos activos.
- [ ] Documentar en `docs/05-contratos.md` el mapeo campo por campo entre el
      tablero del cliente y las tablas. Como Analista RQ, esta es la evidencia
      que sustenta que no se perdió ningún requisito.
- [ ] Pruebas de los endpoints nuevos.

---

## `feat/calidad-trazabilidad` — Juan (Líder QA)

**Archivos suyos:** `libs/common/barmoe_common/auditoria.py`, `middleware.py`,
`scripts/`, y las carpetas `tests/` de los tres componentes.

Ya está hecho: modelo de auditoría compartido, middleware que mide el SLA de 2
segundos, 37 pruebas verdes entre los tres componentes.

Pendiente en este sprint:

- [ ] **Prueba de humo end-to-end** contra el `docker compose` levantado:
      login → crear sede → crear producto → consultar → logout. Es la evidencia
      que se muestra en la Sprint Review.
- [ ] **Seed de datos del Bar de Moe** (`scripts/seed.py`): sedes, mesas,
      productos y un usuario por perfil. Sin datos no hay demo.
- [ ] Medición del RNF-02: script que ejecute N requests y falle si el p95
      supera los 2 segundos.
- [ ] **Checklist OWASP Top 10** aplicado al proyecto, con evidencia por punto.
      Va en `docs/06-owasp.md`.
- [ ] Reporte de cobertura (`pytest --cov`) y umbral mínimo acordado con el equipo.
- [ ] Consolidar el reporte de pruebas que se adjunta a la Review.

---

## Orden sugerido de trabajo

La rama de Felipe toca `docker-compose.yml` y las migraciones, que afectan a
todos. Conviene que **Alembic entre primero**, en los dos o tres primeros días,
para que Angel y David construyan sus tablas ya con migraciones y no haya que
rehacerlo. El resto puede ir en paralelo sin pisarse: cada uno trabaja en
carpetas distintas.

El único archivo que tocan varios es `libs/common/`. Si alguien necesita
cambiarlo, se avisa en el Daily antes de tocarlo.

---

## Definition of Done de cada tarea

Ninguna tarea se marca terminada sin esto:

1. `pytest` verde en el componente que tocó.
2. Endpoint documentado y visible en Swagger (`/docs`).
3. La operación queda registrada en auditoría con usuario, sede y fecha.
4. La respuesta trae `X-Tiempo-Ms` por debajo de 2000.
5. Pull Request con al menos **una revisión aprobada** de otro integrante.
6. CI en verde.
