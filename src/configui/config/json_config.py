from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any


class JsonConfig:
    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._data: Any = None

    def load(self, **kwargs: Any) -> None:
        try:
            self._data = json.loads(self._path.read_text(**kwargs))
        except json.JSONDecodeError as e:
            msg = f"Failed to parse JSON file '{self._path}': {e}"
            raise ValueError(msg) from e

    def save(self, **kwargs: Any) -> None:
        self._path.write_text(json.dumps(self._data, indent=2, ensure_ascii=False, **kwargs))

    def save_as(self, new_path: Path, **kwargs: Any) -> None:
        new_path = Path(new_path)
        fd, tmp_path = tempfile.mkstemp(suffix=".tmp", dir=new_path.parent)
        try:
            with os.fdopen(fd, "w") as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False, **kwargs)
            os.replace(tmp_path, new_path)
        except BaseException:
            os.unlink(tmp_path)
            raise
