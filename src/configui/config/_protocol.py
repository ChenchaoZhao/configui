from collections.abc import Mapping
from pathlib import Path
from typing import Any, Protocol


class Config(Protocol):
    _data: Mapping
    _path: Path

    def load(self, **kwargs: Any) -> None: ...

    def save(self, **kwargs: Any) -> None: ...

    def save_as(self, new_path: Path, **kwargs: Any) -> None: ...

    def update(
        self, data: dict[str, Any], *, allow_new_keys: bool | None = None, allow_missing_keys: bool | None = None
    ) -> None: ...
