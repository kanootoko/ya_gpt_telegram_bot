"""Bot starting CLI command is defined here."""

import asyncio
import sys
from pathlib import Path
from typing import Any

import click
from loguru import logger as global_logger
from loguru._logger import Logger

from ya_gpt_bot.bot_config.launch import run_bot
from ya_gpt_bot.config.app_config import AppConfig, LoggingConfig

from .group import cli


def _inject_event_id(extra: dict[str, Any]) -> str:
    if "event_id" in extra:
        extra["event_id_part"] = f" event_id={extra['event_id']}"


def configure_logging(config: LoggingConfig) -> Logger:
    """Apply logging config."""
    global_logger.remove()
    global_logger.configure(extra={"event_id_part": ""})
    logger = global_logger.patch(lambda record: _inject_event_id(record["extra"]))
    log_format_pretty = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level>"
        " | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan>{extra[event_id_part]}"
        " - <level>{message}</level>"
    )
    log_format = (
        "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line}{extra[event_id_part]} - {message}"
    )
    logger.add(sys.stderr, level=config.console_level, format=log_format_pretty, enqueue=True)
    for sink in config.sinks:
        if sink.output_type == "file":
            logger.add(sink.path, level=sink.level, format=log_format, enqueue=True)

    return logger


@cli.command("run")
@click.argument("config_file", type=click.Path(exists=True, dir_okay=False, path_type=Path), default="config.yaml")
def run(config_file: Path):
    """Start YandexGPT Telegram Bot."""
    config = AppConfig.load(config_file)
    logger = configure_logging(config.logging)

    try:
        asyncio.run(run_bot(config, logger))
    except KeyboardInterrupt:
        logger.info("Exiting because of user interruption")
    except Exception as exc:  # pylint: disable=broad-except
        logger.exception("Exception occured: {!r}", exc)
    finally:
        logger.info("Finishing bot execution")
