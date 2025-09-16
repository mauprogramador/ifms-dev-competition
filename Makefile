-include .env
.PHONY: $(MAKECMDGOALS)

PORT ?= 8000


# Environment setup

venv:
	@bash venv.sh

install:
	@poetry install --no-root
	@poetry run playwright install chromium


# Run application

run:
	@poetry run python3 -m src

docker:
	@docker build -q -t ifms-dev-competition .
	@docker run -d --env HOST=0.0.0.0 --env-file .env --name ifms-dev-competition -p ${PORT}:${PORT} ifms-dev-competition


# Tests

test:
	@poetry run pytest -v --color=yes


# Formatting and Linting

format:
	@poetry run isort .
	@poetry run black .

lint:
	@poetry run isort src/ --check
	@poetry run black src/ --check
	@poetry run pylint src/
	@poetry run mypy src/


# Requirements

req:
	@poetry export -f requirements.txt -o requirements.txt --without-hashes --without-urls --only main
