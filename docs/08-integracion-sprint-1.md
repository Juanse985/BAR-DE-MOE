# Integración del Sprint 1 · Bar de Moe 100 %

**Rama:** `integracion/sprint-1` · **Integró:** Juan Sebastián Rodríguez (Líder QA)
**Fuentes:** `dev/angel` (4e75f16), `dev/david` (6fc325e), `dev/felipe` (f5390d0) y `dev/juan`.

Este documento explica **qué aportó cada integrante**, cómo se unió y cómo
comprobar que el Sprint 1 (M1 Seguridad + M2 Parametrización) quedó completo.

---

## 1. Resultado

| Verificación | Resultado |
|---|---|
| Pruebas automáticas (4 componentes) | **292 en verde, 0 fallidas, 0 defectos abiertos** |
| Cobertura | 94–99 % por componente (umbral acordado: 70 %) |
| Estilo (`ruff`) | Sin errores |
| Prueba de humo por el gateway | **22/22 pasos** |
| RNF-02 (p95 ≤ 2 s, 100 peticiones × 9 operaciones, 8 en paralelo) | Cumple; el más lento fue el login, con ≈ 0,3 s |
| Frontend en navegador con los 3 perfiles | 12/12 verificaciones |
| Colección Postman (`docs/postman/`) | 27 peticiones, 25 aserciones, 0 fallos |

Evidencia en `docs/evidencias/`.

## 2. Qué aportó cada uno

### Angel De Jesús Paniza Sierra · Líder Técnico · `dev/angel`
Angel reescribió el auth-service con otro contrato: perfiles `admin`/`usuario`,
rutas en inglés y sin `validar-sesion`. Esa versión rompía el gateway, el
frontend y la parametrización (ver `docs/07-informe-qa-sprint-1.md`, DEF-01).
Por decisión del equipo, **se llevaron sus funcionalidades al auth-service
compatible**:

| Aporte de Angel | Cómo quedó integrado |
|---|---|
| `GET /audit`: consulta de auditoría (HU-008) | `GET /auditoria` en **ambos** servicios. Filtros por usuario, sede, acción, resultado y rango de fechas; paginado del más reciente al más antiguo; solo ADMINISTRADOR; sin rutas para modificar ni borrar. |
| Bloqueo temporal (`LOCKOUT_MINUTOS`) | `BLOQUEO_MINUTOS`. Por defecto vale `0`: la cuenta queda bloqueada hasta que el administrador la desbloquee, como pide HU-002. Con un valor mayor, se desbloquea sola y lo deja en la auditoría. |
| `DELETE /users/{id}` | `POST /usuarios/{id}/inactivar` y `/activar`. HU-007 exige conservar el historial, así que no hay borrado físico. |
| "No puede eliminar su propia cuenta" | El administrador no puede inactivarse ni quitarse el perfil de administrador. |
| `PUT /users/{id}` con auditoría | `PATCH /usuarios/{id}` ahora queda en la auditoría (DEF-02). |
| Registro de logout | El logout registra usuario y sede (DEF-03). |
| Colección de Postman | `docs/postman/bar-de-moe-sprint-1.postman_collection.json`, adaptada a las rutas reales y ampliada con parametrización y seguridad. |
| Pendientes de su lista (paginación, límite por IP) | `GET /usuarios` paginado, con `X-Total-Count`. Límite de logins fallidos por IP (`MAX_INTENTOS_POR_IP`). |

### Juan David Tovío Montes · Analista RQ · `dev/david`
Se fusionó sin conflictos y sin cambios en su lógica:

- No se puede inactivar una sede, un tipo o un proveedor que tenga mesas o productos activos.
- Carga masiva de productos por CSV (`POST /productos/carga-masiva`).
- Consulta de producto por código y sede (`GET /productos/por-codigo/{codigo}`), que va a necesitar M4.
- Activar e inactivar productos con endpoints propios.
- Sus 17 pruebas de parametrización.

Ajustes al integrar:

- **DEF-06:** CAJERO y MESERO ahora solo ven su sede (mesas, catálogo, sedes y producto por id o código). Si piden otra sede, el sistema responde 403 `SEDE_NO_AUTORIZADA`.
- **DEF-05, DEF-07 y DEF-08:** cada escritura registra la IP real y el request id, y los rechazos quedan en la auditoría.
- Se ordenaron los imports y se partieron las líneas largas que marcaba `ruff`.

### Juan Felipe Cortés Mendoza · Arquitecto · `dev/felipe`
Se fusionó el **frontend por perfiles** (`frontend/`), que el gateway sirve
en `http://localhost:8000/`. Trae:

- login
- cambio obligatorio de contraseña
- menú según el perfil
- administración de usuarios y de la parametrización
- cierre de sesión a los 3 minutos de inactividad

También trae su corrección de DEF-04 (inactivar un usuario cierra sus
sesiones) y la actualización de SQLAlchemy y Pydantic.

Ajustes al integrar:

