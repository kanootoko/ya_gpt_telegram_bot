CODE_DIR := ya_gpt_bot

DOCKER_USER_WITH_SLASH =

format:
	poetry run isort $(CODE_DIR)
	poetry run black $(CODE_DIR)

lint:
	poetry run pylint $(CODE_DIR)

install-dev:
	poetry install --with dev

clear:
	rm -rf ./dist

build:
	poetry build

config-example:
	poetry run ya-gpt-bot config-example config.yaml

run:
	poetry run ya-gpt-bot run config.yaml

db-revision:
	cd ya_gpt_bot/db/migrator && poetry run alembic revision --autogenerate

db-migrate:
	cd ya_gpt_bot/db/migrator && poetry run alembic upgrade head
