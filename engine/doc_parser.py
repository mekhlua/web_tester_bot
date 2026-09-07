import re


def parse_requirements_doc(doc_text, site_name, base_url):
    """
    Parses a plain-text requirements document into a spec dict.
    Produces reliable checks where possible; flags ambiguous
    requirements that need manual selector input.
    """
    lines = [l.strip() for l in doc_text.splitlines() if l.strip()]

    checks = []
    needs_review = []

    for line in lines:
        lower = line.lower()

        if "must load" in lower or "should load" in lower:
            checks.append({"type": "page_loads"})

        elif "display" in lower or "show" in lower or "text" in lower:
            match = re.search(r'"([^"]+)"', line)
            if match:
                checks.append({"type": "text_present", "text": match.group(1)})
            else:
                needs_review.append(line)

        elif "form" in lower or "button" in lower or "link" in lower:
            needs_review.append(line)

        elif "redirect" in lower:
            match = re.search(r'"([^"]+)"|(/[a-zA-Z0-9\-_/]+)', line)
            if match:
                value = match.group(1) or match.group(2)
                needs_review.append(f"{line} (needs workflow step: expect_url_contains '{value}')")
            else:
                needs_review.append(line)

        else:
            needs_review.append(line)

    spec = {
        "site": site_name,
        "base_url": base_url,
        "pages": [
            {"path": "/", "checks": checks}
        ],
        "workflows": [],
    }

    return spec, needs_review
