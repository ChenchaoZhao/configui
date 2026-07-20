from __future__ import annotations

import asyncio
from typing import Any

from textual.app import App
from textual.containers import Vertical

from configui.tui.collector import map_widgets_to_config
from configui.tui.widgets import map_config_to_widgets


def _roundtrip(
    config: dict[str, Any],
    *,
    regex_overrides: dict[str, str] | None = None,
) -> dict[str, Any]:
    class _TestApp(App):
        def compose(self):
            yield map_config_to_widgets(config, regex_overrides=regex_overrides)

    async def _run() -> dict[str, Any]:
        app = _TestApp()
        async with app.run_test():
            root = app.query_one(Vertical)
            return map_widgets_to_config(root)

    return asyncio.run(_run())


def _collect_with_edits(
    config: dict[str, Any],
    edits: dict[str, Any],
    *,
    regex_overrides: dict[str, str] | None = None,
) -> dict[str, Any]:
    class _TestApp(App):
        def compose(self):
            yield map_config_to_widgets(config, regex_overrides=regex_overrides)

    async def _run() -> dict[str, Any]:
        app = _TestApp()
        async with app.run_test():
            for widget_id, new_val in edits.items():
                node = app.query_one(f"#{widget_id}")
                if hasattr(node, "value"):
                    if isinstance(new_val, bool):
                        node.value = new_val
                    else:
                        node.value = str(new_val)
            root = app.query_one(Vertical)
            return map_widgets_to_config(root)

    return asyncio.run(_run())


class TestRoundtrip:
    def test_bool_roundtrip(self) -> None:
        original = {"enabled": True}
        assert _roundtrip(original) == original

    def test_int_roundtrip(self) -> None:
        original = {"count": 42}
        assert _roundtrip(original) == original

    def test_float_roundtrip(self) -> None:
        original = {"ratio": 3.14}
        assert _roundtrip(original) == original

    def test_str_roundtrip(self) -> None:
        original = {"name": "hello"}
        assert _roundtrip(original) == original

    def test_mixed_scalars_roundtrip(self) -> None:
        original = {"a": True, "b": 1, "c": 2.0, "d": "s"}
        assert _roundtrip(original) == original


class TestNestedRoundtrip:
    def test_nested_dict_roundtrip(self) -> None:
        original = {"optimizer": {"lr": 0.001, "momentum": 0.9}}
        assert _roundtrip(original) == original

    def test_list_roundtrip(self) -> None:
        original = {"metrics": ["acc", "f1"]}
        assert _roundtrip(original) == original

    def test_list_of_ints_roundtrip(self) -> None:
        original = {"layers": [10, 20, 30]}
        assert _roundtrip(original) == original

    def test_list_of_floats_roundtrip(self) -> None:
        original = {"values": [1.5, 2.5]}
        assert _roundtrip(original) == original

    def test_list_of_bools_roundtrip(self) -> None:
        original = {"flags": [True, False]}
        assert _roundtrip(original) == original

    def test_nested_dict_three_levels(self) -> None:
        original = {"model": {"config": {"lr": 0.001}}}
        assert _roundtrip(original) == original

    def test_dict_inside_list(self) -> None:
        original = {"items": [{"a": 1}, {"b": 2}]}
        assert _roundtrip(original) == original

    def test_list_inside_dict(self) -> None:
        original = {"model": {"layers": [10, 20]}}
        assert _roundtrip(original) == original

    def test_deeply_nested_complex(self) -> None:
        original = {
            "training": {
                "optimizer": {
                    "lr": 0.001,
                    "scheduler": {"steps": [100, 200, 300], "gamma": 0.1},
                },
                "metrics": ["acc", "f1"],
            }
        }
        assert _roundtrip(original) == original


class TestEdgeCases:
    def test_empty_dict_roundtrip(self) -> None:
        original = {"empty": {}}
        assert _roundtrip(original) == original

    def test_empty_list_roundtrip(self) -> None:
        original = {"empty": []}
        assert _roundtrip(original) == original

    def test_empty_top_level(self) -> None:
        assert _roundtrip({}) == {}

    def test_mixed_empty_containers(self) -> None:
        original = {"a": {}, "b": [], "c": {"d": {}}}
        assert _roundtrip(original) == original


class TestEdits:
    def test_edit_bool(self) -> None:
        original = {"enabled": True}
        result = _collect_with_edits(original, {"enabled": False})
        assert result == {"enabled": False}

    def test_edit_int(self) -> None:
        original = {"count": 42}
        result = _collect_with_edits(original, {"count": 99})
        assert result == {"count": 99}

    def test_edit_float(self) -> None:
        original = {"ratio": 3.14}
        result = _collect_with_edits(original, {"ratio": 2.718})
        assert result == {"ratio": 2.718}

    def test_edit_str(self) -> None:
        original = {"name": "hello"}
        result = _collect_with_edits(original, {"name": "world"})
        assert result == {"name": "world"}

    def test_edit_nested_value(self) -> None:
        original = {"optimizer": {"lr": 0.001, "momentum": 0.9}}
        result = _collect_with_edits(original, {"optimizer_lr": 0.01})
        assert result == {"optimizer": {"lr": 0.01, "momentum": 0.9}}

    def test_empty_int_field_returns_zero(self) -> None:
        original = {"count": 42}
        result = _collect_with_edits(original, {"count": ""})
        assert result == {"count": 0}

    def test_empty_float_field_returns_zero(self) -> None:
        original = {"ratio": 3.14}
        result = _collect_with_edits(original, {"ratio": ""})
        assert result == {"ratio": 0.0}

    def test_empty_int_in_nested_dict_returns_zero(self) -> None:
        original = {"model": {"layers": 10}}
        result = _collect_with_edits(original, {"model_layers": ""})
        assert result == {"model": {"layers": 0}}

    def test_empty_int_in_list_returns_zero(self) -> None:
        original = {"layers": [10, 20, 30]}
        result = _collect_with_edits(original, {"layers_1": ""})
        assert result == {"layers": [10, 0, 30]}


class TestSpecialCharacters:
    def test_dollar_schema_roundtrip(self) -> None:
        original = {"$schema": "https://json-schema.org/draft-07/schema#", "type": "object"}
        assert _roundtrip(original) == original

    def test_dollar_in_nested_key_roundtrip(self) -> None:
        original = {"config": {"$ref": "#/definitions/Foo", "name": "bar"}}
        assert _roundtrip(original) == original

    def test_dollar_schema_edit(self) -> None:
        original = {"$schema": "https://json-schema.org/draft-07/schema#", "version": "1.0"}
        result = _collect_with_edits(original, {"_schema": "https://json-schema.org/draft-07/schema#"})
        assert result == original
