from pathlib import Path
from typing import Any

from configui.config.protocol import Config


class SubclassConfig(Config):
    def __init__(self, path: str | Path) -> None:
        self._data: dict = {}
        self._path = Path(path)

    def load(self, **kwargs: Any) -> None: ...

    def save(self, **kwargs: Any) -> None: ...

    def save_as(self, new_path: Path, **kwargs: Any) -> None: ...


def test_config_is_a_protocol() -> None:
    assert isinstance(Config, type)


def test_concrete_implementation_satisfies_protocol() -> None:
    _: Config = SubclassConfig("config.json")
