import json
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from playwright.sync_api import sync_playwright

from bot.forms import TestSpecForm
from bot.models import TestSpec, TestRun
from engine.doc_parser import parse_requirements_doc
from engine.runner import run_check
from engine.workflow import run_workflow
from engine.report import build_report
import yaml


@login_required
def create_spec(request):
    if request.method == "POST":
        form = TestSpecForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data["name"]
            base_url = form.cleaned_data["base_url"]
            doc_text = form.cleaned_data["requirements_doc"]

            spec_dict, needs_review = parse_requirements_doc(doc_text, name, base_url)

            test_spec = TestSpec.objects.create(
                owner=request.user,
                name=name,
                base_url=base_url,
                raw_document=doc_text,
                spec_yaml=yaml.dump(spec_dict),
                needs_review=json.dumps(needs_review),
            )

            if needs_review:
                messages.warning(
                    request,
                    f"Spec created, but {len(needs_review)} requirement(s) need manual review before running."
                )
            else:
                messages.success(request, "Spec created successfully.")

            return redirect("spec_detail", spec_id=test_spec.id)
    else:
        form = TestSpecForm()

    return render(request, "bot/create_spec.html", {"form": form})


@login_required
def spec_detail(request, spec_id):
    spec = TestSpec.objects.get(id=spec_id, owner=request.user)
    needs_review = json.loads(spec.needs_review) if spec.needs_review else []
    runs = spec.runs.order_by("-started_at")
    return render(request, "bot/spec_detail.html", {"spec": spec, "needs_review": needs_review, "runs": runs})


@login_required
def run_spec_view(request, spec_id):
    spec = TestSpec.objects.get(id=spec_id, owner=request.user)
    spec_dict = yaml.safe_load(spec.spec_yaml)
    base_url = spec_dict["base_url"]

    all_results = []

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        for page_config in spec_dict.get("pages", []):
            path = page_config["path"]
            url = base_url.rstrip("/") + path

            for check_config in page_config.get("checks", []):
                if check_config["type"] == "page_loads":
                    check_config = {**check_config, "url": url}
                else:
                    page.goto(url)

                result = run_check(page, check_config)
                all_results.append(result)

        for workflow in spec_dict.get("workflows", []):
            workflow_results = run_workflow(page, base_url, workflow)
            all_results.extend(workflow_results)

        browser.close()

    report = build_report(spec.name, all_results)

    test_run = TestRun.objects.create(
        spec=spec,
        owner=request.user,
        status="completed",
        report_json=json.dumps(report),
        total_checks=report["total_checks"],
        passed_checks=report["passed"],
        failed_checks=report["failed"],
    )

    messages.info(request, f"Run complete: {report['passed']}/{report['total_checks']} checks passed.")
    return redirect("run_detail", run_id=test_run.id)


@login_required
def run_detail(request, run_id):
    run = TestRun.objects.get(id=run_id, owner=request.user)
    report = json.loads(run.report_json) if run.report_json else None
    return render(request, "bot/run_detail.html", {"run": run, "report": report})
