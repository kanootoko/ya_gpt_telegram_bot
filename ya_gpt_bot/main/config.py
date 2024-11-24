"""Config example CLI command is defined here."""
from pathlib import Path

import click

from ya_gpt_bot.config.app_config import AppConfig

from .group import cli


@cli.command("config-example")
@click.argument("config_file", type=click.Path(dir_okay=False, path_type=Path))
def config_example(config_file: Path):
    """Export example configuration file."""
    config = AppConfig.example()
    config.dump(config_file)
