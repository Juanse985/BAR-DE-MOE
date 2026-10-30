#!/usr/bin/env bash
# ==============================================================================
# Bar de Moe · Script de inicio rápido (Local con .venv o Docker Compose)
# Uso:
#   ./iniciar.sh            # Inicia en modo local (SQLite + Uvicorn en :8000)
#   ./iniciar.sh --docker   # Inicia con Docker Compose + PostgreSQL
#   ./iniciar.sh --stop     # Detiene los servicios en ejecución
# ==============================================================================
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

VENV_DIR="$ROOT_DIR/.venv"
PID_DIR="$ROOT_DIR/.pids"
LOG_DIR="$ROOT_DIR/.logs"
JWT_SECRET_VAL="${JWT_SECRET:-secreto-desarrollo-bar-de-moe-2026}"

detener_locales() {
  if [[ -d "$PID_DIR" ]]; then
    for pid_file in "$PID_DIR"/*.pid; do
      [[ -e "$pid_file" ]] || continue
      pid="$(cat "$pid_file" 2>/dev/null || true)"
      if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
        kill "$pid" 2>/dev/null || true
      fi
      rm -f "$pid_file"
    done
  fi
  # Liberar puertos 8000, 8001, 8002 si quedaron procesos previos
  for port in 8000 8001 8002; do
    fuser -k "${port}/tcp" >/dev/null 2>&1 || true
  done
}

mostrar_credenciales() {
  echo ""
  echo "======================================================================"
  echo "  🍺 BAR DE MOE · PLATAFORMA LISTA EN: http://localhost:8000"
  echo "======================================================================"
  echo "   Estado de salud : http://localhost:8000/health"
  echo "   Swagger Auth    : http://localhost:8000/api/auth/docs"
  echo "   Swagger Param.  : http://localhost:8000/api/parametrizacion/docs"
  echo "----------------------------------------------------------------------"
  echo "  USUARIOS DE PRUEBA (Cambiar clave en primer ingreso si aplica):"
  echo "   • Administrador : admin     / Admin2026   (Todas las sedes)"
  echo "   • Administrador : mszyslak  / Cerveza2026 (Todas las sedes)"
  echo "   • Cajero        : ccarlson  / Cajero2026  (Sede Galerías)"
  echo "   • Mesero        : bgumble   / Mesero2026  (Sede Galerías)"
  echo "   • Cajero        : lleonard  / Cajero2026  (Sede Modelia)"
  echo "   • Mesero        : sgumble   / Mesero2026  (Sede Modelia)"
  echo "   • Cajero        : pbouvier  / Cajero2026  (Sede Zona T)"
  echo "   • Mesero        : omann     / Mesero2026  (Sede Zona T)"
  echo "======================================================================"
}

esperar_salud() {
  local url="$1"
  local intentos=30
  for ((i = 1; i <= intentos; i++)); do
    if curl -fsS "$url" >/dev/null 2>&1; then
      return 0
    fi
    sleep 0.5
  done
  return 1
}

MODO="${1:---local}"

if [[ "$MODO" == "--stop" ]]; then
  echo "→ Deteniendo servicios de Bar de Moe..."
  detener_locales
  if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
    docker compose down 2>/dev/null || true
  fi
  echo "✓ Servicios detenidos."
  exit 0
fi

if [[ "$MODO" == "--docker" ]]; then
  [[ -f .env ]] || cp .env.example .env
  echo "→ Levantando contenedores con Docker Compose..."
  docker compose up --build -d
  echo "→ Esperando a que el Gateway esté disponible en http://localhost:8000/health ..."
  esperar_salud "http://localhost:8000/health"
  if [[ -x "$VENV_DIR/bin/python" ]]; then
    "$VENV_DIR/bin/python" scripts/seed.py || true
  else
    python3 scripts/seed.py || true
  fi
  mostrar_credenciales
  echo "  Para ver logs : docker compose logs -f"
  echo "  Para detener  : ./iniciar.sh --stop"
  exit 0
fi

# Modo local (.venv + SQLite + Uvicorn)
if [[ ! -x "$VENV_DIR/bin/python" ]]; then
  echo "→ Creando entorno virtual en .venv..."
  python3 -m venv "$VENV_DIR"
  "$VENV_DIR/bin/pip" install --upgrade pip
  "$VENV_DIR/bin/pip" install -r requirements-dev.txt
  "$VENV_DIR/bin/pip" install -e libs/common
fi

mkdir -p "$PID_DIR" "$LOG_DIR"
detener_locales

trap 'echo ""; echo "→ Cerrando servicios..."; detener_locales; exit 0' INT TERM

echo "→ [1/3] Iniciando auth-service en :8001 ..."
(
  cd "$ROOT_DIR/services/auth-service"
  ENV=dev \
  DATABASE_URL="sqlite:///./auth.db" \
  JWT_SECRET="$JWT_SECRET_VAL" \
  PERMITIR_MULTISESION=true \
  "$VENV_DIR/bin/uvicorn" app.main:app --host 127.0.0.1 --port 8001 \
    >"$LOG_DIR/auth-service.log" 2>&1 &
  echo $! >"$PID_DIR/auth.pid"
)

echo "→ [2/3] Iniciando parametrizacion-service en :8002 ..."
(
  cd "$ROOT_DIR/services/parametrizacion-service"
  ENV=dev \
  DATABASE_URL="sqlite:///./param.db" \
  JWT_SECRET="$JWT_SECRET_VAL" \
  "$VENV_DIR/bin/uvicorn" app.main:app --host 127.0.0.1 --port 8002 \
    >"$LOG_DIR/parametrizacion-service.log" 2>&1 &
  echo $! >"$PID_DIR/parametrizacion.pid"
)

esperar_salud "http://127.0.0.1:8001/health"
esperar_salud "http://127.0.0.1:8002/health"

echo "→ [3/3] Iniciando API Gateway + Frontend en :8000 ..."
(
  cd "$ROOT_DIR/gateway"
  ENV=dev \
  JWT_SECRET="$JWT_SECRET_VAL" \
  AUTH_URL="http://127.0.0.1:8001" \
  PARAMETRIZACION_URL="http://127.0.0.1:8002" \
  "$VENV_DIR/bin/uvicorn" app.main:app --host 0.0.0.0 --port 8000 \
    >"$LOG_DIR/gateway.log" 2>&1 &
  echo $! >"$PID_DIR/gateway.pid"
)

esperar_salud "http://127.0.0.1:8000/health"

echo "→ Sembrando datos iniciales (sedes, mesas, cervezas y usuarios)..."
BASE_URL="http://127.0.0.1:8000" "$VENV_DIR/bin/python" "$ROOT_DIR/scripts/seed.py" || true

mostrar_credenciales

if [[ "${2:-}" == "--daemon" ]]; then
  echo "  Servicios corriendo en segundo plano (logs en .logs/)."
  echo "  Para detenerlos: ./iniciar.sh --stop"
  exit 0
fi

echo "  Logs en vivo (.logs/). Presiona Ctrl+C para detener todos los servicios."
echo ""
tail -f "$LOG_DIR/gateway.log" "$LOG_DIR/auth-service.log" "$LOG_DIR/parametrizacion-service.log"
