# Arquitectura — Bar de Moe

Decisiones tomadas al inicio del Sprint 1. Cada una tiene su porqué, porque en
la sustentación van a preguntar exactamente eso.

## Panorama

```
                 ┌──────────────┐
   navegador ───▶│   GATEWAY    │  :8000  ← único puerto publicado
                 │ (FastAPI)    │
                 └──┬────────┬──┘
                    │        │
      valida sesión │        │ enruta /api/{servicio}/...
                    ▼        ▼
        ┌────────────────┐  ┌──────────────────────────┐
        │  auth-service  │  │ parametrizacion-service  │
        │      M1        │  │           M2             │
        └───────┬────────┘  └────────────┬─────────────┘
                │                        │
           auth_db              parametrizacion_db
                └────────┬───────────────┘
                    PostgreSQL 16
```

## ADR-01 · Una base de datos por microservicio

**Decisión.** Cada servicio tiene su propia base en la misma instancia de
PostgreSQL. Ningún servicio lee tablas de otro; se hablan solo por HTTP.

**Por qué.** Es el patrón *database-per-service*. Si compartiéramos una sola
base, cualquier cambio de esquema rompería a los demás y dejaríamos de tener
microservicios para tener un monolito distribuido, que es lo peor de los dos
mundos.

**Costo que aceptamos.** No hay JOIN entre servicios. Cuando el reporte del M6
necesite cruzar productos con ventas, tocará componer en el servicio de reportes
o consultar a los dos. Es el precio del aislamiento y lo asumimos a conciencia.

## ADR-02 · El gateway es el único punto expuesto

**Decisión.** Solo el gateway publica puerto al host. `auth-service` y
`parametrizacion-service` viven en la red interna de Docker, sin `ports`.

**Por qué.** Un solo sitio donde se valida la sesión, se aplica CORS y se
inyecta el `X-Request-Id`. Y ningún atacante llega directo a un microservicio.

## ADR-03 · Dónde se validan las cosas

Hay dos validaciones distintas y conviene no confundirlas:

| Qué se valida | Dónde | Por qué ahí |
|---|---|---|
| Firma y vigencia del JWT | En **cada servicio** | Defensa en profundidad: ningún servicio confía en que alguien más ya validó |
| Sesión viva, inactividad, sesión única | En el **gateway**, llamando a `auth-service` | El estado de la sesión vive en `auth_db`; replicarlo en cada servicio sería duplicar la verdad |

Por eso el gateway llama a `POST /auth/validar-sesion` en cada request
protegido. Esa llamada además **refresca la ventana de inactividad**: mientras
el usuario trabaje, su sesión sigue viva; en cuanto pase 3 minutos quieto, se
cierra sola.

## ADR-04 · Sesión única por rechazo, no por expulsión

Si un usuario ya tiene sesión abierta, el segundo login se **rechaza** con
`SESION_ACTIVA` (409). La alternativa era cerrar la sesión anterior.

Se eligió rechazar porque en un bar, dos personas usando la misma cuenta al
tiempo suele significar que se prestaron la clave — y el sistema debe hacerlo
evidente, no resolverlo en silencio. **Pendiente de confirmar con el Product
Owner** (ver `docs/02-plan-ramas-sprint-1.md`).

Se puede cambiar sin tocar código: `PERMITIR_MULTISESION=true`.

## ADR-05 · Los RNF viven en el código, no en un documento

Los requisitos transversales del tablero están implementados donde se pueden
verificar, no solo escritos:

