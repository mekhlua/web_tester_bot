from playwright.sync_api import sync_playwright
from checks.page_checks import page_loads
from engine.spec_loader import load_spec, SpecError
from engine.runner import run_check
import pytest


def test_page_opens():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("https://example.com")
        assert page.title() == "Example Domain"
        browser.close()


def test_page_loads_check():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        result = page_loads(page, "https://example.com")
        assert result["passed"] is True
        print(result["message"])
        browser.close()


def test_load_valid_spec():
    spec = load_spec("specs/example_site.yaml")
    assert spec["site"] == "Example Site"
    assert spec["base_url"] == "https://example.com"
    assert len(spec["pages"]) == 1
    assert spec["pages"][0]["checks"][0]["type"] == "page_loads"


def test_missing_spec_file_raises():
    with pytest.raises(SpecError):
        load_spec("specs/does_not_exist.yaml")


def test_dispatcher_runs_known_check():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        result = run_check(page, {
            "type": "page_loads",
            "url": "https://example.com",
            "max_load_time": 5.0
        })
        assert result["passed"] is True
        assert result["check_type"] == "page_loads"
        browser.close()


def test_dispatcher_unknown_check_type():
    result = run_check(None, {"type": "not_a_real_check"})
    assert result["passed"] is False
    assert "Unknown check type" in result["message"]


def test_element_exists_check():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("https://example.com")
        result = run_check(page, {"type": "element_exists", "selector": "h1"})
        assert result["passed"] is True
        browser.close()


def test_element_exists_check_missing():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("https://example.com")
        result = run_check(page, {"type": "element_exists", "selector": "#does-not-exist", "timeout": 1000})
        assert result["passed"] is False
        browser.close()


def test_text_present_check():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("https://example.com")
        result = run_check(page, {"type": "text_present", "text": "Example Domain"})
        assert result["passed"] is True
        browser.close()


def test_link_valid_check():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("https://example.com")
        result = run_check(page, {"type": "link_valid"})
        assert result["passed"] is True
        browser.close()
