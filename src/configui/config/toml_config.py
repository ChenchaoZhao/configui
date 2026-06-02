from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import tomlkit
from tomlkit.exceptions import TOMLKitError

from configui.config._atomic import _ALLOW_MISSING_KEYS, _ALLOW_NEW_KEYS, atomic_update, atomic_write
from configui.config._protocol import Config

if TYPE_CHECKING:
    from collections.abc import MutableMapping


class TomlConfig(Config):
    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._data: MutableMapping[str, Any] = {}

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

    def update(
        self, data: dict[str, Any], *, allow_new_keys: bool | None = None, allow_missing_keys: bool | None = None
    ) -> None:
        _allow_new = allow_new_keys if allow_new_keys is not None else _ALLOW_NEW_KEYS
        _allow_missing = allow_missing_keys if allow_missing_keys is not None else _ALLOW_MISSING_KEYS
        atomic_update(self._data, data, allow_new_keys=_allow_new, allow_missing_keys=_allow_missing)
