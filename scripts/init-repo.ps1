# Inicializa el repositorio y crea las cuatro ramas del Sprint 1 (Windows).
# Uso:  .\scripts\init-repo.ps1 "git@github.com:usuario/bar-de-moe.git"
param([string]$Remoto = "")

$ErrorActionPreference = "Stop"

git init -b main
git add .
git commit -m "feat(base): esqueleto de microservicios del Sprint 1"

git branch develop
git checkout develop

$ramas = @("feat/auth-usuarios", "feat/infra-gateway", "feat/parametrizacion", "feat/calidad-trazabilidad")
foreach ($rama in $ramas) {
    git branch $rama
    Write-Host "  rama creada: $rama"
}

if ($Remoto -ne "") {
    git remote add origin $Remoto
    git push -u origin main develop @ramas
    Write-Host "✓ Ramas publicadas en $Remoto"
} else {
    Write-Host "✓ Repositorio local listo. Para publicarlo:"
    Write-Host "    git remote add origin <URL>"
    Write-Host "    git push -u origin main develop feat/*"
}
