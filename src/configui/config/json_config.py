from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from configui.config._atomic import atomic_write
from configui.config._protocol import Config

if TYPE_CHECKING:
    from collections.abc import Mapping


class JsonConfig(Config):
    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._data: Mapping[str, Any] = {}

    def load(self, **kwargs: Any) -> None:
        try:
            self._data = json.loads(self._path.read_text(**kwargs))
        except json.JSONDecodeError as e:
            msg = f"Failed to parse JSON file '{self._path}': {e}"
            raise ValueError(msg) from e

    def save(self, **kwargs: Any) -> None:
        atomic_write(self._path, lambda f: json.dump(self._data, f, indent=2, ensure_ascii=False, **kwargs))

    def save_as(self, new_path: Path, **kwargs: Any) -> None:
        atomic_write(new_path, lambda f: json.dump(self._data, f, indent=2, ensure_ascii=False, **kwargs))
