import argparse
import sys
from playwright.sync_api import sync_playwright

from engine.spec_loader import load_spec, SpecError
from engine.runner import run_check
from engine.workflow import run_workflow
from engine.report import build_report, print_report, save_report_json


def run_spec(spec_path, report_path="reports/report.json"):
    spec = load_spec(spec_path)
    base_url = spec["base_url"]
    all_results = []

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        # Run per-page checks
        for page_config in spec.get("pages", []):
            path = page_config["path"]
            url = base_url.rstrip("/") + path

            for check_config in page_config.get("checks", []):
                # 'page_loads' needs a url; others act on whatever page is currently loaded
                if check_config["type"] == "page_loads":
                    check_config = {**check_config, "url": url}
                else:
                    page.goto(url)

                result = run_check(page, check_config)
                all_results.append(result)

        # Run workflows
        for workflow in spec.get("workflows", []):
            workflow_results = run_workflow(page, base_url, workflow)
            all_results.extend(workflow_results)

        browser.close()

    report = build_report(spec["site"], all_results)
    print_report(report)
    saved_path = save_report_json(report, path=report_path)
    print(f"Report saved to: {saved_path}")

    return report


def main():
    parser = argparse.ArgumentParser(description="Run requirement-driven web tests from a spec file.")
    parser.add_argument("spec", help="Path to the YAML spec file (e.g. specs/example_site.yaml)")
    parser.add_argument("--report", default="reports/report.json", help="Path to save the JSON report")
    args = parser.parse_args()

    try:
        report = run_spec(args.spec, args.report)
    except SpecError as e:
        print(f"Spec error: {e}")
        sys.exit(1)

    if report["failed"] > 0:
        sys.exit(1)  # non-zero exit code useful for CI later
    sys.exit(0)


if __name__ == "__main__":
    main()