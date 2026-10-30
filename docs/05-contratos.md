# Contratos · mapeo tablero → pantalla → API → tabla

**Responsable:** Juan David Tovío Montes (Analista de Requisitos) · **Sprint:** 1 · **Versión:** 1.1 (10/10/2026 · estado de hallazgos actualizado por QA, ver 9.1)
**Alcance:** todo el proyecto integrado en `main` (commit `040d62c`): M1 Seguridad, M2 Parametrización y los requisitos transversales.

Este documento sigue cada dato que pidió el cliente en el tablero de
levantamiento hasta la columna donde queda guardado, pasando por la pantalla
y el contrato de la API. Es la evidencia de que **ningún requisito se perdió
en el camino** y, cuando algo sí se desvió, lo dice de frente (sección 9).

---

## 1. Cómo leer este documento

Cada fila de las tablas de mapeo recorre la misma cadena:

```
Tablero del cliente ─▶ Pantalla (frontend/app.js) ─▶ Campo JSON (schemas.py) ─▶ Columna (models.py)
```

| Columna de la tabla | Qué significa |
|---|---|
| **Tablero** | El dato tal como lo nombró el cliente |
| **Pantalla** | Etiqueta del campo en el frontend por perfiles |
| **API** | Nombre del campo en el JSON de entrada/salida (Pydantic) |
| **Columna** | `tabla.columna` en la base del servicio |
| **Tipo BD** | Tipo SQLAlchemy / PostgreSQL |
| **Reglas** | Validaciones: obligatoriedad, longitud, unicidad, dominio |
| **Evidencia** | Prueba automática o paso de la prueba de humo que lo verifica |

Símbolos: **E** = se envía al crear · **A** = se puede actualizar · **S** = sale en la respuesta · **—** = no aplica.

### Sobre la fuente

El tablero del cliente no está versionado en el repositorio. Los campos y
reglas de este documento se tomaron de lo que el propio código declara como
"tomado del tablero" (`auth-service/app/models.py`, `parametrizacion-service/app/models.py`,
`libs/common/barmoe_common/config.py`), de los documentos `01`, `02`, `06`, `07` y `08`,
y de las pruebas que llevan el identificador del requisito en su nombre.

Los identificadores del tablero que **no aparecen en ninguna parte del
repositorio** se listan en la sección 8.3 para confirmarlos con el Product
Owner. No se inventó su contenido.

---

## 2. Mapa general

```
                        TABLERO DEL CLIENTE
          ┌───────────────────┬──────────────────────┐
          │ M1 Seguridad      │ M2 Parametrización   │  Transversales (RNF-xx, HU-025..028)
          └─────────┬─────────┴──────────┬───────────┘
                    ▼                    ▼
             auth-service      parametrizacion-service
                    │                    │
               auth_db            parametrizacion_db
          ┌─────────┴────────┐  ┌────────┴──────────────────────────────┐
          │ usuarios         │  │ sedes ◀── mesas                        │
          │ sesiones         │  │   ▲                                    │
          │ auditoria        │  │   └── productos ──▶ tipos_producto     │
          └──────────────────┘  │             └────▶ proveedores         │
                                │ auditoria                              │
                                └────────────────────────────────────────┘
          usuarios.sede_id ····· referencia LÓGICA a sedes.id (sin FK, ADR-01)
```

| Tabla | Base | Módulo | Entidad del tablero |
|---|---|---|---|
| `usuarios` | `auth_db` | M1 | Usuario |
| `sesiones` | `auth_db` | M1 | Sesión (soporte de RNF-03 y RNF-10) |
| `auditoria` | `auth_db` y `parametrizacion_db` | Transversal | Trazabilidad (RNF-12 · HU-025) |
| `sedes` | `parametrizacion_db` | M2 | Sede |
| `mesas` | `parametrizacion_db` | M2 | Mesa |
| `tipos_producto` | `parametrizacion_db` | M2 | Tipo de producto |
| `proveedores` | `parametrizacion_db` | M2 | Proveedor |
| `productos` | `parametrizacion_db` | M2 | Producto (catálogo por sede) |

Las bases `inventario_db`, `pedidos_db`, `facturacion_db` y `reportes_db`
existen en `infra/postgres/init.sql` pero no tienen tablas: son de M3 a M6.

---

## 3. M1 · Usuario (`auth_db.usuarios`)

El docstring de `models.py` fija los siete campos del tablero: **cédula,
nombre, sede, perfil, usuario, contraseña y estado**. Los siete están.

### 3.1 Campos pedidos por el cliente

