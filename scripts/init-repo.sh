#!/usr/bin/env bash
# Inicializa el repositorio y crea las cuatro ramas del Sprint 1.
# Uso:  ./scripts/init-repo.sh git@github.com:usuario/bar-de-moe.git
set -euo pipefail

REMOTO="${1:-}"

git init -b main
git add .
git commit -m "feat(base): esqueleto de microservicios del Sprint 1

- gateway con enrutamiento y validacion de sesion
- auth-service (M1) con perfiles, bloqueo, sesion unica e inactividad
- parametrizacion-service (M2) con sedes, mesas, productos, tipos y proveedores
- libreria comun, docker-compose, CI y 37 pruebas"

git branch develop
git checkout develop

for rama in feat/auth-usuarios feat/infra-gateway feat/parametrizacion feat/calidad-trazabilidad; do
  git branch "$rama"
  echo "  rama creada: $rama"
done

if [ -n "$REMOTO" ]; then
  git remote add origin "$REMOTO"
  git push -u origin main develop feat/auth-usuarios feat/infra-gateway feat/parametrizacion feat/calidad-trazabilidad
  echo "✓ Ramas publicadas en $REMOTO"
else
  echo "✓ Repositorio local listo. Para publicarlo:"
  echo "    git remote add origin <URL>"
  echo "    git push -u origin main develop feat/*"
fi
