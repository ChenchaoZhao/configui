from __future__ import annotations

import asyncio
import json
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any

from textual.widgets import Collapsible, Header, Switch, Tree

from configui.tui.app import ConfigUIApp

if TYPE_CHECKING:
    from textual.containers import Vertical

SAMPLE_CONFIG: dict[str, Any] = {
    "model": {
        "architecture": "resnet50",
        "pretrained": True,
        "num_classes": 1000,
        "dropout": 0.5,
    },
    "training": {
        "batch_size": 64,
        "epochs": 100,
        "learning_rate": 0.001,
        "use_cuda": True,
    },
}


def _create_config(data: dict[str, Any]) -> Path:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
        json.dump(data, tmp)
        return Path(tmp.name)


def _content_inner(app: ConfigUIApp) -> Vertical:
    content = app.query_one("#main-content")
    return next(iter(content.children))


def test_app_mounts_with_sample_config() -> None:
    path = _create_config(SAMPLE_CONFIG)
    try:

        async def _run() -> None:
            app = ConfigUIApp(str(path))
            async with app.run_test():
                tree = app.query_one("#sidebar-tree", Tree)
                header = app.query_one(Header)

                assert len(list(tree.root.children)) == 2
                inner = _content_inner(app)
                collapsibles = [c for c in inner.children if isinstance(c, Collapsible)]
                assert len(collapsibles) == 2
                assert path.name in str(header.sub_title)

        asyncio.run(_run())
    finally:
        path.unlink(missing_ok=True)


def test_header_shows_filename() -> None:
    path = _create_config(SAMPLE_CONFIG)
    try:

        async def _run() -> None:
            app = ConfigUIApp(str(path))
            async with app.run_test():
                header = app.query_one(Header)
                assert path.name in str(header.sub_title)

        asyncio.run(_run())
    finally:
        path.unlink(missing_ok=True)


def test_ctrl_s_saves() -> None:
    path = _create_config(SAMPLE_CONFIG)
    try:

        async def _run() -> None:
            app = ConfigUIApp(str(path))
            async with app.run_test() as pilot:
                switch = app.query_one(Switch)
                switch.value = not switch.value
                await pilot.pause()
                assert app._dirty  # noqa: SLF001

                await pilot.press("ctrl+s")
                await pilot.pause()

                assert not app._dirty  # noqa: SLF001
                data = json.loads(path.read_text())
                assert data == {
                    "model": {
                        "architecture": "resnet50",
                        "pretrained": False,
                        "num_classes": 1000,
                        "dropout": 0.5,
                    },
                    "training": {
                        "batch_size": 64,
                        "epochs": 100,
                        "learning_rate": 0.001,
                        "use_cuda": True,
                    },
                }

        asyncio.run(_run())
    finally:
        path.unlink(missing_ok=True)


def test_ctrl_q_quits() -> None:
    path = _create_config(SAMPLE_CONFIG)
    try:

        async def _run() -> None:
            app = ConfigUIApp(str(path))
            async with app.run_test() as pilot:
                await pilot.press("ctrl+q")

        asyncio.run(_run())
    finally:
        path.unlink(missing_ok=True)


def test_dirty_indicator() -> None:
    path = _create_config(SAMPLE_CONFIG)
    try:

        async def _run() -> None:
            app = ConfigUIApp(str(path))
            async with app.run_test() as pilot:
                await pilot.pause()
                header = app.query_one(Header)
                assert "*" not in str(header.sub_title)

                switch = app.query_one(Switch)
                switch.value = not switch.value
                await pilot.pause()
                assert app._dirty  # noqa: SLF001
                assert "*" in str(header.sub_title)

                await pilot.press("ctrl+s")
                await pilot.pause()
                assert not app._dirty  # noqa: SLF001
                assert "*" not in str(header.sub_title)

        asyncio.run(_run())
    finally:
        path.unlink(missing_ok=True)


def test_read_only_mode() -> None:
    path = _create_config(SAMPLE_CONFIG)
    try:

        async def _run() -> None:
            app = ConfigUIApp(str(path), read_only=True)
            async with app.run_test() as pilot:
                await pilot.pause()
                header = app.query_one(Header)
                assert "READ ONLY" in str(header.sub_title).upper()

                switch = app.query_one(Switch)
                switch.value = not switch.value

                original = path.read_text()
                await pilot.press("ctrl+s")
                assert path.read_text() == original

        asyncio.run(_run())
    finally:
        path.unlink(missing_ok=True)


def test_save_as_modal_pushes_and_pops() -> None:
    path = _create_config(SAMPLE_CONFIG)
    try:

        async def _run() -> None:
            app = ConfigUIApp(str(path))
            async with app.run_test() as pilot:
                app._dirty = True  # noqa: SLF001
                await pilot.press("ctrl+shift+s")

                assert app.screen is not app
                assert "SaveAsScreen" in type(app.screen).__name__

        asyncio.run(_run())
    finally:
        path.unlink(missing_ok=True)


def test_tree_click_scrolls_to_content() -> None:
    path = _create_config(SAMPLE_CONFIG)
    try:

        async def _run() -> None:
            app = ConfigUIApp(str(path))
            async with app.run_test():
                tree = app.query_one("#sidebar-tree", Tree)
                model_node = next(iter(tree.root.children))
                assert str(model_node.label) == "model"

                model_node.expand()
                model_node.parent.expand()

                collapsible = app.query_one("#model", Collapsible)
                assert collapsible is not None

        asyncio.run(_run())
    finally:
        path.unlink(missing_ok=True)
