"""Browser-backed end-to-end tests.

These tests launch a real Chromium via Playwright and drive the site. All
external network calls (the Azure-hosted APIs) are intercepted so the suite
stays hermetic.

Run only these tests with ``pytest -m e2e`` or skip them with ``-m "not e2e"``.
"""
from __future__ import annotations

import re

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e

# A minimal valid PNG (1x1 transparent) for the Queens solver mock.
_TINY_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000d"
    "49444154789c6300010000000500010d0a2db40000000049454e44ae426082"
)


@pytest.fixture(autouse=True)
def _block_external(page: Page) -> None:
    """Never let a test touch the real Azure endpoints."""
    page.route(
        "**/linkedin-solvers.azurewebsites.net/**",
        lambda route: route.abort(),
    )
    page.route(
        "**/volsurface.azurewebsites.net/**",
        # Iframe navigation — respond with an empty 200 so load completes.
        lambda route: route.fulfill(
            status=200, content_type="text/html", body="<!doctype html><title>mock</title>"
        ),
    )


def test_page_has_expected_title_and_masthead(live_server: str, page: Page) -> None:
    page.goto(live_server)
    expect(page).to_have_title(re.compile(r"Antonis Pishias"))
    expect(page.locator(".masthead__first")).to_have_text("Antonis")
    expect(page.locator(".masthead__last em")).to_have_text("Pishias")


def test_renders_five_project_cards(live_server: str, page: Page) -> None:
    page.goto(live_server)
    expect(page.locator(".projects .card")).to_have_count(5)


def test_ticker_is_visible(live_server: str, page: Page) -> None:
    page.goto(live_server)
    expect(page.locator(".ticker__track")).to_be_visible()


def test_render_surface_updates_iframe_with_uppercased_ticker(
    live_server: str, page: Page
) -> None:
    page.goto(live_server)
    page.fill("#symbolInput", "aapl")
    page.get_by_role("button", name=re.compile("Render surface", re.I)).click()
    expect(page.locator("#volIframe")).to_have_attribute(
        "src", re.compile(r"ticker=AAPL$")
    )


def test_render_surface_reveals_standalone_link(live_server: str, page: Page) -> None:
    page.goto(live_server)
    page.fill("#symbolInput", "MSFT")
    page.get_by_role("button", name=re.compile("Render surface", re.I)).click()
    link = page.locator("#volVisitLink")
    expect(link).to_be_visible()
    expect(link).to_have_attribute("href", re.compile(r"ticker=MSFT$"))


def test_empty_ticker_is_a_noop(live_server: str, page: Page) -> None:
    page.goto(live_server)
    page.fill("#symbolInput", "   ")
    page.get_by_role("button", name=re.compile("Render surface", re.I)).click()
    # src remains the initial (empty) value
    expect(page.locator("#volIframe")).to_have_attribute("src", "")


def test_queens_solver_renders_result_image(live_server: str, page: Page) -> None:
    # Intercept the POST and return a PNG so the image branch fires.
    page.route(
        "**/queens/solve*",
        lambda route: route.fulfill(
            status=200, content_type="image/png", body=_TINY_PNG
        ),
    )
    page.goto(live_server)
    page.get_by_role("button", name=re.compile("Solve board", re.I)).click()
    expect(page.locator("#uploadStatus")).to_have_text(
        "SOLVED — BOARD RECEIVED", timeout=8_000
    )
    expect(page.locator("#resultImage")).to_be_visible()


def test_queens_solver_reports_failure(live_server: str, page: Page) -> None:
    page.route(
        "**/queens/solve*",
        lambda route: route.fulfill(status=500, body="boom"),
    )
    page.goto(live_server)
    page.get_by_role("button", name=re.compile("Solve board", re.I)).click()
    expect(page.locator("#uploadStatus")).to_contain_text("REQUEST FAILED", timeout=8_000)
    expect(page.locator("#resultImage")).to_be_hidden()


def test_no_console_errors_on_load(live_server: str, page: Page) -> None:
    errors: list[str] = []
    page.on("pageerror", lambda exc: errors.append(str(exc)))
    page.on(
        "console",
        lambda msg: errors.append(msg.text) if msg.type == "error" else None,
    )
    page.goto(live_server, wait_until="networkidle")
    assert not errors, f"unexpected console/page errors: {errors}"