| # | Tablero | Pantalla | API | Columna | Tipo BD | E/A/S | Reglas | Evidencia |
|---|---|---|---|---|---|---|---|---|
| 1 | Cédula | Cedula | `cedula` | `usuarios.cedula` | `VARCHAR(20)` | E · — · S | Obligatoria, 5–20 caracteres, **única** (`CEDULA_DUPLICADA` 409). No se edita. | `test_c3_la_entrada_se_valida_por_tipo_y_longitud` |
| 2 | Nombre | Nombre completo | `nombre` | `usuarios.nombre` | `VARCHAR(120)` | E · A · S | Obligatorio, 3–120 caracteres | `test_hu007_el_administrador_si_puede_editar_su_nombre` |
| 3 | Sede | Sede (lista de sedes) | `sede_id` | `usuarios.sede_id` | `INTEGER NULL` | E · A · S | **Obligatoria para CAJERO y MESERO** (H-09). `NULL` = todas las sedes, solo para el administrador. Referencia lógica a `sedes.id` (ver H-05) | `test_c1_un_operario_sin_sede_no_consulta_nada`, `test_h09_no_se_crea_cajero_ni_mesero_sin_sede` |
| 4 | Perfil | Perfil | `perfil` | `usuarios.perfil` | `VARCHAR(20)` | E · A · S | Dominio cerrado: `ADMINISTRADOR`, `CAJERO`, `MESERO` (RNF-05). El administrador no se quita su propio perfil | `test_rnf05_un_mesero_no_puede_administrar_usuarios`, `test_hu007_el_administrador_no_se_quita_el_acceso_a_si_mismo` |
| 5 | Usuario | Usuario | `usuario` | `usuarios.usuario` | `VARCHAR(60)` | E · — · S | Obligatorio, 4–60 caracteres, **único** (`USUARIO_DUPLICADO` 409). No se edita | `test_c3_la_inyeccion_en_el_usuario_no_abre_sesion` |
| 6 | Contraseña | Contraseña inicial | `password` (entrada) | `usuarios.password_hash` | `VARCHAR(120)` | E · (endpoints propios) · **nunca sale** | 8–72 caracteres, al menos una mayúscula, una minúscula y un número (`PASSWORD_DEBIL` 422). Se guarda solo el hash bcrypt de 12 rondas (RNF-08) | `test_rnf08_la_password_se_guarda_cifrada`, `test_hu027_ninguna_tabla_contiene_una_password_legible`, `test_hu027_la_api_nunca_devuelve_el_hash` |
| 7 | Estado (activo/inactivo) | Estado · botón Activar/Desactivar | `estado` | `usuarios.estado` | `VARCHAR(10)` | — · A · S | Dominio `ACTIVO`/`INACTIVO`. Nace `ACTIVO`. No hay borrado físico (HU-007) | `test_hu007_inactivar_y_activar_con_endpoints_propios`, `test_hu007_no_existe_borrado_fisico_de_usuarios` |

**Por qué `password` y `password_hash` tienen nombres distintos.** El dato
del tablero es "contraseña", pero lo que se guarda no es la contraseña. El
nombre de la columna lo deja explícito para que nadie la exponga por error.
`UsuarioSalida` no tiene ningún campo de contraseña.

### 3.2 Columnas agregadas por el equipo (no son campos del tablero)

Existen para cumplir reglas del tablero, no para capturar datos nuevos del cliente.

| Columna | Tipo BD | Sale en la API | Requisito que sostiene |
|---|---|---|---|
| `usuarios.id` | `INTEGER PK` | Sí (`id`) | Identificador técnico |
| `usuarios.intentos_fallidos` | `INTEGER` | No | RNF-09 · HU-002 bloqueo tras `MAX_INTENTOS_LOGIN` (3) |
| `usuarios.bloqueado` | `BOOLEAN` | Sí (`bloqueado`) · pantalla "Bloqueado" | RNF-09 · HU-002 |
| `usuarios.bloqueado_hasta` | `TIMESTAMPTZ NULL` | No | HU-002 bloqueo temporal si `BLOQUEO_MINUTOS > 0` (aporte de Angel) |
| `usuarios.debe_cambiar_password` | `BOOLEAN` | Sí · pantalla "Cambio pendiente" | RNF-07 · cambio obligatorio tras creación o restablecimiento |
| `usuarios.creado_en` | `TIMESTAMPTZ` | Sí | Trazabilidad |
| `usuarios.actualizado_en` | `TIMESTAMPTZ` | No | Trazabilidad |

### 3.3 Operaciones sobre el usuario

| Operación del tablero | Endpoint (por el gateway: `/api/auth…`) | Perfil | Columnas que toca | Auditoría (`accion`) |
|---|---|---|---|---|
| Crear usuario (HU-007) | `POST /usuarios` | ADMINISTRADOR | todas las de 3.1; `estado=ACTIVO`, `debe_cambiar_password=true` | `CREAR_USUARIO` |
| Consultar / listar con filtros (HU-007 crit. 4) | `GET /usuarios?sede_id=&perfil=&estado=&pagina=&tamano=` · `GET /usuarios/{id}` | ADMINISTRADOR | — (total en `X-Total-Count`) | — (las consultas no se auditan) |
| Editar (HU-007) | `PATCH /usuarios/{id}` | ADMINISTRADOR | `nombre`, `sede_id`, `perfil`, `estado` | `ACTUALIZAR_USUARIO` |
| Inactivar / activar (HU-007 crit. 5) | `POST /usuarios/{id}/inactivar` · `/activar` | ADMINISTRADOR | `estado`; al inactivar cierra `sesiones` | `INACTIVAR_USUARIO` · `ACTIVAR_USUARIO` |
| Cambiar la propia contraseña (HU-005 · RNF-07) | `POST /auth/cambiar-password` | Cualquiera | `password_hash`, `debe_cambiar_password=false` | `CAMBIO_PASSWORD` |
| Restablecer contraseña (HU-006 · RNF-07) | `POST /usuarios/{id}/restablecer-password` | ADMINISTRADOR | `password_hash`, `debe_cambiar_password=true`, limpia bloqueo, cierra `sesiones` | `RESTABLECER_PASSWORD` |
| Desbloquear (HU-002 crit. 4) | `POST /usuarios/{id}/desbloquear` | ADMINISTRADOR | `bloqueado`, `bloqueado_hasta`, `intentos_fallidos` | `DESBLOQUEAR_USUARIO` |
| Ver mis datos (HU-001) | `GET /auth/me` | Cualquiera | — | — |

