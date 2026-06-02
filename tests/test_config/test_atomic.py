from pathlib import Path

import pytest

from configui.config._atomic import atomic_write


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
