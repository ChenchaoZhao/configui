from __future__ import annotations

import asyncio
from typing import Any

from textual.app import App

from configui.tui.widgets import DEFAULT_FLOAT_RESTRICT, DEFAULT_INT_RESTRICT, map_config_to_widgets


def _collect(
    config: dict[str, Any],
    regex_overrides: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Run the mapper inside a Textual app and return all widget info as plain dicts."""

    class _TestApp(App):
        def compose(self):
            yield map_config_to_widgets(config, regex_overrides=regex_overrides)

    async def _run() -> list[dict[str, Any]]:
        app = _TestApp()
        async with app.run_test():
            items: list[dict[str, Any]] = []
            for node in app.walk_children():
                _id = node.id
                if _id is not None and not _id.startswith("_default"):
                    info: dict[str, Any] = {"id": _id, "type": type(node).__name__}

                    title = getattr(node, "title", None)
                    if title:
                        info["title"] = str(title)

                    value = getattr(node, "value", None)
                    if value is not None:
                        info["value"] = value

                    inp_type = getattr(node, "type", None)
                    if inp_type:
                        info["input_type"] = inp_type

                    restrict = getattr(node, "restrict", None)
                    if restrict is not None:
                        info["restrict"] = restrict

                    items.append(info)
            return items

    return asyncio.run(_run())


def _top() -> str:
    """Return the type name of the top-level widget returned by map_config_to_widgets."""

    class _TestApp(App):
        def compose(self):
            w = map_config_to_widgets({"a": 1})
            self.top_type = type(w).__name__
            yield w

    async def _run() -> str:
        app = _TestApp()
        async with app.run_test():
            return app.top_type

    return asyncio.run(_run())


class TestScalarMapping:
    def test_bool_maps_to_switch(self) -> None:
        items = _collect({"enabled": True})
        sw = next(i for i in items if i["id"] == "enabled")
        assert sw["type"] == "Switch"
        assert sw["value"] is True

    def test_bool_false_value(self) -> None:
        items = _collect({"enabled": False})
        sw = next(i for i in items if i["id"] == "enabled")
        assert sw["type"] == "Switch"
        assert sw["value"] is False

    def test_int_maps_to_input_integer(self) -> None:
        items = _collect({"count": 42})
        inp = next(i for i in items if i["id"] == "count")
        assert inp["type"] == "Input"
        assert inp["input_type"] == "integer"
        assert inp["value"] == "42"

    def test_int_has_default_restrict(self) -> None:
        items = _collect({"count": 42})
        inp = next(i for i in items if i["id"] == "count")
        assert inp["restrict"] == DEFAULT_INT_RESTRICT

    def test_float_maps_to_input_number(self) -> None:
        items = _collect({"ratio": 3.14})
        inp = next(i for i in items if i["id"] == "ratio")
        assert inp["type"] == "Input"
        assert inp["input_type"] == "number"
        assert inp["value"] == "3.14"

    def test_float_has_default_restrict(self) -> None:
        items = _collect({"ratio": 3.14})
        inp = next(i for i in items if i["id"] == "ratio")
        assert inp["restrict"] == DEFAULT_FLOAT_RESTRICT

    def test_str_maps_to_input_text(self) -> None:
        items = _collect({"name": "hello"})
        inp = next(i for i in items if i["id"] == "name")
        assert inp["type"] == "Input"
        assert inp["input_type"] == "text"
        assert inp["value"] == "hello"

    def test_str_has_no_restrict(self) -> None:
        items = _collect({"name": "hello"})
        inp = next(i for i in items if i["id"] == "name")
        assert "restrict" not in inp


class TestNestedMapping:
    def test_dict_maps_to_collapsible(self) -> None:
        items = _collect({"optimizer": {"lr": 0.001, "momentum": 0.9}})
        coll = next(i for i in items if i["type"] == "Collapsible")
        assert coll["title"] == "optimizer"

    def test_dict_contains_nested_inputs(self) -> None:
        items = _collect({"optimizer": {"lr": 0.001, "momentum": 0.9}})
        lr = next(i for i in items if i["id"] == "optimizer_lr")
        assert lr["value"] == "0.001"
        momentum = next(i for i in items if i["id"] == "optimizer_momentum")
        assert momentum["value"] == "0.9"

    def test_list_maps_to_collapsible_with_count(self) -> None:
        items = _collect({"metrics": ["acc", "f1"]})
        coll = next(i for i in items if i["type"] == "Collapsible" and i["title"] == "metrics [2]")
        assert coll is not None

    def test_list_contains_indexed_inputs(self) -> None:
        items = _collect({"metrics": ["acc", "f1"]})
        assert next(i for i in items if i["id"] == "metrics_0" and i["value"] == "acc")
        assert next(i for i in items if i["id"] == "metrics_1" and i["value"] == "f1")

    def test_nested_dict_creates_nested_collapsible(self) -> None:
        items = _collect({"model": {"config": {"lr": 0.001}}})
        outer = next(i for i in items if i["type"] == "Collapsible" and i["id"] == "model")
        assert outer is not None
        inner = next(i for i in items if i["type"] == "Collapsible" and i["id"] == "model_config")
        assert inner is not None

    def test_list_inside_dict_creates_nested_collapsible(self) -> None:
        items = _collect({"model": {"layers": [10, 20]}})
        layers = next(i for i in items if i["type"] == "Collapsible" and i["id"] == "model_layers")
        assert layers is not None
        assert next(i for i in items if i["id"] == "model_layers_0" and i["value"] == "10")

    def test_empty_dict_becomes_empty_collapsible(self) -> None:
        items = _collect({"empty": {}})
        coll = next(i for i in items if i["type"] == "Collapsible" and i["id"] == "empty")
        assert coll is not None

    def test_empty_list_becomes_empty_collapsible(self) -> None:
        items = _collect({"empty": []})
        coll = next(i for i in items if i["type"] == "Collapsible" and i["title"] == "empty [0]")
        assert coll is not None

    def test_mixed_types_in_dict(self) -> None:
        items = _collect({"a": True, "b": 1, "c": 1.0, "d": "s"})
        assert next(i for i in items if i["id"] == "a" and i["type"] == "Switch")
        assert next(i for i in items if i["id"] == "b" and i["type"] == "Input")
        assert next(i for i in items if i["id"] == "c" and i["type"] == "Input")
        assert next(i for i in items if i["id"] == "d" and i["type"] == "Input")


class TestRegexOverrides:
    def test_override_float_restrict(self) -> None:
        items = _collect({"lr": 0.001}, regex_overrides={"lr": r"^\d+\.\d+$"})
        inp = next(i for i in items if i["id"] == "lr")
        assert inp["restrict"] == r"^\d+\.\d+$"

    def test_override_int_restrict(self) -> None:
        items = _collect({"count": 42}, regex_overrides={"count": r"^\d+$"})
        inp = next(i for i in items if i["id"] == "count")
        assert inp["restrict"] == r"^\d+$"

    def test_override_str_restrict(self) -> None:
        items = _collect({"name": "hello"}, regex_overrides={"name": r"^[a-z]+$"})
        inp = next(i for i in items if i["id"] == "name")
        assert inp["restrict"] == r"^[a-z]+$"

    def test_nested_override_by_dotted_path(self) -> None:
        items = _collect(
            {"optimizer": {"lr": 0.001, "momentum": 0.9}},
            regex_overrides={"optimizer.lr": r"^\d+\.\d+$"},
        )
        lr = next(i for i in items if i["id"] == "optimizer_lr")
        assert lr["restrict"] == r"^\d+\.\d+$"
        momentum = next(i for i in items if i["id"] == "optimizer_momentum")
        assert momentum["restrict"] == DEFAULT_FLOAT_RESTRICT

    def test_override_applies_to_matching_path_only(self) -> None:
        items = _collect(
            {"lr": 0.001, "momentum": 0.9},
            regex_overrides={"lr": r"^\d+\.\d+$"},
        )
        lr = next(i for i in items if i["id"] == "lr")
        assert lr["restrict"] == r"^\d+\.\d+$"
        momentum = next(i for i in items if i["id"] == "momentum")
        assert momentum["restrict"] == DEFAULT_FLOAT_RESTRICT


class TestTopLevel:
    def test_returns_vertical(self) -> None:
        assert _top() == "Vertical"