---

## 4. M1 · Autenticación y sesión (`auth_db.sesiones`)

La sesión no es un dato que capture el cliente: es la tabla que hace
verificables tres reglas del tablero.

### 4.1 Contrato de login (HU-001)

| Tablero | Pantalla | API entrada | Validación contra | API salida |
|---|---|---|---|---|
| Usuario | Usuario | `usuario` | `usuarios.usuario` | `usuario` (objeto `UsuarioSalida`) |
| Contraseña | Contraseña | `password` | `usuarios.password_hash` (bcrypt) | — |
| — | — | — | — | `access_token`, `token_type`, `expira_en`, `inactividad_segundos` |

El JWT lleva `sub` (= `usuarios.id`), `usr`, `perfil`, `sede_id` y `jti`
(= `sesiones.jti`). Es lo que usan los demás servicios para aplicar perfil y sede.

Respuestas de error del login y su regla del tablero:

| Código | HTTP | Regla | Columna que lo decide |
|---|---|---|---|
| `CREDENCIALES_INVALIDAS` | 401 | Mensaje genérico, no revela si el usuario existe (C-4) | `usuarios.usuario`, `password_hash` |
| `USUARIO_BLOQUEADO` | 423 | RNF-09 · HU-002 | `usuarios.bloqueado`, `bloqueado_hasta` |
| `USUARIO_INACTIVO` | 403 | HU-007 | `usuarios.estado` |
| `SESION_ACTIVA` | 409 | RNF-10 · HU-003 (sesión única por rechazo, ADR-04) | `sesiones.activa` |
| `DEMASIADOS_INTENTOS` | 429 | OBS-02 · límite por IP | `auditoria.ip`, `resultado='FALLIDO'` |

### 4.2 Tabla `sesiones`

| Columna | Tipo BD | Requisito | Cómo se usa |
|---|---|---|---|
| `jti` | `VARCHAR(40) PK` | RNF-10 | Una fila por token emitido; el `jti` del JWT apunta aquí |
| `usuario_id` | `INTEGER FK → usuarios.id` | RNF-10 | Dueño de la sesión |
| `activa` | `BOOLEAN` | RNF-10 · HU-003 | No puede haber dos filas activas del mismo usuario |
| `creada_en` | `TIMESTAMPTZ` | RNF-12 | Momento del login |
| `ultima_actividad` | `TIMESTAMPTZ` | RNF-03 · HU-004 | Se refresca en cada `POST /auth/validar-sesion` del gateway; más de 180 s sin actividad cierra la sesión |
| `cerrada_en` | `TIMESTAMPTZ NULL` | RNF-12 | Momento del cierre |
| `motivo_cierre` | `VARCHAR(30) NULL` | RNF-03 · HU-004 | `LOGOUT`, `INACTIVIDAD`, `USUARIO_INACTIVO`, `RESTABLECIMIENTO` |
| `ip` | `VARCHAR(45) NULL` | HU-025 | IP real del cliente al abrir la sesión |

Evidencia: `test_rnf03_la_sesion_caduca_por_inactividad`,
`test_c4_la_inactividad_se_cuenta_desde_la_ultima_actividad`,
`test_rnf10_no_se_permite_una_segunda_sesion`,
`test_c4_despues_del_logout_el_token_no_sirve`,
`test_c1_inactivar_un_usuario_cierra_su_sesion`; prueba de humo pasos 4, 21 y 22.

### 4.3 Parámetros del tablero que viven en configuración

| Requisito | Variable | Valor | Dónde |
|---|---|---|---|
| RNF-02 · 2 s por transacción | `SLA_SEGUNDOS` | `2.0` | `libs/common/barmoe_common/config.py` |
| RNF-03 · inactividad 3 min | `INACTIVIDAD_SEGUNDOS` | `180` | ídem |
| RNF-09 · reintentos | `MAX_INTENTOS_LOGIN` | `3` | ídem |
| RNF-10 · sesión única | `PERMITIR_MULTISESION` | `false` | ídem |
| HU-002 · duración del bloqueo | `BLOQUEO_MINUTOS` | `0` (hasta que el admin desbloquee) | `services/auth-service/app/config.py` |
| OBS-02 · límite por IP | `MAX_INTENTOS_POR_IP` / `VENTANA_IP_MINUTOS` | `10` / `15` | ídem |

---

## 5. M2 · Parametrización (`parametrizacion_db`)

Reglas comunes a todas las entidades del M2:

- **Escritura:** solo `ADMINISTRADOR` (C-1). CAJERO y MESERO reciben 403 `SIN_PERMISOS`.
- **Lectura:** cualquier perfil autenticado; CAJERO y MESERO quedan forzados a
  la sede de su token (`SEDE_NO_AUTORIZADA` 403 si piden otra).
