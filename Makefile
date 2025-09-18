-include .env
.PHONY: $(MAKECMDGOALS)

POETRY_VERSION := 2.1.3
PORT ?= 8000

HAS_POETRY := $(shell command -v poetry >/dev/null 2>&1 && echo 1 || echo 0)


# Environment setup

venv:
	@bash venv.sh

poetry-install:
	pip3 install poetry==$(POETRY_VERSION)
	poetry install --no-root
	poetry run playwright install chromium

pip-install:
	pip3 install -r requirements.txt
	playwright install chromium


# Run application

run:
ifeq ($(HAS_POETRY), 1)
	@poetry run python3 -m src
else
	@python3 -m src
endif

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
