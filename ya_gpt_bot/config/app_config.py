"""Bot app configuration class is defined here."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Generic, Literal, TextIO, TypeVar

import yaml

from ya_gpt_bot.bot_config.utils.dependencies import load_class
from ya_gpt_bot.gpt.client import ArtClient, GPTClient
from ya_gpt_bot.gpt.waiter import AsyncWaiter
from ya_gpt_bot.version import VERSION
from ya_gpt_bot.ya_gpt.auth_service import AuthService

_T = TypeVar("_T")


@dataclass
class ClassInitializer(Generic[_T]):
    """Class initializer configuration class"""

    class_path: str
    kwargs: dict[str, Any] = field(default_factory=dict)

    def construct(self, **additional_kwargs) -> _T:
        """Construct class with arguments from config and additional kwargs."""
        cls = load_class(self.class_path)
        return cls(**(self.kwargs | additional_kwargs))


@dataclass
class YaGPTConfig:
    """Yandex GPT configuration class."""

    waiter: ClassInitializer[AsyncWaiter]
    client: ClassInitializer[GPTClient]

    def __str__(self) -> str:
        return f"YaGPT(client={self.client}, waiter={self.waiter})"

    @property
    def __dict__(self) -> dict:
        """Dict transformer used in `vars()`."""
        return {
            "waiter": vars(self.waiter),
            "client": vars(self.client),
        }

    @classmethod
    def from_init(cls, init_data: dict) -> "YaGPTConfig":
        """Construct YaGPTConfig from json data passed as dict."""
        waiter = ClassInitializer(init_data["waiter"]["class_path"], init_data["waiter"].get("kwargs", {}))
        client = ClassInitializer(init_data["client"]["class_path"], init_data["client"].get("kwargs", {}))
        return cls(waiter, client)

    def get_client(self, oauth_token: str) -> GPTClient:
        """Construct GPTClient based on config."""
        return self.client.construct(
            waiter=self.waiter.construct(),
            auth_service=AuthService(oauth_token),
        )


@dataclass
class YaArtConfig:
    """Yandex Art configuration class."""

    waiter: ClassInitializer[AsyncWaiter]
    client: ClassInitializer[ArtClient]

    def __str__(self) -> str:
        return f"YaArt(client={self.client}, waiter={self.waiter})"

    @property
    def __dict__(self) -> dict:
        """Dict transformer used in `vars()`."""
        return {
            "waiter": vars(self.waiter),
            "client": vars(self.client),
        }

    @classmethod
    def from_init(cls, init_data: dict) -> "YaArtConfig":
        """Construct YaGPTConfig from init data passed as dict."""
        waiter = ClassInitializer(init_data["waiter"]["class_path"], init_data["waiter"].get("kwargs", {}))
        client = ClassInitializer(init_data["client"]["class_path"], init_data["client"].get("kwargs", {}))
        return cls(waiter, client)

    def get_client(self, oauth_token: str) -> ArtClient:
        """Construct GPTClient based on config."""
        return self.client.construct(
            waiter=self.waiter.construct(),
            auth_service=AuthService(oauth_token),
        )


@dataclass
class YCConfig:
    """Yandex Cloud configuration class."""

    oauth_token: str
    ya_gpt: YaGPTConfig
    ya_art: YaArtConfig

    def __str__(self) -> str:
        return f"YC(ya_gpt={self.ya_gpt}, ya_art={self.ya_art}, oauth_token=...{self.oauth_token[-4:]})"

    @property
    def __dict__(self) -> dict:
        """Dict transformer used in `vars()`."""
        return {
            "oauth_token": self.oauth_token,
            "ya_gpt": vars(self.ya_gpt),
            "ya_art": vars(self.ya_art),
        }

    @classmethod
    def from_init(cls, init_data: dict) -> "YCConfig":
        """Construct YaGPTConfig from init data passed as dict."""
        ya_gpt = YaGPTConfig.from_init(init_data["ya_gpt"])
        ya_art = YaGPTConfig.from_init(init_data["ya_art"])
        return cls(init_data["oauth_token"], ya_gpt, ya_art)

    def get_gpt_client(self) -> GPTClient:
        """Construct GPTClient based on config."""
        return self.ya_gpt.get_client(self.oauth_token)

    def get_art_client(self) -> ArtClient:
        """Construct ArtClient based on config."""
        return self.ya_art.get_client(self.oauth_token)


@dataclass
class DatabaseConfig:
    """Database configuration class."""

    host: str
    port: int
    name: str
    user: str
    password: str
    pool_size: int = 15
    application_name: str = f"YaGPTBotPy_v{VERSION}"

    def __str__(self) -> str:
        return (
            f"Database(postgresql://{self.user}:...@{self.host}:{self.port}/{self.name}"
            f"?application_name={self.application_name})"
        )


@dataclass
class TgBotConfig:
    """Telegram Bot configuration class."""

    token: str
    gpt_trigger_prefixes: list[str] = field(default_factory=list)
    art_trigger_prefixes: list[str] = field(default_factory=list)
    ignore_prefixes: list[str] = field(default_factory=list)
    ignore_postfixes: list[str] = field(default_factory=list)
    max_retry_count: int = 3


@dataclass
class LoggingSink:
    """Logging sing class."""

    level: Literal["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"]
    path: str
    output_type: Literal["file"] = "file"


@dataclass
class LoggingConfig:
    """Logging configuration class."""

    console_level: Literal["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    sinks: list[LoggingSink] = field(default_factory=list)

    @classmethod
    def from_init(cls, init_data: dict[str, Any]):
        """Construct LoggingConfig from init data passed as dict."""
        return cls(init_data["console_level"], [LoggingSink(**sink) for sink in init_data.get("sinks", [])])

    @property
    def __dict__(self) -> dict:
        """Dict transformer used in `vars()`."""
        return {
            "console_level": self.console_level,
            "sinks": [vars(sink) for sink in self.sinks],
        }


class AppConfig:  # pylint: disable=too-many-instance-attributes
    """Bot application configuration class holding info about YandexGPT
    and database configurations.
    """

    def __init__(
        self,
        yc: YCConfig = ...,  # type: ignore
        db: DatabaseConfig = ...,  # type: ignore
        tg_bot: TgBotConfig = ...,  # type: ignore
        logging: LoggingConfig = ...,  # type: ignore
    ):
        if not hasattr(self, "ya_gpt") or yc is not ... and getattr(self, "ya_gpt") != yc:
            self.yc = yc
        if not hasattr(self, "db") or db is not ... and getattr(self, "db") != db:
            self.db = db
        if not hasattr(self, "tg_bot") or tg_bot is not ... and getattr(self, "tg_bot") != tg_bot:
            self.tg_bot = tg_bot
        if not hasattr(self, "logging") or logging is not ... and getattr(self, "logging") != logging:
            self.logging = logging

    @classmethod
    def example(cls) -> "AppConfig":
        """Return example config to understand the structure."""
        return cls(
            YCConfig(
                "yandex-cloud-oauth-token",
                YaGPTConfig(
                    ClassInitializer(
                        "ya_gpt_bot.ya_gpt.waiter.AsyncWaiterLock",
                        kwargs={
                            "max_requests_per_second": 1,
                            "simultanious_requests": 1,
                        },
                    ),
                    ClassInitializer(
                        "ya_gpt_bot.ya_gpt.client.YaGPTClient",
                        kwargs={
                            "host": "https://llm.api.cloud.yandex.net",
                            "folder_id": "yandex-cloud-folder-id",
                            "model": "general",
                            "creativity": 0.5,
                            "instruction_text": "",
                        },
                    ),
                ),
                YaArtConfig(
                    ClassInitializer(
                        "ya_gpt_bot.ya_gpt.waiter.AsyncWaiterLock",
                        kwargs={
                            "max_requests_per_second": 1,
                            "simultanious_requests": 1,
                        },
                    ),
                    ClassInitializer(
                        "ya_gpt_bot.ya_gpt.client.YaArtClient",
                        kwargs={
                            "host": "https://llm.api.cloud.yandex.net",
                            "folder_id": "yandex-cloud-folder-id",
                            "model": "yandex-art/latest",
                        },
                    ),
                ),
            ),
            DatabaseConfig("localhost", 5432, "ya_gpt_bot", "ya_gpt_bot", "ya-gpt-bot-password-in-db"),
            TgBotConfig(
                "tg-bot-token",
                gpt_trigger_prefixes=["Alice", "yagpt"],
                art_trigger_prefixes=["yaart"],
                ignore_prefixes=["-"],
                ignore_postfixes=["-"],
                max_retry_count=3,
            ),
            LoggingConfig("INFO", sinks=[LoggingSink("DEBUG", "debug.log", "file")]),
        )

    @property
    def __dict__(self) -> dict:
        """Dict transformer used in `vars()`."""
        return {
            "yc": vars(self.yc),
            "db": vars(self.db),
            "tg_bot": vars(self.tg_bot),
            "logging": vars(self.logging),
        }

    def __str__(self) -> str:
        return f"AppConfig(yc={self.yc}, db={self.db}, tg_bot={self.tg_bot}, logging={self.logging})"

    def dump(self, file: str | Path | TextIO) -> None:
        """Export current configuration to a file"""

        class MyDumper(yaml.Dumper):  # pylint: disable=too-many-ancestors
            """Custom dumper to increase indent for lists."""

            def increase_indent(self, flow=False, indentless=False):
                return super(MyDumper, self).increase_indent(flow, False)  # pylint: disable=super-with-arguments

        if isinstance(file, (str, Path)):
            with open(str(file), "w", encoding="utf-8") as file_w:
                yaml.dump(vars(self), file_w, Dumper=MyDumper)
        else:
            yaml.dump(vars(self), file, Dumper=MyDumper)

    @classmethod
    def load(cls, file: str | Path | TextIO) -> "AppConfig":
        """Import config from the given filename or raise `ValueError` on error."""
        try:
            if isinstance(file, (str, Path)):
                with open(file, "r", encoding="utf-8") as file_r:
                    data = yaml.safe_load(file_r)
            else:
                data = yaml.safe_load(file)
            return cls(
                YCConfig.from_init(data["yc"]),
                DatabaseConfig(**data["db"]),
                TgBotConfig(**data["tg_bot"]),
                LoggingConfig.from_init(data["logging"]),
            )
        except Exception as exc:
            raise ValueError("Could not read app config file") from exc