- **Sin borrado físico:** se inactiva con `activa`/`activo`.
- **Auditoría:** cada escritura deja `CREAR`, `ACTUALIZAR`, `ACTIVAR` o
  `INACTIVAR` con usuario, sede, IP y `request_id`.

### 5.1 Sede (`sedes`) · HU-017

| Tablero | Pantalla | API | Columna | Tipo BD | E/A/S | Reglas | Evidencia |
|---|---|---|---|---|---|---|---|
| Nombre de la sede | Nombre | `nombre` | `sedes.nombre` | `VARCHAR(120)` | E · A · S | Obligatorio, 3–120, **único** (`SEDE_DUPLICADA` 409 al crear; ver H-03 al editar) | `test_no_se_repite_el_nombre_de_sede` |
| Dirección | Direccion | `direccion` | `sedes.direccion` | `VARCHAR(200) NULL` | E · A · S | Opcional, hasta 200 | `test_se_crea_y_se_lista_una_sede` |
| Teléfono | Telefono | `telefono` | `sedes.telefono` | `VARCHAR(30) NULL` | E · A · S | Opcional, hasta 30 | ídem |
| Estado | Estado · Activar/Inactivar | `activa` | `sedes.activa` | `BOOLEAN` | — · A · S | Nace `true`. No se inactiva con mesas o productos activos (`SEDE_CON_RECURSOS_ACTIVOS` 409) | `test_no_se_inactiva_una_sede_con_productos_activos` |
| — | — | `id` | `sedes.id` | `INTEGER PK` | — · — · S | Técnico | — |
| — | — | — | `sedes.creada_en` | `TIMESTAMPTZ` | — | Técnico, no sale en la API | — |

Endpoints: `POST /sedes` · `GET /sedes?solo_activas=` · `GET /sedes/{id}` · `PATCH /sedes/{id}`.

### 5.2 Mesa (`mesas`) · HU-018 · HU-013

| Tablero | Pantalla | API | Columna | Tipo BD | E/A/S | Reglas | Evidencia |
|---|---|---|---|---|---|---|---|
| Sede de la mesa | Sede (lista; en gris al editar) | `sede_id` | `mesas.sede_id` | `INTEGER FK → sedes.id` | E · — · S | Obligatoria y debe existir (404) | `test_no_se_crea_una_mesa_en_una_sede_inexistente` |
| Número de mesa | Numero (en gris al editar) | `numero` | `mesas.numero` | `INTEGER` | E · — · S | > 0; **único por sede** (`uq_mesa_por_sede`, `MESA_DUPLICADA` 409) | `test_la_mesa_nace_libre_y_no_se_repite_en_la_sede` |
| Capacidad | Capacidad | `capacidad` | `mesas.capacidad` | `INTEGER` | E · A · S | 1–30, por defecto 4 | ídem |
| Estado (libre/ocupada) | — (solo lectura) | `estado` | `mesas.estado` | `VARCHAR(10)` | — · A · S | Dominio `LIBRE`/`OCUPADA`, nace `LIBRE`. Las transiciones automáticas son de M4 (Sprint 2) | `test_c3_el_filtro_de_estado_de_mesa_no_se_puede_inyectar` |
| Activa | Estado · Activar/Inactivar | `activa` | `mesas.activa` | `BOOLEAN` | — · A · S | Nace `true` | — |
| — | — | `id` | `mesas.id` | `INTEGER PK` | — · — · S | Técnico | — |

Endpoints: `POST /mesas` · `GET /mesas?sede_id=&estado=` · `PATCH /mesas/{id}`.
HU-013 (el mesero ve las mesas de su sede): prueba de humo paso 18 y
`test_c1_sin_filtro_el_operario_solo_recibe_su_sede`.

### 5.3 Tipo de producto (`tipos_producto`) · HU-019 · HU-011

| Tablero | Pantalla | API | Columna | Tipo BD | E/A/S | Reglas | Evidencia |
|---|---|---|---|---|---|---|---|
| Nombre del tipo | Nombre | `nombre` | `tipos_producto.nombre` | `VARCHAR(80)` | E · A · S | Obligatorio, 2–80, **único** (`TIPO_DUPLICADO` 409 al crear; ver H-03 al editar) | prueba de humo paso 7 |
| Descripción | Descripcion | `descripcion` | `tipos_producto.descripcion` | `VARCHAR(200) NULL` | E · A · S | Opcional | — |
| Estado | Estado | `activo` | `tipos_producto.activo` | `BOOLEAN` | — · A · S | No se inactiva con productos activos (`TIPO_CON_PRODUCTOS_ACTIVOS` 409) | — |
| — | — | `id` | `tipos_producto.id` | `INTEGER PK` | — · — · S | Técnico | — |

Endpoints: `POST /tipos-producto` · `GET /tipos-producto` · `PATCH /tipos-producto/{id}`.

### 5.4 Proveedor (`proveedores`) · HU-019

