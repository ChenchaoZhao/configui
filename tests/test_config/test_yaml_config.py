# ruff: noqa: SLF001

from pathlib import Path

import pytest

from configui.config.yaml_config import YamlConfig


class TestYamlConfig:
    def test_load_reads_valid_yaml_object(self, tmp_path: Path) -> None:
        path = tmp_path / "config.yaml"
        path.write_text("key: value\n")
        config = YamlConfig(path)
        config.load()
        assert config._data == {"key": "value"}

    def test_load_reads_yaml_with_all_types(self, tmp_path: Path) -> None:
        path = tmp_path / "config.yaml"
        path.write_text(
            "null_val: null\n"
            "bool_val: true\n"
            "int_val: 42\n"
            "float_val: 3.14\n"
            "str_val: hello\n"
            "list_val:\n"
            "  - 1\n"
            "  - 2\n"
            "  - 3\n"
            "dict_val:\n"
            "  a: 1\n"
        )
        config = YamlConfig(path)
        config.load()
        assert config._data["null_val"] is None
        assert config._data["bool_val"] is True
        assert config._data["int_val"] == 42
        assert config._data["float_val"] == 3.14
        assert config._data["str_val"] == "hello"
        assert config._data["list_val"] == [1, 2, 3]
        assert config._data["dict_val"] == {"a": 1}

    def test_load_reads_yaml_array(self, tmp_path: Path) -> None:
        path = tmp_path / "config.yaml"
        path.write_text("- 1\n- 2\n- 3\n")
        config = YamlConfig(path)
        config.load()
        assert config._data == [1, 2, 3]

    def test_load_reads_nested_structure(self, tmp_path: Path) -> None:
        path = tmp_path / "config.yaml"
        path.write_text("level1:\n  level2:\n    level3: deep\n")
        config = YamlConfig(path)
        config.load()
        assert config._data["level1"]["level2"]["level3"] == "deep"

    def test_load_with_malformed_yaml_raises_value_error(self, tmp_path: Path) -> None:
        path = tmp_path / "config.yaml"
        path.write_text("[1, 2\n")
        config = YamlConfig(path)
        with pytest.raises(ValueError, match="Failed to parse YAML"):
            config.load()

    def test_load_with_nonexistent_file_raises_file_not_found(self, tmp_path: Path) -> None:
        path = tmp_path / "nonexistent.yaml"
        config = YamlConfig(path)
        with pytest.raises(FileNotFoundError):
            config.load()

    def test_save_writes_correct_content(self, tmp_path: Path) -> None:
        path = tmp_path / "config.yaml"
        path.write_text("key: value\n")
        config = YamlConfig(path)
        config.load()
        config.save()
        assert path.read_text() == "key: value\n"

    def test_save_as_writes_to_new_path(self, tmp_path: Path) -> None:
        path = tmp_path / "config.yaml"
        new_path = tmp_path / "new_config.yaml"
        path.write_text("key: value\n")
        config = YamlConfig(path)
        config.load()
        config.save_as(new_path)
        assert new_path.read_text() == "key: value\n"
        assert config._path == path

    def test_round_trip_preserves_comments(self, tmp_path: Path) -> None:
        path = tmp_path / "config.yaml"
        content = "# Top-level comment\nkey: value\n# Nested comment\nnested:\n  # Inner comment\n  inner: value\n"
        path.write_text(content)
        config = YamlConfig(path)
        config.load()
        config._data["new_key"] = "new_value"
        config.save()
        saved = path.read_text()
        assert "# Top-level comment" in saved
        assert "# Nested comment" in saved
        assert "# Inner comment" in saved
        assert "new_key: new_value" in saved

    def test_round_trip_preserves_anchors(self, tmp_path: Path) -> None:
        path = tmp_path / "config.yaml"
        content = "defaults: &defaults\n  key: value\nitem:\n  <<: *defaults\n"
        path.write_text(content)
        config = YamlConfig(path)
        config.load()
        assert config._data["item"]["key"] == "value"
        config.save()
        saved = path.read_text()
        assert "&defaults" in saved
        assert "*defaults" in saved

    def test_update_round_trip(self, tmp_path: Path) -> None:
        path = tmp_path / "config.yaml"
        path.write_text("key: value\n")
        config = YamlConfig(path)
        config.load()
        config.update({"key": "new_value"})
        config.save()
        config2 = YamlConfig(path)
        config2.load()
        assert config2._data == {"key": "new_value"}

    def test_round_trip_preserves_data(self, tmp_path: Path) -> None:
        path = tmp_path / "config.yaml"
        config = YamlConfig(path)
        config._data = {"name": "test", "count": 42, "nested": {"flag": True}}
        config.save()
        config2 = YamlConfig(path)
        config2.load()
        assert config2._data == {"name": "test", "count": 42, "nested": {"flag": True}}
