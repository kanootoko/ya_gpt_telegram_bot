"""Alembic environment preparation script."""
import importlib
import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

project_root_dir = Path(__file__).resolve().parent.parent.parent.parent

sys.path.append(str(project_root_dir))

from ya_gpt_bot.config.app_config import AppConfig  # pylint: disable=wrong-import-position

# from ya_gpt_bot.db.entities import *  # pylint: disable=wrong-import-position,wildcard-import
from ya_gpt_bot.db.metadata import metadata  # pylint: disable=wrong-import-position

for py_file in (project_root_dir / "ya_gpt_bot" / "db" / "entities").glob("*.py"):
    module = importlib.import_module(f"ya_gpt_bot.db.entities.{py_file.name[:-3]}")
    for key, value in vars(module).items():
        if not key.startswith("t_"):
            continue
        globals()[key] = value


config = context.config
section = config.config_ini_section

try:
    config_file = os.environ.get("CONFIG", str(project_root_dir / "config.yaml"))
    app_config = AppConfig.load(config_file)
except Exception as exc:  # pylint: disable=broad-except
    print(
        f"Could not open config file with database configuration located at {config_file}"
        " (changed in CONFIG environment variable)"
    )
    sys.exit(1)

config.set_section_option(section, "POSTGRES_DB", app_config.db.name)
config.set_section_option(section, "POSTGRES_HOST", app_config.db.host)
config.set_section_option(section, "POSTGRES_USER", app_config.db.user)
config.set_section_option(section, "POSTGRES_PASSWORD", app_config.db.password)
config.set_section_option(section, "POSTGRES_PORT", str(app_config.db.port))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