| Tablero | Pantalla | API | Columna | Tipo BD | E/A/S | Reglas | Evidencia |
|---|---|---|---|---|---|---|---|
| NIT | NIT (en gris al editar) | `nit` | `proveedores.nit` | `VARCHAR(20)` | E · — · S | Obligatorio, 5–20, **único** (`PROVEEDOR_DUPLICADO` 409). No se edita | prueba de humo paso 8 |
| Razón social / nombre | Nombre | `nombre` | `proveedores.nombre` | `VARCHAR(120)` | E · A · S | Obligatorio, 3–120 | ídem |
| Contacto | Contacto | `contacto` | `proveedores.contacto` | `VARCHAR(120) NULL` | E · A · S | Opcional | — |
| Teléfono | Telefono | `telefono` | `proveedores.telefono` | `VARCHAR(30) NULL` | E · A · S | Opcional | — |
| Estado | Estado | `activo` | `proveedores.activo` | `BOOLEAN` | — · A · S | No se inactiva con productos activos (`PROVEEDOR_CON_PRODUCTOS_ACTIVOS` 409) | — |
| — | — | `id` | `proveedores.id` | `INTEGER PK` | — · — · S | Técnico | — |

Endpoints: `POST /proveedores` · `GET /proveedores` · `PATCH /proveedores/{id}`.

### 5.5 Producto (`productos`) · HU-020

El tablero pide el catálogo **por sede**: el mismo código puede existir en
varias sedes, pero no dos veces en la misma (`uq_producto_por_sede`).

| Tablero | Pantalla | API | Columna | Tipo BD | E/A/S | Reglas | Evidencia |
|---|---|---|---|---|---|---|---|
| Código | Codigo (en gris al editar) | `codigo` | `productos.codigo` | `VARCHAR(30)` | E · — · S | Obligatorio, 2–30; **único por sede** (`PRODUCTO_DUPLICADO` 409). No se edita | `test_el_catalogo_se_gestiona_por_sede` |
| Nombre | Nombre | `nombre` | `productos.nombre` | `VARCHAR(120)` | E · A · S | Obligatorio, 3–120 | `test_se_crea_un_producto_con_sus_relaciones` |
| Sede | Sede (lista; en gris al editar) | `sede_id` | `productos.sede_id` | `INTEGER FK → sedes.id` | E · — · S | Obligatoria y debe existir (404). No se edita | `test_los_productos_se_filtran_por_sede` |
| Tipo de producto | Tipo (lista) | `tipo_producto_id` | `productos.tipo_producto_id` | `INTEGER FK → tipos_producto.id` | E · A · S | Debe existir al crear (404); ver H-02 al editar | `test_se_crea_un_producto_con_sus_relaciones` |
| Proveedor | Proveedor (lista) | `proveedor_id` | `productos.proveedor_id` | `INTEGER FK → proveedores.id` | E · A · S | Debe existir al crear (404); ver H-02 al editar | ídem |
| Valor de compra | Valor compra | `valor_compra` | `productos.valor_compra` | `NUMERIC(12,2)` | E · A · S | ≥ 0 | `test_c3_un_valor_de_venta_negativo_o_de_texto_no_entra` |
| Valor de venta | Valor venta | `valor_venta` | `productos.valor_venta` | `NUMERIC(12,2)` | E · A · S | ≥ 0 y **≥ `valor_compra`** (422 al crear, `MARGEN_NEGATIVO` 422 al editar). Lo necesita M6 para calcular la ganancia | `test_el_valor_de_venta_no_puede_ser_menor_que_el_de_compra` |
| Estado | Estado · Activar/Inactivar | `activo` | `productos.activo` | `BOOLEAN` | — · (endpoints propios) · S | `PRODUCTO_YA_INACTIVO` / `PRODUCTO_YA_ACTIVO` 409 | `test_inactivar_y_activar_producto` |
| — | — | `id` | `productos.id` | `INTEGER PK` | — · — · S | Técnico | — |
| — | — | — | `productos.creado_en` | `TIMESTAMPTZ` | — | Técnico, no sale en la API | — |

Endpoints: `POST /productos` · `GET /productos?sede_id=&tipo_producto_id=&solo_activos=` ·
`GET /productos/{id}` · `GET /productos/por-codigo/{codigo}?sede_id=` (lo consume M4) ·
`PATCH /productos/{id}` · `POST /productos/{id}/inactivar` · `/activar`.

`valor_compra` y `valor_venta` viajan como texto decimal (`"2500.00"`) en la
respuesta: así no se pierde precisión entre Python, JSON y PostgreSQL.

### 5.6 Carga masiva de productos (CSV)

`POST /productos/carga-masiva?sede_id=` · solo ADMINISTRADOR · archivo `.csv` en UTF-8 (con o sin BOM).

| Columna del CSV | Campo API equivalente | Columna BD | Obligatoria |
|---|---|---|---|
| `codigo` | `codigo` | `productos.codigo` | Sí |
| `nombre` | `nombre` | `productos.nombre` | Sí |
| `tipo_producto_id` | `tipo_producto_id` | `productos.tipo_producto_id` | Sí |
| `proveedor_id` | `proveedor_id` | `productos.proveedor_id` | Sí |
| `valor_compra` | `valor_compra` | `productos.valor_compra` | Sí |
| `valor_venta` | `valor_venta` | `productos.valor_venta` | Sí |
| *(parámetro `sede_id`)* | `sede_id` | `productos.sede_id` | Sí, en la URL |

Cada fila pasa por las mismas validaciones de `ProductoCrear` y se confirma
por separado: una fila mala no tumba las buenas. Respuesta:
`{"creados": n, "errores": [{"fila": 3, "mensaje": "..."}]}` (la fila 1 es el
encabezado). Cada fila creada se audita con `detalle="carga_masiva"`.
Evidencia: `test_carga_masiva_de_productos`, `test_carga_masiva_reporta_errores_de_fila`.

