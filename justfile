default:
    @just --list

format:
    uv run ruff format .

lint:
    uv run ruff check .

typecheck:
    uv run pyright

test:
    uv run pytest

check: lint typecheck test
