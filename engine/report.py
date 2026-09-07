import json
from datetime import datetime, timezone


def build_report(site_name, results):
    """
    Takes a list of check result dicts (each with 'passed', 'message', 'check_type')
    and builds a structured report.
    """
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    failed = total - passed

    return {
        "site": site_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_checks": total,
        "passed": passed,
        "failed": failed,
        "results": results,
    }


def print_report(report):
    """
    Prints a human-readable summary of the report to the console.
    """
    print(f"\n{'=' * 50}")
    print(f"Report: {report['site']}")
    print(f"Run at: {report['timestamp']}")
    print(f"{'=' * 50}")

    for r in report["results"]:
        status = "PASS" if r["passed"] else "FAIL"
        print(f"[{status}] {r['check_type']}: {r['message']}")

    print(f"{'-' * 50}")
    print(f"Total: {report['total_checks']}  |  Passed: {report['passed']}  |  Failed: {report['failed']}")
    print(f"{'=' * 50}\n")


def save_report_json(report, path="reports/report.json"):
    """
    Saves the report as a JSON file for later inspection or CI use.
    """
    with open(path, "w") as f:
        json.dump(report, f, indent=2)
    return path