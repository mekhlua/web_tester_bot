def action_goto(page, base_url, path, **kwargs):
    url = base_url.rstrip("/") + path
    page.goto(url)
    return {"passed": True, "message": f"Navigated to {url}"}


def action_fill(page, selector, value, **kwargs):
    try:
        page.fill(selector, value)
        return {"passed": True, "message": f"Filled {selector}"}
    except Exception as e:
        return {"passed": False, "message": f"Failed to fill {selector}: {e}"}


def action_click(page, selector, **kwargs):
    try:
        page.click(selector)
        return {"passed": True, "message": f"Clicked {selector}"}
    except Exception as e:
        return {"passed": False, "message": f"Failed to click {selector}: {e}"}


def action_expect_element(page, selector, timeout=5000, **kwargs):
    try:
        page.wait_for_selector(selector, timeout=timeout)
        return {"passed": True, "message": f"Element present: {selector}"}
    except Exception:
        return {"passed": False, "message": f"Element missing: {selector}"}


def action_expect_text(page, value, **kwargs):
    content = page.content()
    if value in content:
        return {"passed": True, "message": f"Text present: '{value}'"}
    return {"passed": False, "message": f"Text missing: '{value}'"}


def action_expect_url_contains(page, value, **kwargs):
    if value in page.url:
        return {"passed": True, "message": f"URL contains '{value}'"}
    return {"passed": False, "message": f"URL does not contain '{value}' (got {page.url})"}


ACTION_REGISTRY = {
    "goto": action_goto,
    "fill": action_fill,
    "click": action_click,
    "expect_element": action_expect_element,
    "expect_text": action_expect_text,
    "expect_url_contains": action_expect_url_contains,
}


def run_workflow(page, base_url, workflow):
    """
    Runs an ordered list of steps. Stops early if a step fails,
    since later steps usually depend on earlier ones succeeding.
    """
    results = []
    for step in workflow["steps"]:
        action_name = step["action"]
        action_fn = ACTION_REGISTRY.get(action_name)

        if action_fn is None:
            results.append({
                "passed": False,
                "message": f"Unknown action: {action_name}",
                "check_type": f"workflow:{action_name}",
            })
            break

        kwargs = {k: v for k, v in step.items() if k != "action"}
        try:
            result = action_fn(page, base_url=base_url, **kwargs)
        except Exception as e:
            result = {"passed": False, "message": f"Step raised an error: {e}"}

        result["check_type"] = f"workflow:{action_name}"
        results.append(result)

        if not result["passed"]:
            break

    return results
