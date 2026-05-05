#!/bin/sh
set -e

cd "$(dirname "$0")"

uv sync --all-extras

case "${1}" in
    test)      cd backend && uv run pytest -v ;;
    lint)      uv run ruff check backend ;;
    typecheck) uv run pyright backend ;;
    *)    cd backend && uv run uvicorn main:app --reload ;;
esac
