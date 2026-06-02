# ruff: noqa: SLF001

import json
from pathlib import Path

import pytest

from configui.config.json_config import JsonConfig


class TestJsonConfig:
    def test_load_reads_valid_json_object(self, tmp_path: Path) -> None:
        path = tmp_path / "config.json"
        path.write_text('{"key": "value"}')
        config = JsonConfig(path)
        config.load()
        assert config._data == {"key": "value"}

    def test_load_reads_json_with_all_types(self, tmp_path: Path) -> None:
        path = tmp_path / "config.json"
        path.write_text(
            json.dumps(
                {
                    "null_val": None,
                    "bool_val": True,
                    "int_val": 42,
                    "float_val": 3.14,
                    "str_val": "hello",
                    "list_val": [1, 2, 3],
                    "dict_val": {"a": 1},
                }
            )
        )
        config = JsonConfig(path)
        config.load()
        assert config._data["null_val"] is None
        assert config._data["bool_val"] is True
        assert config._data["int_val"] == 42
        assert config._data["float_val"] == 3.14
        assert config._data["str_val"] == "hello"
        assert config._data["list_val"] == [1, 2, 3]
        assert config._data["dict_val"] == {"a": 1}

    def test_load_reads_json_array(self, tmp_path: Path) -> None:
        path = tmp_path / "config.json"
        path.write_text("[1, 2, 3]")
        config = JsonConfig(path)
        config.load()
        assert config._data == [1, 2, 3]

    def test_load_reads_nested_structure(self, tmp_path: Path) -> None:
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"level1": {"level2": {"level3": "deep"}}}))
        config = JsonConfig(path)
        config.load()
        assert config._data["level1"]["level2"]["level3"] == "deep"

    def test_load_with_malformed_json_raises_value_error(self, tmp_path: Path) -> None:
        path = tmp_path / "config.json"
        path.write_text("{invalid}")
        config = JsonConfig(path)
        with pytest.raises(ValueError, match="Failed to parse JSON"):
            config.load()

    def test_load_with_empty_file_raises_value_error(self, tmp_path: Path) -> None:
        path = tmp_path / "config.json"
        path.write_text("")
        config = JsonConfig(path)
        with pytest.raises(ValueError, match="Failed to parse JSON"):
            config.load()

    def test_load_with_nonexistent_file_raises_file_not_found(self, tmp_path: Path) -> None:
        path = tmp_path / "nonexistent.json"
        config = JsonConfig(path)
        with pytest.raises(FileNotFoundError):
            config.load()

    def test_save_writes_correct_content(self, tmp_path: Path) -> None:
        path = tmp_path / "config.json"
        path.write_text('{"key": "value"}')
        config = JsonConfig(path)
        config.load()
        config.save()
        assert path.read_text() == '{\n  "key": "value"\n}'

    def test_save_with_unicode_preserves_chars(self, tmp_path: Path) -> None:
        path = tmp_path / "config.json"
        path.write_text('{"emoji": "🎉", "chinese": "你好"}')
        config = JsonConfig(path)
        config.load()
        config.save()
        content = path.read_text()
        assert "🎉" in content
        assert "你好" in content

    def test_save_as_writes_to_new_path(self, tmp_path: Path) -> None:
        path = tmp_path / "config.json"
        new_path = tmp_path / "new_config.json"
        path.write_text('{"key": "value"}')
        config = JsonConfig(path)
        config.load()
        config.save_as(new_path)
        assert new_path.read_text() == '{\n  "key": "value"\n}'
        assert config._path == path

    def test_update_round_trip(self, tmp_path: Path) -> None:
        path = tmp_path / "config.json"
        path.write_text('{"key": "value"}')
        config = JsonConfig(path)
        config.load()
        config.update({"key": "new_value"})
        config.save()
        config2 = JsonConfig(path)
        config2.load()
        assert config2._data == {"key": "new_value"}

    def test_round_trip_preserves_data(self, tmp_path: Path) -> None:
        original = {"name": "test", "count": 42, "nested": {"flag": True}}
        path = tmp_path / "config.json"
        config = JsonConfig(path)
        config._data = original
        config.save()
        config2 = JsonConfig(path)
        config2.load()
        assert config2._data == original
