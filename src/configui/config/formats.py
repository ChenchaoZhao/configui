from __future__ import annotations

from enum import StrEnum, auto
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from configui.config._protocol import Config

from configui.config.json_config import JsonConfig
from configui.config.toml_config import TomlConfig
from configui.config.yaml_config import YamlConfig

_YAML_ALIASES: set[str] = {"yml", "yaml"}


class SupportedConfigFormat(StrEnum):
    JSON = auto()
    YAML = auto()
    TOML = auto()

    @classmethod
    def from_filename(cls, filename: str) -> SupportedConfigFormat:
        ext = Path(filename).suffix.lstrip(".").lower()
        if ext in _YAML_ALIASES:
            ext = "yaml"
        return cls(ext)

    def get_config_cls(self) -> type[Config]:
        return _CONFIG_CLASSES[self]


_CONFIG_CLASSES: dict[SupportedConfigFormat, type[Config]] = {
    SupportedConfigFormat.JSON: JsonConfig,
    SupportedConfigFormat.YAML: YamlConfig,
    SupportedConfigFormat.TOML: TomlConfig,
}
