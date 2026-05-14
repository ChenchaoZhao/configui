from __future__ import annotations

from enum import StrEnum, auto
from pathlib import Path

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
