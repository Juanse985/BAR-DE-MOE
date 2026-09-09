# Guía rápida

## Levantar todo con Docker

```bash
cp .env.example .env
docker compose up --build
```

Cuando termine:

| Qué | Dónde |
|---|---|
| Gateway | http://localhost:8000 |
| Estado de la plataforma | http://localhost:8000/health |
| Swagger del auth | http://localhost:8000/api/auth/docs |
| Swagger de parametrización | http://localhost:8000/api/parametrizacion/docs |
| PostgreSQL | `localhost:5432` · usuario `barmoe` · clave `barmoe` |

El primer arranque crea el administrador **`admin` / `Admin2026`**. Cámbienlo
antes de cualquier demo.

## Probar el flujo completo a mano

```bash
# 1. Login
curl -s -X POST http://localhost:8000/api/auth/auth/login \
  -H "Content-Type: application/json" \
  -d '{"usuario":"admin","password":"Admin2026"}'

# 2. Guardar el token que devuelve
TOKEN="pegar-aqui-el-access_token"

# 3. Crear una sede
curl -s -X POST http://localhost:8000/api/parametrizacion/sedes \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"nombre":"Bar de Moe · Centro","direccion":"Av. Siempreviva 742"}'

# 4. Consultarlas
curl -s http://localhost:8000/api/parametrizacion/sedes \
  -H "Authorization: Bearer $TOKEN"

# 5. Cerrar sesión (necesario: no se permite multisesión)
curl -s -X POST http://localhost:8000/api/auth/auth/logout \
  -H "Authorization: Bearer $TOKEN"
```

> Si al volver a entrar les responde `SESION_ACTIVA`, es el RNF-10 funcionando:
> hay una sesión abierta. Hagan logout, o esperen 3 minutos a que caduque sola.

## Trabajar sin Docker

Útil para programar rápido: usa SQLite y no necesita Postgres.

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
pip install -e libs/common

# auth-service
cd services/auth-service
DATABASE_URL="sqlite:///./auth.db" uvicorn app.main:app --reload --port 8001

# parametrizacion-service (en otra terminal)
cd services/parametrizacion-service
DATABASE_URL="sqlite:///./param.db" uvicorn app.main:app --reload --port 8002
```

## Pruebas

```bash
make test            # los tres componentes
make test-auth       # solo auth-service
make lint            # ruff
```

Las pruebas corren sobre SQLite en archivos temporales: no tocan Postgres ni
necesitan Docker.

## Problemas frecuentes

| Síntoma | Causa | Solución |
|---|---|---|
| `SESION_ACTIVA` al hacer login | RNF-10, ya hay sesión abierta | Logout, o esperar 3 minutos |
| `USUARIO_BLOQUEADO` | RNF-09, tres claves erradas | `POST /usuarios/{id}/desbloquear` con el admin |
| `SESION_EXPIRADA` | RNF-03, 3 minutos sin actividad | Volver a hacer login |
| El gateway responde `degradado` | Un servicio no arrancó | `docker compose logs auth-service` |
| Cambié un modelo y la tabla no cambió | No hay migraciones todavía | `docker compose down -v` y volver a levantar |
