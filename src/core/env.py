from typing import Self, Tuple, Type

from pydantic import Field, model_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

from src.common.patterns import HOST_PATTERN


class EnvConfig(BaseSettings):
    """Loads and retrieves dotenv configuration data"""

    model_config = SettingsConfigDict(
        str_strip_whitespace=True,
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
    )

    database_file: str = Field(default="database.db", min_length=1)
    host: str = Field(
        default="127.0.0.1",
        pattern=HOST_PATTERN,
        min_length=7,
        max_length=15,
    )
    port: int = Field(default=8000, gt=0, lt=65535, decimal_places=None)
    reload: bool = Field(default=False)
    workers: int = Field(default=1, gt=0, lt=5, decimal_places=None)
    logging_file: bool = Field(default=False)
    debug: bool = Field(default=False)

    @classmethod
    def settings_customise_sources(  # pylint: disable=R0913,R0917
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        return (
            dotenv_settings,
            env_settings,
        )

    @model_validator(mode="after")
    def check_reload_with_workers(self) -> Self:
        if self.reload is True and self.workers > 1:
            raise ValueError(
                "\033[33mConfiguration conflict error:\033[31m cannot"
                " use reload together with multiple workers\033[m"
            )
        return self

    @property
    def log_config(self) -> tuple[str, int, bool, bool]:
        return self.host, self.port, self.logging_file, self.debug