---

## 6. Transversal · Auditoría (`auditoria`) · RNF-12 · HU-025 · HU-008

La misma tabla existe en `auth_db` y en `parametrizacion_db` (modelo común en
`libs/common/barmoe_common/auditoria.py`). El tablero exige **quién, en qué
sede y cuándo**; el equipo agregó lo necesario para rastrear y para el control C-1.

| Requisito del tablero | Columna | Tipo BD | Origen del dato |
|---|---|---|---|
| Cuándo | `fecha` | `TIMESTAMPTZ` | Servidor, en UTC |
| Quién | `usuario_id`, `usuario` | `INTEGER NULL`, `VARCHAR(60) NULL` | Token JWT (o `sistema` en el arranque) |
| En qué sede | `sede_id` | `INTEGER NULL` | Token JWT (`NULL` para el administrador general) |
| Qué hizo | `accion` | `VARCHAR(60)` | `LOGIN`, `LOGOUT`, `CREAR`, `ACTUALIZAR`, `CREAR_USUARIO`, `ACCESO_DENEGADO`… |
| Sobre qué | `entidad`, `entidad_id` | `VARCHAR(60) NULL` ×2 | Tabla y id afectados |
| Con qué resultado | `resultado` | `VARCHAR(20)` | `OK`, `FALLIDO`, `BLOQUEADO`, `INACTIVO`, `RECHAZADO` |
| Desde dónde (agregado) | `ip` | `VARCHAR(45) NULL` | `X-Forwarded-For` que pone el gateway (DEF-07) |
| Rastreo entre servicios (agregado) | `request_id` | `VARCHAR(64) NULL` | `X-Request-Id` del gateway (DEF-08) |
| Detalle (agregado) | `detalle` | `TEXT NULL` | Campos cambiados o motivo del fallo. **Nunca contraseñas** |

Consulta (HU-008): `GET /auditoria?usuario_id=&usuario=&sede_id=&accion=&resultado=&desde=&hasta=&pagina=&tamano=`
en cada servicio, solo ADMINISTRADOR, del más reciente al más antiguo, total en
`X-Total-Count` y **sin** rutas para modificar o borrar.

Evidencia: `test_hu025_el_registro_trae_usuario_sede_y_fecha`,
`test_hu025_crear_cada_entidad_deja_su_registro`,
`test_hu025_ninguna_fila_de_auditoria_guarda_passwords`,
`test_hu008_la_auditoria_no_se_puede_modificar_ni_borrar`; prueba de humo pasos 19 y 20.

---

## 7. Relaciones entre servicios

Por ADR-01 (una base por servicio) no hay llaves foráneas entre `auth_db` y
`parametrizacion_db`. Las referencias cruzadas son lógicas:

| Campo | Apunta a | Cómo se garantiza hoy |
|---|---|---|
| `usuarios.sede_id` | `parametrizacion_db.sedes.id` | **No se valida** al crear ni al editar (H-05) |
| JWT `sede_id` | `sedes.id` | Lo usa el parametrizacion-service para forzar la sede de CAJERO y MESERO |
| `auditoria.sede_id` (ambas bases) | `sedes.id` | Copia del token; es histórico, no necesita integridad referencial |

---

## 8. Matriz de trazabilidad inversa (requisito → contrato)

Lectura para la Review: cada requisito del tablero y dónde quedó.

### 8.1 Historias de usuario

| ID | Requisito (según el repositorio) | Tabla(s) · columna(s) | Endpoint(s) | Estado |
|---|---|---|---|---|
| HU-001 | Ingreso al sistema | `usuarios.usuario`, `password_hash`; `sesiones` | `POST /auth/login`, `GET /auth/me` | ✅ |
| HU-002 | Bloqueo por intentos fallidos | `usuarios.intentos_fallidos`, `bloqueado`, `bloqueado_hasta` | `POST /auth/login`, `POST /usuarios/{id}/desbloquear` | ✅ |
| HU-003 | Sesión única | `sesiones.activa` | `POST /auth/login` (409) | ✅ |
| HU-004 | Cierre de sesión e inactividad | `sesiones.ultima_actividad`, `cerrada_en`, `motivo_cierre` | `POST /auth/logout`, `POST /auth/validar-sesion` | ✅ |
| HU-005 | Cambio de la propia contraseña | `usuarios.password_hash`, `debe_cambiar_password` | `POST /auth/cambiar-password` | ✅ |
| HU-006 | Restablecimiento por el administrador | `usuarios.password_hash`, `debe_cambiar_password`; `sesiones` | `POST /usuarios/{id}/restablecer-password` | ✅ |
| HU-007 | Gestión de usuarios | `usuarios` (sección 3) | `/usuarios` | ✅ |
| HU-008 | Consulta de auditoría | `auditoria` (ambas bases) | `GET /auditoria` | ✅ |
| HU-009 · HU-010 | Frontend por perfiles | — (menú según `perfil`) | `GET /` (gateway) | ✅ |
| HU-011 | Menú del administrador (incluye Tipos de producto) | — | `GET /` | ✅ |
| HU-013 | El mesero ve las mesas de su sede | `mesas.sede_id` + JWT `sede_id` | `GET /mesas` | ✅ |
| HU-017 | Sedes | `sedes` | `/sedes` | ✅ |
| HU-018 | Mesas | `mesas` | `/mesas` | ✅ |
| HU-019 | Tipos de producto y proveedores | `tipos_producto`, `proveedores` | `/tipos-producto`, `/proveedores` | ✅ |
| HU-020 | Productos (catálogo por sede) | `productos` | `/productos` | ✅ (con H-02) |
| HU-025 | Trazabilidad | `auditoria` | todas las escrituras | ✅ |
| HU-026 | Tiempo de respuesta | — (cabecera `X-Tiempo-Ms`) | todas | ✅ |
| HU-027 | Cifrado de contraseñas | `usuarios.password_hash` | — | ✅ |
| HU-028 | Seguridad verificable (OWASP C-1 a C-4) | `auditoria` (rechazos), `usuarios`, `sesiones` | todas | ✅ (C-2 parcial por HTTPS) |

