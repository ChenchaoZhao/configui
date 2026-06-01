from __future__ import annotations

import os
import tempfile
from contextlib import suppress
from pathlib import Path
from typing import IO, TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable


def atomic_write(path: Path, writer: Callable[[IO[str]], None]) -> None:
    path = Path(path)
    fd, tmp_path = tempfile.mkstemp(suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as f:
            writer(f)
        os.replace(tmp_path, path)
    except BaseException as e:
        msg = f"Failed to save config to '{path}'"
        raise RuntimeError(msg) from e
    finally:
        with suppress(BaseException):
            os.unlink(tmp_path)
