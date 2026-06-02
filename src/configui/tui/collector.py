from __future__ import annotations

from typing import Any, cast

from textual.containers import Horizontal, Vertical
from textual.widgets import Collapsible, Input, Static, Switch


def _extract_value(widget: Switch | Input) -> Any:
    if isinstance(widget, Switch):
        return widget.value
    if widget.type == "integer":
        return int(widget.value)
    if widget.type == "number":
        return float(widget.value)
    return widget.value


def _content_children(coll: Collapsible):
    """Yield actual user-provided children of a Collapsible, skipping internal wrappers."""
    contents = list(coll.children)[1]
    yield from contents.children


def _collect(widget: Horizontal | Collapsible, container: dict[str, Any] | list[Any]) -> None:
    if isinstance(widget, Horizontal):
        label = cast("Static", widget.children[0])
        value_widget = cast("Switch | Input", widget.children[1])
        key = str(label.content)
        value = _extract_value(value_widget)
        if isinstance(container, dict):
            container[key] = value
        else:
            container.append(value)
    elif isinstance(widget, Collapsible):
        sub: list[Any] | dict[str, Any]
        if "container-dict" in widget.classes:
            sub = {}
            for child in _content_children(widget):
                _collect(cast("Horizontal | Collapsible", child), sub)
        elif "container-list" in widget.classes:
            sub = []
            for child in _content_children(widget):
                _collect(cast("Horizontal | Collapsible", child), sub)
        else:
            return

        if isinstance(container, dict):
            key = str(widget.title)
            if "container-list" in widget.classes:
                key = key.rsplit(" [", 1)[0]
            container[key] = sub
        else:
            container.append(sub)


def map_widgets_to_config(root: Vertical) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for child in root.children:
        _collect(cast("Horizontal | Collapsible", child), result)
    return result
