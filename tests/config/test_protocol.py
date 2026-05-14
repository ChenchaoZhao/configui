from pathlib import Path

from configui.config.protocol import Config


class JSONConfig:
    def __init__(self, path: Path) -> None:
        self._data: dict = {}
        self._path = path

    def load(self, **kwargs: object) -> None: ...

    def save(self, **kwargs: object) -> None: ...

    def save_as(self, new_path: Path, **kwargs: object) -> None: ...


def test_config_is_a_protocol() -> None:
    assert isinstance(Config, type)


def test_concrete_implementation_satisfies_protocol() -> None:
    _: Config = JSONConfig(Path("config.json"))
