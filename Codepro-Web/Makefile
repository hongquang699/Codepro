.PHONY: up down build migrate test logs help

help:
	@echo "Coding Platform Makefile commands:"
	@echo "  make up       - Start all Docker services"
	@echo "  make down     - Stop all Docker services"
	@echo "  make build    - Build Docker images"
	@echo "  make migrate  - Run database migrations"
	@echo "  make test     - Run full test suite"
	@echo "  make logs     - Follow server logs"

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

migrate:
	python manage.py migrate

test:
	python manage.py test tests

logs:
	docker compose logs -f