### 8.2 Requisitos no funcionales

| ID | Requisito | Dónde quedó en datos o contrato | Evidencia |
|---|---|---|---|
| RNF-01 | Uso desde el celular (según `docs/evidencias/frontend-perfiles.md`) | Frontend responsive | "login sin scroll horizontal en celular" |
| RNF-02 | 2 s por transacción | Cabecera `X-Tiempo-Ms`; `SLA_SEGUNDOS=2.0` | `test_rnf02_*`, `scripts/medir_rnf02.py` |
| RNF-03 | Inactividad de 3 minutos | `sesiones.ultima_actividad`; `INACTIVIDAD_SEGUNDOS=180` | `test_rnf03_la_sesion_caduca_por_inactividad` |
| RNF-05 | Tres perfiles | `usuarios.perfil` ∈ {ADMINISTRADOR, CAJERO, MESERO} | `test_rnf05_un_mesero_no_puede_administrar_usuarios` |
| RNF-07 | Cambio de contraseña (usuario y admin) | `usuarios.password_hash`, `debe_cambiar_password` | `test_rnf07_*` |
| RNF-08 | Contraseñas cifradas | `usuarios.password_hash` (bcrypt, 12 rondas) | `test_rnf08_*` |
| RNF-09 | Bloqueo por reintentos | `usuarios.intentos_fallidos`, `bloqueado`; `MAX_INTENTOS_LOGIN=3` | `test_rnf09_la_cuenta_se_bloquea_tras_los_reintentos` |
| RNF-10 | Sesión única | `sesiones.activa`; `PERMITIR_MULTISESION=false` | `test_rnf10_no_se_permite_una_segunda_sesion` |
| RNF-11 | Seguridad OWASP | Ver `docs/06-owasp.md` | `test_c1_*` a `test_c4_*` |
| RNF-12 | Trazabilidad | `auditoria` en ambas bases | `test_rnf12_*`, `test_hu025_*` |

### 8.3 Identificadores sin rastro en el repositorio

Estos IDs no aparecen en código, pruebas ni documentos. Pueden ser de M3–M6
(sprints siguientes) o requisitos que nadie tomó. **Hay que confirmarlos
contra el tablero antes de la Review**, porque son justo el tipo de requisito
que se pierde sin que nadie lo note:

- HU-012, HU-014, HU-015, HU-016
- HU-021, HU-022, HU-023, HU-024
- RNF-04, RNF-06

Acción: el Analista RQ completa esta lista con el texto del tablero y marca
cada uno como "Sprint 1 (falta)", "Sprint 2+" o "descartado con el PO".

---

## 9. Hallazgos del mapeo

Encontrados al cruzar pantalla, contrato y tabla. Los H-01 a H-04 se
reprodujeron con el `TestClient` del parametrizacion-service sobre el código
de `main`.

