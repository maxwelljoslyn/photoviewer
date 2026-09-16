default: fix format

fix:
    uv run ruff check --fix

format:
    uv run ruff format

test:
    uv run pytest -n 6
