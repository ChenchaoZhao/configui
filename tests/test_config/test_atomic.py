# ruff: noqa: SLF001

from pathlib import Path

import pytest

from configui.config._atomic import atomic_update, atomic_write


class TestAtomicUpdate:
    def test_updates_existing_keys(self) -> None:
        data: dict[str, str] = {"a": "1", "b": "2"}
        atomic_update(data, {"a": "10", "b": "20"}, allow_new_keys=False, allow_missing_keys=True)
        assert data == {"a": "10", "b": "20"}

    def test_raises_on_extra_key(self) -> None:
        data: dict[str, str] = {"a": "1"}
        with pytest.raises(KeyError, match="Keys not found in config"):
            atomic_update(data, {"a": "1", "b": "2"}, allow_new_keys=False, allow_missing_keys=True)
        assert data == {"a": "1"}

    def test_adds_new_key_when_allowed(self) -> None:
        data: dict[str, str] = {"a": "1"}
        atomic_update(data, {"a": "10", "b": "20"}, allow_new_keys=True, allow_missing_keys=True)
        assert data == {"a": "10", "b": "20"}

    def test_raises_on_missing_key(self) -> None:
        data: dict[str, str] = {"a": "1", "b": "2"}
        with pytest.raises(KeyError, match="Missing keys in update"):
            atomic_update(data, {"a": "10"}, allow_new_keys=True, allow_missing_keys=False)
        assert data == {"a": "1", "b": "2"}

    def test_exact_match_succeeds(self) -> None:
        data: dict[str, str] = {"a": "1", "b": "2"}
        atomic_update(data, {"a": "10", "b": "20"}, allow_new_keys=False, allow_missing_keys=False)
        assert data == {"a": "10", "b": "20"}

    def test_preserves_data_on_failure(self) -> None:
        data: dict[str, str] = {"a": "1"}
        with pytest.raises(KeyError):
            atomic_update(data, {"b": "2"}, allow_new_keys=False, allow_missing_keys=True)
        assert data == {"a": "1"}

    def test_empty_data_raises_key_error(self) -> None:
        data: dict[str, str] = {}
        with pytest.raises(KeyError, match="Keys not found in config"):
            atomic_update(data, {"a": "1"}, allow_new_keys=False, allow_missing_keys=True)
        assert data == {}

    def test_env_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import configui.config._atomic as m  # noqa: PLC0415 — need module ref for setattr

        monkeypatch.setattr(m, "_ALLOW_NEW_KEYS", False)
        monkeypatch.setattr(m, "_ALLOW_MISSING_KEYS", False)
        data: dict[str, str] = {"a": "1", "b": "2"}
        m.atomic_update(
            data, {"a": "10", "b": "20"}, allow_new_keys=m._ALLOW_NEW_KEYS, allow_missing_keys=m._ALLOW_MISSING_KEYS
        )
        assert data == {"a": "10", "b": "20"}


class TestAtomicWrite:
    def test_writes_content_to_file(self, tmp_path: Path) -> None:
        path = tmp_path / "config.json"

        def writer(f):
            f.write("hello world")

        atomic_write(path, writer)
        assert path.read_text() == "hello world"

    def test_overwrites_existing_file(self, tmp_path: Path) -> None:
        path = tmp_path / "config.json"
        path.write_text("old content")

        def writer(f):
            f.write("new content")

        atomic_write(path, writer)
        assert path.read_text() == "new content"

    def test_leaves_no_temp_file_on_success(self, tmp_path: Path) -> None:
        path = tmp_path / "config.json"
        temp_files_before = set(tmp_path.iterdir())

        def writer(f):
            f.write("data")

        atomic_write(path, writer)
        temp_files_after = set(tmp_path.iterdir())
        assert temp_files_after == temp_files_before | {path}

    def test_leaves_no_temp_file_on_writer_failure(self, tmp_path: Path) -> None:
        path = tmp_path / "config.json"

        class WriterError(Exception):
            pass

        msg = "oh no"

        def writer(_):
            raise WriterError(msg)

        with pytest.raises(RuntimeError, match="Failed to save config"):
            atomic_write(path, writer)
        assert not path.exists()
        assert not list(tmp_path.iterdir())

    def test_does_not_corrupt_existing_file_on_writer_failure(self, tmp_path: Path) -> None:
        path = tmp_path / "config.json"
        path.write_text("original")

        class WriterError(Exception):
            pass

        msg = "oh no"

        def writer(_):
            raise WriterError(msg)

        with pytest.raises(RuntimeError, match="Failed to save config"):
            atomic_write(path, writer)
        assert path.read_text() == "original"

    def test_raises_file_not_found_on_nonexistent_parent_dir(self) -> None:
        path = Path("/nonexistent_dir/config.json")

        def writer(_):
            pass

        with pytest.raises(FileNotFoundError):
            atomic_write(path, writer)
