import os
import json
import google.generativeai as genai

SYSTEM_PROMPT = """You are a requirements-to-test-spec converter for a web testing tool.

Given a requirements document for a website, extract testable checks and workflows. Output ONLY valid JSON, no markdown code fences, no explanation.

Available check types (independent, page-level checks):
- "page_loads": the page loads successfully (no parameters needed)
- "text_present": specific text/content should appear on the page. Use the field "text" with the ACTUAL text you infer should be checked (e.g. if the requirement says "display the owner's name" and other context tells you the name, use the real name; if you cannot infer real content, put the concept itself for a human to refine, e.g. "the owner's name")
- "link_valid": all links on the page should not be broken (no parameters needed)

Available workflow step actions (ordered, for requirements involving clicking, filling forms, or navigation, like login flows or buttons):
- {"action": "goto", "path": "/some-path"}
- {"action": "fill", "selector": "CSS_SELECTOR", "value": "text to type"}
- {"action": "click", "selector": "CSS_SELECTOR"}
- {"action": "expect_element", "selector": "CSS_SELECTOR"}
- {"action": "expect_text", "value": "text that should appear after the action"}
- {"action": "expect_url_contains", "value": "/expected-path"}

IMPORTANT: You do NOT know the real CSS selectors for this specific site's buttons/forms. For any requirement needing a click/fill/button/form interaction, do NOT invent a workflow with a guessed selector. Instead, put that requirement sentence into "needs_review" with a note that a selector is needed, e.g. "There must be a login form (needs CSS selector for the form/button before a workflow can be built)".

For any requirement that is subjective/non-functional (responsiveness, browser compatibility, usability, performance targets) or otherwise unclear, also put the ORIGINAL requirement sentence into "needs_review".

Output this exact JSON shape:
{
  "checks": [
    {"type": "page_loads"},
    {"type": "text_present", "text": "..."},
    {"type": "link_valid"}
  ],
  "workflows": [],
  "needs_review": ["original sentence 1", "original sentence 2 (needs CSS selector)"]
}
"""


def parse_requirements_doc_llm(doc_text, site_name, base_url, site_context=""):
    """
    Uses Gemini to parse a requirements document into a spec dict.
    Same return shape as the keyword-based parser: (spec, needs_review).

    site_context: optional extra info (e.g. known real content from the
    target site) to help the LLM resolve descriptive requirements into
    real literal text checks.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY environment variable not set")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-3.6-flash")

    user_prompt = f"Requirements document:\n{doc_text}"
    if site_context:
        user_prompt += f"\n\nKnown site content (for resolving descriptive requirements):\n{site_context}"

    response = model.generate_content(
        SYSTEM_PROMPT + "\n\n" + user_prompt
    )

    raw_text = response.text.strip()
    # Strip markdown code fences if Gemini adds them despite instructions
    if raw_text.startswith("```"):
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
        raw_text = raw_text.strip()

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Gemini returned invalid JSON: {e}\nRaw response: {raw_text}")

    checks = parsed.get("checks", [])
    needs_review = parsed.get("needs_review", [])
    workflows = parsed.get("workflows", [])

    spec = {
        "site": site_name,
        "base_url": base_url,
        "pages": [
            {"path": "/", "checks": checks}
        ],
        "workflows": workflows,
    }

    return spec, needs_review


def parse_requirements_doc_smart(doc_text, site_name, base_url, site_context=""):
    """
    Tries the Gemini-based parser first. If it fails for any reason
    (missing API key, network error, rate limit, bad response), falls
    back to the deterministic keyword-based parser so the user still
    gets a usable spec instead of a crash.

    Returns (spec, needs_review, parser_used) where parser_used is
    either "llm" or "keyword" so callers can inform the user which
    one actually ran.
    """
    from engine.doc_parser import parse_requirements_doc

    try:
        spec, needs_review = parse_requirements_doc_llm(
            doc_text, site_name, base_url, site_context=site_context
        )
        return spec, needs_review, "llm"
    except Exception as e:
        print(f"LLM parser failed, falling back to keyword parser: {e}")
        spec, needs_review = parse_requirements_doc(doc_text, site_name, base_url)
        return spec, needs_review, "keyword"
