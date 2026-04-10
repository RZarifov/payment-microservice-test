.PHONY: up down logs migrate revision run test

up:
	docker compose up -d

down:
	docker compose down -v

logs:
	docker compose logs -f

migrate:
	alembic upgrade head

revision:
	alembic revision --autogenerate -m "$(m)"

run:
	uvicorn app.main:app --host 0.0.0.0

run_dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

run_both:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 & \
	python -m app.workers & \
	wait

consumer:
	python -m app.workers

test:
	pytest tests/ -v
