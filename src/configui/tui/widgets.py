from __future__ import annotations

from typing import TYPE_CHECKING, Any

from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Collapsible, DirectoryTree, Input, Static, Switch
from textual.widgets._directory_tree import DirEntry

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from textual.widgets._tree import TreeNode

DEFAULT_INT_RESTRICT: str = r"^-?\d*$"
DEFAULT_FLOAT_RESTRICT: str = r"^-?\d*(\.\d*)?([eE][+-]?\d+)?$"


def _safe_id(prefix: str, key: str) -> str:
    raw = f"{prefix}_{key}" if prefix else key
    return raw.replace(".", "_")


def _make_scalar_row(
    label: str,
    value: Any,
    *,
    widget_id: str | None = None,
    restrict: str | None = None,
    dotted_path: str | None = None,
) -> Horizontal:
    widget: Switch | Input
    if isinstance(value, bool):
        widget = Switch(value=value, id=widget_id)
    elif isinstance(value, int):
        widget = Input(
            type="integer",
            value=str(value),
            restrict=restrict or DEFAULT_INT_RESTRICT,
            id=widget_id,
        )
    elif isinstance(value, float):
        widget = Input(
            type="number",
            value=str(value),
            restrict=restrict or DEFAULT_FLOAT_RESTRICT,
            id=widget_id,
        )
    else:
        widget = Input(type="text", value=str(value), id=widget_id, restrict=restrict)

    widget.add_class("scalar-input")
    reset_btn = Button("↺", id=f"reset-{widget_id}" if widget_id else None, classes="reset-btn")
    row = Horizontal(Static(label, classes="scalar-label"), widget, reset_btn, classes="scalar-row")
    row.reset_path = dotted_path  # type: ignore[attr-defined]
    return row


def _map_value(
    key: str,
    value: Any,
    *,
    prefix: str = "",
    regex_overrides: dict[str, str] | None = None,
) -> Horizontal | Collapsible:
    dotted_path = f"{prefix}.{key}" if prefix else key
    wid = _safe_id(prefix, key)
    overrides = regex_overrides or {}

    if isinstance(value, dict):
        children = [_map_value(k, v, prefix=dotted_path, regex_overrides=overrides) for k, v in value.items()]
        return Collapsible(*children, title=key, id=wid, classes="container-dict", collapsed=False)

    if isinstance(value, list):
        children = [
            _map_value(str(i), item, prefix=dotted_path, regex_overrides=overrides) for i, item in enumerate(value)
        ]
        title = f"{key} [{len(value)}]"
        return Collapsible(*children, title=title, id=wid, classes="container-list", collapsed=False)

    restrict = overrides.get(dotted_path)
    return _make_scalar_row(key, value, widget_id=wid, restrict=restrict, dotted_path=dotted_path)


class NavigableDirectoryTree(DirectoryTree):
    def _populate_node(self, node: TreeNode[DirEntry], content: Iterable[Path]) -> None:
        node.remove_children()
        if node.data is not None:
            parent_path = node.data.path.parent
            if parent_path != node.data.path:
                node.add("..", data=DirEntry(parent_path), allow_expand=True)
        for path in content:
            node.add(
                path.name,
                data=DirEntry(path),
                allow_expand=self._safe_is_dir(path),
            )
        node.expand()


def map_config_to_widgets(
    data: dict[str, Any],
    *,
    regex_overrides: dict[str, str] | None = None,
) -> Vertical:
    overrides = regex_overrides or {}
    children = [_map_value(key, value, regex_overrides=overrides) for key, value in data.items()]
    return Vertical(*children, classes="content-wrapper")
