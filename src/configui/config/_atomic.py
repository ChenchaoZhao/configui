from __future__ import annotations

import os
import tempfile
from contextlib import suppress
from pathlib import Path
from typing import IO, TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable, MutableMapping

_ALLOW_NEW_KEYS: bool = os.environ.get("CONFIGUI_UPDATE_ALLOW_NEW_KEYS", "0") == "1"
_ALLOW_MISSING_KEYS: bool = os.environ.get("CONFIGUI_UPDATE_ALLOW_MISSING_KEYS", "1") == "1"


def atomic_update(
    data: MutableMapping,
    updates: dict[str, Any],
    *,
    allow_new_keys: bool,
    allow_missing_keys: bool,
) -> None:
    if not allow_new_keys:
        extra = updates.keys() - data.keys()
        if extra:
            msg = f"Keys not found in config: {sorted(extra)}"
            raise KeyError(msg)
    if not allow_missing_keys:
        missing = data.keys() - updates.keys()
        if missing:
            msg = f"Missing keys in update: {sorted(missing)}"
            raise KeyError(msg)
    for k, v in updates.items():
        data[k] = v


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
