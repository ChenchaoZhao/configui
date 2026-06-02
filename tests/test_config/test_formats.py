import pytest

from configui.config.formats import SupportedConfigFormat


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
