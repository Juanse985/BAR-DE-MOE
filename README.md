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

| Integrante | Rol | Rama |
|---|---|---|
| Angel De Jesús Paniza Sierra | Líder Técnico / Scrum Master | `feat/auth-usuarios` |
| Juan Felipe Cortés Mendoza | Arquitecto | `feat/infra-gateway` |
| Juan David Tovío Montes | Analista de Requisitos | `feat/parametrizacion` |
| Juan Sebastián Rodríguez Jiménez | Líder de QA | `feat/calidad-trazabilidad` |

Los roles definen quién decide en cada frente. **Los cuatro programan.**

## Arrancar en tres comandos

```bash
cp .env.example .env
docker compose up --build
# abrir http://localhost:8000/health
```

Usuario inicial: **`admin` / `Admin2026`** (cámbienlo antes de la demo).

## Estructura

```
bar-de-moe/
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

## Pruebas

```bash
make test
```

**37 pruebas** entre los tres componentes. Las que verifican un requisito del
tablero lo llevan en el nombre, para que la evidencia de la Sprint Review salga
directo del reporte de pytest:

```
test_rnf03_la_sesion_caduca_por_inactividad
test_rnf05_un_mesero_no_puede_administrar_usuarios
test_rnf08_la_password_se_guarda_cifrada
test_rnf09_la_cuenta_se_bloquea_tras_los_reintentos
test_rnf10_no_se_permite_una_segunda_sesion
test_rnf12_cada_accion_queda_en_la_auditoria
```

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
