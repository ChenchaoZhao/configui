from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

from configui.config._atomic import atomic_write
from configui.config._protocol import Config

if TYPE_CHECKING:
    from collections.abc import Mapping


class YamlConfig(Config):
    def __init__(self, path: str | Path, yaml_type: str = "rt") -> None:
        """Initialize YamlConfig.

        Args:
            path: Path to the YAML file.
            yaml_type: ruamel.yaml round-trip mode — ``"rt"`` preserves
                comments, anchors, aliases, and key ordering on load/edit/save.
        """
        self._path = Path(path)
        self._data: Mapping[str, Any] = {}
        self._yaml = YAML(typ=yaml_type)

    def load(self, **kwargs: Any) -> None:
        try:
            self._data = self._yaml.load(self._path.read_text(**kwargs))
        except YAMLError as e:
            msg = f"Failed to parse YAML file '{self._path}': {e}"
            raise ValueError(msg) from e

    def save(self, **_kwargs: Any) -> None:
        atomic_write(self._path, lambda f: self._yaml.dump(self._data, f))

    def save_as(self, new_path: Path, **_kwargs: Any) -> None:
        atomic_write(new_path, lambda f: self._yaml.dump(self._data, f))
