import re

from configui import __version__


def test_version():
    assert isinstance(__version__, str)
    assert re.match(r"\d+\.\d+\.\d+", __version__)
