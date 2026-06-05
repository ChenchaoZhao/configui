from __future__ import annotations

import click

from configui.tui.app import ConfigUIApp


@click.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("-r", "--read-only", is_flag=True, help="Open in read-only mode")
def main(path: str, read_only: bool) -> None:  # noqa: FBT001
    """Open a configuration file in the ConfigUI TUI editor."""
    app = ConfigUIApp(path, read_only=read_only)
    app.run()
