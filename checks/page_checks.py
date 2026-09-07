import time


def page_loads(page, url, max_load_time=5.0, expected_status=200):
    """
    Navigates to `url` and checks:
    - HTTP status matches expected_status
    - Page loads within max_load_time seconds

    Returns a result dict: {"passed": bool, "message": str}
    """
    start = time.time()
    response = page.goto(url)
    load_time = time.time() - start

    if response is None:
        return {"passed": False, "message": f"No response received from {url}"}

    status = response.status

    if status != expected_status:
        return {
            "passed": False,
            "message": f"Expected status {expected_status}, got {status}"
        }

    if load_time > max_load_time:
        return {
            "passed": False,
            "message": f"Page took {load_time:.2f}s, exceeds limit of {max_load_time}s"
        }

    return {
        "passed": True,
        "message": f"Loaded in {load_time:.2f}s with status {status}"
    }
def element_exists(page, selector, timeout=5000):
    """
    Checks that at least one element matching `selector` exists on the page.
    """
    try:
        page.wait_for_selector(selector, timeout=timeout)
        return {"passed": True, "message": f"Element found: {selector}"}
    except Exception:
        return {"passed": False, "message": f"Element not found: {selector}"}

def text_present(page, text, case_sensitive=False):
    """
    Checks that `text` appears somewhere in the page's visible content.
    """
    content = page.content()
    if not case_sensitive:
        content = content.lower()
        text = text.lower()

    if text in content:
        return {"passed": True, "message": f"Text found: '{text}'"}
    return {"passed": False, "message": f"Text not found: '{text}'"}

def link_valid(page, selector="a", max_links=20):
    """
    Checks that links matching `selector` on the current page don't return
    broken (4xx/5xx) statuses. Limits how many it checks via max_links
    to avoid hammering large pages.
    """
    hrefs = page.eval_on_selector_all(
        selector, "elements => elements.map(e => e.href).filter(h => h)"
    )
    hrefs = hrefs[:max_links]

    broken = []
    for href in hrefs:
        try:
            response = page.request.get(href)
            if response.status >= 400:
                broken.append((href, response.status))
        except Exception as e:
            broken.append((href, str(e)))

    if broken:
        details = "; ".join(f"{url} -> {status}" for url, status in broken)
        return {"passed": False, "message": f"Broken links found: {details}"}

    return {"passed": True, "message": f"Checked {len(hrefs)} links, all valid"}

def no_console_errors(page):
    """
    Checks that no console.error() messages were logged.
    NOTE: this only catches errors that occur AFTER this check runs
    and the page reloads/interacts — for full coverage, register the
    listener before navigation (we'll wire this into the runner properly
    in Step 5b).
    """
    errors = []

    def handle_console(msg):
        if msg.type == "error":
            errors.append(msg.text)

    page.on("console", handle_console)
    page.reload()

    if errors:
        return {"passed": False, "message": f"Console errors: {'; '.join(errors)}"}
    return {"passed": True, "message": "No console errors detected"}