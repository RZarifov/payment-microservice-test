.PHONY: up down logs migrate revision run test

include .env
export

up:
ifeq ($(ENV),DEV)
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
else
	docker compose up -d
endif

down:
ifeq ($(ENV),DEV)
	docker compose -f docker-compose.yml -f docker-compose.dev.yml down -v
else
	docker compose down -v
endif

logs:
	docker compose logs -f

migrate:
	alembic upgrade head

revision:
	alembic revision --autogenerate -m "$(m)"

run:
ifeq ($(ENV),DEV)
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
else
	uvicorn app.main:app --host 0.0.0.0
endif

run_both:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 & \
	python -m app.workers & \
	wait

consumer:
	python -m app.workers

test:
	pytest tests/ -v
