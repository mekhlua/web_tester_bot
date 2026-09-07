import re


def parse_requirements_doc(doc_text, site_name, base_url):
    """
    Parses a plain-text requirements document into a spec dict.
    Splits on sentences (not lines) so multiple requirements typed
    in one paragraph are each evaluated independently.
    """
    # Split into sentences on '.', '!', '?' followed by space or end of text
    raw_sentences = re.split(r'(?<=[.!?])\s+', doc_text.strip())
    sentences = [s.strip() for s in raw_sentences if s.strip()]

    checks = []
    needs_review = []

    for sentence in sentences:
        lower = sentence.lower()
        matched = False

        if "must load" in lower or "should load" in lower:
            checks.append({"type": "page_loads"})
            matched = True

        if "display" in lower or "show" in lower or ("text" in lower and '"' in sentence):
            match = re.search(r'"([^"]+)"', sentence)
            if match:
                checks.append({"type": "text_present", "text": match.group(1)})
                matched = True

        if "form" in lower or "button" in lower or "link" in lower:
            needs_review.append(sentence)
            matched = True

        if "redirect" in lower:
            match = re.search(r'"([^"]+)"|(/[a-zA-Z0-9\-_/]+)', sentence)
            if match:
                value = match.group(1) or match.group(2)
                needs_review.append(f"{sentence} (needs workflow step: expect_url_contains '{value}')")
            else:
                needs_review.append(sentence)
            matched = True

        if not matched:
            needs_review.append(sentence)

    spec = {
        "site": site_name,
        "base_url": base_url,
        "pages": [
            {"path": "/", "checks": checks}
        ],
        "workflows": [],
    }

    return spec, needs_review
