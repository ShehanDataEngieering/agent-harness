.PHONY: check lint types test mutate up down

check: lint types test

lint:
	uv run ruff check .
	uv run ruff format --check .

types:
	uv run pyright

test:
	uv run pytest -q

mutate:
	uv run mutmut run

up:
	docker compose up -d

down:
	docker compose down
