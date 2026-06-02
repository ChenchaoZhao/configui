from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

from configui.config._atomic import _ALLOW_MISSING_KEYS, _ALLOW_NEW_KEYS, atomic_update, atomic_write
from configui.config._protocol import Config

if TYPE_CHECKING:
    from collections.abc import MutableMapping


class YamlConfig(Config):
    def __init__(self, path: str | Path, yaml_type: str = "rt") -> None:
        """Initialize YamlConfig.

        Args:
            path: Path to the YAML file.
            yaml_type: ruamel.yaml round-trip mode — ``"rt"`` preserves
                comments, anchors, aliases, and key ordering on load/edit/save.
        """
        self._path = Path(path)
        self._data: MutableMapping[str, Any] = {}
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

    def update(
        self, data: dict[str, Any], *, allow_new_keys: bool | None = None, allow_missing_keys: bool | None = None
    ) -> None:
        _allow_new = allow_new_keys if allow_new_keys is not None else _ALLOW_NEW_KEYS
        _allow_missing = allow_missing_keys if allow_missing_keys is not None else _ALLOW_MISSING_KEYS
        atomic_update(self._data, data, allow_new_keys=_allow_new, allow_missing_keys=_allow_missing)