| ID | Severidad | Hallazgo | Efecto | Propuesta |
|---|---|---|---|---|
| **H-01** | Media | La pantalla de edición muestra como editables campos que el contrato de actualización no acepta: `sede_id` y `numero` de mesa, `nit` de proveedor, `codigo` y `sede_id` de producto. Pydantic los **ignora en silencio**: `PATCH /mesas/1 {"numero": 9}` responde 200 y la mesa sigue siendo la 1 | El administrador cree que cambió el dato y no cambió | Backend: `model_config = ConfigDict(extra="forbid")` en los `*Actualizar` para que respondan 422. Frontend: campos de solo lectura al editar |
| **H-02** | Media | `PATCH /productos/{id}` no valida que el nuevo `tipo_producto_id` o `proveedor_id` exista. Con `tipo_producto_id=999` responde 200 en SQLite; en PostgreSQL la llave foránea lo rechaza con **500** | Error sin formato estándar en producción | Reusar `obtener_o_404` para ambos campos antes de aplicar cambios |
| **H-03** | Media | Editar `sedes.nombre` o `tipos_producto.nombre` a uno ya existente lanza `IntegrityError` (500). La unicidad solo se valida al crear | Error 500 en vez de `SEDE_DUPLICADA` / `TIPO_DUPLICADO` 409 | Validar el duplicado también en el `PATCH` |
| **H-04** | Baja | Se puede crear o reasignar un producto a un tipo o proveedor **inactivo** (201) | El catálogo activo puede apuntar a maestros inactivos | Confirmar con el PO; si aplica, rechazar con 409 |
| **H-05** | Media | `usuarios.sede_id` no se valida contra `sedes` (bases distintas, ADR-01). Se puede crear un cajero en la sede 999; al consultar, verá listas vacías sin ningún error | Usuario mal configurado difícil de detectar | Que el auth-service consulte `GET /sedes/{id}` por HTTP al crear/editar, o validar en el frontend con un selector de sedes |
| **H-06** | Baja | Inactivar una sede solo revisa mesas y productos, no usuarios asignados (están en otra base) | Usuarios activos en una sede inactiva | Documentar la regla con el PO; resolver junto con H-05 |
| **H-07** | Info | El tablero pide mesa LIBRE/OCUPADA; hoy el estado solo lo cambia el administrador por `PATCH`. Las transiciones al abrir y cerrar pedidos son de M4 | Ninguno en Sprint 1 | Tomar en Sprint 2 |
| **H-08** | Info | Sin migraciones (Alembic): `create_all` no agrega columnas nuevas a bases existentes (ya pasó con `request_id` y `bloqueado_hasta`) | Esquemas desalineados entre portátiles | Prioridad de la rama de Felipe; ver `docs/08-integracion-sprint-1.md` §4 |
| **H-09** | Media | Se podía crear un CAJERO o un MESERO sin sede (201). Después, el parametrizacion-service le responde 403 `SIN_SEDE` en todo | Usuario que existe pero no puede trabajar | Exigir `sede_id` cuando el perfil no es ADMINISTRADOR, al crear y al editar |
| **H-10** | Baja | Se puede crear una mesa o un producto en una sede **inactiva** (201) | Datos nuevos colgando de una sede que ya no opera | Rechazar con 409 si la sede está inactiva (complementa H-04) |
| **H-11** | Baja | Los listados de parametrización (`/sedes`, `/mesas`, `/productos`, …) no están paginados: no reciben `pagina`/`tamano` ni devuelven `X-Total-Count`. Solo usuarios y auditoría paginan, aunque RNF-06 y la práctica 9.4.3 del documento de arquitectura lo presentan como regla general | Respuestas grandes cuando crezca el catálogo | Agregar la paginación o precisar el documento de arquitectura |

Ninguno de estos hallazgos implica un requisito perdido: todos los datos del
tablero identificados tienen pantalla, contrato y columna. Son reglas de
integridad que faltan en los caminos de edición.

H-09 a H-11 los agregó QA el 10/10/2026, reproducidos con el `TestClient`
de cada servicio.

### 9.1 Estado de los hallazgos (actualizado 30/10/2026, Sprint 2)

| ID | Estado | Qué se hizo |
|---|---|---|
| H-01 | **Corregido** (Sprint 2) | Pantalla: campos en gris. API: los `*Actualizar` tienen `extra="forbid"`; `PATCH /mesas/1 {"numero": 9}` responde 422 `numero: no se puede enviar ni modificar`. Prueba: `test_hallazgos_sprint1.py` |
| H-02 | **Corregido** (Sprint 2) | `PATCH /productos` valida tipo y proveedor: 404 `No existe el tipo de producto con id 999.` |
| H-03 | **Corregido** (Sprint 2) | Renombrar sede o tipo a un nombre existente → 409 `SEDE_DUPLICADA` / `TIPO_DUPLICADO` |
| H-04 | **Corregido** (Sprint 2) | Tipo o proveedor inactivo → 409 `TIPO_INACTIVO` / `PROVEEDOR_INACTIVO` al crear, editar o reactivar un producto |
| H-05 | **Mitigado** | La sede del usuario, de la mesa y del producto se elige de una lista (selector de sedes, la segunda propuesta). Falta la validación por HTTP en el auth-service |
| H-06 | Abierto | Necesita consultar el auth-service por HTTP; se resuelve con H-05 |
| H-07 | **Corregido** (Sprint 2) | Abrir pedido pasa la mesa a OCUPADA; con pedido abierto no se libera ni se inactiva a mano (409 `MESA_CON_PEDIDO_ABIERTO`). Liberarla al facturar es de HU-023 (Sprint 3) |
| H-08 | Sprint 2 | Deuda técnica declarada en el documento de arquitectura |
| H-09 | **Corregido** | Crear cajero o mesero sin sede → 422 `DATOS_INVALIDOS`. Quitarle la sede, o pasar un administrador sin sede a cajero o mesero → 422 `SEDE_OBLIGATORIA`. Pruebas en `services/auth-service/tests/test_h09_sede_obligatoria.py` |
| H-10 | **Corregido** (Sprint 2) | Mesa en sede inactiva → 409 `SEDE_INACTIVA`. Los productos nuevos solo se cargan al inventario de las sedes activas |
| H-11 | Abierto | — |

---

## 10. Cómo mantener este documento

1. Toda columna nueva en un `models.py` entra aquí en el mismo Pull Request,
   con su requisito del tablero o marcada como "agregada por el equipo" y su porqué.
2. Si un campo cambia de nombre entre tablero, pantalla, API o tabla, se
   justifica en la columna **Reglas** (como `password` → `password_hash`).
3. Los IDs de la sección 8.3 se cierran antes de la Sprint Review.
4. Los hallazgos de la sección 9 se convierten en tareas del Sprint 2 o se
   cierran con una prueba que los verifique.