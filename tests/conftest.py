"""Shared pytest fixtures for the portfolio test suite."""
from __future__ import annotations

import http.server
import socketserver
import threading
from pathlib import Path
from typing import Iterator

import pytest

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def project_root() -> Path:
    return ROOT


@pytest.fixture(scope="session")
def index_html(project_root: Path) -> str:
    return (project_root / "index.html").read_text(encoding="utf-8")


@pytest.fixture(scope="session")
def main_js(project_root: Path) -> str:
    return (project_root / "assets" / "main.js").read_text(encoding="utf-8")


@pytest.fixture(scope="session")
def style_css(project_root: Path) -> str:
    return (project_root / "assets" / "style.css").read_text(encoding="utf-8")


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *_args, **_kwargs) -> None:  # silence stdout
        return


@pytest.fixture(scope="session")
def live_server(project_root: Path) -> Iterator[str]:
    """Serve the repo over http on an ephemeral port for the session."""

    def handler_factory(*args, **kwargs):
        return _QuietHandler(*args, directory=str(project_root), **kwargs)

    with socketserver.TCPServer(("127.0.0.1", 0), handler_factory) as httpd:
        port = httpd.server_address[1]
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        try:
            yield f"http://127.0.0.1:{port}"
        finally:
            httpd.shutdown()
