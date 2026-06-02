from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from configui.config.formats import SupportedConfigFormat
from configui.config.json_config import JsonConfig
from configui.config.toml_config import TomlConfig
from configui.config.yaml_config import YamlConfig

if TYPE_CHECKING:
    from configui.config._protocol import Config


class TestSupportedConfigFormat:
    def test_values(self) -> None:
        assert SupportedConfigFormat.JSON == "json"
        assert SupportedConfigFormat.YAML == "yaml"
        assert SupportedConfigFormat.TOML == "toml"

    @pytest.mark.parametrize(
        ("filename", "expected"),
        [
            ("config.json", SupportedConfigFormat.JSON),
            ("config.yaml", SupportedConfigFormat.YAML),
            ("config.yml", SupportedConfigFormat.YAML),
            ("config.toml", SupportedConfigFormat.TOML),
            ("/path/to/config.json", SupportedConfigFormat.JSON),
            ("/path/to/config.YAML", SupportedConfigFormat.YAML),
        ],
    )
    def test_from_filename_returns_correct_format(self, filename: str, expected: SupportedConfigFormat) -> None:
        assert SupportedConfigFormat.from_filename(filename) == expected

    @pytest.mark.parametrize(
        "filename",
        [
            "config.txt",
            "config",
            "config.ini",
            "",
        ],
    )
    def test_from_filename_with_unsupported_extension_raises_value_error(self, filename: str) -> None:
        with pytest.raises(ValueError, match=r"'[^']*' is not a valid SupportedConfigFormat"):
            SupportedConfigFormat.from_filename(filename)

    @pytest.mark.parametrize(
        ("fmt", "expected_cls"),
        [
            (SupportedConfigFormat.JSON, JsonConfig),
            (SupportedConfigFormat.YAML, YamlConfig),
            (SupportedConfigFormat.TOML, TomlConfig),
        ],
    )
    def test_get_config_cls_returns_correct_class(self, fmt: SupportedConfigFormat, expected_cls: type[Config]) -> None:
        assert fmt.get_config_cls() is expected_cls