- **Conflicto** en `libs/common/barmoe_common/auditoria.py`: se conservó el estilo de tipos de Felipe y se agregó la columna `request_id`.
- **DEF-10:** el gateway montaba el frontend con una ruta fija y fuera de Docker ni siquiera arrancaba. Ahora busca la carpeta; si no existe, arranca igual.
- **DEF-07 y DEF-09:** el gateway envía la IP del cliente a los servicios y responde 502 si un servicio devuelve algo que no es JSON.
- **Frontend:**
  - Se agregó *Tipos de producto* al menú del administrador (HU-011).
  - Botón *Desbloquear* en usuarios.
  - Activar e inactivar con los endpoints nuevos.
  - El botón *Cerrar sesión* era invisible (texto blanco sobre fondo blanco).
  - Cajero y mesero ya no ven los botones *Nuevo* ni *Editar*, que el servidor les iba a rechazar.
  - Favicon.

### Juan Sebastián Rodríguez Jiménez · Líder QA · `dev/juan`

- Auditoría transversal en `libs/common`: request id, IP real y registro de accesos rechazados.
- Corrección del pánico de bcrypt con hashes truncados.
- Pruebas de HU-025 a HU-028.
- Scripts de seed, prueba de humo, medición del RNF-02 y reporte.
- Cobertura mínima en el CI.
- Documentos `06-owasp.md` y `07-informe-qa-sprint-1.md`.
- Esta integración y la corrección de DEF-02 a DEF-10.

## 3. Cómo se unió (historial de git)

```
integracion/sprint-1
├── db49857  test(calidad): ...                     ← dev/juan
├── merge:   integrar dev/david                     ← sin conflictos
├── merge:   integrar dev/felipe                    ← conflicto en auditoria.py resuelto
└── feat:    integración Sprint 1 (aportes de Angel + DEF-02..DEF-10)
```

`dev/angel` **no se fusionó con git**: sus cambios se trajeron a mano, así que
su commit no aparece en el historial. Su aporte queda acreditado en este
documento y en el mensaje del commit de integración.

## 4. Cambios de base de datos

Mientras no exista Alembic, `create_all` **no agrega columnas a tablas que ya
existen**. Quien tenga una base de datos creada antes de esta integración debe
hacer una de estas dos cosas:

```bash
make limpiar && make up           # opción 1: empezar de cero
```

```sql
-- opción 2: en auth_db
ALTER TABLE auditoria ADD COLUMN request_id VARCHAR(64);
ALTER TABLE usuarios  ADD COLUMN bloqueado_hasta TIMESTAMPTZ;
-- en parametrizacion_db
ALTER TABLE auditoria ADD COLUMN request_id VARCHAR(64);
```

## 5. Endpoints nuevos o cambiados

| Método y ruta (por el gateway) | Perfil | Nota |
|---|---|---|
| `GET /api/auth/auditoria` | ADMINISTRADOR | HU-008 |
| `GET /api/parametrizacion/auditoria` | ADMINISTRADOR | HU-008 |
| `GET /api/auth/usuarios?sede_id=&perfil=&estado=&pagina=&tamano=` | ADMINISTRADOR | Devuelve el total en `X-Total-Count` |
| `POST /api/auth/usuarios/{id}/inactivar` · `/activar` | ADMINISTRADOR | Reemplazan el DELETE de Angel |
| `POST /api/auth/auth/login` → **429** `DEMASIADOS_INTENTOS` | — | Límite por IP |
| `GET /api/parametrizacion/{mesas,productos,sedes}` | Todos | CAJERO y MESERO quedan forzados a su sede |
| `GET /` | — | Frontend de Felipe |

## 6. Cómo verificarlo

```bash
cp .env.example .env
make up                 # terminal 1 → http://localhost:8000
make test               # terminal 2: 292 pruebas
make evidencias         # seed + humo + RNF-02 + reporte
```

Usuarios del seed (el sistema pide cambiar la contraseña en el primer ingreso):

| Usuario | Contraseña | Perfil | Sede |
|---|---|---|---|
| `admin` | `Admin2026` | ADMINISTRADOR | Todas |
| `mszyslak` | `Cerveza2026` | ADMINISTRADOR | Centro |
| `ccarlson` | `Cajero2026` | CAJERO | Centro |
| `bgumble` | `Mesero2026` | MESERO | Centro |
| `lleonard` | `Cajero2026` | CAJERO | Norte |
| `sgumble` | `Mesero2026` | MESERO | Norte |

Postman: importar `docs/postman/bar-de-moe-sprint-1.postman_collection.json` y
correrla completa. Necesita el seed cargado y la contraseña del admin en la
variable `admin_password`.

## 7. Lo que queda para los siguientes sprints

- **Migraciones con Alembic** (lo más urgente, por la sección 4).
- **HTTPS** delante del gateway (OBS-01).
- **Seguridad del administrador inicial:** el backend todavía permite operar sin cambiar la contraseña inicial; hoy solo el frontend obliga a cambiarla (OBS-03).
- **Secreto JWT real** en cada ambiente (OBS-04).
- **Pantallas de pedidos, facturación y reportes:** están en el menú, pero son de los sprints 2 a 4.
- **Docker:** en esta verificación no se pudieron descargar imágenes. Antes de la Review hay que correr `make up` y `make evidencias` en el portátil de la demo.
