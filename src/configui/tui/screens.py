from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, Label, Static

from configui.tui.widgets import NavigableDirectoryTree

if TYPE_CHECKING:
    from textual.app import ComposeResult


class ConfirmExitScreen(Screen[bool]):
    CSS = """
    ConfirmExitScreen {
        align: center middle;
    }

    #confirm-exit-box {
        width: 50;
        height: auto;
        padding: 2;
        border: round $primary;
    }

    #confirm-exit-box > Label {
        text-align: center;
        margin: 1 0 2 0;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="confirm-exit-box"):
            yield Label("You have unsaved changes. Exit anyway?")
            yield Button("Cancel", variant="primary", id="cancel")
            yield Button("Exit", variant="error", id="exit")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "exit":
            self.dismiss(True)
        else:
            self.dismiss(False)


class ResetConfirmScreen(Screen[bool]):
    CSS = """
    ResetConfirmScreen {
        align: center middle;
    }

    #reset-confirm-box {
        width: 50;
        height: auto;
        padding: 2;
        border: round $primary;
    }

    #reset-confirm-box > Label {
        text-align: center;
        margin: 1 0 2 0;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="reset-confirm-box"):
            yield Label("Reset all fields to their original values?")
            yield Button("Cancel", variant="primary", id="cancel")
            yield Button("Reset All", variant="error", id="reset")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "reset":
            self.dismiss(True)
        else:
            self.dismiss(False)


class SaveAsScreen(Screen[Path | None]):
    CSS = """
    SaveAsScreen {
        align: center middle;
    }

    #save-as-box {
        width: 80;
        height: auto;
        padding: 2;
        border: round $primary;
    }

    #save-as-box > Label {
        text-align: center;
        text-style: bold;
        margin: 0 0 1 0;
    }

    #save-directory-tree {
        height: 20;
        width: 1fr;
        border: round $surface;
    }

    #save-filename {
        margin: 1 0;
        border: round $primary;
    }

    #save-filename:focus {
        border: round $primary;
    }

    #save-path-preview {
        margin: 1 0;
    }

    #save-as-box > Button {
        margin: 1 0 0 0;
    }
    """

    def __init__(self, current_path: Path) -> None:
        super().__init__()
        self._current_path = current_path
        self._selected_dir: Path = current_path.parent

    def compose(self) -> ComposeResult:
        with Vertical(id="save-as-box"):
            yield Label("Save As")
            yield NavigableDirectoryTree(str(self._current_path.parent), id="save-directory-tree")
            yield Input(value=self._current_path.name, id="save-filename", placeholder="Filename")
            yield Static(id="save-path-preview")
            yield Button("Browse", id="browse")
            yield Button("Save", variant="primary", id="save")
            yield Button("Cancel", id="cancel")

    def on_mount(self) -> None:
        self._update_preview()

    def _get_save_path(self) -> Path | None:
        filename = self.query_one("#save-filename", Input).value.strip()
        if not filename:
            return None
        try:
            candidate = Path(filename).expanduser()
        except RuntimeError:
            return None
        if candidate.is_absolute():
            return candidate
        return self._selected_dir / candidate

    def _update_preview(self) -> None:
        save_path = self._get_save_path()
        preview = self.query_one("#save-path-preview", Static)
        if save_path:
            preview.update(f"Save path: {save_path}")
        else:
            preview.update("")

    def on_input_changed(self, _event: Input.Changed) -> None:
        self._update_preview()

    def on_directory_tree_directory_selected(self, event: NavigableDirectoryTree.DirectorySelected) -> None:
        self._selected_dir = event.path
        tree = self.query_one("#save-directory-tree", NavigableDirectoryTree)
        tree.path = event.path
        self._update_preview()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            save_path = self._get_save_path()
            if save_path:
                self.dismiss(save_path)
        elif event.button.id == "cancel":
            self.dismiss(None)
        elif event.button.id == "browse":
            self.query_one("#save-directory-tree", NavigableDirectoryTree).focus()