| Requisito | Dónde está | Cómo se comprueba |
|---|---|---|
| RNF-02 · 2 segundos | `middleware.TiempoRespuestaMiddleware` | Cabecera `X-Tiempo-Ms` en toda respuesta |
| RNF-03 · inactividad 3 min | `Sesion.ultima_actividad` + gateway | `test_rnf03_la_sesion_caduca_por_inactividad` |
| RNF-05 · tres perfiles | `deps.requiere_perfil` | `test_rnf05_un_mesero_no_puede_administrar_usuarios` |
| RNF-07 · cambio de contraseña | `servicio.cambiar_password` / `restablecer_password` | Dos pruebas, una por vía |
| RNF-08 · cifrado | `security.hashear_password` (bcrypt, 12 rondas) | `test_rnf08_la_password_se_guarda_cifrada` |
| RNF-09 · bloqueo por reintentos | `servicio.login` | `test_rnf09_la_cuenta_se_bloquea_tras_los_reintentos` |
| RNF-10 · sesión única | `servicio.login` | `test_rnf10_no_se_permite_una_segunda_sesion` |
| RNF-12 · trazabilidad | `auditoria.registrar` | Dos pruebas, una por servicio |

> ADR-06 (el código habla el idioma del negocio) y ADR-07 (librería común para lo
> transversal) están en el documento de arquitectura en PDF (`docs/arquitectura/`).

## ADR-08 · Inventario y pedidos viven en `parametrizacion-service` (Sprint 2)

**Decisión.** Las tablas `inventario_sede`, `movimientos_inventario`, `pedidos` y
`pedido_lineas` se crearon en `parametrizacion_db`, y sus rutas (`/inventario`,
`/pedidos`) en `parametrizacion-service`. **No** se crearon `inventario-service` ni
`pedidos-service` con `inventario_db` y `pedidos_db`, como preveía ADR-01.

**Por qué.** CU-18 exige que registrar un producto en el pedido, verificar la
existencia y descontarla ocurra **en una sola transacción**: o queda todo o no queda
nada. Con dos servicios y dos bases eso pide una transacción distribuida (saga o
patrón *outbox*) y compensaciones. Es mucho riesgo para un sprint de dos semanas y
no lo necesita un bar con tres sedes. En una sola base, un `SELECT … FOR UPDATE`
sobre la fila de inventario y un `CHECK existencia >= 0` lo garantizan.

**Costo que aceptamos.** `parametrizacion-service` deja de ser solo configuración y
crece. Si en el futuro hay que escalar pedidos por separado, se parte el servicio:
las rutas ya están agrupadas en sus propios `APIRouter` y los algoritmos en un módulo
aparte. Las bases `inventario_db` y `pedidos_db` siguen creadas en `init.sql`, pero
están vacías. Detalle en `docs/09-sprint-2-david.md` §1.

## ADR-09 · Los algoritmos de la asignatura son funciones puras (Sprint 2)

**Decisión.** Los 7 algoritmos (mochila, MCD, existencia acumulada, vueltas, ruta
voraz del mesero y cola de la barra) están en `app/algoritmos.py`. No importan nada
de la base de datos ni de FastAPI. El endpoint consulta, les pasa listas simples y
devuelve el resultado.

**Por qué.** Así se prueban solos, contra fuerza bruta y con los ejemplos de clase,
y se explican en la sustentación sin tener que mostrar SQL. Detalle en
`docs/11-algoritmos.md`.

## Lo que este esqueleto todavía NO tiene

Dicho de frente, para que nadie se lleve una sorpresa en la Review:

- **No hay migraciones.** Las tablas se crean con `create_all()`. Sirve para
  arrancar; se rompe en cuanto alguien cambie una columna. Alembic es la primera
  tarea de la rama de Felipe.
- **No hay refresh token.** El usuario vuelve a autenticarse cuando expira.
- **No hay rate limiting** en el gateway.
- **No hay HTTPS.** En desarrollo va HTTP plano; para producción hay que poner
  un reverse proxy con TLS delante.
- **M3 y M4 (Sprint 2) quedaron dentro de `parametrizacion-service`** (ADR-08).
  M5 y M6 (facturación y reportes) todavía no existen. Sus bases ya están creadas
  en `init.sql`.
- **No se puede cerrar un pedido todavía.** Llega con la facturación (HU-023,
  Sprint 3). Al cerrarse, la mesa volverá a quedar libre.
