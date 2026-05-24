"""Static structural assertions — fast, no browser required.

Parses ``index.html`` once and verifies the markup contract the rest of the
site depends on (IDs wired up to ``main.js``, ticker present, four project
cards, accessible attributes on links/images, etc.).
"""
from __future__ import annotations

import re

import pytest
from bs4 import BeautifulSoup


@pytest.fixture(scope="module")
def soup(index_html: str) -> BeautifulSoup:
    return BeautifulSoup(index_html, "html.parser")


class TestDocumentShell:
    def test_title_mentions_owner(self, soup: BeautifulSoup) -> None:
        assert "Antonis Pishias" in soup.title.string

    def test_has_viewport_meta(self, soup: BeautifulSoup) -> None:
        assert soup.find("meta", attrs={"name": "viewport"}) is not None

    def test_loads_stylesheet(self, soup: BeautifulSoup) -> None:
        link = soup.find("link", rel="stylesheet", href="assets/style.css")
        assert link is not None, "assets/style.css must be linked"

    def test_loads_main_js(self, soup: BeautifulSoup) -> None:
        script = soup.find("script", src="assets/main.js")
        assert script is not None, "assets/main.js must be loaded"

    def test_declares_language(self, soup: BeautifulSoup) -> None:
        assert soup.html.get("lang") == "en"


class TestMasthead:
    def test_wordmark_renders_both_names(self, soup: BeautifulSoup) -> None:
        first = soup.select_one(".masthead__first")
        last = soup.select_one(".masthead__last em")
        assert first is not None and first.get_text(strip=True) == "Antonis"
        assert last is not None and last.get_text(strip=True) == "Pishias"

    def test_has_expected_spec_items(self, soup: BeautifulSoup) -> None:
        specs = soup.select(".masthead__specs > div")
        assert len(specs) == 4
        labels = {s.find("dt").get_text(strip=True) for s in specs}
        assert labels == {"Base", "Stack", "Focus", "Status"}

    def test_has_stamp_badges(self, soup: BeautifulSoup) -> None:
        stamps = soup.select(".masthead__meta .stamp")
        assert len(stamps) >= 2

    def test_has_live_feed_pulse(self, soup: BeautifulSoup) -> None:
        assert soup.select_one(".stamp--live .pulse") is not None


class TestTicker:
    def test_track_is_present(self, soup: BeautifulSoup) -> None:
        assert soup.select_one(".ticker .ticker__track") is not None

    def test_track_is_duplicated_for_seamless_loop(self, soup: BeautifulSoup) -> None:
        track = soup.select_one(".ticker__track")
        items = [s.get_text(strip=True) for s in track.find_all("span") if "sep" not in (s.get("class") or [])]
        # the content appears twice for a seamless scroll; every entry should
        # have a pair somewhere in the track.
        assert len(items) >= 6 and len(items) % 2 == 0


class TestProjects:
    def test_exactly_six_cards(self, soup: BeautifulSoup) -> None:
        cards = soup.select(".projects-section .projects .card")
        assert len(cards) == 6

    def test_cards_numbered_in_order(self, soup: BeautifulSoup) -> None:
        nums = [c.get_text(strip=True) for c in soup.select(".projects-section .card__index")]
        assert nums == ["01", "02", "03", "04", "05", "06"]

    def test_each_card_has_heading_and_tag(self, soup: BeautifulSoup) -> None:
        for card in soup.select(".projects .card"):
            assert card.find("h3") is not None, "card missing h3"
            assert card.select_one(".card__tag") is not None, "card missing tag"

    @pytest.mark.parametrize(
        "required_id",
        [
            "previewImage",
            "imageInput",
            "uploadStatus",
            "resultImage",
            "symbolInput",
            "volIframe",
            "volVisitLink",
        ],
    )
    def test_js_wiring_ids_present(self, soup: BeautifulSoup, required_id: str) -> None:
        assert soup.find(id=required_id) is not None, f"missing #{required_id}"


class TestAccessibility:
    def test_images_have_alt_text(self, soup: BeautifulSoup) -> None:
        for img in soup.find_all("img"):
            alt = img.get("alt")
            assert alt is not None and alt.strip(), f"image missing alt: {img}"

    def test_external_links_are_safe(self, soup: BeautifulSoup) -> None:
        externals = [a for a in soup.find_all("a", href=True) if a["href"].startswith("http")]
        assert externals, "expected at least one external link"
        for a in externals:
            assert a.get("target") == "_blank", f"external link must open in new tab: {a}"
            rel = (a.get("rel") or [])
            assert "noopener" in rel, f"external link missing rel=noopener: {a}"

    def test_iframe_has_title(self, soup: BeautifulSoup) -> None:
        iframe = soup.find("iframe")
        assert iframe is not None
        assert iframe.get("title"), "iframe must have a title for screen readers"

    def test_inputs_are_labelled(self, soup: BeautifulSoup) -> None:
        for input_el in soup.find_all("input"):
            # either a wrapping <label> or an associated label by id
            in_label = input_el.find_parent("label") is not None
            assert in_label, f"input not wrapped in a label: {input_el}"


class TestStyleContract:
    """Keep the look-and-feel promises honest."""

    def test_uses_distinctive_font_stack(self, index_html: str) -> None:
        assert "Big+Shoulders+Display" in index_html
        assert "JetBrains+Mono" in index_html
        assert "Instrument+Serif" in index_html

    def test_css_defines_brutalist_palette(self, style_css: str) -> None:
        for token in ("--bone", "--ink", "--volt", "--blood"):
            assert token in style_css, f"missing design token {token}"

    def test_css_keeps_respect_for_reduced_motion(self, style_css: str) -> None:
        assert "prefers-reduced-motion" in style_css


class TestMainJsContract:
    """Light-touch lint of the JS file without executing it."""

    def test_exposes_expected_functions(self, main_js: str) -> None:
        assert re.search(r"\basync function sendImage\s*\(", main_js)
        assert re.search(r"\bfunction updateIframe\s*\(", main_js)

    def test_uses_cors_mode_for_post(self, main_js: str) -> None:
        assert '"cors"' in main_js or "'cors'" in main_js

    def test_has_placeholder_config_keys(self, main_js: str) -> None:
        # Static deploy pipeline substitutes these; tests ensure the hooks exist.
        assert "__QUEENS_AZURE_API_KEY__" in main_js
        assert "__VOL_AZURE_API_KEY__" in main_js
