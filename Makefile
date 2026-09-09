.PHONY: help up down logs test test-auth test-param test-gateway lint seed limpiar

help:
	@echo "up            Levanta toda la plataforma con Docker"
	@echo "down          La baja"
	@echo "logs          Sigue los logs"
	@echo "test          Corre las pruebas de los tres componentes"
	@echo "lint          Revisa el estilo con ruff"
	@echo "seed          Carga datos de ejemplo del Bar de Moe"
	@echo "limpiar       Borra volúmenes y bases de datos locales"

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f

test: test-auth test-param test-gateway

test-auth:
	cd services/auth-service && python -m pytest

test-param:
	cd services/parametrizacion-service && python -m pytest

test-gateway:
	cd gateway && python -m pytest

lint:
	ruff check services gateway libs

seed:
	python scripts/seed.py

limpiar:
	docker compose down -v
	find . -name "*.db" -delete
	find . -type d -name __pycache__ -exec rm -rf {} +
