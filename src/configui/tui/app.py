from __future__ import annotations

import asyncio
from copy import deepcopy
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, cast

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Collapsible, Footer, Header, Input, Switch, Tree

from configui.config import SupportedConfigFormat
from configui.tui.collector import map_widgets_to_config
from configui.tui.screens import ConfirmExitScreen, ResetConfirmScreen, SaveAsScreen
from configui.tui.widgets import map_config_to_widgets

if TYPE_CHECKING:
    from textual.widgets.tree import TreeNode

_MOUNT_SETTLE_YIELDS: int = 100


class ConfigUIApp(App[None]):
    TITLE = "ConfigUI"

    CSS = """
    Screen {
        layout: grid;
        grid-size: 1 3;
        grid-rows: auto 1fr auto;
    }

    #main-container {
        layout: horizontal;
    }

    #sidebar-tree {
        dock: left;
        width: 30%;
        min-width: 30;
        max-width: 50;
        border: round $primary;
        overflow-y: auto;
        margin: 0 0 0 1;
    }

    #sidebar-tree:focus-within {
        border: round $primary;
    }

    #main-content {
        width: 1fr;
        height: 1fr;
        border: round $primary;
        overflow-y: auto;
        padding: 1 2;
        margin: 0 1;
    }

    #main-content:focus-within {
        border: round $primary;
    }

    .scalar-row {
        height: auto;
        margin: 0 0 1 0;
    }

    .scalar-label {
        width: auto;
        height: 3;
        padding: 0 1 0 0;
        color: $text;
        text-style: bold;
        content-align: left middle;
    }

    .scalar-input {
        width: 1fr;
        height: 3;
    }

    Input.scalar-input {
        background: $surface;
        border: round $primary;
    }

    Input.scalar-input:focus {
        background: $surface;
        border: round $primary;
    }

    Switch.scalar-input {
        width: auto;
        height: 3;
        border: round $primary;
    }

    Switch.scalar-input:focus {
        border: round $primary;
    }

    .reset-btn {
        width: auto;
        height: 3;
        min-width: 3;
        margin: 0 0 0 1;
        background: transparent;
        border: none;
        color: $text;
    }

    .reset-btn:hover {
        color: $primary;
    }

    .content-wrapper {
        height: auto;
    }

    Collapsible > .container-dict,
    Collapsible > .container-list {
        margin: 0 0 0 1;
    }

    Tree {
        padding: 0 1;
    }
    """

    BINDINGS: ClassVar[list[Binding]] = [  # type: ignore[assignment]
        Binding("ctrl+s", "save", "Save", priority=True),
        Binding("ctrl+shift+s", "save_as", "Save As", priority=True),
        Binding("ctrl+r", "reset_all", "Reset All", priority=True),
        Binding("ctrl+q", "quit", "Quit", priority=True),
    ]

    def __init__(self, path: str, *, read_only: bool = False) -> None:
        super().__init__()
        self._filepath = Path(path)
        self._read_only = read_only
        self._dirty = False
        self._config = None
        self._original_data: dict[str, Any] = {}
        self._tree_nodes: dict[str, TreeNode] = {}
        self._header: Header | None = None
        self._mount_phase = True

    def _load_config(self):
        fmt = SupportedConfigFormat.from_filename(self._filepath.name)
        config = fmt.get_config_cls()(self._filepath)
        config.load()
        return config

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Horizontal(id="main-container"):
            yield Tree("config", id="sidebar-tree")
            yield Vertical(id="main-content")
        yield Footer()

    async def on_mount(self) -> None:
        self._config = self._load_config()
        data: dict[str, Any] = cast("dict[str, Any]", self._config._data)  # type: ignore[attr-defined,union-attr]  # noqa: SLF001
        self._original_data = deepcopy(data)

        self._header = self.query_one(Header)
        content = self.query_one("#main-content", Vertical)
        content.remove_children()
        content.mount(map_config_to_widgets(data))

        tree = self.query_one("#sidebar-tree", Tree)
        tree.clear()
        self._tree_nodes.clear()
        self._populate_tree(tree.root, data)

        if self._read_only:
            self._header.sub_title = "[READ ONLY]"  # type: ignore[union-attr,attr-defined]
        else:
            self._header.sub_title = self._filepath.name  # type: ignore[union-attr,attr-defined]

        for _ in range(_MOUNT_SETTLE_YIELDS):
            await asyncio.sleep(0)

        self.call_later(self._end_mount_phase)

    def _end_mount_phase(self) -> None:
        self._mount_phase = False
        self._dirty = False
        if self._read_only:
            self._header.sub_title = "[READ ONLY]"  # type: ignore[union-attr,attr-defined]
        else:
            self._header.sub_title = self._filepath.name  # type: ignore[union-attr,attr-defined]

    def _get_nested(self, data: dict[str, Any], dotted_path: str) -> Any:
        parts = dotted_path.split(".")
        current: Any = data
        for part in parts:
            current = current[int(part)] if isinstance(current, list) and part.isdigit() else current[part]  # type: ignore[index]
        return current

    def _populate_tree(self, node: TreeNode, data: dict[str, Any], prefix: str = "") -> None:
        for key, value in data.items():
            path = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                child = node.add(key, expand=True)
                child.data = {"path": path}
                self._tree_nodes[path] = child
                self._populate_tree(child, value, prefix=path)
            else:
                child = node.add_leaf(key)
                child.data = {"path": path}
                self._tree_nodes[path] = child

    def _expand_tree_ancestors(self, key_path: str) -> None:
        parts = key_path.split(".")
        for i in range(1, len(parts)):
            ancestor_path = ".".join(parts[:i])
            ancestor = self._tree_nodes.get(ancestor_path)
            if ancestor is not None:
                ancestor.expand()

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        if event.node.tree.id != "sidebar-tree":
            return
        data = event.node.data
        if data is None or "path" not in data:
            return
        dotted_path = data["path"]
        wid = dotted_path.replace(".", "_")
        try:
            widget = self.query_one(f"#{wid}")
            if isinstance(widget, Collapsible) and widget.collapsed:
                widget.collapsed = False
            widget.scroll_visible()
        except Exception:  # noqa: BLE001, S110
            pass

    def _sync_tree_from_collapsible(self, collapsible_id: str, *, expanded: bool) -> None:
        key_path = collapsible_id.replace("_", ".")
        node = self._tree_nodes.get(key_path)
        if node is not None:
            if expanded:
                node.expand()
            else:
                node.collapse()
            self._expand_tree_ancestors(key_path)

    def on_collapsible_expanded(self, event: Collapsible.Expanded) -> None:
        wid = event.collapsible.id
        if wid:
            self._sync_tree_from_collapsible(wid, expanded=True)

    def on_collapsible_collapsed(self, event: Collapsible.Collapsed) -> None:
        wid = event.collapsible.id
        if wid:
            self._sync_tree_from_collapsible(wid, expanded=False)

    def _mark_dirty(self) -> None:
        if self._mount_phase or self._read_only:
            return
        if not self._dirty:
            self._dirty = True
            self._header.sub_title = f"{self._filepath.name} *"  # type: ignore[union-attr,attr-defined]

    def on_input_changed(self, _event: Input.Changed) -> None:
        self._mark_dirty()

    def on_switch_changed(self, _event: Switch.Changed) -> None:
        self._mark_dirty()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id is None:
            return
        if button_id.startswith("reset-") and "reset-btn" in event.button.classes:
            widget_id = button_id[6:]
            widget = self.query_one(f"#{widget_id}")
            row = widget.parent if isinstance(widget.parent, Horizontal) else None
            dotted_path = getattr(row, "reset_path", None) or widget_id.replace("_", ".")
            original_value = self._get_nested(self._original_data, dotted_path)
            if isinstance(widget, Switch):
                widget.value = bool(original_value)
            elif isinstance(widget, Input):
                widget.value = str(original_value)
            self._mark_dirty()

    def action_save(self) -> None:
        if self._read_only or not self._dirty:
            return
        try:
            content = self.query_one("#main-content", Vertical)
            data = map_widgets_to_config(content)
            self._config.update(data)  # type: ignore[attr-defined]
            self._config.save()  # type: ignore[attr-defined]
            self._dirty = False
            self._header.sub_title = self._filepath.name  # type: ignore[union-attr,attr-defined]
        except Exception as exc:  # noqa: BLE001
            self.notify(str(exc), severity="error", title="Save failed")

    def action_save_as(self) -> None:
        if self._read_only:
            return
        self.push_screen(SaveAsScreen(self._filepath), self._on_save_as_result)

    def _on_save_as_result(self, new_path: Path | None) -> None:
        if new_path is None:
            return
        try:
            content = self.query_one("#main-content", Vertical)
            data = map_widgets_to_config(content)
            self._config.update(data)  # type: ignore[attr-defined]
            self._config.save_as(new_path)  # type: ignore[attr-defined]
            self._filepath = new_path
            self._dirty = False
            self._header.sub_title = self._filepath.name  # type: ignore[union-attr,attr-defined]
        except Exception as exc:  # noqa: BLE001
            self.notify(str(exc), severity="error", title="Save As failed")

    def action_reset_all(self) -> None:
        if self._read_only or not self._dirty:
            return
        self.push_screen(ResetConfirmScreen(), self._on_reset_all_result)  # type: ignore[arg-type]

    def _on_reset_all_result(self, confirmed: bool) -> None:  # noqa: FBT001
        if not confirmed:
            return
        content = self.query_one("#main-content", Vertical)
        content.remove_children()
        content.mount(map_config_to_widgets(self._original_data))
        tree = self.query_one("#sidebar-tree", Tree)
        tree.clear()
        self._tree_nodes.clear()
        self._populate_tree(tree.root, self._original_data)
        self._dirty = False
        self._header.sub_title = self._filepath.name  # type: ignore[union-attr,attr-defined]

    def action_quit(self) -> None:  # type: ignore[override]
        if self._dirty:
            self.push_screen(ConfirmExitScreen(), self._on_quit_result)  # type: ignore[arg-type]
        else:
            self.exit()

    def _on_quit_result(self, confirmed: bool) -> None:  # noqa: FBT001
        if confirmed:
            self.exit()
