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


from engine.report import build_report, print_report, save_report_json
import os


def test_build_report():
    fake_results = [
        {"passed": True, "message": "ok", "check_type": "page_loads"},
        {"passed": False, "message": "broken", "check_type": "element_exists"},
    ]
    report = build_report("Test Site", fake_results)
    assert report["total_checks"] == 2
    assert report["passed"] == 1
    assert report["failed"] == 1
    assert report["site"] == "Test Site"


def test_save_report_json(tmp_path):
    fake_results = [{"passed": True, "message": "ok", "check_type": "page_loads"}]
    report = build_report("Test Site", fake_results)
    out_path = str(tmp_path / "test_report.json")
    saved_path = save_report_json(report, path=out_path)
    assert os.path.exists(saved_path)


from engine.workflow import run_workflow


def test_workflow_runs_and_passes():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        spec = load_spec("specs/example_site.yaml")
        workflow = spec["workflows"][0]

        results = run_workflow(page, spec["base_url"], workflow)

        assert all(r["passed"] for r in results)
        assert len(results) == 3
        browser.close()


def test_workflow_stops_on_failure():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        bad_workflow = {
            "name": "Bad flow",
            "steps": [
                {"action": "goto", "path": "/"},
                {"action": "expect_element", "selector": "#does-not-exist", "timeout": 1000},
                {"action": "expect_text", "value": "This should not run"},
            ],
        }

        results = run_workflow(page, "https://example.com", bad_workflow)

        assert len(results) == 2
        assert results[-1]["passed"] is False
        browser.close()


from engine.doc_parser import parse_requirements_doc


def test_parse_requirements_doc():
    doc = '''
    The homepage must load successfully.
    It should display the text "Welcome to Acme".
    There must be a login form with username and password fields.
    '''
    spec, needs_review = parse_requirements_doc(doc, "Acme Site", "https://acme.com")

    assert spec["site"] == "Acme Site"
    assert {"type": "page_loads"} in spec["pages"][0]["checks"]
    assert {"type": "text_present", "text": "Welcome to Acme"} in spec["pages"][0]["checks"]
    assert len(needs_review) == 1
    assert "login form" in needs_review[0]
