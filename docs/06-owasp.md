# Seguridad verificable — controles OWASP (HU-028 · RNF-11)

**Responsable:** Juan Sebastián Rodríguez (Líder QA) · **Sprint:** 1 · **Versión:** 1.1 (integración)

La propuesta comercial v2 (sección 4.1) no promete "cumplir OWASP" en general.
Se compromete con **cuatro controles del OWASP Top 10 (2021)**, que son los
riesgos reales de esta aplicación, y cada uno con una forma de comprobarse en
la Sprint Review. Este documento dice dónde está implementado cada control,
qué prueba lo verifica y qué queda pendiente.

Cómo reproducir toda la evidencia:

```bash
make cov        # pruebas automáticas con cobertura
make up         # en otra terminal: plataforma levantada
make evidencias # seed + prueba de humo + RNF-02 + reporte
```

Los resultados quedan en `docs/evidencias/`.

---

## Resumen

| Control | Riesgo OWASP | Estado Sprint 1 | Pruebas en verde | Defectos abiertos |
|---|---|---|---|---|
| C-1 | A01 Control de acceso roto | 🟢 Cumple | Perfil **y sede** validados en el servidor; rechazos auditados | — (DEF-04, 05 y 06 corregidos) |
| C-2 | A02 Fallas criptográficas | 🟡 Parcial | Contraseñas con bcrypt, ninguna legible en BD | HTTPS pendiente (OBS-01) |
| C-3 | A03 Inyección | 🟢 Cumple | Login, filtros y textos resisten inyección | — |
| C-4 | A07 Fallas de autenticación | 🟢 Cumple | Bloqueo por usuario **y por IP**, sesión única, inactividad de 3 min | OBS-03 pendiente |

🟢 cumple con evidencia · 🟡 implementado con defectos abiertos · 🔴 no implementado

---

## C-1 · Control de acceso roto (A01)

**Compromiso.** El perfil y la sede se validan en el servidor en cada
operación, no solo al mostrar el menú. Un mesero no puede facturar aunque
conozca la dirección de la pantalla. Todo intento rechazado queda registrado.

**Implementación.**

| Pieza | Dónde |
|---|---|
| Validación de firma del JWT en cada servicio | `libs/common/barmoe_common/deps.py` → `usuario_actual` |
| Validación de perfil | `deps.requiere_perfil("ADMINISTRADOR")` en cada escritura |
| Sesión viva validada en el gateway | `gateway/app/main.py` → `_validar_sesion` |
| Solo viajan `Authorization`, `Content-Type` y `Accept` hacia los servicios | `gateway/app/main.py` → `proxy` |
| Registro de intentos rechazados (401/403) | `libs/common/barmoe_common/middleware.py` → `AuditoriaRechazosMiddleware` (nuevo) |

**Verificación (prueba negativa por perfil).**

| Prueba | Archivo |
|---|---|
| CAJERO y MESERO reciben 403 en las 6 operaciones de administración de usuarios | `services/auth-service/tests/test_hu028_owasp.py` |
| CAJERO y MESERO reciben 403 en las 10 escrituras de parametrización | `services/parametrizacion-service/tests/test_hu028_owasp.py` |
| Un rechazo no modifica datos | ídem |
| Cabeceras sueltas (`X-Perfil`, `X-Sede-Id`) no dan permisos | ídem y `gateway/tests/test_qa_gateway.py` |
| Tokens vencidos, firmados con otro secreto, `alg=none` o con el perfil alterado a mano → 401 | `libs/common/tests/test_hu028_tokens_y_permisos.py` |
| Ninguna ruta privada se enruta sin token | `gateway/tests/test_qa_gateway.py` |
| Un intento rechazado queda en `auditoria` con usuario, sede, IP y request id | `libs/common/tests/test_hu025_trazabilidad.py` |
| En vivo: el mesero no puede crear sedes, listar usuarios ni ver otra sede | `scripts/prueba_humo.py` (pasos 15 a 17) |

