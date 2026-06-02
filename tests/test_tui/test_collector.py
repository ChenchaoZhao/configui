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
