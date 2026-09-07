import re

TEXT_PRESENCE_KEYWORDS = [
    "display", "show", "contain", "appear", "state",
    "include", "mention", "read", "say", "have the text"
]


def parse_requirements_doc(doc_text, site_name, base_url):
    """
    Parses a plain-text requirements document into a spec dict.
    Splits on sentences (not lines) so multiple requirements typed
    in one paragraph are each evaluated independently.
    Supports quoted text, unquoted phrases after a wide set of
    "content presence" keywords, and link-validity phrases.
    """
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

        if "link" in lower and (
            "must work" in lower or "should work" in lower
            or "not be broken" in lower or "no broken" in lower
            or "must be valid" in lower or "should be valid" in lower
        ):
            checks.append({"type": "link_valid"})
            matched = True

        text_keyword = next((kw for kw in TEXT_PRESENCE_KEYWORDS if kw in lower), None)
        if text_keyword:
            quoted = re.search(r'"([^"]+)"', sentence)
            if quoted:
                checks.append({"type": "text_present", "text": quoted.group(1)})
                matched = True
            else:
                unquoted = re.search(
                    re.escape(text_keyword) + r's?\s+(?:the\s+text\s+)?(.+?)[\.\!\?]?$',
                    sentence,
                    re.IGNORECASE
                )
                if unquoted:
                    phrase = unquoted.group(1).strip().rstrip(".!?")
                    if phrase:
                        checks.append({"type": "text_present", "text": phrase})
                        matched = True

        if "form" in lower or "button" in lower:
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