**Estado tras la integración.** DEF-04, DEF-05 y DEF-06 están corregidos y
sus pruebas pasan sin `xfail`. Además, la auditoría (incluidos los rechazos)
se puede consultar en `GET /auditoria` de cada servicio (HU-008). Lo que
sigue es el diagnóstico original.

**Pendiente (diagnóstico original).**

- **DEF-05.** La auditoría de rechazos ya existe en la librería común, pero
  ningún servicio la activó todavía. Es una línea en cada `main.py`:
  `crear_app(config, ..., auditar_rechazos=SessionLocal)`.
- **DEF-06.** El parametrizacion-service valida el **perfil** pero no la
  **sede**: un mesero del Centro puede listar las mesas y el catálogo del
  Norte con `?sede_id=`. Para CAJERO y MESERO el filtro debe forzarse a la sede
  del token.
- **DEF-04.** Al inactivar un usuario, sus sesiones siguen vivas y el gateway
  lo deja pasar a parametrización. Debe cerrar sus sesiones (la rama de Felipe
  ya trae este arreglo) y `validar-sesion` debe revisar el estado del usuario.

---

## C-2 · Fallas criptográficas (A02)

**Compromiso.** Contraseñas con función de hash de un solo sentido y con sal;
el tráfico viaja sobre HTTPS.

**Implementación.** `libs/common/barmoe_common/security.py`: bcrypt con 12
rondas (la sal va incluida en el hash). La API nunca devuelve el hash.

**Verificación (inspección de la tabla de usuarios).**

| Prueba | Archivo |
|---|---|
| Se recorren **todas** las tablas del auth-service y ninguna contiene una contraseña legible, ni después de crear, cambiar o restablecer | `services/auth-service/tests/test_hu027_cifrado.py` |
| Todos los hashes son `$2b$12$`, de 60 caracteres y distintos aunque la contraseña sea igual | ídem |
| La API no expone `password` ni `password_hash` en ninguna respuesta | ídem |
| La auditoría nunca guarda contraseñas, ni las equivocadas | `services/auth-service/tests/test_hu025_trazabilidad.py` |
| Un hash corrupto nunca valida y no tumba el servicio | `libs/common/tests/test_hu027_cifrado.py` |

**Hallazgo corregido en este sprint.** Con un hash truncado en la base, la
librería bcrypt (escrita en Rust) entraba en *pánico* en lugar de lanzar un
error: el `except ValueError` no lo atrapaba y el login respondía 500. Ahora
`verificar_password` valida el formato antes de llamar a bcrypt.

**Pendiente.**

