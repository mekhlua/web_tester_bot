import json
import threading
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from playwright.sync_api import sync_playwright

from bot.forms import TestSpecForm, AddInteractionCheckForm
from bot.models import TestSpec, TestRun
from engine.llm_doc_parser import parse_requirements_doc_smart
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

            spec_dict, needs_review, parser_used = parse_requirements_doc_smart(doc_text, name, base_url)

            test_spec = TestSpec.objects.create(
                owner=request.user,
                name=name,
                base_url=base_url,
                raw_document=doc_text,
                spec_yaml=yaml.dump(spec_dict),
                needs_review=json.dumps(needs_review),
                requires_login=form.cleaned_data["requires_login"],
                login_path=form.cleaned_data["login_path"],
                username_selector=form.cleaned_data["username_selector"],
                password_selector=form.cleaned_data["password_selector"],
                submit_selector=form.cleaned_data["submit_selector"],
                login_username=form.cleaned_data["login_username"],
                login_password=form.cleaned_data["login_password"],
            )

            parser_label = "AI-powered" if parser_used == "llm" else "basic keyword-based (AI parser unavailable)"

            if needs_review:
                messages.warning(
                    request,
                    f"Spec created using the {parser_label} parser, but {len(needs_review)} requirement(s) need manual review before running."
                )
            else:
                messages.success(request, f"Spec created successfully using the {parser_label} parser.")

            return redirect("spec_detail", spec_id=test_spec.id)
    else:
        form = TestSpecForm()

    return render(request, "bot/create_spec.html", {"form": form})


@login_required
def spec_detail(request, spec_id):
    spec = TestSpec.objects.get(id=spec_id, owner=request.user)
    needs_review = json.loads(spec.needs_review) if spec.needs_review else []
    runs = spec.runs.order_by("-started_at")
    interaction_form = AddInteractionCheckForm()
    return render(request, "bot/spec_detail.html", {
        "spec": spec, "needs_review": needs_review, "runs": runs, "interaction_form": interaction_form
    })


@login_required
def add_interaction_check(request, spec_id):
    spec = TestSpec.objects.get(id=spec_id, owner=request.user)

    if request.method == "POST":
        form = AddInteractionCheckForm(request.POST)
        if form.is_valid():
            spec_dict = yaml.safe_load(spec.spec_yaml)
            spec_dict.setdefault("workflows", [])

            steps = [{"action": "click", "selector": form.cleaned_data["selector"]}]
            if form.cleaned_data.get("expect_url_contains"):
                steps.append({"action": "expect_url_contains", "value": form.cleaned_data["expect_url_contains"]})
            if form.cleaned_data.get("expect_text"):
                steps.append({"action": "expect_text", "value": form.cleaned_data["expect_text"]})

            spec_dict["workflows"].append({
                "name": f"Click {form.cleaned_data['selector']}",
                "steps": steps,
            })

            spec.spec_yaml = yaml.dump(spec_dict)
            spec.save()
            messages.success(request, "Interaction check added.")
        else:
            messages.error(request, "Could not add check: " + str(form.errors))

    return redirect("spec_detail", spec_id=spec.id)


def _build_login_workflow(spec):
    """Builds a workflow dict that logs in using the spec's stored login fields."""
    return {
        "name": "Login",
        "steps": [
            {"action": "goto", "path": spec.login_path},
            {"action": "fill", "selector": spec.username_selector, "value": spec.login_username},
            {"action": "fill", "selector": spec.password_selector, "value": spec.login_password},
            {"action": "click", "selector": spec.submit_selector},
        ],
    }


def _execute_test_run(test_run_id):
    """
    Runs the actual Playwright test for a TestRun. Designed to run in a
    background thread — takes only the ID (not request/user objects,
    which aren't safe to share across threads) and updates the TestRun
    row directly when finished.
    """
    from django.db import connection
    connection.close()  # ensure this thread gets its own fresh DB connection

    test_run = TestRun.objects.get(id=test_run_id)
    spec = test_run.spec
    spec_dict = yaml.safe_load(spec.spec_yaml)
    base_url = spec_dict["base_url"]

    all_results = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()

            if spec.requires_login:
                login_workflow = _build_login_workflow(spec)
                login_results = run_workflow(page, base_url, login_workflow)
                all_results.extend(login_results)

                if not all(r["passed"] for r in login_results):
                    browser.close()
                    report = build_report(spec.name, all_results)
                    test_run.status = "failed"
                    test_run.report_json = json.dumps(report)
                    test_run.total_checks = report["total_checks"]
                    test_run.passed_checks = report["passed"]
                    test_run.failed_checks = report["failed"]
                    test_run.finished_at = timezone.now()
                    test_run.save()
                    return

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
        test_run.status = "completed"
        test_run.report_json = json.dumps(report)
        test_run.total_checks = report["total_checks"]
        test_run.passed_checks = report["passed"]
        test_run.failed_checks = report["failed"]
        test_run.finished_at = timezone.now()
        test_run.save()

    except Exception as e:
        report = build_report(spec.name, all_results)
        test_run.status = "failed"
        test_run.report_json = json.dumps(report)
        test_run.total_checks = report["total_checks"]
        test_run.passed_checks = report["passed"]
        test_run.failed_checks = report["failed"]
        test_run.finished_at = timezone.now()
        test_run.save()
        print(f"Test run {test_run_id} crashed: {e}")


@login_required
def run_spec_view(request, spec_id):
    spec = TestSpec.objects.get(id=spec_id, owner=request.user)

    test_run = TestRun.objects.create(
        spec=spec,
        owner=request.user,
        status="running",
    )

    thread = threading.Thread(target=_execute_test_run, args=(test_run.id,), daemon=True)
    thread.start()

    messages.info(request, "Test started — this page will update once it's finished.")
    return redirect("run_detail", run_id=test_run.id)


@login_required
def run_detail(request, run_id):
    run = TestRun.objects.get(id=run_id, owner=request.user)
    report = json.loads(run.report_json) if run.report_json else None
    return render(request, "bot/run_detail.html", {"run": run, "report": report})


def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created. Please log in.")
            return redirect("login")
    else:
        form = UserCreationForm()
    return render(request, "registration/register.html", {"form": form})
