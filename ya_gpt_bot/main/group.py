"""Main Click CLI group (application entrypoint) is defined here."""
import click

from ya_gpt_bot.version import VERSION


@click.version_option(VERSION)
@click.group
def cli():
    """Configurable YandexGPT Telegram Bot.

    To get an example config file run config-example command.
    """
