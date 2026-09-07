from django.shortcuts import render

# Create your views here.
import json
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages

from bot.forms import TestSpecForm
from bot.models import TestSpec
from engine.doc_parser import parse_requirements_doc
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
    return render(request, "bot/spec_detail.html", {"spec": spec, "needs_review": needs_review})