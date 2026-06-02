# ruff: noqa: SLF001

from pathlib import Path

import pytest

from configui.config.toml_config import TomlConfig


class TestTomlConfig:
    def test_load_reads_valid_toml_object(self, tmp_path: Path) -> None:
        path = tmp_path / "config.toml"
        path.write_text('key = "value"\n')
        config = TomlConfig(path)
        config.load()
        assert config._data == {"key": "value"}

    def test_load_reads_toml_with_all_types(self, tmp_path: Path) -> None:
        path = tmp_path / "config.toml"
        path.write_text(
            "bool_val = true\n"
            "int_val = 42\n"
            "float_val = 3.14\n"
            'str_val = "hello"\n'
            "list_val = [1, 2, 3]\n"
            "dict_val = {a = 1}\n"
        )
        config = TomlConfig(path)
        config.load()
        assert config._data["bool_val"] is True
        assert config._data["int_val"] == 42
        assert config._data["float_val"] == 3.14
        assert config._data["str_val"] == "hello"
        assert config._data["list_val"] == [1, 2, 3]
        assert config._data["dict_val"] == {"a": 1}

    def test_load_reads_nested_structure(self, tmp_path: Path) -> None:
        path = tmp_path / "config.toml"
        path.write_text("[a]\n[b.c]\nd = 1\n")
        config = TomlConfig(path)
        config.load()
        assert config._data["a"] == {}
        assert config._data["b"]["c"]["d"] == 1

    def test_load_with_malformed_toml_raises_value_error(self, tmp_path: Path) -> None:
        path = tmp_path / "config.toml"
        path.write_text("key = = value\n")
        config = TomlConfig(path)
        with pytest.raises(ValueError, match="Failed to parse TOML"):
            config.load()

    def test_load_with_nonexistent_file_raises_file_not_found(self, tmp_path: Path) -> None:
        path = tmp_path / "nonexistent.toml"
        config = TomlConfig(path)
        with pytest.raises(FileNotFoundError):
            config.load()

    def test_save_writes_correct_content(self, tmp_path: Path) -> None:
        path = tmp_path / "config.toml"
        path.write_text('key = "value"\n')
        config = TomlConfig(path)
        config.load()
        config.save()
        assert path.read_text() == 'key = "value"\n'

    def test_save_as_writes_to_new_path(self, tmp_path: Path) -> None:
        path = tmp_path / "config.toml"
        new_path = tmp_path / "new_config.toml"
        path.write_text('key = "value"\n')
        config = TomlConfig(path)
        config.load()
        config.save_as(new_path)
        assert new_path.read_text() == 'key = "value"\n'
        assert config._path == path

    def test_round_trip_preserves_inline_tables(self, tmp_path: Path) -> None:
        path = tmp_path / "config.toml"
        content = "key = {a = 1, b = 2}\n"
        path.write_text(content)
        config = TomlConfig(path)
        config.load()
        config.save()
        saved = path.read_text()
        assert "{" in saved
        assert "}" in saved

    def test_round_trip_preserves_comments(self, tmp_path: Path) -> None:
        path = tmp_path / "config.toml"
        content = '# This is a comment\nkey = "value"\n'
        path.write_text(content)
        config = TomlConfig(path)
        config.load()
        config._data["new_key"] = "new_value"
        config.save()
        saved = path.read_text()
        assert "# This is a comment" in saved
        assert 'new_key = "new_value"' in saved

    def test_update_round_trip(self, tmp_path: Path) -> None:
        path = tmp_path / "config.toml"
        path.write_text('key = "value"\n')
        config = TomlConfig(path)
        config.load()
        config.update({"key": "new_value"})
        config.save()
        config2 = TomlConfig(path)
        config2.load()
        assert config2._data["key"] == "new_value"

    def test_round_trip_preserves_data(self, tmp_path: Path) -> None:
        path = tmp_path / "config.toml"
        content = 'name = "test"\ncount = 42\n'
        path.write_text(content)
        config = TomlConfig(path)
        config.load()
        config.save()
        config2 = TomlConfig(path)
        config2.load()
        assert config2._data["name"] == "test"
        assert config2._data["count"] == 42
