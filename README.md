# Bar de Moe · Sistema de Gestión Operativa Multisede

Plataforma de microservicios para la operación multisede del Bar de Moe.
Desarrollada por **DATHEON S.A.S.** — Diseño de Algoritmos, UNIMINUTO.

| | |
|---|---|
| **Sprint actual** | Sprint 1 · semanas 1 y 2 |
| **Sprint Goal** | El bar queda parametrizado y con acceso seguro por perfil |
| **Módulos** | M1 Seguridad · M2 Parametrización |
| **Stack** | FastAPI · PostgreSQL · Docker · una base de datos por servicio |

## Equipo

| Integrante | Rol | Rama | Aporte al Sprint 1 |
|---|---|---|---|
| Angel De Jesús Paniza Sierra | Líder Técnico / Scrum Master | `dev/angel` | M1: consulta de auditoría, bloqueo temporal, activar/inactivar, colección Postman |
| Juan Felipe Cortés Mendoza | Arquitecto | `dev/felipe` | Frontend por perfiles servido por el gateway |
| Juan David Tovío Montes | Analista de Requisitos | `dev/david` | M2: carga masiva CSV, producto por código, inactivación con validaciones |
| Juan Sebastián Rodríguez Jiménez | Líder de QA | `dev/juan` | Trazabilidad, pruebas, evidencias e integración |

Las cuatro ramas quedaron unidas en `integracion/sprint-1`
(detalle en [`docs/08-integracion-sprint-1.md`](docs/08-integracion-sprint-1.md)).

Los roles definen quién decide en cada frente. **Los cuatro programan.**

## Arrancar en tres comandos

```bash
cp .env.example .env
docker compose up --build
# abrir http://localhost:8000          → frontend por perfiles
# abrir http://localhost:8000/health   → estado de la plataforma
```

Usuario inicial: **`admin` / `Admin2026`** (cámbienlo antes de la demo).

## Estructura

```
bar-de-moe/
├── frontend/                      Pantallas por perfil (las sirve el gateway)
├── gateway/                       Punto de entrada único (:8000)
├── services/
│   ├── auth-service/              M1 · seguridad y usuarios
│   └── parametrizacion-service/   M2 · sedes, mesas, productos, proveedores
├── libs/common/                   Config, BD, JWT, cifrado, auditoría, middlewares
├── infra/postgres/init.sql        Una base de datos por microservicio
├── scripts/                       seed de datos e inicialización del repo
├── docs/                          Arquitectura, plan de ramas y convenciones
└── docker-compose.yml
```

## Documentación

| Documento | Para qué |
|---|---|
| [`docs/01-arquitectura.md`](docs/01-arquitectura.md) | Las decisiones y su porqué. **Léanlo antes de la sustentación.** |
| [`docs/02-plan-ramas-sprint-1.md`](docs/02-plan-ramas-sprint-1.md) | Qué le toca a cada uno en este sprint |
| [`docs/03-convenciones-git.md`](docs/03-convenciones-git.md) | Ramas, commits y Pull Requests |
| [`docs/04-guia-rapida.md`](docs/04-guia-rapida.md) | Cómo levantarlo, probarlo y resolver problemas |
| [`docs/06-owasp.md`](docs/06-owasp.md) | Los cuatro controles de seguridad de la propuesta y su evidencia |
| [`docs/07-informe-qa-sprint-1.md`](docs/07-informe-qa-sprint-1.md) | Defectos abiertos y riesgos de integración del Sprint 1 |
| [`docs/08-integracion-sprint-1.md`](docs/08-integracion-sprint-1.md) | Qué aportó cada integrante y cómo se unieron las ramas |
| [`docs/postman/`](docs/postman/) | Colección Postman de la API del Sprint 1 |
| [`docs/evidencias/`](docs/evidencias/) | Reporte de pruebas, prueba de humo y medición del RNF-02 para la Review |

## Pruebas

```bash
make test       # los cuatro componentes
make cov        # con cobertura; falla por debajo del 70 %
```

**292 pruebas** entre la librería común, los dos servicios y el gateway,
todas en verde y sin defectos abiertos. Las que
verifican un requisito del tablero lo llevan en el nombre, para que la
evidencia de la Sprint Review salga directo del reporte de pytest:

```
test_rnf03_la_sesion_caduca_por_inactividad
test_rnf08_la_password_se_guarda_cifrada
test_hu025_login_exitoso_guarda_usuario_sede_fecha_e_ip
test_c1_perfiles_no_admin_no_ejecutan_operaciones_de_administrador
test_c3_la_inyeccion_en_el_usuario_no_abre_sesion
test_c4_la_inactividad_se_cuenta_desde_la_ultima_actividad
```

### Evidencia para la Sprint Review

Con la plataforma levantada (`make up`), en otra terminal:

```bash
make evidencias   # seed + prueba de humo + medición RNF-02 + reporte consolidado
```

Todo queda en `docs/evidencias/`.

## Publicar el repositorio

```bash
# Linux / macOS
./scripts/init-repo.sh git@github.com:usuario/bar-de-moe.git

# Windows
.\scripts\init-repo.ps1 "git@github.com:usuario/bar-de-moe.git"
```

Crea `main`, `develop` y las cuatro ramas de trabajo.

> **No pongan el repositorio dentro de Google Drive.** El cliente de Drive
> sincroniza la carpeta `.git` archivo por archivo y termina corrompiéndola.
> Úsenlo en una ruta local, por ejemplo `C:\proyectos\bar-de-moe`.
