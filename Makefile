.PHONY: install format format-check lint typecheck test ci run

install:
	uv sync --locked --all-groups

format:
	uv run ruff format .
	uv run ruff check --fix .

format-check:
	uv run ruff format --check .

lint:
	uv run ruff check .

typecheck:
	uv run mypy

test:
	uv run pytest

ci: format-check lint typecheck test

run:
	uv run uvicorn services.payment_api.main:app --host 0.0.0.0 --port 8000