- **OBS-01 · HTTPS.** En desarrollo todo va por HTTP. Para la demo en la sede
  piloto se necesita un proxy inverso con TLS (Caddy o Nginx) delante del
  gateway. La verificación de la propuesta ("revisión del certificado del
  ambiente") no se puede hacer hasta que exista ese ambiente.
- **OBS-04 · Secreto JWT.** `.env.example` trae un secreto de ejemplo. Antes de
  cualquier despliegue se genera uno real con `openssl rand -hex 32` (tarea de
  la rama de Felipe).

---

## C-3 · Inyección (A03)

**Compromiso.** Todo acceso a datos usa consultas parametrizadas por medio del
ORM, y las entradas se validan por tipo y longitud antes de procesarse.

**Implementación.** SQLAlchemy 2.0 con `select(...).where(...)` (parámetros
enlazados) en todos los servicios; ningún SQL armado con texto. Pydantic valida
tipo y longitud de cada campo, y los errores salen con el formato único
`DATOS_INVALIDOS`.

**Verificación.**

| Prueba | Archivo |
|---|---|
| 6 cadenas de inyección en usuario y en contraseña del login → 401, nunca sesión | `services/auth-service/tests/test_hu028_owasp.py` |
| Después de los ataques la tabla de usuarios sigue intacta | ídem |
| Inyección en filtros de texto (`perfil`, `estado`) → lista vacía, no todos los registros | `test_hu028_owasp.py` de ambos servicios |
| Inyección en filtros numéricos (`sede_id`, `tipo_producto_id`) → 422 | `services/parametrizacion-service/tests/test_hu028_owasp.py` |
| `'; DROP TABLE ...` en un nombre se guarda como texto y las tablas siguen existiendo | ídem |
| Longitudes, perfiles inválidos, números negativos y valores no numéricos → 422 | ambos servicios |

**Estado:** cumple. No se encontraron defectos.

---

## C-4 · Fallas de identificación y autenticación (A07)

**Compromiso.** Bloqueo por reintentos (RNF-09), sesión única (RNF-10) y
cierre por inactividad de 3 minutos (RNF-03), probados en la Review.

**Verificación.**

| Comportamiento | Prueba |
|---|---|
| A los 3 intentos fallidos la cuenta se bloquea, y ni la contraseña correcta entra (423) | `test_c4_bloqueada_la_cuenta_ni_la_password_correcta_entra` |
| El desbloqueo del administrador devuelve el acceso | `test_c4_el_desbloqueo_del_admin_devuelve_el_acceso` |
| Un login correcto reinicia el contador | `test_c4_un_login_correcto_reinicia_el_contador` |
| La segunda sesión se rechaza (409) y la primera sigue viva | `test_c4_la_segunda_sesion_se_rechaza_y_la_primera_sigue_viva` |
| Con 179 s de inactividad la sesión vale; con 181 s se cierra | `test_c4_la_inactividad_se_cuenta_desde_la_ultima_actividad` |
| Una sesión vencida libera el login y queda cerrada con motivo `INACTIVIDAD` | `test_c4_una_sesion_vencida_por_inactividad_libera_el_login` |
| Después del logout y del restablecimiento el token ya no sirve | `test_c4_despues_del_logout_el_token_no_sirve`, `test_c4_el_restablecimiento_cierra_las_sesiones_del_usuario` |
| El mensaje de error no revela si el usuario existe | `test_c4_el_mensaje_de_error_no_distingue_usuario_de_password` |
| En vivo, por el gateway | `scripts/prueba_humo.py` (pasos 4, 21 y 22) |

**Observaciones (no bloquean el sprint).**

- **OBS-02 (resuelto al integrar).** El bloqueo era solo por usuario: un atacante
  podía probar una contraseña contra muchos usuarios distintos sin que nada lo
  frenara. Ahora el auth-service
  corta con 429 `DEMASIADOS_INTENTOS` tras `MAX_INTENTOS_POR_IP` fallos en
  `VENTANA_IP_MINUTOS`, usando la IP real que reenvía el gateway.
- **OBS-03.** El administrador inicial nace con `debe_cambiar_password=true`,
  pero nada obliga a cambiarla: se puede operar con `Admin2026`. Se recomienda
  que el backend rechace cualquier operación distinta de
  `/auth/cambiar-password` mientras esa marca esté activa.

---

## Resto del OWASP Top 10 (fuera del compromiso)

La propuesta los deja fuera del compromiso verificable, pero no los ignora.
Estado actual para que nadie se sorprenda en la sustentación:

| Riesgo | Estado |
|---|---|
| A04 Diseño inseguro | Parcial: las reglas de negocio viven en el backend, no en el frontend. |
| A05 Configuración de seguridad incorrecta | Parcial: CORS restringido a orígenes conocidos (probado); faltan cabeceras de seguridad y cerrar `/docs` en producción. |
| A06 Componentes vulnerables | Versiones fijadas en `requirements.txt`; falta `pip-audit` en el CI. |
| A08 Integridad de software y datos | CI con pruebas obligatorias antes del merge. |
| A09 Registro y monitoreo | Auditoría en BD, `X-Request-Id` y aviso en el log cuando se pasa del SLA. Faltan DEF-03, DEF-07 y DEF-08. |
| A10 SSRF | No aplica: el gateway solo llama a URLs fijas de su configuración. |

Si el cliente pide una auditoría completa, se cotiza como sprint adicional
(bloque B de la propuesta).
