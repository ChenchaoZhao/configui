from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import tomlkit
from tomlkit.exceptions import TOMLKitError

from configui.config._atomic import atomic_write
from configui.config._protocol import Config

if TYPE_CHECKING:
    from collections.abc import Mapping


class TomlConfig(Config):
    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._data: Mapping[str, Any] = {}

    def load(self, **kwargs: Any) -> None:
        try:
            self._data = tomlkit.parse(self._path.read_text(**kwargs))
        except TOMLKitError as e:
            msg = f"Failed to parse TOML file '{self._path}': {e}"
            raise ValueError(msg) from e

    def save(self, **_kwargs: Any) -> None:
        atomic_write(self._path, lambda f: tomlkit.dump(self._data, f))

    def save_as(self, new_path: Path, **_kwargs: Any) -> None:
        atomic_write(new_path, lambda f: tomlkit.dump(self._data, f))
