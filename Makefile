.PHONY: help up down logs test test-common test-auth test-param test-gateway cov lint seed humo rnf02 reporte evidencias limpiar

# Umbral mínimo de cobertura acordado por el equipo (Sprint 1). El CI usa el mismo.
COBERTURA_MINIMA ?= 70
COV = --cov-report=term-missing --cov-fail-under=$(COBERTURA_MINIMA)

help:
	@echo "up            Levanta toda la plataforma con Docker"
	@echo "down          La baja"
	@echo "logs          Sigue los logs"
	@echo "test          Corre las pruebas de los cuatro componentes"
	@echo "cov           Pruebas con cobertura (falla por debajo de $(COBERTURA_MINIMA) %)"
	@echo "lint          Revisa el estilo con ruff"
	@echo "seed          Carga datos de ejemplo del Bar de Moe"
	@echo "humo          Prueba de humo de punta a punta contra la plataforma levantada"
	@echo "rnf02         Mide el p95 de las operaciones (RNF-02, 2 segundos)"
	@echo "reporte       Reporte consolidado de pruebas para la Sprint Review"
	@echo "evidencias    seed + humo + rnf02 + reporte, todo en docs/evidencias"
	@echo "limpiar       Borra volúmenes y bases de datos locales"

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f

test: test-common test-auth test-param test-gateway

test-common:
	cd libs/common && python -m pytest

test-auth:
	cd services/auth-service && python -m pytest

test-param:
	cd services/parametrizacion-service && python -m pytest

test-gateway:
	cd gateway && python -m pytest

cov:
	cd libs/common && python -m pytest --cov=barmoe_common $(COV)
	cd services/auth-service && python -m pytest --cov=app $(COV)
	cd services/parametrizacion-service && python -m pytest --cov=app $(COV)
	cd gateway && python -m pytest --cov=app $(COV)

lint:
	ruff check services gateway libs scripts

seed:
	python scripts/seed.py

humo:
	python scripts/prueba_humo.py --evidencia docs/evidencias

rnf02:
	python scripts/medir_rnf02.py --evidencia docs/evidencias

reporte:
	python scripts/reporte_pruebas.py

evidencias: seed humo rnf02 reporte

limpiar:
	docker compose down -v
	find . -name "*.db" -delete
	find . -type d -name __pycache__ -exec rm -rf {} +
